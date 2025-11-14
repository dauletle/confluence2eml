"""Image processing and CID embedding for email generation.

This module provides functionality to find images in HTML, download them
from Confluence, and embed them as Content-IDs (CIDs) for email attachment.
"""

import logging
import mimetypes
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

from email.utils import make_msgid

logger = logging.getLogger(__name__)


class ImageProcessorError(Exception):
    """Base exception for ImageProcessor errors."""
    pass


class ImageDownloadError(ImageProcessorError):
    """Exception raised when image download fails."""
    pass


class ImageData:
    """Data structure for image information and content."""
    
    def __init__(
        self,
        cid: str,
        data: bytes,
        content_type: str,
        filename: Optional[str] = None
    ):
        """Initialize ImageData.
        
        Args:
            cid: Content-ID for the image (without angle brackets)
            data: Image binary data
            content_type: MIME content type (e.g., 'image/png')
            filename: Optional filename for the image
        """
        self.cid = cid
        self.data = data
        self.content_type = content_type
        self.filename = filename
    
    @property
    def maintype(self) -> str:
        """Get the main MIME type (e.g., 'image')."""
        return self.content_type.split('/')[0]
    
    @property
    def subtype(self) -> str:
        """Get the MIME subtype (e.g., 'png')."""
        parts = self.content_type.split('/')
        return parts[1] if len(parts) > 1 else 'octet-stream'


