"""Tests for utility functions."""

import pytest
from pathlib import Path

from confluence2eml.utils import (
    sanitize_filename,
    generate_markdown_filename,
    save_markdown_file,
)


@pytest.mark.unit
class TestSanitizeFilename:
    """Test cases for sanitize_filename function."""
    
    def test_simple_title(self):
        """Test sanitization of a simple, valid title."""
        result = sanitize_filename("My Page Title")
        assert result == "My Page Title"
    
    def test_title_with_invalid_chars(self):
        """Test sanitization removes invalid filesystem characters."""
        result = sanitize_filename('Page: With/Invalid\\Chars?')
        assert ':' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '?' not in result
        assert result == "Page With Invalid Chars"
    
    def test_title_with_angle_brackets(self):
        """Test sanitization removes angle brackets."""
        result = sanitize_filename("Page <Important>")
        assert '<' not in result
        assert '>' not in result
        assert result == "Page Important"
    
    def test_title_with_quotes(self):
        """Test sanitization removes quotes."""
        result = sanitize_filename('Page "Quoted" Title')
        assert '"' not in result
        assert result == "Page Quoted Title"
    
    def test_title_with_pipe(self):
        """Test sanitization removes pipe character."""
        result = sanitize_filename("Page | Separated")
        assert '|' not in result
        assert result == "Page Separated"
    
    def test_title_with_asterisk(self):
        """Test sanitization removes asterisk."""
        result = sanitize_filename("Page * Important")
        assert '*' not in result
        assert result == "Page Important"
    
    def test_title_with_multiple_spaces(self):
        """Test sanitization collapses multiple spaces."""
        result = sanitize_filename("Page   With    Multiple    Spaces")
        assert "  " not in result
        assert result == "Page With Multiple Spaces"
    
    def test_title_with_leading_trailing_spaces(self):
        """Test sanitization removes leading/trailing spaces."""
        result = sanitize_filename("  Page Title  ")
        assert result == "Page Title"
    
    def test_title_with_trailing_dots(self):
        """Test sanitization removes trailing dots (Windows restriction)."""
        result = sanitize_filename("Page Title...")
        assert not result.endswith('.')
        assert result == "Page Title"
    
    def test_empty_title(self):
        """Test sanitization handles empty title."""
        result = sanitize_filename("")
        assert result == "untitled"
    
    def test_whitespace_only_title(self):
        """Test sanitization handles whitespace-only title."""
        result = sanitize_filename("   ")
        assert result == "untitled"
    
    def test_title_with_only_invalid_chars(self):
        """Test sanitization handles title with only invalid characters."""
        result = sanitize_filename("<>:\"/\\|?*")
        assert result == "untitled"
    
    def test_title_truncation(self):
        """Test sanitization truncates very long titles."""
        long_title = "A" * 300
        result = sanitize_filename(long_title, max_length=50)
        assert len(result) <= 50
    
    def test_title_with_unicode(self):
        """Test sanitization preserves valid Unicode characters."""
        result = sanitize_filename("Page with émojis 🎉 and ñoño")
        # Unicode should be preserved (valid in most filesystems)
        assert "émojis" in result or "mojis" in result
        assert "ñoño" in result or "nono" in result
    
    def test_title_with_control_characters(self):
        """Test sanitization removes control characters."""
        result = sanitize_filename("Page\x00With\x1fControl\x02Chars")
        assert '\x00' not in result
        assert '\x1f' not in result
        assert '\x02' not in result


@pytest.mark.unit
class TestGenerateMarkdownFilename:
    """Test cases for generate_markdown_filename function."""
    
    def test_simple_title_no_directory(self):
        """Test filename generation from simple title without directory."""
        result = generate_markdown_filename("My Page Title")
        assert isinstance(result, Path)
        assert result.name == "My Page Title.md"
        assert result.parent == Path('.')
    
    def test_title_with_directory(self):
        """Test filename generation with output directory."""
        output_dir = Path("/tmp/output")
        result = generate_markdown_filename("My Page Title", output_dir)
        assert isinstance(result, Path)
        assert result.name == "My Page Title.md"
        assert result.parent == output_dir
    
    def test_title_with_invalid_chars(self):
        """Test filename generation sanitizes invalid characters."""
        result = generate_markdown_filename("Page: With/Invalid\\Chars?")
        assert result.name == "Page With Invalid Chars.md"
    
    def test_empty_title(self):
        """Test filename generation handles empty title."""
        result = generate_markdown_filename("")
        assert result.name == "untitled.md"
    
    def test_always_adds_md_extension(self):
        """Test that .md extension is always added."""
        result = generate_markdown_filename("Some Title")
        assert result.suffix == ".md"
        assert result.name.endswith(".md")


@pytest.mark.unit
class TestSaveMarkdownFile:
    """Test cases for save_markdown_file function."""
    
    def test_save_markdown_file(self, temp_output_dir, sample_markdown_content):
        """Test saving Markdown content to a file."""
        filepath = temp_output_dir / "test_page.md"
        
        saved_path = save_markdown_file(sample_markdown_content, filepath)
        
        assert saved_path == filepath
        assert filepath.exists()
        assert filepath.read_text(encoding='utf-8') == sample_markdown_content
    
    def test_save_markdown_file_creates_directory(self, tmp_path, sample_markdown_content):
        """Test that save_markdown_file creates parent directories."""
        nested_dir = tmp_path / "nested" / "deep" / "path"
        filepath = nested_dir / "test_page.md"
        
        # Directory shouldn't exist yet
        assert not nested_dir.exists()
        
        saved_path = save_markdown_file(sample_markdown_content, filepath)
        
        # Directory should be created
        assert nested_dir.exists()
        assert filepath.exists()
        assert saved_path.read_text(encoding='utf-8') == sample_markdown_content
    
    def test_save_markdown_file_overwrites_existing(self, temp_output_dir, sample_markdown_content):
        """Test that save_markdown_file overwrites existing files."""
        filepath = temp_output_dir / "test_page.md"
        
        # Create file with initial content
        filepath.write_text("Initial content", encoding='utf-8')
        assert filepath.read_text(encoding='utf-8') == "Initial content"
        
        # Save new content
        saved_path = save_markdown_file(sample_markdown_content, filepath)
        
        # Content should be overwritten
        assert saved_path.read_text(encoding='utf-8') == sample_markdown_content
    
    def test_save_markdown_file_unicode_content(self, temp_output_dir):
        """Test saving Markdown file with Unicode content."""
        unicode_content = "# Page with émojis 🎉\n\nContent with ñoño and 中文"
        filepath = temp_output_dir / "unicode_page.md"
        
        saved_path = save_markdown_file(unicode_content, filepath)
        
        assert saved_path.exists()
        assert saved_path.read_text(encoding='utf-8') == unicode_content
    
    def test_save_markdown_file_empty_content(self, temp_output_dir):
        """Test saving Markdown file with empty content."""
        filepath = temp_output_dir / "empty_page.md"
        
        saved_path = save_markdown_file("", filepath)
        
        assert saved_path.exists()
        assert saved_path.read_text(encoding='utf-8') == ""

