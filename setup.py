from setuptools import setup

long_description = ""
with open("README.md", "r") as fh:
    long_description = fh.read()
    # search for any lines that contain <img and remove them
    long_description = long_description.split('\n')
    long_description = [line for line in long_description if not '<img' in line]
    # now join all the lines back together
    long_description = '\n'.join(long_description)
    

setup(
    name='researchassistant',
    version='0.1.8',
    description="Find what you're looking for",
    long_description=long_description,  # added this line
    long_description_content_type="text/markdown",  # and this line
    url='https://github.com/lalalune/researchassistant',
    author='Moon',
    author_email='shawmakesmagic@gmail.com',
    license='MIT',
    packages=['researchassistant'],
    install_requires=['agentmemory', 'easycompletion'],
    readme = "README.md",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
)