class ImageProcessor:
    """Processor for finding, downloading, and embedding images as CIDs.
    
    This class handles the critical step of embedding images in emails.
    It finds all images in HTML, downloads them from Confluence with
    authentication, generates unique Content-IDs (CIDs), and rewrites
    the HTML to reference these CIDs.
    
    Example:
        >>> processor = ImageProcessor(
        ...     base_url="https://confluence.example.com",
        ...     user="user@example.com",
        ...     token="api_token"
        ... )
        >>> html = '<img src="https://confluence.example.com/download/image.png" />'
        >>> processed_html, images = processor.process_images(html)
        >>> assert 'cid:' in processed_html
        >>> assert len(images) > 0
    """
    
    def __init__(
        self,
        base_url: str,
        user: str,
        token: str,
        timeout: int = 30,
        parser: str = 'html.parser'
    ):
        """Initialize the ImageProcessor.
        
        Args:
            base_url: Base URL of the Confluence instance
                     (e.g., https://company.atlassian.net)
            user: Confluence username or email for authentication
            token: Confluence API token for authentication
            timeout: Request timeout in seconds (default: 30)
            parser: BeautifulSoup parser to use (default: 'html.parser')
        
        Raises:
            ImageProcessorError: If required libraries are not installed
        """
        if BeautifulSoup is None:
            raise ImageProcessorError(
                "beautifulsoup4 library is not installed. "
                "Please install it with: pip install beautifulsoup4"
            )
        
        if requests is None:
            raise ImageProcessorError(
                "requests library is not installed. "
                "Please install it with: pip install requests"
            )
        
        self.base_url = base_url.rstrip('/')
        self.user = user
        self.token = token
        self.timeout = timeout
        self.parser = parser
        
        # Create requests session with authentication
        self.session = requests.Session()
        self.session.auth = (user, token)
        
        logger.debug(
            f"ImageProcessor initialized: base_url={base_url}, "
            f"user={user}, timeout={timeout}"
        )
    
    def process_images(self, html_content: str) -> Tuple[str, List[ImageData]]:
        """Process all images in HTML and embed them as CIDs.
        
        This method:
        1. Parses HTML to find all <img> tags
        2. Downloads each image from its URL with authentication
        3. Generates unique Content-IDs for each image
        4. Rewrites HTML src attributes to use CID references
        5. Returns processed HTML and image data for attachment
        
        Args:
            html_content: HTML content containing image tags
            
        Returns:
            Tuple of (processed_html, image_data_list):
            - processed_html: HTML with src attributes rewritten to use cid:
            - image_data_list: List of ImageData objects for attachment
            
        Raises:
            ImageProcessorError: If processing fails
            ImageDownloadError: If image download fails
            
        Example:
            >>> processor = ImageProcessor(base_url, user, token)
            >>> html = '<img src="https://example.com/image.png" />'
            >>> processed, images = processor.process_images(html)
            >>> assert 'cid:' in processed
            >>> assert len(images) == 1
        """
        if not isinstance(html_content, str):
            raise ImageProcessorError(
                f"html_content must be a string, got {type(html_content)}"
            )
        
        try:
            logger.debug("Processing images in HTML content...")
            logger.debug(f"Input HTML length: {len(html_content)} characters")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, self.parser)
            
            # Find all image tags
            img_tags = soup.find_all('img')
            logger.debug(f"Found {len(img_tags)} image(s) in HTML")
            
            if not img_tags:
                logger.debug("No images found, returning original HTML")
                return html_content, []
            
            # Process each image
            image_data_list: List[ImageData] = []
            
            for idx, img_tag in enumerate(img_tags):
                try:
                    img_url = img_tag.get('src')
                    if not img_url:
                        logger.warning(f"Image tag {idx + 1} has no src attribute, skipping")
                        continue
                    
                    # Skip data URIs (already embedded)
                    if img_url.startswith('data:'):
                        logger.debug(f"Image {idx + 1} is a data URI, skipping download")
                        continue
                    
                    # Skip existing CID references
                    if img_url.startswith('cid:'):
                        logger.debug(f"Image {idx + 1} already uses CID, skipping")
                        continue
                    
                    logger.debug(f"Processing image {idx + 1}: {img_url}")
                    
                    # Download image
                    img_data, content_type = self._download_image(img_url)
                    
                    # Generate CID
                    cid = self._generate_cid()
                    
                    # Detect content type if not provided
                    if not content_type:
                        content_type = self._detect_content_type(img_data, img_url)
                    
                    # Extract filename from URL if possible
                    filename = self._extract_filename(img_url)
                    
                    # Create ImageData object
                    image_data = ImageData(
                        cid=cid,
                        data=img_data,
                        content_type=content_type,
                        filename=filename
                    )
                    image_data_list.append(image_data)
                    
                    # Rewrite HTML src attribute to use CID
                    # CID format in src should be without angle brackets
                    cid_value = cid[1:-1] if cid.startswith('<') and cid.endswith('>') else cid
                    img_tag['src'] = f'cid:{cid_value}'
                    
                    logger.debug(
                        f"Image {idx + 1} processed: CID={cid}, "
                        f"content_type={content_type}, size={len(img_data)} bytes"
                    )
                    
                except ImageDownloadError as e:
                    logger.warning(f"Failed to download image {idx + 1} ({img_url}): {e}")
                    # Continue processing other images
                    continue
                except Exception as e:
                    logger.warning(
                        f"Unexpected error processing image {idx + 1} ({img_url}): {e}"
                    )
                    # Continue processing other images
                    continue
            
            # Generate final HTML
            processed_html = str(soup)
            
            logger.info(
                f"Image processing complete: {len(image_data_list)} image(s) processed, "
                f"output HTML length: {len(processed_html)} characters"
            )
            
            return processed_html, image_data_list
            
        except Exception as e:
            error_msg = f"Failed to process images: {e}"
            logger.error(error_msg, exc_info=True)
            raise ImageProcessorError(error_msg) from e
    
    def _download_image(self, url: str) -> Tuple[bytes, Optional[str]]:
        """Download an image from a URL with authentication.
        
        Args:
            url: Image URL (can be absolute or relative)
            
        Returns:
            Tuple of (image_data, content_type):
            - image_data: Binary image data
            - content_type: MIME content type (or None if not available)
            
        Raises:
            ImageDownloadError: If download fails
        """
        try:
            # Convert relative URLs to absolute
            if url.startswith('/'):
                url = f"{self.base_url}{url}"
            elif not url.startswith('http'):
                # Relative URL without leading slash
                url = f"{self.base_url}/{url}"
            
            logger.debug(f"Downloading image from: {url}")
            
            # Download with authentication
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Get content type from response headers
            content_type = response.headers.get('Content-Type')
            if content_type:
                # Remove any charset or other parameters
                content_type = content_type.split(';')[0].strip()
            
            # Read image data
            image_data = response.content
            
            if not image_data:
                raise ImageDownloadError(f"Downloaded image is empty: {url}")
            
            logger.debug(
                f"Image downloaded successfully: size={len(image_data)} bytes, "
                f"content_type={content_type}"
            )
            
            return image_data, content_type
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to download image from {url}: {e}"
            logger.error(error_msg)
            raise ImageDownloadError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error downloading image from {url}: {e}"
            logger.error(error_msg)
            raise ImageDownloadError(error_msg) from e
    
    def _generate_cid(self) -> str:
        """Generate a unique Content-ID for an image.
        
        Returns:
            Content-ID string (e.g., '<12345.abcdef@confluence-export>')
        """
        cid = make_msgid(domain='confluence-export')
        logger.debug(f"Generated CID: {cid}")
        return cid
    
    def _detect_content_type(self, image_data: bytes, url: Optional[str] = None) -> str:
        """Detect the MIME content type of image data.
        
        Args:
            image_data: Binary image data
            url: Optional URL for filename-based detection
            
        Returns:
            MIME content type (default: 'image/png' if unknown)
        """
        # Try to detect from URL first
        if url:
            content_type, _ = mimetypes.guess_type(url)
            if content_type and content_type.startswith('image/'):
                return content_type
        
        # Try to detect from file signature (magic bytes)
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif image_data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return 'image/gif'
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
            return 'image/webp'
        elif image_data.startswith(b'<svg') or image_data.startswith(b'<?xml'):
            return 'image/svg+xml'
        
        # Default fallback
        logger.warning(f"Could not detect image type, defaulting to image/png")
        return 'image/png'
    
    def _extract_filename(self, url: str) -> Optional[str]:
        """Extract filename from URL.
        
        Args:
            url: Image URL
            
        Returns:
            Filename if extractable, None otherwise
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            if path:
                # Get the last component of the path
                filename = path.split('/')[-1]
                if filename and '.' in filename:
                    return filename
        except Exception:
            pass
        
        return None
    
    def close(self):
        """Close the requests session.
        
        This should be called when done with the processor to clean up resources.
        """
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("ImageProcessor session closed")

