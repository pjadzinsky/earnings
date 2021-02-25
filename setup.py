# -*- coding: utf-8 -*-
"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# with open(path.join(here, "version.txt"), encoding="utf-8") as f:
#     version = f.read().rstrip()
version = "0.0.1"

packages = find_packages()

setup(
    name="earnings",
    version=version,
    description="earnings resports",
    long_description=long_description,
    url="",
    author="Pablo Jadzinsky",
    include_package_data=True,
    packages=packages,
    extras_require={},
)
