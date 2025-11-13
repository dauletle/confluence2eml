"""Utility functions for confluence2eml.

This module provides utility functions for filename sanitization,
file operations, CSS loading, and other helper functions.
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


def load_email_css() -> str:
    """Load the email-friendly CSS stylesheet.
    
    This function loads the CSS file from the package resources directory.
    The CSS is designed for email client compatibility and will be inlined
    by premailer in the next phase.
    
    Returns:
        CSS content as a string
        
    Raises:
        OSError: If the CSS file cannot be read
        FileNotFoundError: If the CSS file does not exist
        
    Example:
        >>> css = load_email_css()
        >>> assert 'body {' in css
        >>> assert 'h1 {' in css
    """
    # Get the path to the CSS file relative to this module
    css_path = Path(__file__).parent / 'resources' / 'email_styles.css'
    
    if not css_path.exists():
        raise FileNotFoundError(
            f"Email CSS stylesheet not found at: {css_path}"
        )
    
    return css_path.read_text(encoding='utf-8')


def wrap_html_with_css(html_content: str, css_content: Optional[str] = None) -> str:
    """Wrap HTML content with a CSS stylesheet in a <style> tag.
    
    This function wraps the provided HTML content with a complete HTML document
    structure including a <style> tag containing the email-friendly CSS.
    The CSS will be inlined by premailer in the next phase.
    
    Args:
        html_content: HTML content to wrap (can be partial HTML or full document)
        css_content: Optional CSS content. If not provided, loads the default
                    email CSS stylesheet.
        
    Returns:
        Complete HTML document with CSS stylesheet in <style> tag
        
    Raises:
        OSError: If the CSS file cannot be read (when css_content is None)
        FileNotFoundError: If the CSS file does not exist (when css_content is None)
        
    Example:
        >>> html = "<h1>Hello</h1><p>World</p>"
        >>> wrapped = wrap_html_with_css(html)
        >>> assert '<style>' in wrapped
        >>> assert '<html>' in wrapped
        >>> assert '<body>' in wrapped
    """
    # Load CSS if not provided
    if css_content is None:
        css_content = load_email_css()
    
    # Check if HTML already has a complete structure
    html_lower = html_content.lower().strip()
    has_html_tag = '<html' in html_lower
    has_body_tag = '<body' in html_lower
    has_head_tag = '<head' in html_lower
    
    if has_html_tag and has_body_tag and has_head_tag:
        # HTML already has complete structure, just add style tag to head
        # Try to find head tag and insert style before closing head
        # Look for </head> tag
        if re.search(r'</head>', html_content, re.IGNORECASE):
            # Insert style before closing head tag
            style_tag = f'<style type="text/css">\n{css_content}\n</style>'
            html_content = re.sub(
                r'(</head>)',
                f'{style_tag}\n\\1',
                html_content,
                flags=re.IGNORECASE
            )
            return html_content
        else:
            # Has head tag but no closing tag, append style
            style_tag = f'<style type="text/css">\n{css_content}\n</style>'
            # Try to insert before </head> or append to head
            if re.search(r'<head[^>]*>', html_content, re.IGNORECASE):
                html_content = re.sub(
                    r'(<head[^>]*>)',
                    f'\\1\n{style_tag}',
                    html_content,
                    flags=re.IGNORECASE
                )
                return html_content
    
    # If HTML has body tag but no html/head structure, wrap it
    if has_body_tag and not has_html_tag:
        # Extract body content
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.IGNORECASE | re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
        else:
            # Body tag without closing, extract everything after <body>
            body_match = re.search(r'<body[^>]*>(.*)', html_content, re.IGNORECASE | re.DOTALL)
            body_content = body_match.group(1) if body_match else html_content
    else:
        # No body tag, treat entire content as body
        body_content = html_content
    
    # Create complete HTML document
    wrapped_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style type="text/css">
{css_content}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""
    
    return wrapped_html

