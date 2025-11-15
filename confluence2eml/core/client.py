"""Confluence API client wrapper for content extraction.

This module provides a wrapper around the confluence-markdown-exporter library
to extract content from Confluence pages programmatically.
"""

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class ConfluenceClientError(Exception):
    """Base exception for ConfluenceClient errors."""
    pass


class ConfluenceAuthenticationError(ConfluenceClientError):
    """Exception raised when authentication fails."""
    pass


class ConfluencePageNotFoundError(ConfluenceClientError):
    """Exception raised when a page cannot be found."""
    pass


class URLResolver:
    """Resolves various Confluence URL formats to extract page ID and base URL.
    
    Supports multiple Confluence URL formats:
    - Pretty URLs: https://company.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
    - Page ID URLs: https://company.atlassian.net/wiki/spaces/SPACE/pages/123456
    - Viewpage URLs: https://company.atlassian.net/wiki/pages/viewpage.action?pageId=123456
    - Server URLs: https://confluence.company.com/display/SPACE/Page+Title
    """
    
    # Pattern for pretty URLs: /spaces/SPACE/pages/PAGE_ID/...
    PRETTY_URL_PATTERN = re.compile(r'/spaces/[^/]+/pages/(\d+)')
    
    # Pattern for viewpage URLs: ?pageId=123456
    VIEWPAGE_PATTERN = re.compile(r'[?&]pageId=(\d+)')
    
    # Pattern for server display URLs: /display/SPACE/...
    SERVER_DISPLAY_PATTERN = re.compile(r'/display/[^/]+/(.+)')
    
    @staticmethod
    def extract_page_id(url: str) -> str:
        """Extract page ID from a Confluence URL.
        
        Args:
            url: Confluence page URL in any supported format
            
        Returns:
            Page ID as a string
            
        Raises:
            ConfluenceClientError: If page ID cannot be extracted from URL
        """
        if not url:
            raise ConfluenceClientError("URL cannot be empty")
        
        # Try pretty URL pattern first (most common in Cloud)
        match = URLResolver.PRETTY_URL_PATTERN.search(url)
        if match:
            return match.group(1)
        
        # Try viewpage pattern
        match = URLResolver.VIEWPAGE_PATTERN.search(url)
        if match:
            return match.group(1)
        
        # For server display URLs, we'd need to make an API call to resolve
        # For now, raise an error
        if '/display/' in url:
            raise ConfluenceClientError(
                f"Server display URLs require API resolution. "
                f"Please use a pageId-based URL format. URL: {url}"
            )
        
        raise ConfluenceClientError(
            f"Could not extract page ID from URL: {url}. "
            f"Supported formats: /spaces/.../pages/PAGE_ID or ?pageId=PAGE_ID"
        )
    
    @staticmethod
    def extract_base_url(url: str) -> str:
        """Extract base Confluence URL from a page URL.
        
        Args:
            url: Confluence page URL
            
        Returns:
            Base URL (e.g., https://company.atlassian.net)
            
        Raises:
            ConfluenceClientError: If base URL cannot be extracted
        """
        if not url:
            raise ConfluenceClientError("URL cannot be empty")
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ConfluenceClientError(
                    f"Invalid URL format. Expected format: https://domain.com/path. "
                    f"Got: {url}"
                )
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            return base_url
        except ConfluenceClientError:
            raise
        except Exception as e:
            raise ConfluenceClientError(f"Could not extract base URL from {url}: {e}")


