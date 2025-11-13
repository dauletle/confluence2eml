"""Utility functions for confluence2eml.

This module provides utility functions for filename sanitization,
file operations, and other helper functions.
"""

import re
from pathlib import Path
from typing import Optional


def sanitize_filename(title: str, max_length: int = 200) -> str:
    """Sanitize a page title to create a valid filename.
    
    This function:
    - Removes or replaces invalid filesystem characters
    - Truncates to a reasonable length
    - Handles special cases (empty strings, only invalid chars, etc.)
    - Preserves Unicode characters that are valid in filenames
    
    Args:
        title: The page title to sanitize
        max_length: Maximum length for the filename (default: 200)
        
    Returns:
        Sanitized filename (without extension)
        
    Examples:
        >>> sanitize_filename("My Page Title")
        'My Page Title'
        >>> sanitize_filename("Page: With/Invalid\\Chars?")
        'Page With Invalid Chars'
        >>> sanitize_filename("")
        'untitled'
    """
    if not title or not title.strip():
        return "untitled"
    
    # Remove leading/trailing whitespace
    filename = title.strip()
    
    # Replace invalid filesystem characters with spaces or hyphens
    # Invalid characters: < > : " / \ | ? *
    # Also remove control characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, ' ', filename)
    
    # Replace multiple spaces/hyphens with single space
    filename = re.sub(r'[\s\-]+', ' ', filename)
    
    # Remove leading/trailing spaces and dots (Windows doesn't allow trailing dots)
    filename = filename.strip(' .')
    
    # Truncate to max_length
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip()
    
    # If after sanitization we have an empty string, use default
    if not filename:
        return "untitled"
    
    return filename


def generate_markdown_filename(page_title: str, output_dir: Optional[Path] = None) -> Path:
    """Generate a full path for the Markdown file based on page title.
    
    Args:
        page_title: The Confluence page title
        output_dir: Optional directory for the output file.
                   If None, uses current directory.
        
    Returns:
        Path object for the Markdown file
        
    Examples:
        >>> generate_markdown_filename("My Page Title")
        Path('My Page Title.md')
        >>> generate_markdown_filename("Page: With/Invalid\\Chars?", Path('/output'))
        Path('/output/Page With Invalid Chars.md')
    """
    # Sanitize the title
    sanitized = sanitize_filename(page_title)
    
    # Add .md extension
    filename = f"{sanitized}.md"
    
    # Combine with output directory if provided
    if output_dir:
        return output_dir / filename
    else:
        return Path(filename)


def save_markdown_file(content: str, filepath: Path) -> Path:
    """Save Markdown content to a file.
    
    Args:
        content: Markdown content to save
        filepath: Path where the file should be saved
        
    Returns:
        Path to the saved file
        
    Raises:
        OSError: If the file cannot be written
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the content
    filepath.write_text(content, encoding='utf-8')
    
    return filepath

