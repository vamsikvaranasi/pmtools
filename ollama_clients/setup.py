from setuptools import setup, find_packages

setup(
    name="ollama_clients",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        'console_scripts': [
            'ollama-clients=ollama_clients.text_client:main',
            'ollama-image=ollama_clients.image_client:main',
        ],
    },
)
