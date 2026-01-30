from setuptools import setup, find_packages

setup(
    name="reddit_market_research",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "tqdm>=4.65.0",
        "pydantic>=2.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
        "pandas>=2.0",
        "python-dateutil>=2.8",
    ],
    entry_points={
        'console_scripts': [
            'reddit-qa=qa_processing:main',
        ],
    },
)