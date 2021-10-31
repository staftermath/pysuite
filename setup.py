#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from setuptools import setup, find_packages

here = Path(__file__).resolve().parent

def get_version():
    init_file = here / "pysuite" / "__init__.py"
    with open(init_file, 'r') as f:
        for l in f.readlines():
            if l.startswith("__version__"):
                version = eval(l.strip().split(" ")[-1])
                return version

    raise RuntimeError("version not found")

NAME = 'pysuite'
DESCRIPTION = "A data scientist's toolbox for Google Suite Apps"
URL = 'https://staftermath.github.io/pysuite/index.html'
EMAIL = 'gwengww@gmail.com'
AUTHOR = 'Weiwen Gu'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = get_version()

REQUIRED = [
    "google-api-python-client>=1.7.8",
    "google-api-core>=1.31.1",
    "google-auth>=1.20.1",
    "pyparsing>=2.4.7, <3.0.0",
    "google-auth-httplib2>=0.0.4",
    "google-auth-oauthlib>=0.4.1",
    "googleapis-common-protos>=1.6",
    "google-cloud-vision>=2.4.2",
    "google-cloud-storage>=1.42.3"
]

try:
    with open(here / 'README.md', encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

about = {'__version__': VERSION}

setup(
    name=NAME,
    version=about['__version__'],
    license='bsd-3-clause',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    download_url = f'https://github.com/staftermath/pysuite/archive/{VERSION}.tar.gz',
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=REQUIRED,
    include_package_data=True,
)