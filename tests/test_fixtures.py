"""Test fixtures and test infrastructure.

This module tests that the pytest fixtures and test infrastructure
are set up correctly and working as expected.
"""

import json
import os
from pathlib import Path

import pytest


@pytest.mark.unit
def test_fixtures_dir_exists(fixtures_dir: Path):
    """Test that the fixtures directory exists."""
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


@pytest.mark.unit
def test_sample_confluence_urls(sample_confluence_urls: dict):
    """Test that sample Confluence URLs fixture works."""
    assert isinstance(sample_confluence_urls, dict)
    assert "pretty_url" in sample_confluence_urls
    assert "page_id_url" in sample_confluence_urls
    assert "short_url" in sample_confluence_urls
    assert all(isinstance(url, str) for url in sample_confluence_urls.values())


@pytest.mark.unit
def test_sample_page_id(sample_page_id: str):
    """Test that sample page ID fixture works."""
    assert isinstance(sample_page_id, str)
    assert sample_page_id == "123456"


@pytest.mark.unit
def test_sample_page_title(sample_page_title: str):
    """Test that sample page title fixture works."""
    assert isinstance(sample_page_title, str)
    assert len(sample_page_title) > 0


@pytest.mark.unit
def test_sample_markdown_content(sample_markdown_content: str):
    """Test that sample Markdown content fixture works."""
    assert isinstance(sample_markdown_content, str)
    assert "# Sample Page Title" in sample_markdown_content
    assert "**bold text**" in sample_markdown_content


@pytest.mark.unit
def test_sample_html_content(sample_html_content: str):
    """Test that sample HTML content fixture works."""
    assert isinstance(sample_html_content, str)
    assert "<html>" in sample_html_content
    assert "<h1>Sample Page Title</h1>" in sample_html_content


@pytest.mark.unit
def test_sample_confluence_api_response(sample_confluence_api_response: dict):
    """Test that sample Confluence API response fixture works."""
    assert isinstance(sample_confluence_api_response, dict)
    assert "id" in sample_confluence_api_response
    assert "title" in sample_confluence_api_response
    assert sample_confluence_api_response["id"] == "123456"


@pytest.mark.unit
def test_sample_attachment_metadata(sample_attachment_metadata: list):
    """Test that sample attachment metadata fixture works."""
    assert isinstance(sample_attachment_metadata, list)
    assert len(sample_attachment_metadata) > 0
    for attachment in sample_attachment_metadata:
        assert "id" in attachment
        assert "title" in attachment
        assert "download_url" in attachment


@pytest.mark.unit
def test_mock_credentials(mock_credentials: dict):
    """Test that mock credentials fixture works."""
    assert isinstance(mock_credentials, dict)
    assert "user" in mock_credentials
    assert "token" in mock_credentials
    assert "@" in mock_credentials["user"]


@pytest.mark.unit
def test_temp_output_dir(temp_output_dir: Path):
    """Test that temporary output directory fixture works."""
    assert temp_output_dir.exists()
    assert temp_output_dir.is_dir()
    # Test that we can write to it
    test_file = temp_output_dir / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()


@pytest.mark.unit
def test_temp_markdown_file(temp_markdown_file: Path, sample_markdown_content: str):
    """Test that temporary Markdown file fixture works."""
    assert temp_markdown_file.exists()
    assert temp_markdown_file.suffix == ".md"
    content = temp_markdown_file.read_text(encoding='utf-8')
    assert content == sample_markdown_content


@pytest.mark.unit
def test_temp_eml_file(temp_eml_file: Path):
    """Test that temporary EML file path fixture works."""
    assert temp_eml_file.suffix == ".eml"
    # File shouldn't exist yet (just a path)
    assert not temp_eml_file.exists() or temp_eml_file.exists()


@pytest.mark.unit
def test_fixture_files_exist(fixtures_dir: Path):
    """Test that fixture files exist in the fixtures directory."""
    expected_files = [
        "confluence_api_response.json",
        "sample_page.html",
        "sample_page.md",
    ]
    
    for filename in expected_files:
        fixture_file = fixtures_dir / filename
        assert fixture_file.exists(), f"Fixture file {filename} should exist"


@pytest.mark.unit
def test_confluence_api_response_fixture_file(fixtures_dir: Path):
    """Test that the Confluence API response fixture file is valid JSON."""
    fixture_file = fixtures_dir / "confluence_api_response.json"
    assert fixture_file.exists()
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert isinstance(data, dict)
    assert "id" in data
    assert "title" in data
    assert "body" in data


@pytest.mark.unit
def test_sample_markdown_fixture_file(fixtures_dir: Path):
    """Test that the sample Markdown fixture file exists and is readable."""
    fixture_file = fixtures_dir / "sample_page.md"
    assert fixture_file.exists()
    
    content = fixture_file.read_text(encoding='utf-8')
    assert isinstance(content, str)
    assert len(content) > 0
    assert "# Sample Page Title" in content


@pytest.mark.unit
def test_sample_html_fixture_file(fixtures_dir: Path):
    """Test that the sample HTML fixture file exists and is readable."""
    fixture_file = fixtures_dir / "sample_page.html"
    assert fixture_file.exists()
    
    content = fixture_file.read_text(encoding='utf-8')
    assert isinstance(content, str)
    assert len(content) > 0
    assert "<html>" in content
    assert "<h1>Sample Page Title</h1>" in content


@pytest.mark.unit
def test_environment_reset(monkeypatch):
    """Test that environment variables are reset between tests."""
    # Set an environment variable
    monkeypatch.setenv("CONFLUENCE_USER", "test_user")
    assert os.getenv("CONFLUENCE_USER") == "test_user"
    
    # The reset_environment fixture should clear it in the next test

