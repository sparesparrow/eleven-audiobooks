from setuptools import setup, find_packages

setup(
    name="eleven-audiobooks",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "httpx",
        "pymongo",
        "python-dotenv",
        "elevenlabs",
        "deep-translator",
        "pypdf2",
        "requests",
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
        "pytest-cov",
        "pyyaml"
    ],
)
