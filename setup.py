#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="molsaic",
    version="0.2.0",
    author="Molecular Simulation Laboratory",
    author_email="molsaic-dev@example.org",
    description="MolSAIC (Molecular Structure Analysis and Integration Console) - Comprehensive molecular toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/molsim-lab/molsaic",
    project_urls={
        "Bug Tracker": "https://github.com/molsim-lab/molsaic/issues",
        "Documentation": "https://github.com/molsim-lab/molsaic/docs",
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
            "molsaic=molsaic.cli:main",
        ],
    },
    include_package_data=True,
)
