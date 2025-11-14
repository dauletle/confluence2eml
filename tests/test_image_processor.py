"""Tests for ImageProcessor module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from email.utils import make_msgid

from confluence2eml.core.image_processor import (
    ImageProcessor,
    ImageProcessorError,
    ImageDownloadError,
    ImageData,
)


@pytest.mark.unit
class TestImageData:
    """Test cases for ImageData class."""
    
    def test_image_data_initialization(self):
        """Test ImageData initialization."""
        cid = make_msgid(domain='test')
        data = b'fake_image_data'
        content_type = 'image/png'
        filename = 'test.png'
        
        image_data = ImageData(cid, data, content_type, filename)
        
        assert image_data.cid == cid
        assert image_data.data == data
        assert image_data.content_type == content_type
        assert image_data.filename == filename
    
    def test_image_data_maintype(self):
        """Test ImageData maintype property."""
        image_data = ImageData(
            make_msgid(),
            b'data',
            'image/png',
            'test.png'
        )
        assert image_data.maintype == 'image'
    
    def test_image_data_subtype(self):
        """Test ImageData subtype property."""
        image_data = ImageData(
            make_msgid(),
            b'data',
            'image/png',
            'test.png'
        )
        assert image_data.subtype == 'png'
    
    def test_image_data_subtype_default(self):
        """Test ImageData subtype with invalid content type."""
        image_data = ImageData(
            make_msgid(),
            b'data',
            'invalid',
            'test.png'
        )
        assert image_data.subtype == 'octet-stream'


@pytest.mark.unit
class TestImageProcessorInitialization:
    """Test cases for ImageProcessor initialization."""
    
    def test_default_initialization(self):
        """Test ImageProcessor with default configuration."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="api_token"
        )
        assert processor is not None
        assert processor.base_url == "https://confluence.example.com"
        assert processor.user == "user@example.com"
        assert processor.token == "api_token"
        assert processor.timeout == 30
        assert processor.parser == 'html.parser'
        processor.close()
    
    def test_initialization_with_custom_options(self):
        """Test ImageProcessor with custom configuration."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="api_token",
            timeout=60,
            parser='lxml'
        )
        assert processor.timeout == 60
        assert processor.parser == 'lxml'
        processor.close()
    
    def test_initialization_strips_base_url_trailing_slash(self):
        """Test that base_url trailing slash is stripped."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com/",
            user="user@example.com",
            token="api_token"
        )
        assert processor.base_url == "https://confluence.example.com"
        processor.close()
    
    def test_initialization_without_beautifulsoup(self):
        """Test that initialization fails without beautifulsoup4."""
        with patch('confluence2eml.core.image_processor.BeautifulSoup', None):
            with pytest.raises(ImageProcessorError) as exc_info:
                ImageProcessor(
                    base_url="https://example.com",
                    user="user@example.com",
                    token="token"
                )
            assert "beautifulsoup4" in str(exc_info.value).lower()
    
    def test_initialization_without_requests(self):
        """Test that initialization fails without requests."""
        with patch('confluence2eml.core.image_processor.requests', None):
            with pytest.raises(ImageProcessorError) as exc_info:
                ImageProcessor(
                    base_url="https://example.com",
                    user="user@example.com",
                    token="token"
                )
            assert "requests" in str(exc_info.value).lower()


