"""Integration tests for Markdown file saving in the main workflow."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from confluence2eml.core.utils import generate_markdown_filename, save_markdown_file
from confluence2eml.core.client import ConfluenceClient


@pytest.mark.integration
class TestMarkdownSavingIntegration:
    """Integration tests for Markdown file saving in complete workflow."""
    
    def test_markdown_saving_with_various_titles(
        self, temp_output_dir, mock_credentials, sample_markdown_content
    ):
        """Test Markdown file saving with various page titles."""
        test_titles = [
            "Simple Page Title",
            "Page: With/Invalid\\Chars?",
            "Page <Important>",
            "Page with émojis 🎉",
            "  Page with spaces  ",
            "Page...with...dots...",
        ]
        
        for title in test_titles:
            # Generate filename
            markdown_path = generate_markdown_filename(title, temp_output_dir)
            
            # Save content
            saved_path = save_markdown_file(sample_markdown_content, markdown_path)
            
            # Verify file exists and has correct content
            assert saved_path.exists(), f"File should exist for title: {title}"
            assert saved_path.read_text(encoding='utf-8') == sample_markdown_content
            assert saved_path.suffix == ".md"
            
            # Verify filename is sanitized
            assert ":" not in saved_path.name
            assert "/" not in saved_path.name
            assert "\\" not in saved_path.name
    
    def test_markdown_saving_in_output_directory(self, tmp_path, mock_credentials):
        """Test that Markdown file is saved in the same directory as EML output."""
        # Simulate EML output path
        eml_output_path = tmp_path / "output" / "export.eml"
        output_dir = eml_output_path.parent
        
        # Generate Markdown filename in same directory
        page_title = "Test Page Title"
        markdown_path = generate_markdown_filename(page_title, output_dir)
        
        # Save content
        content = "# Test Page\n\nContent here"
        save_markdown_file(content, markdown_path)
        
        # Verify both files would be in same directory
        assert markdown_path.parent == output_dir
        assert markdown_path.exists()
        assert markdown_path.name == "Test Page Title.md"
    
    def test_markdown_saving_with_empty_title(self, temp_output_dir, sample_markdown_content):
        """Test Markdown file saving handles empty page title."""
        markdown_path = generate_markdown_filename("", temp_output_dir)
        
        save_markdown_file(sample_markdown_content, markdown_path)
        
        assert markdown_path.exists()
        assert markdown_path.name == "untitled.md"
        assert markdown_path.read_text(encoding='utf-8') == sample_markdown_content
    
    def test_markdown_saving_with_very_long_title(self, temp_output_dir, sample_markdown_content):
        """Test Markdown file saving handles very long page titles."""
        long_title = "A" * 500  # Very long title
        markdown_path = generate_markdown_filename(long_title, temp_output_dir)
        
        save_markdown_file(sample_markdown_content, markdown_path)
        
        assert markdown_path.exists()
        # Filename should be truncated but still valid
        assert len(markdown_path.name) <= 200 + len(".md")  # max_length + extension
        assert markdown_path.read_text(encoding='utf-8') == sample_markdown_content
    
    @patch('confluence2eml.core.client.subprocess')
    @patch('confluence2eml.core.client.Path')
    @patch('confluence2eml.core.client.tempfile')
    def test_complete_workflow_with_markdown_saving(
        self, mock_tempfile, mock_path_class, mock_subprocess,
        temp_output_dir, mock_credentials, sample_markdown_content
    ):
        """Test complete workflow including Markdown file saving."""
        # Setup mocks for ConfluenceClient
        mock_tmp_file = MagicMock()
        mock_tmp_file.name = "/tmp/test.md"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_tmp_file
        mock_tempfile.NamedTemporaryFile.return_value.__exit__.return_value = None
        
        mock_path_instance = MagicMock()
        mock_path_instance.read_text.return_value = sample_markdown_content
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
        client._exporter = None
        
        # Get page content
        page_content = client.get_page_content("123456")
        
        # Simulate Markdown saving (as done in main script)
        page_title = page_content.get('title', 'Unknown')
        markdown_path = generate_markdown_filename(page_title, temp_output_dir)
        saved_path = save_markdown_file(
            content=page_content.get('markdown', ''),
            filepath=markdown_path
        )
        
        # Verify Markdown file was saved
        assert saved_path.exists()
        assert saved_path.read_text(encoding='utf-8') == sample_markdown_content
        assert saved_path.suffix == ".md"

