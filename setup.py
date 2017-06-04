#!/usr/bin/python3

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="skilltest",
    version="1.0.0",
    description="Alexa Skill Tester",
    long_description=long_description,
    url="https://github.com/lllucius/skilltest",
    author="Leland Lucius",
    author_email="skilltest@homerow.net",
    license="AGPLv3+",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Testing",
    ],
    keywords="alexa automated testing",
    py_modules=["skilltest"],
    install_requires=["bs4",
                      "numpy",
                      "requests",
                      "requests_toolbelt",
                      "samplerate",
                      "soundfile"],
    entry_points={
        "console_scripts": [
            "skilltest=skilltest:main",
        ],
    },
)

