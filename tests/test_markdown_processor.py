"""Tests for MarkdownProcessor module."""

import pytest
from pathlib import Path

from confluence2eml.core.markdown_processor import (
    MarkdownProcessor,
    MarkdownProcessorError,
)


@pytest.mark.unit
class TestMarkdownProcessorInitialization:
    """Test cases for MarkdownProcessor initialization."""
    
    def test_default_initialization(self):
        """Test MarkdownProcessor with default configuration."""
        processor = MarkdownProcessor()
        assert processor is not None
        assert 'tables' in processor.extensions
        assert 'fenced_code' in processor.extensions
        assert 'codehilite' in processor.extensions
    
    def test_custom_extensions(self):
        """Test MarkdownProcessor with custom extensions."""
        custom_extensions = ['tables', 'fenced_code']
        processor = MarkdownProcessor(extensions=custom_extensions)
        assert processor.extensions == custom_extensions
    
    def test_custom_extension_configs(self):
        """Test MarkdownProcessor with custom extension configurations."""
        custom_configs = {
            'codehilite': {
                'css_class': 'custom-highlight',
                'use_pygments': False,
            }
        }
        processor = MarkdownProcessor(extension_configs=custom_configs)
        assert processor.extension_configs['codehilite']['css_class'] == 'custom-highlight'
    
    def test_extension_configs_merge_with_defaults(self):
        """Test that custom configs merge with defaults."""
        custom_configs = {
            'codehilite': {
                'css_class': 'custom-highlight',
            }
        }
        processor = MarkdownProcessor(extension_configs=custom_configs)
        # Should have both custom and default configs
        assert processor.extension_configs['codehilite']['css_class'] == 'custom-highlight'
        assert 'use_pygments' in processor.extension_configs['codehilite']


@pytest.mark.unit
class TestMarkdownProcessorConvert:
    """Test cases for MarkdownProcessor.convert method."""
    
    def test_convert_simple_text(self):
        """Test converting simple Markdown text."""
        processor = MarkdownProcessor()
        markdown = "This is simple text."
        html = processor.convert(markdown)
        assert "<p>This is simple text.</p>" in html
    
    def test_convert_heading(self):
        """Test converting Markdown headings."""
        processor = MarkdownProcessor()
        markdown = "# Heading 1\n## Heading 2\n### Heading 3"
        html = processor.convert(markdown)
        assert "<h1>Heading 1</h1>" in html
        assert "<h2>Heading 2</h2>" in html
        assert "<h3>Heading 3</h3>" in html
    
    def test_convert_bold_and_italic(self):
        """Test converting bold and italic text."""
        processor = MarkdownProcessor()
        markdown = "This is **bold** and *italic* text."
        html = processor.convert(markdown)
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
    
    def test_convert_lists(self):
        """Test converting unordered and ordered lists."""
        processor = MarkdownProcessor()
        
        # Unordered list
        markdown = "- Item 1\n- Item 2\n- Item 3"
        html = processor.convert(markdown)
        assert "<ul>" in html
        assert "<li>Item 1</li>" in html
        assert "<li>Item 2</li>" in html
        assert "<li>Item 3</li>" in html
        
        # Ordered list
        markdown = "1. First\n2. Second\n3. Third"
        html = processor.convert(markdown)
        assert "<ol>" in html
        assert "<li>First</li>" in html
    
    def test_convert_links(self):
        """Test converting Markdown links."""
        processor = MarkdownProcessor()
        markdown = "[Link Text](https://example.com)"
        html = processor.convert(markdown)
        assert "<a href=\"https://example.com\">Link Text</a>" in html
    
    def test_convert_images(self):
        """Test converting Markdown images."""
        processor = MarkdownProcessor()
        markdown = "![Alt Text](https://example.com/image.png)"
        html = processor.convert(markdown)
        assert "<img" in html
        assert "alt=\"Alt Text\"" in html
        assert "src=\"https://example.com/image.png\"" in html
    
    def test_convert_code_inline(self):
        """Test converting inline code."""
        processor = MarkdownProcessor()
        markdown = "This is `inline code` in text."
        html = processor.convert(markdown)
        assert "<code>inline code</code>" in html
    
    def test_convert_code_block_fenced(self):
        """Test converting fenced code blocks."""
        processor = MarkdownProcessor()
        markdown = """```python
def hello():
    print("Hello, World!")
```"""
        html = processor.convert(markdown)
        assert "<pre>" in html
        assert "<code" in html
        assert "def hello()" in html
    
    def test_convert_tables(self):
        """Test converting Markdown tables."""
        processor = MarkdownProcessor()
        markdown = """| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |"""
        html = processor.convert(markdown)
        assert "<table>" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "<th>Column 1</th>" in html
        assert "<td>Value 1</td>" in html
    
    def test_convert_blockquote(self):
        """Test converting blockquotes."""
        processor = MarkdownProcessor()
        markdown = "> This is a quote\n> with multiple lines"
        html = processor.convert(markdown)
        assert "<blockquote>" in html
    
    def test_convert_horizontal_rule(self):
        """Test converting horizontal rules."""
        processor = MarkdownProcessor()
        markdown = "Text above\n\n---\n\nText below"
        html = processor.convert(markdown)
        assert "<hr" in html
    
    def test_convert_empty_string(self):
        """Test converting empty Markdown string."""
        processor = MarkdownProcessor()
        html = processor.convert("")
        # Empty string should produce empty or minimal HTML
        assert isinstance(html, str)
    
    def test_convert_multiline_content(self):
        """Test converting complex multiline Markdown content."""
        processor = MarkdownProcessor()
        markdown = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Section 1

