# Global set for deduplication
crawled_links = set()

keywords = ["artificial intelligence", "existential risk"]

whitelist_urls = [
    "https://www.lesswrong.com/posts/gEchYntjSXk9KXorK/uncontrollable-ai-as-an-existential-risk",
]

whitelist_domains = ["slatestarcodex.com"]

media_domains = ["youtube.com", "facebook.com", "twitter.com", "instagram.com", "tiktok.com", "soundcloud.com", "vimeo.com", "imdb.com"]

skip_media_types = ["pdf", "svg", "png", "jpg", "jpeg", "mp3", "mp4", "aif", "wav", "ogg", "mov", "wmv", "zip", "exe", "bin"]

link_blacklist = [
    "home",
    "next",
    "about us",
    "contact",
    "log in",
    "account",
    "sign up",
    "sign in",
    "sign out",
    "privacy policy",
    "terms of service",
    "terms and conditions",
    "terms",
    "conditions",
    "privacy",
    "legal",
    "guidelines",
    "filter",
    "theme",
    "english",
    "accessibility",
    "authenticate",
    "join",
    "edition",
    "subscribe",
    "news",
    "home",
    "blog",
    "jump to",
    "español",
    "world",
    "europe",
    "politics",
    "profile",
    "election",
    "health",
    "business",
    "tech",
    "sports"
]

element_blacklist = [
    "sidebar",
    "nav",
    "footer",
    "header",
    "menu",
    "account",
    "login",
    "form",
    "search",
    "advertisement",
    "masthead",
    "popup",
    "overlay",
    "floater",
    "modal",
]