import csv
import sys

import PyPDF2
from dotenv import load_dotenv
from fuzzysearch import find_near_matches

from topics import format_topics, search_topics

load_dotenv()

from easycompletion import (
    openai_function_call,
    compose_prompt,
    compose_function,
    chunk_prompt,
)

from agentbrowser import navigate_to, get_body_text, create_page


def get_content_from_url(url):
    page = create_page()

    navigate_to(url, page)

    body_text = get_body_text(page)

    return body_text


def get_content_from_pdf(input_file):
    with open(input_file, "rb") as f:
        try:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for i in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[i].extract_text()
            return text
        except PyPDF2.utils.PdfReadError:
            print("Failed to read PDF file.")
            sys.exit()


def get_content_from_txt(input_file):
    with open(input_file, "r") as f:
        text = f.read()
        return text


def get_content_from_file(input_file):
    if input_file.startswith("http"):
        text = get_content_from_url(input_file)
        return text
    else:
        if input_file.endswith(".pdf"):
            return get_content_from_pdf(input_file)
        elif input_file.endswith(".txt"):
            return get_content_from_txt(input_file)
        else:
            print("Invalid input file format. Please provide a URL or a PDF file.")
            sys.exit()


# rewrittten with compose_function
summarization_function = compose_function(
    name="summarize_text",
    description="Summarize the text. Include the topic, subtopics.",
    properties={
        "summary": {
            "type": "string",
            "description": "Detailed summary of the text.",
        },
        "topic": {
            "type": "string",
            "description": "Primary, broad topic.",
        },
        "subtopic": {
            "type": "string",
            "description": "Specific subtopic.",
        },
        "explanation": {
            "type": "string",
            "description": "Explanation of why the text is or isn't relevant to my goal topics.",
        },
        "relevant": {
            "type": "boolean",
            "description": "Is the text relevant to my goal topics?",
        },
    },
    required_property_names=["summary"],
)

summarization_prompt_template = """
I have the following document
```
{{text}}
```

I am a researcher with the following goal:
{{goal}}

Please do the following:
- Determine if the topic is relevant to the goal topics
- Determine the closest topic and subtopic from the provided list
- Summarize the document
- Explain why the document is relevant to the goal topics
Please summarize the document, classify the topic and subtopic, determine if the document is relevant to my goal topics and explain why it is or isn't relevant."
"""

claim_extraction_prompt_template = """\
I am a researcher with the following goal:
{{goal}}

My list of topics and subtopics:
{{topics}}

Summary of the full document:
{{summary}}

Current section of the document I am working on:
{{text}}

TASK: Extract claims from the currect section I am working on.

- Include the specific passage of source text that the claim references as the source parameter.
- Please extract the specific and distinct claims from this text, and respond with all factual claims as a JSON array. Avoid duplicate claims.
- Each claim should be one statement. Ignore questions, section headers, fiction, feelings and rhetoric: they are not factual claims.
- DO NOT just of use pronouns or shorthand like 'he' or 'they' in claims. Use the actual complete name of the person or thing you are referring to and be very detailed and specific.
- Claims should include extensive detail so that they can stand alone without the source text. This includes detailed descriptions of who, what and when.
- ALWAYS use the full name and title of people along with any relationship to organizations. For example, instead of 'the president', use 'Current U.S. President Joe Biden'. Do not use nicknames or short names when referring to people. Instead of "Mayor Pete", use "Pete Buttigieg".
- Ignore anything that isn't relevant to the topics and goal, including political opinions, feelings, and rhetoric. We are only interested in claims that are factual, i.e. can be proven or disproven.
- Please disambiguate and fully describe known entities. For example, instead of 'Kim the Rocketman', use 'North Korean leader Kim Jong Un'. Instead of 'the 2016 election', use 'the 2016 U.S. presidential election'.
- Split claims up into specific statements, even if the source text has combined the claims into a single statement. There can be multiple claims for a source. For example, if a source sentence makes multiple claims, these should be separated
- Write a debate question which the claim would be most relevant to. Ideally the question is one which the claim directly answers or at least in which the claim is foundational to another claim.

Output should be formatted as an array of claims, which each have the following structure:
[{
    source: string # "The exact source text referenced in the claim",
    claim: string # "The factual claim being made in the source text",
    relevant: boolean # Is the claim relevant to the goal topics and summary?
    debate_question: string # A debate question which the claim is relevant to or which the claim directly answers.
    topic: string # The most appropriate topic from the topic list
    subtopic: string # The most appropriate subtopic from the subtopic list, given the topic
}, {...}]
"""