- List item 1
- List item 2

### Subsection

Here's some `inline code` and a [link](https://example.com).

```python
def example():
    return True
```

| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |
"""
        html = processor.convert(markdown)
        assert "<h1>Main Title</h1>" in html
        assert "<h2>Section 1</h2>" in html
        assert "<h3>Subsection</h3>" in html
        assert "<ul>" in html
        assert "<table>" in html
        assert "<pre>" in html
    
    def test_convert_invalid_input_type(self):
        """Test that convert raises error for invalid input type."""
        processor = MarkdownProcessor()
        with pytest.raises(MarkdownProcessorError) as exc_info:
            processor.convert(123)  # type: ignore
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_convert_unicode_content(self):
        """Test converting Markdown with Unicode characters."""
        processor = MarkdownProcessor()
        markdown = "# Page with émojis 🎉\n\nContent with ñoño and 中文"
        html = processor.convert(markdown)
        assert "<h1>" in html
        # Unicode should be preserved in HTML
        assert "émojis" in html or "mojis" in html


@pytest.mark.unit
class TestMarkdownProcessorConvertFile:
    """Test cases for MarkdownProcessor.convert_file method."""
    
    def test_convert_file(self, temp_markdown_file):
        """Test converting a Markdown file to HTML."""
        processor = MarkdownProcessor()
        html = processor.convert_file(str(temp_markdown_file))
        
        assert isinstance(html, str)
        assert len(html) > 0
        # Should contain HTML from the sample markdown
        assert "<h1>" in html or "<p>" in html
    
    def test_convert_file_not_found(self, tmp_path):
        """Test that convert_file raises error for non-existent file."""
        processor = MarkdownProcessor()
        non_existent = tmp_path / "nonexistent.md"
        
        with pytest.raises(MarkdownProcessorError) as exc_info:
            processor.convert_file(str(non_existent))
        assert "not found" in str(exc_info.value).lower()
    
    def test_convert_file_custom_encoding(self, tmp_path):
        """Test converting file with custom encoding."""
        processor = MarkdownProcessor()
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent", encoding='utf-8')
        
        html = processor.convert_file(str(md_file), encoding='utf-8')
        assert "<h1>Test</h1>" in html
    
    def test_convert_file_with_complex_content(self, tmp_path, sample_markdown_content):
        """Test converting file with complex Markdown content."""
        processor = MarkdownProcessor()
        md_file = tmp_path / "complex.md"
        md_file.write_text(sample_markdown_content, encoding='utf-8')
        
        html = processor.convert_file(str(md_file))
        
        # Verify various elements are present
        assert "<h1>" in html or "<h2>" in html
        assert "<p>" in html
        assert "<ul>" in html or "<ol>" in html
        assert "<table>" in html
        assert "<pre>" in html or "<code>" in html


@pytest.mark.unit
class TestMarkdownProcessorExtensions:
    """Test cases for Markdown extensions functionality."""
    
    def test_tables_extension_works(self):
        """Test that tables extension is working."""
        processor = MarkdownProcessor()
        markdown = """| A | B |
