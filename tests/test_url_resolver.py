"""Tests for URLResolver module."""

import pytest

from confluence2eml.core.client import URLResolver, ConfluenceClientError


@pytest.mark.unit
class TestURLResolver:
    """Test cases for URLResolver class."""
    
    def test_extract_page_id_from_pretty_url(self, sample_confluence_urls):
        """Test extracting page ID from pretty URL format."""
        url = sample_confluence_urls["pretty_url"]
        page_id = URLResolver.extract_page_id(url)
        assert page_id == "123456"
    
    def test_extract_page_id_from_page_id_url(self, sample_confluence_urls):
        """Test extracting page ID from page ID URL format."""
        url = sample_confluence_urls["page_id_url"]
        page_id = URLResolver.extract_page_id(url)
        assert page_id == "123456"
    
    def test_extract_page_id_from_short_url(self, sample_confluence_urls):
        """Test extracting page ID from short viewpage URL format."""
        url = sample_confluence_urls["short_url"]
        page_id = URLResolver.extract_page_id(url)
        assert page_id == "123456"
    
    def test_extract_page_id_from_url_with_special_chars(self, sample_confluence_urls):
        """Test extracting page ID from URL with special characters."""
        url = sample_confluence_urls["url_with_special_chars"]
        page_id = URLResolver.extract_page_id(url)
        assert page_id == "123456"
    
    def test_extract_page_id_from_server_url_raises_error(self, sample_confluence_urls):
        """Test that server display URLs raise appropriate error."""
        url = sample_confluence_urls["server_url"]
        with pytest.raises(ConfluenceClientError) as exc_info:
            URLResolver.extract_page_id(url)
        assert "Server display URLs require API resolution" in str(exc_info.value)
    
    def test_extract_page_id_from_invalid_url_raises_error(self):
        """Test that invalid URLs raise appropriate error."""
        with pytest.raises(ConfluenceClientError) as exc_info:
            URLResolver.extract_page_id("https://example.com/not-a-confluence-url")
        assert "Could not extract page ID" in str(exc_info.value)
    
    def test_extract_page_id_from_empty_url_raises_error(self):
        """Test that empty URLs raise appropriate error."""
        with pytest.raises(ConfluenceClientError) as exc_info:
            URLResolver.extract_page_id("")
        assert "URL cannot be empty" in str(exc_info.value)
    
    def test_extract_page_id_from_none_raises_error(self):
        """Test that None URLs raise appropriate error."""
        with pytest.raises(ConfluenceClientError):
            URLResolver.extract_page_id(None)
    
    @pytest.mark.parametrize("url,expected_base", [
        ("https://company.atlassian.net/wiki/spaces/SPACE/pages/123456", 
         "https://company.atlassian.net"),
        ("https://confluence.company.com/display/SPACE/Page", 
         "https://confluence.company.com"),
        ("http://localhost:8090/wiki/spaces/SPACE/pages/123456", 
         "http://localhost:8090"),
    ])
    def test_extract_base_url(self, url, expected_base):
        """Test extracting base URL from various URL formats."""
        base_url = URLResolver.extract_base_url(url)
        assert base_url == expected_base
    
    def test_extract_base_url_from_empty_raises_error(self):
        """Test that empty URLs raise appropriate error."""
        with pytest.raises(ConfluenceClientError) as exc_info:
            URLResolver.extract_base_url("")
        assert "URL cannot be empty" in str(exc_info.value)
    
    def test_extract_base_url_from_invalid_raises_error(self):
        """Test that invalid URLs raise appropriate error."""
        with pytest.raises(ConfluenceClientError):
            URLResolver.extract_base_url("not-a-valid-url")

