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
from confluence2eml.core.css_inliner import (
    CssInliner,
    CssInlinerError,
)
from confluence2eml.core.image_processor import (
    ImageProcessor,
    ImageProcessorError,
    ImageDownloadError,
    ImageData,
)
from confluence2eml.core.markdown_processor import (
    MarkdownProcessor,
    MarkdownProcessorError,
)
from confluence2eml.core.mime_generator import (
    MimeGenerator,
    MimeGeneratorError,
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

