"""Setup configuration for confluence2eml package."""

from setuptools import setup, find_packages

# Core dependencies required to run the application
# Note: These should match the dependencies in pyproject.toml and requirements.txt
INSTALL_REQUIRES = [
    # Confluence API client and content extraction
    "confluence-markdown-exporter>=0.1.0",
    # Markdown to HTML conversion
    "markdown>=3.4.0",
    # HTML parsing and sanitization
    "beautifulsoup4>=4.12.0",
    # CSS inlining for email client compatibility
    "premailer>=3.10.0",
    # HTTP client for downloading images and attachments
    # (Required for future image embedding and attachment processing features)
    "requests>=2.31.0",
]

# Development dependencies (optional)
# Install with: pip install -e ".[dev]"
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
            "confluence2eml=confluence2eml.main:main",
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

