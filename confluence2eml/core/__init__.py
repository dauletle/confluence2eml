"""Core modules for confluence2eml.

This package contains the core functionality modules:
- client: Confluence API client wrapper
- utils: Utility functions for file operations
- markdown_processor: Markdown to HTML conversion
- html_processor: HTML sanitization and email compatibility
- css_inliner: CSS inlining for email compatibility
- image_processor: Image processing and CID embedding for email
- mime_generator: MIME message generation and EML file creation
"""

from .client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
)
from .html_processor import (
    HtmlProcessor,
    HtmlProcessorError,
)
from .css_inliner import (
    CssInliner,
    CssInlinerError,
)
from .image_processor import (
    ImageProcessor,
    ImageProcessorError,
    ImageDownloadError,
    ImageData,
)
from .markdown_processor import (
    MarkdownProcessor,
    MarkdownProcessorError,
)
from .mime_generator import (
    MimeGenerator,
    MimeGeneratorError,
)
from .utils import (
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
    'CssInliner',
    'CssInlinerError',
    'ImageProcessor',
    'ImageProcessorError',
    'ImageDownloadError',
    'ImageData',
    'MarkdownProcessor',
    'MarkdownProcessorError',
    'MimeGenerator',
    'MimeGeneratorError',
    'sanitize_filename',
    'generate_markdown_filename',
    'save_markdown_file',
]

