"""CSS inlining processor for email compatibility.

This module provides functionality to inline CSS styles into HTML elements
for email client compatibility. It uses the premailer library to:
- Inline CSS from <style> tags into style attributes
- Convert relative URLs to absolute URLs
- Ensure email client compatibility
"""

import logging
from typing import Optional

try:
    from premailer import Premailer
except ImportError:
    Premailer = None  # type: ignore

from .utils import wrap_html_with_css, load_email_css

logger = logging.getLogger(__name__)


class CssInlinerError(Exception):
    """Base exception for CssInliner errors."""
    pass


class CssInliner:
    """Processor for inlining CSS styles into HTML for email compatibility.
    
    This class handles the critical step of inlining CSS styles into HTML
    elements. Most email clients (especially Outlook and Gmail) strip <style>
    blocks and external stylesheets for security reasons. The only reliable
    method for styling HTML email is to use inline style attributes on
    every individual HTML element.
    
    This class uses the premailer library to:
    - Inline CSS from <style> tags into style attributes on elements
    - Convert relative URLs to absolute URLs (crucial for images and links)
    - Remove <style> tags after inlining
    - Preserve HTML structure
    
    Example:
        >>> inliner = CssInliner()
        >>> html = "<html><head><style>p { color: red; }</style></head><body><p>Hello</p></body></html>"
        >>> inlined = inliner.inline(html)
        >>> assert 'style="color: red"' in inlined
        >>> assert '<style>' not in inlined
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        strip_important: bool = False,
        keep_style_tags: bool = False,
        disable_validation: bool = True,
        cssutils_logging_level: Optional[int] = None
    ):
        """Initialize the CssInliner.
        
        Args:
            base_url: Base URL for converting relative URLs to absolute.
                    If None, relative URLs will remain relative (not recommended
                    for email). Should be the Confluence base URL.
            strip_important: If True, remove !important flags from CSS
                           (default: False)
            keep_style_tags: If True, keep <style> tags after inlining
                           (default: False, as email clients strip them)
            disable_validation: If True, disable CSS validation (default: True,
                              recommended for email compatibility)
            cssutils_logging_level: Logging level for cssutils library
                                  (default: None, uses premailer default)
        
        Raises:
            CssInlinerError: If premailer library is not installed
        """
        if Premailer is None:
            raise CssInlinerError(
                "premailer library is not installed. "
                "Please install it with: pip install premailer"
            )
        
        self.base_url = base_url
        self.strip_important = strip_important
        self.keep_style_tags = keep_style_tags
        self.disable_validation = disable_validation
        self.cssutils_logging_level = cssutils_logging_level
        
        logger.debug(
            f"CssInliner initialized: base_url={base_url}, "
            f"strip_important={strip_important}, "
            f"keep_style_tags={keep_style_tags}"
        )
    
    def inline(
        self,
        html_content: str,
        wrap_with_css: bool = True,
        css_content: Optional[str] = None
    ) -> str:
        """Inline CSS styles into HTML elements.
        
        This method:
        1. Optionally wraps HTML with CSS stylesheet (if wrap_with_css=True)
        2. Uses premailer to inline CSS from <style> tags into style attributes
        3. Converts relative URLs to absolute URLs (if base_url is set)
        4. Returns the inlined HTML
        
        Args:
            html_content: HTML content to inline (can be partial or full document)
            wrap_with_css: If True, wrap HTML with default email CSS stylesheet
                          before inlining (default: True)
            css_content: Optional custom CSS content. If wrap_with_css=True and
                        css_content is None, uses default email CSS.
                        If wrap_with_css=False, this parameter is ignored.
        
        Returns:
            HTML content with CSS inlined as style attributes
        
        Raises:
            CssInlinerError: If inlining fails
            
        Example:
            >>> inliner = CssInliner(base_url="https://confluence.example.com")
            >>> html = "<p>Hello</p>"
            >>> inlined = inliner.inline(html)
            >>> assert 'style=' in inlined
        """
        if not isinstance(html_content, str):
            raise CssInlinerError(
                f"html_content must be a string, got {type(html_content)}"
            )
        
        try:
            logger.debug("Starting CSS inlining process...")
            logger.debug(f"Input HTML length: {len(html_content)} characters")
            logger.debug(f"wrap_with_css={wrap_with_css}, base_url={self.base_url}")
            
            # Step 1: Wrap HTML with CSS if requested
            if wrap_with_css:
                logger.debug("Wrapping HTML with CSS stylesheet...")
                html_content = wrap_html_with_css(html_content, css_content=css_content)
                logger.debug(f"HTML wrapped with CSS. Length: {len(html_content)} characters")
            
            # Step 2: Create Premailer instance with configuration
            premailer_kwargs = {
                'strip_important': self.strip_important,
                'keep_style_tags': self.keep_style_tags,
                'disable_validation': self.disable_validation,
            }
            
            if self.base_url:
                premailer_kwargs['base_url'] = self.base_url
            
            if self.cssutils_logging_level is not None:
                premailer_kwargs['cssutils_logging_level'] = self.cssutils_logging_level
            
            premailer = Premailer(
                html_content,
                **premailer_kwargs
            )
            
            # Step 3: Transform HTML (inline CSS and absolutize URLs)
            logger.debug("Transforming HTML with premailer (inlining CSS, absolutizing URLs)...")
            inlined_html = premailer.transform()
            
            logger.debug(f"CSS inlining complete. Output length: {len(inlined_html)} characters")
            
            # Verify that inlining occurred (check for style attributes)
            if '<style' in inlined_html.lower() and not self.keep_style_tags:
                logger.warning("Style tags still present after inlining (may be expected in some cases)")
            
            return inlined_html
            
        except Exception as e:
            error_msg = f"Failed to inline CSS: {e}"
            logger.error(error_msg, exc_info=True)
            raise CssInlinerError(error_msg) from e
    
    def inline_with_custom_css(
        self,
        html_content: str,
        css_content: str
    ) -> str:
        """Inline CSS using custom CSS content.
        
        This is a convenience method that wraps HTML with custom CSS
        and then inlines it.
        
        Args:
            html_content: HTML content to inline
            css_content: Custom CSS content to use
        
        Returns:
            HTML content with CSS inlined as style attributes
        
        Raises:
            CssInlinerError: If inlining fails
        """
        return self.inline(html_content, wrap_with_css=True, css_content=css_content)
    
    def inline_without_wrapping(
        self,
        html_content: str
    ) -> str:
        """Inline CSS from existing <style> tags without wrapping.
        
        This method assumes the HTML already contains <style> tags
        and only performs the inlining step without wrapping.
        
        Args:
            html_content: HTML content with existing <style> tags
        
        Returns:
            HTML content with CSS inlined as style attributes
        
        Raises:
            CssInlinerError: If inlining fails
        """
        return self.inline(html_content, wrap_with_css=False)

