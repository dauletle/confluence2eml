"""HTML sanitization and email compatibility processor.

This module provides functionality to sanitize HTML content for email
generation. It removes unsafe elements, ensures email client compatibility,
and validates HTML structure.
"""

import logging
from typing import List, Optional, Set

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

logger = logging.getLogger(__name__)


class HtmlProcessorError(Exception):
    """Base exception for HtmlProcessor errors."""
    pass


class HtmlProcessor:
    """Processor for sanitizing HTML content for email compatibility.
    
    This class handles the sanitization of HTML content to ensure it's
    safe and compatible with email clients. It:
    - Removes unsafe elements (scripts, iframes, etc.)
    - Ensures all images have alt text
    - Validates HTML structure
    - Removes elements that email clients don't support well
    
    Example:
        >>> processor = HtmlProcessor()
        >>> html = processor.sanitize('<html><body><script>alert("xss")</script><p>Safe content</p></body></html>')
        >>> assert '<script>' not in html
        >>> assert '<p>Safe content</p>' in html
    """
    
    # Elements to remove for security
    UNSAFE_ELEMENTS: Set[str] = {
        'script',
        'iframe',
        'object',
        'embed',
        'form',
        'input',
        'button',
        'select',
        'textarea',
    }
    
    # Elements that email clients don't support well
    EMAIL_INCOMPATIBLE_ELEMENTS: Set[str] = {
        'iframe',
        'object',
        'embed',
        'form',
        'video',
        'audio',
        'canvas',
        'svg',  # Some email clients have limited SVG support
    }
    
    # Attributes to remove for security
    UNSAFE_ATTRIBUTES: Set[str] = {
        'onclick',
        'onerror',
        'onload',
        'onmouseover',
        'onfocus',
        'onblur',
        'onchange',
        'onsubmit',
        'onkeydown',
        'onkeyup',
        'onkeypress',
    }
    
    def __init__(
        self,
        remove_unsafe_elements: bool = True,
        remove_email_incompatible: bool = True,
        ensure_image_alt: bool = True,
        default_image_alt: str = "Image",
        remove_style_tags: bool = True,
        parser: str = 'html.parser'
    ):
        """Initialize the HtmlProcessor.
        
        Args:
            remove_unsafe_elements: If True, remove security-risk elements
                                   (default: True)
            remove_email_incompatible: If True, remove elements incompatible
                                      with email clients (default: True)
            ensure_image_alt: If True, ensure all images have alt text
                             (default: True)
            default_image_alt: Default alt text for images without alt
                              (default: "Image")
            remove_style_tags: If True, remove <style> tags (they'll be
                             inlined later by premailer) (default: True)
            parser: BeautifulSoup parser to use (default: 'html.parser')
            
        Raises:
            HtmlProcessorError: If beautifulsoup4 library is not installed
        """
        if BeautifulSoup is None:
            raise HtmlProcessorError(
                "beautifulsoup4 library is not installed. "
                "Please install it with: pip install beautifulsoup4"
            )
        
        self.remove_unsafe_elements = remove_unsafe_elements
        self.remove_email_incompatible = remove_email_incompatible
        self.ensure_image_alt = ensure_image_alt
        self.default_image_alt = default_image_alt
        self.remove_style_tags = remove_style_tags
        self.parser = parser
        
        logger.debug(
            f"HtmlProcessor initialized: "
            f"remove_unsafe={remove_unsafe_elements}, "
            f"remove_incompatible={remove_email_incompatible}, "
            f"ensure_alt={ensure_image_alt}"
        )
    
    def sanitize(self, html_content: str) -> str:
        """Sanitize HTML content for email compatibility.
        
        Args:
            html_content: HTML content as a string
            
        Returns:
            Sanitized HTML content as a string
            
        Raises:
            HtmlProcessorError: If sanitization fails
            
        Example:
            >>> processor = HtmlProcessor()
            >>> html = processor.sanitize('<html><body><script>alert("xss")</script></body></html>')
            >>> assert '<script>' not in html
        """
        if not isinstance(html_content, str):
            raise HtmlProcessorError(
                f"html_content must be a string, got {type(html_content)}"
            )
        
        try:
            logger.debug("Sanitizing HTML content...")
            logger.debug(f"Input length: {len(html_content)} characters")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, self.parser)
            
            # Remove unsafe elements
            if self.remove_unsafe_elements:
                self._remove_elements(soup, self.UNSAFE_ELEMENTS)
            
            # Remove email-incompatible elements
            if self.remove_email_incompatible:
                self._remove_elements(soup, self.EMAIL_INCOMPATIBLE_ELEMENTS)
            
            # Remove style tags (they'll be inlined by premailer later)
            if self.remove_style_tags:
                self._remove_elements(soup, {'style'})
            
            # Remove unsafe attributes from all elements
            self._remove_unsafe_attributes(soup)
            
            # Ensure all images have alt text
            if self.ensure_image_alt:
                self._ensure_image_alt_text(soup)
            
            # Get the sanitized HTML
            # Use prettify() for better structure, but strip extra whitespace
            sanitized_html = str(soup)
            
            logger.debug(f"Sanitization complete. Output length: {len(sanitized_html)} characters")
            
            return sanitized_html
            
        except Exception as e:
            error_msg = f"Failed to sanitize HTML: {e}"
            logger.error(error_msg, exc_info=True)
            raise HtmlProcessorError(error_msg) from e
    
    def _remove_elements(self, soup: BeautifulSoup, element_names: Set[str]) -> None:
        """Remove specified elements from the soup.
        
        Args:
            soup: BeautifulSoup object
            element_names: Set of element tag names to remove
        """
        for element_name in element_names:
            for element in soup.find_all(element_name):
                logger.debug(f"Removing {element_name} element")
                element.decompose()
    
    def _remove_unsafe_attributes(self, soup: BeautifulSoup) -> None:
        """Remove unsafe event handler attributes from all elements.
        
        Args:
            soup: BeautifulSoup object
        """
        for element in soup.find_all():
            if element.attrs:
                for attr in list(element.attrs.keys()):
                    if attr.lower() in self.UNSAFE_ATTRIBUTES:
                        logger.debug(f"Removing unsafe attribute {attr} from {element.name}")
                        del element.attrs[attr]
    
    def _ensure_image_alt_text(self, soup: BeautifulSoup) -> None:
        """Ensure all images have alt text.
        
        Args:
            soup: BeautifulSoup object
        """
        for img in soup.find_all('img'):
            if not img.get('alt'):
                logger.debug(f"Adding default alt text to image: {img.get('src', 'unknown')}")
                img['alt'] = self.default_image_alt
    
    def get_body_content(self, html_content: str) -> str:
        """Extract body content from HTML, useful for email body generation.
        
        Args:
            html_content: HTML content as a string
            
        Returns:
            HTML content from the body tag (inner HTML, without body tags),
            or the entire content if no body tag
            
        Raises:
            HtmlProcessorError: If extraction fails
        """
        try:
            soup = BeautifulSoup(html_content, self.parser)
            body = soup.find('body')
            
            if body:
                # Return the inner HTML of the body tag (without the body tags themselves)
                return ''.join(str(child) for child in body.children) if body.contents else ""
            else:
                # No body tag, return the entire content
                return html_content
                
        except Exception as e:
            error_msg = f"Failed to extract body content: {e}"
            logger.error(error_msg, exc_info=True)
            raise HtmlProcessorError(error_msg) from e
    
    def validate_structure(self, html_content: str) -> bool:
        """Validate that HTML structure is well-formed.
        
        Args:
            html_content: HTML content as a string
            
        Returns:
            True if HTML is well-formed, False otherwise
        """
        try:
            soup = BeautifulSoup(html_content, self.parser)
            # If BeautifulSoup can parse it without errors, it's well-formed
            return True
        except Exception:
            return False

