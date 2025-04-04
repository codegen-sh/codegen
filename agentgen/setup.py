#!/usr/bin/env python3
"""
Setup script for the agentgen package.
"""

from setuptools import setup, find_packages

setup(
    name="agentgen",
    version="0.1.0",
    description="Agent framework for building AI-powered applications",
    author="Codegen Team",
    author_email="team@codegen.sh",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.3.22",
        "langchain-core>=0.3.50",
        "langchain-anthropic>=0.3.10",
        "langchain-openai>=0.3.12",
        "langgraph>=0.3.25",
        "langgraph-prebuilt>=0.1.8",
        "langchain-xai>=0.2.2",
        "langsmith>=0.1.22",
        "fastapi>=0.115.8",
        "uvicorn>=0.27.0",
        "PyGithub>=2.1.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "markdown>=3.5",
        "beautifulsoup4>=4.12.2",
        "pyngrok>=7.0.0",
    ],
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)