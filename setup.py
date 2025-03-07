#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="monet",
    version="0.2.0",
    author="Molecular Simulation Laboratory",
    author_email="monet-dev@example.org",
    description="MONET (MOlecular NEtwork Toolkit) - Comprehensive molecular toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/molsim-lab/monet",
    project_urls={
        "Bug Tracker": "https://github.com/molsim-lab/monet/issues",
        "Documentation": "https://github.com/molsim-lab/monet/docs",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "monet=monet.cli:main",
        ],
    },
    include_package_data=True,
)
