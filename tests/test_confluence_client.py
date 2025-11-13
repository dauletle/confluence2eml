"""Tests for ConfluenceClient module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from confluence2eml.client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
)


@pytest.mark.unit
class TestConfluenceClient:
    """Test cases for ConfluenceClient class."""
    
    def test_client_initialization(self, mock_credentials):
        """Test that ConfluenceClient initializes correctly."""
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        assert client.base_url == "https://company.atlassian.net"
        assert client.user == mock_credentials["user"]
        assert client.token == mock_credentials["token"]
    
    def test_client_initialization_strips_trailing_slash(self, mock_credentials):
        """Test that base URL trailing slash is stripped."""
        client = ConfluenceClient(
            base_url="https://company.atlassian.net/",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        assert client.base_url == "https://company.atlassian.net"
    
    @patch('confluence2eml.client.subprocess')
    @patch('confluence2eml.client.Path')
    @patch('confluence2eml.client.tempfile')
    def test_get_page_content_subprocess_success(
        self, mock_tempfile, mock_path_class, mock_subprocess, mock_credentials
    ):
        """Test successful page content extraction via subprocess."""
        # Setup mocks
        mock_tmp_file = MagicMock()
        mock_tmp_file.name = "/tmp/test.md"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_tmp_file
        mock_tempfile.NamedTemporaryFile.return_value.__exit__.return_value = None
        
        mock_path_instance = MagicMock()
        mock_path_instance.read_text.return_value = "# Test Page\n\nContent here"
        mock_path_instance.unlink.return_value = None
        mock_path_class.return_value = mock_path_instance
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        
        # Create client and get content
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        
        # Mock the exporter to be None to force subprocess path
        client._exporter = None
        
        content = client.get_page_content("123456")
        
        assert content['page_id'] == "123456"
        assert 'markdown' in content
        assert 'title' in content
        assert 'attachments' in content
    
    @patch('confluence2eml.client.subprocess')
    def test_get_page_content_authentication_error(
        self, mock_subprocess, mock_credentials
    ):
        """Test that authentication errors are properly raised."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "401 Unauthorized"
        mock_subprocess.run.return_value = mock_result
        
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user="invalid@example.com",
            token="invalid_token"
        )
        client._exporter = None
        
        with pytest.raises(ConfluenceAuthenticationError):
            client.get_page_content("123456")
    
    @patch('confluence2eml.client.subprocess')
    def test_get_page_content_page_not_found_error(
        self, mock_subprocess, mock_credentials
    ):
        """Test that page not found errors are properly raised."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "404 Page not found"
        mock_subprocess.run.return_value = mock_result
        
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        client._exporter = None
        
        with pytest.raises(ConfluencePageNotFoundError):
            client.get_page_content("999999")
    
    @patch('confluence2eml.client.subprocess')
    def test_get_page_content_generic_error(
        self, mock_subprocess, mock_credentials
    ):
        """Test that generic errors are properly raised."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "500 Internal Server Error"
        mock_subprocess.run.return_value = mock_result
        
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        client._exporter = None
        
        with pytest.raises(ConfluenceClientError):
            client.get_page_content("123456")
    
    def test_get_page_metadata(self, mock_credentials):
        """Test getting page metadata."""
        client = ConfluenceClient(
            base_url="https://company.atlassian.net",
            user=mock_credentials["user"],
            token=mock_credentials["token"]
        )
        
        # Mock get_page_content to return test data
        mock_content = {
            'page_id': '123456',
            'title': 'Test Page',
            'url': 'https://company.atlassian.net/wiki/spaces/SPACE/pages/123456',
            'attachments': [],
            'markdown': '# Test Page\n\nContent'
        }
        client.get_page_content = Mock(return_value=mock_content)
        
        metadata = client.get_page_metadata("123456")
        
        assert metadata['page_id'] == '123456'
        assert metadata['title'] == 'Test Page'
        assert 'markdown' not in metadata  # Metadata should not include full content
        client.get_page_content.assert_called_once_with("123456")

