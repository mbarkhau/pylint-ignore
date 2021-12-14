# This file is part of the pylint-ignore project
# https://github.com/mbarkhau/pylint-ignore
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fh:
        return fh.read().decode("utf-8")


install_requires = [
    line.strip()
    for line in read("requirements", "pypi.txt").splitlines()
    if line.strip() and not line.startswith("#") and not line.startswith("-")
]


long_description = "\n\n".join((read("README.md"), read("CHANGELOG.md")))


# See https://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Environment :: Other Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Unix",
    "Operating System :: POSIX",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
]


setuptools.setup(
    name="pylint-ignore",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://github.com/mbarkhau/pylint-ignore",
    version="2021.1023",
    keywords="pylint ignore noise flake8 pep8 linter",
    description="Start with silence, not with noise. But do start!",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages("src/"),
    package_dir={"": "src"},
    install_requires=install_requires,
    python_requires=">=3.7",
    zip_safe=True,
    classifiers=classifiers,

    entry_points={
        'console_scripts': [
            "pylint-ignore = pylint_ignore.__main__:main"
        ],
    }
)