|---|---|
| 1 | 2 |"""
        html = processor.convert(markdown)
        assert "<table>" in html
        assert "<thead>" in html
        assert "<tbody>" in html
    
    def test_fenced_code_extension_works(self):
        """Test that fenced_code extension is working."""
        processor = MarkdownProcessor()
        markdown = """```python
print("Hello")
```"""
        html = processor.convert(markdown)
        assert "<pre>" in html
        assert "<code" in html
    
    def test_codehilite_extension_works(self):
        """Test that codehilite extension is working."""
        processor = MarkdownProcessor()
        markdown = """```python
def test():
    return True
```"""
        html = processor.convert(markdown)
        # codehilite should add classes even if pygments is not used
        assert "<pre>" in html
        assert "<code" in html
    
    def test_extensions_without_codehilite(self):
        """Test processor with extensions excluding codehilite."""
        processor = MarkdownProcessor(extensions=['tables', 'fenced_code'])
        markdown = """```python
def test():
    return True
```"""
        html = processor.convert(markdown)
        assert "<pre>" in html
        assert "<code" in html


@pytest.mark.unit
class TestMarkdownProcessorErrorHandling:
    """Test cases for error handling in MarkdownProcessor."""
    
    def test_convert_handles_malformed_markdown_gracefully(self):
        """Test that convert handles malformed Markdown gracefully."""
        processor = MarkdownProcessor()
        # Malformed markdown should still produce some output
        markdown = "**unclosed bold\n\n[unclosed link"
        html = processor.convert(markdown)
        assert isinstance(html, str)
        assert len(html) > 0
    
    def test_error_message_includes_context(self):
        """Test that error messages include helpful context."""
        processor = MarkdownProcessor()
        with pytest.raises(MarkdownProcessorError) as exc_info:
            processor.convert(123)  # type: ignore
        error_msg = str(exc_info.value)
        assert "string" in error_msg.lower()


@pytest.mark.integration
class TestMarkdownProcessorIntegration:
    """Integration tests for MarkdownProcessor with real-world scenarios."""
    
    def test_full_page_conversion(self, sample_markdown_content):
        """Test converting a full page of Markdown content."""
        processor = MarkdownProcessor()
        html = processor.convert(sample_markdown_content)
        
        # Verify all major elements are present
        assert "<h1>" in html or "<h2>" in html  # Headings
        assert "<p>" in html  # Paragraphs
        assert "<ul>" in html or "<ol>" in html  # Lists
        assert "<table>" in html  # Tables
        assert "<pre>" in html or "<code>" in html  # Code blocks
        assert "<img" in html or "<a" in html  # Images or links
    
    def test_multiple_conversions_same_processor(self):
        """Test that same processor can handle multiple conversions."""
        processor = MarkdownProcessor()
        
        html1 = processor.convert("# First Document\n\nContent 1")
        html2 = processor.convert("# Second Document\n\nContent 2")
        
        assert "<h1>First Document</h1>" in html1
        assert "<h1>Second Document</h1>" in html2
        assert html1 != html2