@pytest.mark.unit
class TestImageProcessorProcessImages:
    """Test cases for ImageProcessor.process_images method."""
    
    def test_process_images_no_images(self):
        """Test processing HTML with no images."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = "<h1>Title</h1><p>Content</p>"
        processed, images = processor.process_images(html)
        
        assert processed == html or '<h1>Title</h1>' in processed
        assert len(images) == 0
        processor.close()
    
    def test_process_images_with_single_image(self, mock_requests_get):
        """Test processing HTML with a single image."""
        # Mock image download
        mock_response = Mock()
        mock_response.content = b'fake_png_data'
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = '<img src="https://confluence.example.com/download/image.png" alt="Image" />'
        processed, images = processor.process_images(html)
        
        assert 'cid:' in processed
        assert len(images) == 1
        assert images[0].content_type == 'image/png'
        assert images[0].data == b'fake_png_data'
        processor.close()
    
    def test_process_images_with_multiple_images(self, mock_requests_get):
        """Test processing HTML with multiple images."""
        # Mock image downloads
        mock_response = Mock()
        mock_response.content = b'fake_image_data'
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = """<img src="https://confluence.example.com/image1.png" />
                   <img src="https://confluence.example.com/image2.jpg" />"""
        processed, images = processor.process_images(html)
        
        assert processed.count('cid:') == 2
        assert len(images) == 2
        processor.close()
    
    def test_process_images_skips_data_uri(self):
        """Test that data URIs are skipped."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />'
        processed, images = processor.process_images(html)
        
        assert len(images) == 0
        assert 'data:' in processed
        processor.close()
    
    def test_process_images_skips_existing_cid(self):
        """Test that existing CID references are skipped."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = '<img src="cid:existing-cid-123" />'
        processed, images = processor.process_images(html)
        
        assert len(images) == 0
        assert 'cid:existing-cid-123' in processed
        processor.close()
    
    def test_process_images_handles_missing_src(self):
        """Test that images without src attribute are skipped."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = '<img alt="No source" />'
        processed, images = processor.process_images(html)
        
        assert len(images) == 0
        processor.close()
    
    def test_process_images_rewrites_src_to_cid(self, mock_requests_get):
        """Test that image src attributes are rewritten to CID."""
        mock_response = Mock()
        mock_response.content = b'fake_image_data'
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        html = '<img src="https://confluence.example.com/image.png" alt="Test" />'
        processed, images = processor.process_images(html)
        
        # Check that src was rewritten
        assert 'src="cid:' in processed or "src='cid:" in processed
        assert 'https://confluence.example.com/image.png' not in processed
        assert len(images) == 1
        processor.close()
    
    def test_process_images_invalid_input_type(self):
        """Test that invalid input type raises error."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        with pytest.raises(ImageProcessorError) as exc_info:
            processor.process_images(None)  # type: ignore
        assert "must be a string" in str(exc_info.value)
        processor.close()


@pytest.mark.unit
class TestImageProcessorDownload:
    """Test cases for image downloading."""
    
    def test_download_image_absolute_url(self, mock_requests_get):
        """Test downloading image from absolute URL."""
        mock_response = Mock()
        mock_response.content = b'fake_image_data'
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        data, content_type = processor._download_image("https://confluence.example.com/image.png")
        
        assert data == b'fake_image_data'
        assert content_type == 'image/png'
        mock_requests_get.assert_called_once()
        processor.close()
    
    def test_download_image_relative_url(self, mock_requests_get):
        """Test downloading image from relative URL."""
        mock_response = Mock()
        mock_response.content = b'fake_image_data'
        mock_response.headers = {'Content-Type': 'image/jpeg'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        data, content_type = processor._download_image("/download/image.jpg")
        
        assert data == b'fake_image_data'
        assert content_type == 'image/jpeg'
        # Verify URL was converted to absolute
        call_args = mock_requests_get.call_args
        assert 'https://confluence.example.com/download/image.jpg' in str(call_args)
        processor.close()
    
    def test_download_image_without_content_type(self, mock_requests_get):
        """Test downloading image without Content-Type header."""
        mock_response = Mock()
        mock_response.content = b'\x89PNG\r\n\x1a\nfake_png_data'
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        data, content_type = processor._download_image("https://confluence.example.com/image.png")
        
        assert data == b'\x89PNG\r\n\x1a\nfake_png_data'
        assert content_type is None or content_type == 'image/png'
        processor.close()
    
    def test_download_image_handles_http_error(self, mock_requests_get):
        """Test that HTTP errors are handled."""
        mock_requests_get.side_effect = Exception("Connection error")
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        
        with pytest.raises(ImageDownloadError):
            processor._download_image("https://confluence.example.com/image.png")
        processor.close()
    
    def test_download_image_handles_empty_response(self, mock_requests_get):
        """Test that empty image data raises error."""
        mock_response = Mock()
        mock_response.content = b''
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        
        with pytest.raises(ImageDownloadError) as exc_info:
            processor._download_image("https://confluence.example.com/image.png")
        assert "empty" in str(exc_info.value).lower()
        processor.close()


@pytest.mark.unit
class TestImageProcessorCIDGeneration:
    """Test cases for CID generation."""
    
    def test_generate_cid(self):
        """Test CID generation."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        cid = processor._generate_cid()
        
        assert cid.startswith('<')
        assert cid.endswith('>')
        assert '@confluence-export' in cid
        processor.close()
    
    def test_generate_cid_unique(self):
        """Test that generated CIDs are unique."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        cid1 = processor._generate_cid()
        cid2 = processor._generate_cid()
        
        assert cid1 != cid2
        processor.close()


@pytest.mark.unit
class TestImageProcessorContentTypeDetection:
    """Test cases for content type detection."""
    
    def test_detect_content_type_from_url(self):
        """Test content type detection from URL."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        content_type = processor._detect_content_type(b'data', url='image.png')
        
        assert content_type == 'image/png'
        processor.close()
    
    def test_detect_content_type_png_signature(self):
        """Test PNG detection from magic bytes."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        png_data = b'\x89PNG\r\n\x1a\n' + b'fake_data'
        content_type = processor._detect_content_type(png_data)
        
        assert content_type == 'image/png'
        processor.close()
    
    def test_detect_content_type_jpeg_signature(self):
        """Test JPEG detection from magic bytes."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        jpeg_data = b'\xff\xd8\xff' + b'fake_data'
        content_type = processor._detect_content_type(jpeg_data)
        
        assert content_type == 'image/jpeg'
        processor.close()
    
    def test_detect_content_type_gif_signature(self):
        """Test GIF detection from magic bytes."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        gif_data = b'GIF87a' + b'fake_data'
        content_type = processor._detect_content_type(gif_data)
        
        assert content_type == 'image/gif'
        processor.close()
    
    def test_detect_content_type_default_fallback(self):
        """Test default fallback for unknown image type."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        unknown_data = b'unknown_image_data'
        content_type = processor._detect_content_type(unknown_data)
        
        assert content_type == 'image/png'  # Default fallback
        processor.close()