class ConfluenceClient:
    """Client for interacting with Confluence API via confluence-markdown-exporter.
    
    This class wraps the confluence-markdown-exporter library to provide
    a clean programmatic interface for extracting Confluence page content.
    """
    
    def __init__(self, base_url: str, user: str, token: str):
        """Initialize the Confluence client.
        
        Args:
            base_url: Base URL of the Confluence instance
                     (e.g., https://company.atlassian.net)
            user: Confluence username or email
            token: Confluence API token or Personal Access Token (PAT)
            
        Raises:
            ConfluenceAuthenticationError: If credentials are invalid
        """
        self.base_url = base_url.rstrip('/')
        self.user = user
        self.token = token
        self._exporter = None
        
        # Try to import and initialize the exporter
        self._initialize_exporter()
    
    def _initialize_exporter(self):
        """Initialize the confluence-markdown-exporter library.
        
        This method attempts to use the library programmatically if available,
        otherwise it will be initialized when needed for subprocess calls.
        """
        try:
            # Try to import the library's internal modules
            # The exact import path may vary, so we'll handle this flexibly
            import confluence_markdown_exporter  # type: ignore  # noqa: F401
            self._exporter = confluence_markdown_exporter
            logger.debug("confluence-markdown-exporter imported successfully")
        except ImportError as e:
            logger.warning(
                f"Could not import confluence-markdown-exporter as library: {e}. "
                f"Will use subprocess approach if needed."
            )
            self._exporter = None
    
    def get_page_content(self, page_id: str) -> Dict[str, any]:
        """Extract page content and metadata from Confluence.
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Dictionary containing:
                - 'markdown': Markdown content as string
                - 'title': Page title
                - 'attachments': List of attachment metadata
                - 'page_id': Page ID
                - 'url': Full page URL
                
        Raises:
            ConfluencePageNotFoundError: If page is not found
            ConfluenceAuthenticationError: If authentication fails
            ConfluenceClientError: For other errors
        """
        logger.info(f"Extracting content for page ID: {page_id}")
        
        try:
            # Try to use the library programmatically first
            if self._exporter and hasattr(self._exporter, 'export_page'):
                return self._export_page_programmatic(page_id)
            else:
                # Use direct REST API approach (more reliable than subprocess)
                return self._export_page_rest_api(page_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ConfluencePageNotFoundError(f"Page {page_id} not found: {e}")
            elif "401" in str(e) or "403" in str(e) or "unauthorized" in str(e).lower():
                raise ConfluenceAuthenticationError(f"Authentication failed: {e}")
            else:
                raise ConfluenceClientError(f"Failed to extract page content: {e}")
    
    def _export_page_programmatic(self, page_id: str) -> Dict[str, any]:
        """Export page using library's programmatic API.
        
        This method will be implemented once we understand the library's API.
        For now, it falls back to REST API.
        """
        # TODO: Implement once library API is understood
        logger.debug("Programmatic API not yet implemented, using REST API")
        return self._export_page_rest_api(page_id)
    
    def _export_page_rest_api(self, page_id: str) -> Dict[str, any]:
        """Export page using Confluence REST API directly.
        
        This method uses the Confluence REST API to fetch page content
        and convert it to markdown format.
        """
        if requests is None:
            raise ConfluenceClientError(
                "requests library is required but not installed. "
                "Please install it with: pip install requests"
            )
        
        # Create authentication using requests built-in Basic Auth
        # For Confluence Cloud, use email:token format
        auth = (self.user, self.token)
        
        headers = {
            'Accept': 'application/json',
        }
        
        # API endpoint for getting page content
        # For Confluence Cloud: /rest/api/content/{page_id}
        # For Confluence Server: /rest/api/content/{page_id}
        # Remove /wiki if present in base_url (it's added automatically by Confluence)
        api_base = self.base_url.rstrip('/')
        if api_base.endswith('/wiki'):
            api_base = api_base[:-5]  # Remove /wiki suffix
        
        api_url = f"{api_base}/rest/api/content/{page_id}"
        params = {
            'expand': 'body.storage,version,title,space'
        }
        
        try:
            logger.debug(f"Fetching page from API: {api_url}")
            logger.debug(f"Using authentication for user: {self.user}")
            response = requests.get(api_url, auth=auth, headers=headers, params=params, timeout=30)
            
            if response.status_code == 404:
                raise ConfluencePageNotFoundError(f"Page {page_id} not found")
            elif response.status_code == 401:
                error_detail = response.text
                logger.error(f"Authentication failed. Response: {error_detail}")
                raise ConfluenceAuthenticationError(
                    f"Authentication failed (HTTP 401). Please verify:\n"
                    f"  - Your email address is correct: {self.user}\n"
                    f"  - Your API token is valid and not expired\n"
                    f"  - You're using an API token (not a password)\n"
                    f"  - The API token has the necessary permissions\n"
                    f"Server response: {error_detail[:200]}"
                )
            elif response.status_code == 403:
                error_detail = response.text
                logger.error(f"Authorization failed. Response: {error_detail}")
                raise ConfluenceAuthenticationError(
                    f"Authorization failed (HTTP 403). The credentials are valid but "
                    f"you don't have permission to access this page. "
                    f"Server response: {error_detail[:200]}"
                )
            elif response.status_code != 200:
                raise ConfluenceClientError(
                    f"API request failed with status {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            # Extract page information
            title = data.get('title', f"Page {page_id}")
            page_url = data.get('_links', {}).get('webui', '')
            if not page_url.startswith('http'):
                page_url = f"{self.base_url}/wiki{page_url}" if page_url.startswith('/') else f"{self.base_url}/wiki/{page_url}"
            
            # Get body content (in storage format - Confluence's internal format)
            body_storage = data.get('body', {}).get('storage', {})
            storage_content = body_storage.get('value', '')
            
            # Convert storage format to markdown
            # This is a simplified conversion - confluence-markdown-exporter does this more thoroughly
            markdown_content = self._convert_storage_to_markdown(storage_content)
            
            # Get attachments if available
            attachments = []
            # Note: Attachments would need a separate API call to /rest/api/content/{page_id}/child/attachment
            
            return {
                'markdown': markdown_content,
                'title': title,
                'attachments': attachments,
                'page_id': page_id,
                'url': page_url or f"{self.base_url}/wiki/pages/viewpage.action?pageId={page_id}",
            }
            
        except requests.exceptions.RequestException as e:
            raise ConfluenceClientError(f"Failed to connect to Confluence API: {e}")
        except ConfluencePageNotFoundError:
            raise
        except ConfluenceAuthenticationError:
            raise
        except Exception as e:
            raise ConfluenceClientError(f"Failed to extract page content: {e}")
    
    def _convert_storage_to_markdown(self, storage_content: str) -> str:
        """Convert Confluence storage format to Markdown.
        
        This is a simplified converter. For production use, consider using
        confluence-markdown-exporter's conversion logic or a more complete converter.
        """
        import html
        
        # Basic HTML to Markdown conversion
        # This is a simplified version - a full converter would handle more cases
        markdown = storage_content
        
        # Decode HTML entities
        markdown = html.unescape(markdown)
        
        # Convert common Confluence/HTML elements to Markdown
        # Headers
        markdown = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Bold and italic
        markdown = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Links
        markdown = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Code blocks
        markdown = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Paragraphs
        markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Line breaks
        markdown = re.sub(r'<br[^>]*/?>', r'\n', markdown, flags=re.IGNORECASE)
        
        # Lists
        markdown = re.sub(r'<ul[^>]*>', '', markdown, flags=re.IGNORECASE)
        markdown = re.sub(r'</ul>', '', markdown, flags=re.IGNORECASE)
        markdown = re.sub(r'<ol[^>]*>', '', markdown, flags=re.IGNORECASE)
        markdown = re.sub(r'</ol>', '', markdown, flags=re.IGNORECASE)
        markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove remaining HTML tags
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        # Clean up extra whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = markdown.strip()
        
        return markdown
    
    def _export_page_subprocess(self, page_id: str) -> Dict[str, any]:
        """Export page using confluence-markdown-exporter as subprocess.
        
        This is a fallback method when programmatic API is not available.
        """
        import sys
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Build the command using Python module execution
            # confluence-markdown-exporter is a Python package, so we need to run it as a module
            # Use viewpage URL format which only requires page ID (no space name needed)
            page_url = f"{self.base_url}/wiki/pages/viewpage.action?pageId={page_id}"
            
            cmd = [
                sys.executable,
                '-m',
                'confluence_markdown_exporter',
                '--url', page_url,
                '--output', output_path,
                '--user', self.user,
                '--token', self.token,
            ]
            
            logger.debug(f"Running command: {sys.executable} -m confluence_markdown_exporter ...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Subprocess failed with return code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                logger.error(f"stdout: {result.stdout}")
                raise ConfluenceClientError(f"Export failed: {error_msg}")
            
            # Read the markdown file
            if not Path(output_path).exists():
                raise ConfluenceClientError(f"Output file was not created: {output_path}")
            
            markdown_content = Path(output_path).read_text(encoding='utf-8')
            
            # Extract metadata (this would need to be parsed from output or API)
            # For now, return basic structure
            return {
                'markdown': markdown_content,
                'title': f"Page {page_id}",  # Will be extracted from actual API
                'attachments': [],  # Will be populated from API
                'page_id': page_id,
                'url': page_url,
            }
            
        finally:
            # Clean up temporary file
            try:
                Path(output_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def get_page_metadata(self, page_id: str) -> Dict[str, any]:
        """Get page metadata without full content.
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Dictionary with page metadata (title, space, etc.)
        """
        # This can be optimized to fetch only metadata
        # For now, we'll use get_page_content and extract metadata
        content = self.get_page_content(page_id)
        return {
            'page_id': content['page_id'],
            'title': content['title'],
            'url': content['url'],
            'attachments': content['attachments'],
        }

