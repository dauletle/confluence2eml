"""Core modules for confluence2eml.

This package contains the core functionality modules:
- client: Confluence API client wrapper
- utils: Utility functions for file operations
"""

from confluence2eml.core.client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
)
from confluence2eml.core.utils import (
    sanitize_filename,
    generate_markdown_filename,
    save_markdown_file,
)

__all__ = [
    'ConfluenceClient',
    'ConfluenceClientError',
    'ConfluenceAuthenticationError',
    'ConfluencePageNotFoundError',
    'URLResolver',
    'sanitize_filename',
    'generate_markdown_filename',
    'save_markdown_file',
]

