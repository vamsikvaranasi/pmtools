"""
QA Processor Plus Setup

Setup configuration for the QA Processor Plus system.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Use global README.md from parent directory
readme_path = Path(__file__).parent.parent / "README.md"
with open(readme_path, "r") as fh:
    long_description = fh.read()

# Use global requirements.txt from parent directory
requirements_path = Path(__file__).parent.parent / "requirements.txt"
with open(requirements_path, "r") as f:
    requirements = f.read().splitlines()

setup(
    name="qa_processor_plus",
    version="1.0.0",
    author="PM Tools Team",
    author_email="team@pmtools.com",
    description="Advanced QA processing system for product management insights",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pmtools/qa_processor_plus",
    packages=find_packages(),
    package_data={
        "qa_processor_plus": [
            "prompts/*.jinja2",
            "plugins/*.py",
            "config.yaml"
        ]
    },
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="qa processing nlp clustering embeddings insights",
    project_urls={
        "Bug Reports": "https://github.com/pmtools/qa_processor_plus/issues",
        "Source": "https://github.com/pmtools/qa_processor_plus",
    },
    entry_points={
        "console_scripts": [
            "qa_processor=qa_processor_plus.__main__:main",
        ],
    },
    zip_safe=False,
)