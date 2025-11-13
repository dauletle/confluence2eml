"""Pytest configuration and shared fixtures for confluence2eml tests.

This module provides common fixtures and test utilities used across
all test modules in the test suite.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

import pytest


# Get the test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_confluence_urls() -> Dict[str, str]:
    """Return a dictionary of sample Confluence URLs for testing.
    
    Returns:
        Dictionary mapping URL type to URL string
    """
    return {
        "pretty_url": "https://company.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title",
        "page_id_url": "https://company.atlassian.net/wiki/spaces/SPACE/pages/123456",
        "short_url": "https://company.atlassian.net/wiki/pages/viewpage.action?pageId=123456",
        "url_with_special_chars": "https://company.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title+%28with+parentheses%29",
        "cloud_url": "https://company.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title",
        "server_url": "https://confluence.company.com/display/SPACE/Page+Title",
    }


@pytest.fixture
def sample_page_id() -> str:
    """Return a sample Confluence page ID for testing."""
    return "123456"


@pytest.fixture
def sample_page_title() -> str:
    """Return a sample Confluence page title for testing."""
    return "Sample Page Title"


@pytest.fixture
def sample_markdown_content() -> str:
    """Return sample Markdown content for testing."""
    return """# Sample Page Title

This is a sample Confluence page converted to Markdown.

## Section 1

Here is some **bold text** and *italic text*.

### Subsection

- Item 1
- Item 2
- Item 3

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

## Table

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |

## Link

[External Link](https://example.com)
"""


@pytest.fixture
def sample_html_content() -> str:
    """Return sample HTML content for testing."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Sample Page Title</title>
</head>
<body>
    <h1>Sample Page Title</h1>
    <p>This is a sample HTML content.</p>
    <img src="https://example.com/image.png" alt="Sample Image">
    <a href="https://example.com">External Link</a>
</body>
</html>
"""


@pytest.fixture
def sample_confluence_api_response(fixtures_dir: Path) -> Dict[str, Any]:
    """Load and return a sample Confluence API response from fixtures.
    
    Returns:
        Dictionary containing sample API response data
    """
    fixture_file = fixtures_dir / "confluence_api_response.json"
    if fixture_file.exists():
        with open(fixture_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Return a minimal sample response if fixture file doesn't exist
        return {
            "id": "123456",
            "type": "page",
            "title": "Sample Page Title",
            "space": {
                "key": "SPACE",
                "name": "Sample Space"
            },
            "body": {
                "storage": {
                    "value": "<p>Sample content</p>",
                    "representation": "storage"
                }
            }
        }


@pytest.fixture
def sample_attachment_metadata() -> list:
    """Return sample attachment metadata for testing."""
    return [
        {
            "id": "att1",
            "title": "document.pdf",
            "download_url": "https://company.atlassian.net/wiki/download/attachments/123456/document.pdf",
            "media_type": "application/pdf",
            "file_size": 102400
        },
        {
            "id": "att2",
            "title": "image.png",
            "download_url": "https://company.atlassian.net/wiki/download/attachments/123456/image.png",
            "media_type": "image/png",
            "file_size": 51200
        }
    ]


@pytest.fixture
def mock_credentials() -> Dict[str, str]:
    """Return mock Confluence credentials for testing."""
    return {
        "user": "test@example.com",
        "token": "test_api_token_12345"
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for test output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_markdown_file(tmp_path: Path, sample_markdown_content: str) -> Path:
    """Create a temporary Markdown file for testing."""
    md_file = tmp_path / "test_page.md"
    md_file.write_text(sample_markdown_content, encoding='utf-8')
    return md_file


@pytest.fixture
def temp_eml_file(tmp_path: Path) -> Path:
    """Return a path for a temporary EML file."""
    return tmp_path / "test_export.eml"


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test.
    
    This ensures tests don't interfere with each other through
    environment variable pollution.
    """
    # Clear Confluence-related environment variables
    env_vars = ['CONFLUENCE_USER', 'CONFLUENCE_TOKEN', 'CONFLUENCE_URL']
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

