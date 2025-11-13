"""Integration tests for ConfluenceClient and URLResolver.

These tests verify the complete workflow of URL parsing, client initialization,
and content extraction (with mocked API calls).
"""

import pytest
from unittest.mock import patch, MagicMock

from confluence2eml.client import (
    ConfluenceClient,
    URLResolver,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
)


@pytest.mark.integration
class TestConfluenceIntegration:
    """Integration tests for the complete Confluence extraction workflow."""
    
    def test_complete_workflow_url_parsing_and_content_extraction(
        self, sample_confluence_urls, mock_credentials
    ):
        """Test complete workflow from URL to content extraction."""
        url = sample_confluence_urls["pretty_url"]
        
        # Step 1: Parse URL
        page_id = URLResolver.extract_page_id(url)
        base_url = URLResolver.extract_base_url(url)
        
        assert page_id == "123456"
        assert base_url == "https://company.atlassian.net"
        
        # Step 2: Initialize client
        with patch('confluence2eml.client.subprocess') as mock_subprocess, \
             patch('confluence2eml.client.Path') as mock_path_class, \
             patch('confluence2eml.client.tempfile') as mock_tempfile:
            
            # Setup mocks
            mock_tmp_file = MagicMock()
            mock_tmp_file.name = "/tmp/test.md"
            mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_tmp_file
            mock_tempfile.NamedTemporaryFile.return_value.__exit__.return_value = None
            
            mock_path_instance = MagicMock()
            mock_path_instance.read_text.return_value = "# Test Page\n\nContent"
            mock_path_instance.unlink.return_value = None
            mock_path_class.return_value = mock_path_instance
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_subprocess.run.return_value = mock_result
            
            client = ConfluenceClient(
                base_url=base_url,
                user=mock_credentials["user"],
                token=mock_credentials["token"]
            )
            client._exporter = None  # Force subprocess path
            
            # Step 3: Extract content
            content = client.get_page_content(page_id)
            
            assert content['page_id'] == page_id
            assert 'markdown' in content
            assert 'title' in content
    
    @pytest.mark.parametrize("url_format", [
        "pretty_url",
        "page_id_url",
        "short_url",
        "url_with_special_chars",
    ])
    def test_various_url_formats(
        self, sample_confluence_urls, url_format, mock_credentials
    ):
        """Test that various URL formats work correctly."""
        url = sample_confluence_urls[url_format]
        
        page_id = URLResolver.extract_page_id(url)
        base_url = URLResolver.extract_base_url(url)
        
        assert page_id == "123456"
        assert "atlassian.net" in base_url or "company.com" in base_url
        
        # Verify client can be initialized
        with patch('confluence2eml.client.subprocess') as mock_subprocess, \
             patch('confluence2eml.client.Path') as mock_path_class, \
             patch('confluence2eml.client.tempfile') as mock_tempfile:
            
            mock_tmp_file = MagicMock()
            mock_tmp_file.name = "/tmp/test.md"
            mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_tmp_file
            mock_tempfile.NamedTemporaryFile.return_value.__exit__.return_value = None
            
            mock_path_instance = MagicMock()
            mock_path_instance.read_text.return_value = "# Test\n\nContent"
            mock_path_instance.unlink.return_value = None
            mock_path_class.return_value = mock_path_instance
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_subprocess.run.return_value = mock_result
            
            client = ConfluenceClient(
                base_url=base_url,
                user=mock_credentials["user"],
                token=mock_credentials["token"]
            )
            client._exporter = None
            
            # Should not raise an error
            content = client.get_page_content(page_id)
            assert content is not None
    
    def test_error_handling_invalid_url(self):
        """Test error handling for invalid URLs."""
        with pytest.raises(ConfluenceClientError):
            URLResolver.extract_page_id("https://example.com/not-confluence")
    
    def test_error_handling_authentication_failure(self, mock_credentials):
        """Test error handling for authentication failures."""
        with patch('confluence2eml.client.subprocess') as mock_subprocess:
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
    
    def test_error_handling_page_not_found(self, mock_credentials):
        """Test error handling for page not found."""
        with patch('confluence2eml.client.subprocess') as mock_subprocess, \
             patch('confluence2eml.client.tempfile') as mock_tempfile:
            
            mock_tmp_file = MagicMock()
            mock_tmp_file.name = "/tmp/test.md"
            mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_tmp_file
            mock_tempfile.NamedTemporaryFile.return_value.__exit__.return_value = None
            
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
            
            # The error handling in get_page_content checks for "404" or "not found"
            # and raises ConfluencePageNotFoundError
            from confluence2eml.client import ConfluencePageNotFoundError
            with pytest.raises(ConfluencePageNotFoundError):
                client.get_page_content("999999")

