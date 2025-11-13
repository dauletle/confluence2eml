"""Confluence to EML Exporter Package.

A Python utility that converts Atlassian Confluence pages into
self-contained Microsoft Outlook email files (.EML format).
"""

__version__ = "0.1.0"

# Import main components for easy access
from confluence2eml.core import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
    MarkdownProcessor,
    MarkdownProcessorError,
    sanitize_filename,
    generate_markdown_filename,
    save_markdown_file,
)

# Import main function for CLI entry point
from confluence2eml.main import main

__all__ = [
    'ConfluenceClient',
    'ConfluenceClientError',
    'ConfluenceAuthenticationError',
    'ConfluencePageNotFoundError',
    'URLResolver',
    'MarkdownProcessor',
    'MarkdownProcessorError',
    'sanitize_filename',
    'generate_markdown_filename',
    'save_markdown_file',
    'main',
]
