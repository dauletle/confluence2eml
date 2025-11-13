"""Core modules for confluence2eml.

This package contains the core functionality modules:
- client: Confluence API client wrapper
- utils: Utility functions for file operations
- markdown_processor: Markdown to HTML conversion
- html_processor: HTML sanitization and email compatibility
"""

from confluence2eml.core.client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
)
from confluence2eml.core.html_processor import (
    HtmlProcessor,
    HtmlProcessorError,
)
from confluence2eml.core.markdown_processor import (
    MarkdownProcessor,
    MarkdownProcessorError,
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
    'HtmlProcessor',
    'HtmlProcessorError',
    'MarkdownProcessor',
    'MarkdownProcessorError',
    'sanitize_filename',
    'generate_markdown_filename',
    'save_markdown_file',
]