claim_extraction_function = compose_function(
    name="extract_claims",
    description="Extract all factual claims from the section of text. From the list of topics and subtopics, choose the most appropriate one for each claim. If the claim is not relevant to the goal topics, set 'relevant' to False, if it is relevant set it to True. Also include a debate question which the claim would be most relevant to.",
    properties={
        "claims": {
            "type": "array",
            "description": "Array of claims extracted from the current section of the source text",
            "items": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "The exact source text from which the claim has been extracted",
                    },
                    "claim": {
                        "type": "string",
                        "description": "A factual claim made in the source text",
                    },
                    "relevant": {
                        "type": "boolean",
                        "description": "Determine whether this claim is relevant to the goal topics. If it is not relevant, set this to False, otherwise set it to True.",
                    },
                    "debate_question": {
                        "type": "string",
                        "description": "A debate question which the claim is relevant to. Ideally the question is one which the claim directly answers or at least in which the claim is foundational to another claim.",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic. For example, 'AI Training and Deployment'.",
                    },
                    "subtopic": {
                        "type": "string",
                        "description": "The subtopic. For example, 'New Definitions of Benefits'.",
                    },
                },
            },
        }
    },
    required_property_names=["claims"],
)


def summarize_text(text):
    summarization_prompt = compose_prompt(
        summarization_prompt_template,
        {
            "text": text,
        },
    )

    response = openai_function_call(
        text=summarization_prompt,
        functions=[summarization_function],
        function_call="summarize_text",
    )

    return response["arguments"]["summary"]


def validate_claims(claims):
    # check to make sure that arguments has source, claim, relevant, debate_question, topic, subtopic
    # if the keys are missing, return false
    print("***** VALIDATING ARGUMENTS")
    print(claims)
    for claim in claims:
        for key in [
            "source",
            "claim",
            "relevant",
            "debate_question",
            "topic",
            "subtopic",
        ]:
            if key not in claim:
                print("Missing key", key)
                return False


def validate_claim(claim, document):
    claim_source = claim["source"]
    if claim_source is None or claim_source == "":
        print("Claim is empty")
        return False

    matches = find_near_matches(claim_source, document, max_l_dist=6)

    if len(matches) == 0:
        print("Claim source not found in document")
        return False
    else:
        print("Claim source found in document")

    return True


def extract_from_chunk(text, document_summary, goal, topics):
    arguments = None
    max_tries = 3
    tries = 0
    while arguments is None and tries < max_tries:
        tries += 1
        text_prompt = compose_prompt(
            claim_extraction_prompt_template,
            {
                "goal": goal,
                "summary": document_summary,
                "topics": topics,
                "text": text,
            },
        )

        response = openai_function_call(
            text=text_prompt,
            functions=[claim_extraction_function],
            function_call={"name": "extract_claims"},
        )

        if response["arguments"] is None:
            continue

        if response["arguments"]["claims"] is None:
            print("No claims")
            continue

        if validate_claims(response["arguments"]["claims"]) is False:
            print("Invalid arguments")
            continue

        arguments = response["arguments"]
        break

    if arguments is None:
        print("Couldn't extract claims")
        arguments = {"claims": []}

    return arguments["claims"]


def extract_from_file_or_url(input_file_or_url, output_file, goal, summary=None):
    text = get_content_from_file(input_file_or_url)
    return extract(input_file_or_url, text, output_file, goal, summary)


def extract(source, text, output_file, goal, summary=None):
    text_chunks = chunk_prompt(text)

    if summary is None:
        text_chunks_long = chunk_prompt(text, 10000)
        summary = summarize_text(text_chunks_long[0])
        # make sure summary is not too long, shouldn't be more than 1200 characters
        if len(summary) > 1200:
            summary = summary[:1200]

    topics = format_topics(search_topics(summary))
    print("Topics", topics)

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Input",
                "Source",
                "Claim",
                "Relevant",
                "In Source Text",
                "Topic",
                "Subtopic",
                "Debate Question",
            ]
        )

    for i, text_chunk in enumerate(text_chunks):
        claims = extract_from_chunk(text_chunk, summary, goal, topics)
        for k in range(len(claims)):
            claim = claims[k]
            if claim is None:
                continue
            claim_is_valid = validate_claim(claim, text_chunk)
            with open(output_file, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        source,
                        claim["source"],
                        claim["claim"],
                        claim["relevant"],
                        claim_is_valid,
                        claim["topic"],
                        claim["subtopic"],
                        claim["debate_question"],
                    ]
                )
