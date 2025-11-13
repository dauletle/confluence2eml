"""Markdown to HTML conversion processor.

This module provides functionality to convert Markdown content to HTML
for email generation. It uses the markdown library with extensions to
handle tables, code blocks, and other advanced Markdown features.
"""

import logging
from typing import Optional

try:
    import markdown
    from markdown.extensions import tables, fenced_code, codehilite
except ImportError:
    markdown = None  # type: ignore
    tables = None
    fenced_code = None
    codehilite = None

logger = logging.getLogger(__name__)


class MarkdownProcessorError(Exception):
    """Base exception for MarkdownProcessor errors."""
    pass


class MarkdownProcessor:
    """Processor for converting Markdown content to HTML.
    
    This class handles the conversion of Markdown content (extracted from
    Confluence pages) to HTML format suitable for email generation. It
    uses the markdown library with extensions to support:
    - Tables
    - Fenced code blocks
    - Syntax highlighting (codehilite)
    
    Example:
        >>> processor = MarkdownProcessor()
        >>> html = processor.convert("# Hello World\\n\\nThis is **bold** text.")
        >>> print(html)
        '<h1>Hello World</h1>\\n<p>This is <strong>bold</strong> text.</p>'
    """
    
    def __init__(
        self,
        extensions: Optional[list] = None,
        extension_configs: Optional[dict] = None
    ):
        """Initialize the MarkdownProcessor.
        
        Args:
            extensions: List of markdown extensions to use.
                       Defaults to ['tables', 'fenced_code', 'codehilite']
            extension_configs: Configuration dictionary for extensions.
                             Keys are extension names, values are config dicts.
                             
        Raises:
            MarkdownProcessorError: If markdown library is not installed
        """
        if markdown is None:
            raise MarkdownProcessorError(
                "markdown library is not installed. "
                "Please install it with: pip install markdown"
            )
        
        # Default extensions for email-friendly HTML
        self.extensions = extensions or ['tables', 'fenced_code', 'codehilite']
        
        # Default extension configurations
        default_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,  # Don't require pygments for basic highlighting
            }
        }
        
        # Merge user-provided configs with defaults (deep merge for nested dicts)
        if extension_configs:
            for key, value in extension_configs.items():
                if key in default_configs and isinstance(default_configs[key], dict) and isinstance(value, dict):
                    # Deep merge nested dictionaries
                    default_configs[key] = {**default_configs[key], **value}
                else:
                    # Replace or add new config
                    default_configs[key] = value
        
        self.extension_configs = default_configs
        
        logger.debug(
            f"MarkdownProcessor initialized with extensions: {self.extensions}"
        )
    
    def convert(self, markdown_content: str) -> str:
        """Convert Markdown content to HTML.
        
        Args:
            markdown_content: Markdown content as a string
            
        Returns:
            HTML content as a string
            
        Raises:
            MarkdownProcessorError: If conversion fails
            
        Example:
            >>> processor = MarkdownProcessor()
            >>> html = processor.convert("# Title\\n\\nParagraph text.")
            >>> assert "<h1>Title</h1>" in html
            >>> assert "<p>Paragraph text.</p>" in html
        """
        if not isinstance(markdown_content, str):
            raise MarkdownProcessorError(
                f"markdown_content must be a string, got {type(markdown_content)}"
            )
        
        try:
            logger.debug("Converting Markdown to HTML...")
            logger.debug(f"Input length: {len(markdown_content)} characters")
            
            # Convert Markdown to HTML using configured extensions
            html_content = markdown.markdown(
                markdown_content,
                extensions=self.extensions,
                extension_configs=self.extension_configs
            )
            
            logger.debug(f"Conversion complete. Output length: {len(html_content)} characters")
            
            return html_content
            
        except Exception as e:
            error_msg = f"Failed to convert Markdown to HTML: {e}"
            logger.error(error_msg, exc_info=True)
            raise MarkdownProcessorError(error_msg) from e
    
    def convert_file(self, markdown_file_path: str, encoding: str = 'utf-8') -> str:
        """Convert a Markdown file to HTML.
        
        Args:
            markdown_file_path: Path to the Markdown file
            encoding: File encoding (default: 'utf-8')
            
        Returns:
            HTML content as a string
            
        Raises:
            MarkdownProcessorError: If file cannot be read or conversion fails
        """
        from pathlib import Path
        
        try:
            file_path = Path(markdown_file_path)
            if not file_path.exists():
                raise MarkdownProcessorError(
                    f"Markdown file not found: {markdown_file_path}"
                )
            
            logger.debug(f"Reading Markdown file: {markdown_file_path}")
            markdown_content = file_path.read_text(encoding=encoding)
            
            return self.convert(markdown_content)
            
        except MarkdownProcessorError:
            raise
        except Exception as e:
            error_msg = f"Failed to read or convert Markdown file: {e}"
            logger.error(error_msg, exc_info=True)
            raise MarkdownProcessorError(error_msg) from e

