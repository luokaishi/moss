#!/usr/bin/env python3
"""
MOSS v9.6.0 - Setup Script
"""

from setuptools import setup, find_packages

setup(
    name="moss-refactor",
    version="9.6.0",
    description="MOSS - Multi-Objective Self-Driven System for Intelligent Code Refactoring",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="MOSS DevTools",
    author_email="support@moss-devtools.com",
    url="https://github.com/moss-devtools/moss",
    packages=find_packages(exclude=["tests", "experiments", "docs-site"]),
    package_data={
        "moss": ["py.typed"],
    },
    install_requires=[
        "networkx>=2.8",
    ],
    extras_require={
        "ml": ["numpy>=1.21"],
        "local-llm": ["torch>=2.0", "transformers>=4.30"],
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "docs": [
            "mkdocs>=1.4",
            "mkdocs-material>=9.0",
            "mkdocstrings[python]>=0.20",
        ],
    },
    entry_points={
        "console_scripts": [
            "moss=moss.cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="refactoring code-analysis python IDE LSP ML",
    license="MIT",
    zip_safe=False,
)
