"""Tests for utility functions."""

import pytest
from pathlib import Path

from confluence2eml.core.utils import (
    sanitize_filename,
    generate_markdown_filename,
    save_markdown_file,
    load_email_css,
    wrap_html_with_css,
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


@pytest.mark.unit
class TestLoadEmailCss:
    """Test cases for load_email_css function."""
    
    def test_load_email_css_exists(self):
        """Test that CSS file can be loaded."""
        css = load_email_css()
        assert isinstance(css, str)
        assert len(css) > 0
    
    def test_load_email_css_contains_body_style(self):
        """Test that CSS contains body styling."""
        css = load_email_css()
        assert 'body {' in css or 'body{' in css.replace(' ', '')
    
    def test_load_email_css_contains_heading_styles(self):
        """Test that CSS contains heading styles."""
        css = load_email_css()
        assert 'h1 {' in css or 'h1{' in css.replace(' ', '')
        assert 'h2 {' in css or 'h2{' in css.replace(' ', '')
    
    def test_load_email_css_contains_table_styles(self):
        """Test that CSS contains table styling."""
        css = load_email_css()
        assert 'table {' in css or 'table{' in css.replace(' ', '')
        assert 'th {' in css or 'th{' in css.replace(' ', '')
        assert 'td {' in css or 'td{' in css.replace(' ', '')
    
    def test_load_email_css_contains_list_styles(self):
        """Test that CSS contains list styling."""
        css = load_email_css()
        assert 'ul {' in css or 'ul{' in css.replace(' ', '')
        assert 'ol {' in css or 'ol{' in css.replace(' ', '')
        assert 'li {' in css or 'li{' in css.replace(' ', '')
    
    def test_load_email_css_contains_link_styles(self):
        """Test that CSS contains link styling."""
        css = load_email_css()
        assert 'a {' in css or 'a{' in css.replace(' ', '')
    
    def test_load_email_css_contains_code_styles(self):
        """Test that CSS contains code block styling."""
        css = load_email_css()
        assert 'code {' in css or 'code{' in css.replace(' ', '')
        assert 'pre {' in css or 'pre{' in css.replace(' ', '')
    
    def test_load_email_css_contains_typography(self):
        """Test that CSS contains typography styles."""
        css = load_email_css()
        assert 'font-family' in css
        assert 'font-size' in css
        assert 'line-height' in css


@pytest.mark.unit
class TestWrapHtmlWithCss:
    """Test cases for wrap_html_with_css function."""
    
    def test_wrap_html_with_css_simple_content(self):
        """Test wrapping simple HTML content."""
        html = "<h1>Hello</h1><p>World</p>"
        wrapped = wrap_html_with_css(html)
        
        assert '<html' in wrapped.lower()
        assert '<head' in wrapped.lower()
        assert '<body' in wrapped.lower()
        assert '<style' in wrapped.lower()
        assert 'h1' in wrapped
        assert 'Hello' in wrapped
        assert 'World' in wrapped
    
    def test_wrap_html_with_css_includes_css(self):
        """Test that wrapped HTML includes CSS content."""
        html = "<p>Test</p>"
        wrapped = wrap_html_with_css(html)
        
        # Check that CSS is included in style tag
        assert '<style' in wrapped.lower()
        assert '</style>' in wrapped.lower()
        # CSS should contain body styling
        css_start = wrapped.lower().find('<style')
        css_end = wrapped.lower().find('</style>')
        css_content = wrapped[css_start:css_end]
        assert 'body' in css_content or 'font-family' in css_content
    
    def test_wrap_html_with_css_custom_css(self):
        """Test wrapping HTML with custom CSS content."""
        html = "<p>Test</p>"
        custom_css = "body { color: red; }"
        wrapped = wrap_html_with_css(html, css_content=custom_css)
        
        assert custom_css in wrapped
        assert 'color: red' in wrapped
    
    def test_wrap_html_with_css_already_has_html_structure(self):
        """Test wrapping HTML that already has html/head/body structure."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello</h1>
</body>
</html>"""
        wrapped = wrap_html_with_css(html)
        
        # Should still have the structure
        assert '<html' in wrapped.lower()
        assert '<head' in wrapped.lower()
        assert '<body' in wrapped.lower()
        # Should have style tag
        assert '<style' in wrapped.lower()
        # Should preserve original content
        assert 'Hello' in wrapped
    
    def test_wrap_html_with_css_has_body_tag_only(self):
        """Test wrapping HTML that has body tag but no html/head."""
        html = "<body><p>Content</p></body>"
        wrapped = wrap_html_with_css(html)
        
        assert '<html' in wrapped.lower()
        assert '<head' in wrapped.lower()
        assert '<body' in wrapped.lower()
        assert '<style' in wrapped.lower()
        assert 'Content' in wrapped
    
    def test_wrap_html_with_css_preserves_content(self):
        """Test that wrapping preserves all original content."""
        html = """<h1>Title</h1>
<p>Paragraph with <strong>bold</strong> text.</p>
<ul>
    <li>Item 1</li>
    <li>Item 2</li>
</ul>
<table>
    <tr><th>Header</th></tr>
    <tr><td>Data</td></tr>
</table>"""
        wrapped = wrap_html_with_css(html)
        
        assert 'Title' in wrapped
        assert 'Paragraph' in wrapped
        assert '<strong>bold</strong>' in wrapped
        assert 'Item 1' in wrapped
        assert 'Item 2' in wrapped
        assert '<table>' in wrapped
        assert 'Header' in wrapped
        assert 'Data' in wrapped
    
    def test_wrap_html_with_css_includes_meta_tags(self):
        """Test that wrapped HTML includes meta tags."""
        html = "<p>Test</p>"
        wrapped = wrap_html_with_css(html)
        
        assert 'charset' in wrapped.lower()
        assert 'utf-8' in wrapped.lower()
        assert 'viewport' in wrapped.lower() or 'meta' in wrapped.lower()
    
    def test_wrap_html_with_css_empty_content(self):
        """Test wrapping empty HTML content."""
        html = ""
        wrapped = wrap_html_with_css(html)
        
        assert '<html' in wrapped.lower()
        assert '<body' in wrapped.lower()
        assert '<style' in wrapped.lower()
    
    def test_wrap_html_with_css_complex_content(self):
        """Test wrapping complex HTML with various elements."""
        html = """<h1>Main Title</h1>
<h2>Subtitle</h2>
<p>Paragraph with <a href="http://example.com">link</a>.</p>
<blockquote>Quote text</blockquote>
<pre><code>code block</code></pre>
<img src="image.png" alt="Image">"""
        wrapped = wrap_html_with_css(html)
        
        assert 'Main Title' in wrapped
        assert 'Subtitle' in wrapped
        assert 'link' in wrapped
        assert 'Quote text' in wrapped
        assert 'code block' in wrapped
        assert 'image.png' in wrapped
    
    def test_wrap_html_with_css_doctype(self):
        """Test that wrapped HTML includes DOCTYPE."""
        html = "<p>Test</p>"
        wrapped = wrap_html_with_css(html)
        
        assert wrapped.strip().startswith('<!DOCTYPE')

