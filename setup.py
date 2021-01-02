import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

# Get the version from __init__.py
# This solution was taken from biopython, which is licensed under the
# Biopython License Agreement
# https://biopython.org
__version__ = "Undefined"
with open("swampymud/__init__.py") as mod_init:
    for line in mod_init:
        if line.startswith("__version__"):
            exec(line)

setuptools.setup(
    name="swampymud",
    author="The UF Open Source Club",
    author_email="will@ovvens.com",
    description="Create multi-user dungeons (MUDs) and RPGs with telnet / WebSockets.",
    url="https://swampymud.net",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(), # Should we include tests/ ?
    install_requires=[
        "websockets",
        "PyYaml"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
        "Intended Audience :: Developers",
        "Intended Audience :: Education"
    ],
    python_requires=">=3.6",
    version=__version__
)
