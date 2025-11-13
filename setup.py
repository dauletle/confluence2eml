"""Setup configuration for confluence2eml package."""

from setuptools import setup, find_packages

# Read dependencies from pyproject.toml approach
# For compatibility, we'll define them here as well
INSTALL_REQUIRES = [
    "confluence-markdown-exporter>=0.1.0",
    "markdown>=3.4.0",
    "beautifulsoup4>=4.12.0",
    "premailer>=3.10.0",
    "requests>=2.31.0",
]

DEV_REQUIRES = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
]

setup(
    name="confluence2eml",
    version="0.1.0",
    description="Convert Atlassian Confluence pages to self-contained Microsoft Outlook email files (.EML format)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Confluence2EML Contributors",
    license="MIT",
    python_requires=">=3.7",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
    },
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "confluence2eml=confluence2eml:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