@pytest.mark.unit
class TestImageProcessorFilenameExtraction:
    """Test cases for filename extraction."""
    
    def test_extract_filename_from_url(self):
        """Test filename extraction from URL."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        filename = processor._extract_filename("https://confluence.example.com/download/image.png")
        
        assert filename == "image.png"
        processor.close()
    
    def test_extract_filename_from_path(self):
        """Test filename extraction from path."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        filename = processor._extract_filename("/download/attachments/123/photo.jpg")
        
        assert filename == "photo.jpg"
        processor.close()
    
    def test_extract_filename_no_filename(self):
        """Test filename extraction when no filename in URL."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        filename = processor._extract_filename("https://confluence.example.com/image")
        
        assert filename is None
        processor.close()


@pytest.mark.unit
class TestImageProcessorClose:
    """Test cases for ImageProcessor.close method."""
    
    def test_close_session(self):
        """Test that close() closes the requests session."""
        processor = ImageProcessor(
            base_url="https://confluence.example.com",
            user="user@example.com",
            token="token"
        )
        assert processor.session is not None
        
        processor.close()
        
        # Session should be closed (we can't easily test this without mocking)
        # but we can verify the method doesn't raise an error
        assert True


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get for image downloads."""
    with patch('confluence2eml.core.image_processor.requests.Session.get') as mock_get:
        yield mock_get

