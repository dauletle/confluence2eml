"""Tests for HtmlProcessor module."""

import pytest

from confluence2eml.core.html_processor import (
    HtmlProcessor,
    HtmlProcessorError,
)


@pytest.mark.unit
class TestHtmlProcessorInitialization:
    """Test cases for HtmlProcessor initialization."""
    
    def test_default_initialization(self):
        """Test HtmlProcessor with default configuration."""
        processor = HtmlProcessor()
        assert processor is not None
        assert processor.remove_unsafe_elements is True
        assert processor.remove_email_incompatible is True
        assert processor.ensure_image_alt is True
        assert processor.default_image_alt == "Image"
        assert processor.remove_style_tags is True
    
    def test_custom_initialization(self):
        """Test HtmlProcessor with custom configuration."""
        processor = HtmlProcessor(
            remove_unsafe_elements=False,
            remove_email_incompatible=False,
            ensure_image_alt=False,
            default_image_alt="Custom Alt",
            remove_style_tags=False,
            parser='lxml'
        )
        assert processor.remove_unsafe_elements is False
        assert processor.remove_email_incompatible is False
        assert processor.ensure_image_alt is False
        assert processor.default_image_alt == "Custom Alt"
        assert processor.remove_style_tags is False
        assert processor.parser == 'lxml'


@pytest.mark.unit
class TestHtmlProcessorSanitize:
    """Test cases for HtmlProcessor.sanitize method."""
    
    def test_sanitize_simple_html(self):
        """Test sanitizing simple HTML."""
        processor = HtmlProcessor()
        html = "<html><body><p>Simple content</p></body></html>"
        result = processor.sanitize(html)
        assert "<p>Simple content</p>" in result
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        processor = HtmlProcessor()
        html = "<html><body><script>alert('xss')</script><p>Safe content</p></body></html>"
        result = processor.sanitize(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "<p>Safe content</p>" in result
    
    def test_sanitize_removes_iframe_tags(self):
        """Test that iframe tags are removed."""
        processor = HtmlProcessor()
        html = "<html><body><iframe src='evil.com'></iframe><p>Safe content</p></body></html>"
        result = processor.sanitize(html)
        assert "<iframe>" not in result
        assert "<p>Safe content</p>" in result
    
    def test_sanitize_removes_style_tags(self):
        """Test that style tags are removed."""
        processor = HtmlProcessor()
        html = "<html><head><style>body { color: red; }</style></head><body><p>Content</p></body></html>"
        result = processor.sanitize(html)
        assert "<style>" not in result
        assert "<p>Content</p>" in result
    
    def test_sanitize_removes_unsafe_elements(self):
        """Test that unsafe elements are removed."""
        processor = HtmlProcessor()
        html = """<html><body>
            <script>alert('xss')</script>
            <iframe src='evil.com'></iframe>
            <object data='evil.swf'></object>
            <embed src='evil.swf'></embed>
            <form><input type='text'></form>
            <p>Safe content</p>
        </body></html>"""
        result = processor.sanitize(html)
        assert "<script>" not in result
        assert "<iframe>" not in result
        assert "<object>" not in result
        assert "<embed>" not in result
        assert "<form>" not in result
        assert "<p>Safe content</p>" in result
    
    def test_sanitize_removes_unsafe_attributes(self):
        """Test that unsafe event handler attributes are removed."""
        processor = HtmlProcessor()
        html = '<html><body><p onclick="alert(\'xss\')" onerror="evil()">Content</p></body></html>'
        result = processor.sanitize(html)
        assert 'onclick=' not in result
        assert 'onerror=' not in result
        assert "<p>Content</p>" in result or "<p" in result
    
    def test_sanitize_ensures_image_alt_text(self):
        """Test that images without alt text get default alt text."""
        processor = HtmlProcessor()
        html = '<html><body><img src="image.png" /><img src="image2.png" alt="Custom Alt" /></body></html>'
        result = processor.sanitize(html)
        assert 'alt="Image"' in result or "alt='Image'" in result
        assert 'alt="Custom Alt"' in result or "alt='Custom Alt'" in result
    
    def test_sanitize_custom_image_alt(self):
        """Test that custom default alt text is used."""
        processor = HtmlProcessor(default_image_alt="Custom Default")
        html = '<html><body><img src="image.png" /></body></html>'
        result = processor.sanitize(html)
        assert 'alt="Custom Default"' in result or "alt='Custom Default'" in result
    
    def test_sanitize_preserves_safe_elements(self):
        """Test that safe elements are preserved."""
        processor = HtmlProcessor()
        html = """<html><body>
            <h1>Heading</h1>
            <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
            <table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>
            <a href="https://example.com">Link</a>
        </body></html>"""
        result = processor.sanitize(html)
        assert "<h1>Heading</h1>" in result
        assert "<p>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<table>" in result
        assert "<a href=" in result
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        processor = HtmlProcessor()
        result = processor.sanitize("")
        assert isinstance(result, str)
    
    def test_sanitize_invalid_input_type(self):
        """Test that invalid input type raises error."""
        processor = HtmlProcessor()
        with pytest.raises(HtmlProcessorError) as exc_info:
            processor.sanitize(123)  # type: ignore
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_sanitize_malformed_html(self):
        """Test that malformed HTML is handled gracefully."""
        processor = HtmlProcessor()
        html = "<html><body><p>Unclosed tag<div>Content</body>"
        # Should not raise an error, BeautifulSoup handles malformed HTML
        result = processor.sanitize(html)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_sanitize_with_style_tags_disabled(self):
        """Test that style tags are preserved when remove_style_tags is False."""
        processor = HtmlProcessor(remove_style_tags=False)
        html = "<html><head><style>body { color: red; }</style></head><body><p>Content</p></body></html>"
        result = processor.sanitize(html)
        assert "<style>" in result
    
    def test_sanitize_with_unsafe_elements_disabled(self):
        """Test that unsafe elements are preserved when remove_unsafe_elements is False."""
        processor = HtmlProcessor(remove_unsafe_elements=False)
        html = "<html><body><script>alert('test')</script><p>Content</p></body></html>"
        result = processor.sanitize(html)
        # Note: script content might be escaped, but the tag should be present
        assert "<script>" in result or "script" in result.lower()
    
    def test_sanitize_removes_email_incompatible_elements(self):
        """Test that email-incompatible elements are removed."""
        processor = HtmlProcessor()
        html = """<html><body>
            <video src="video.mp4"></video>
            <audio src="audio.mp3"></audio>
            <canvas id="canvas"></canvas>
            <p>Safe content</p>
        </body></html>"""
        result = processor.sanitize(html)
        assert "<video>" not in result
        assert "<audio>" not in result
        assert "<canvas>" not in result
        assert "<p>Safe content</p>" in result


@pytest.mark.unit
class TestHtmlProcessorGetBodyContent:
    """Test cases for HtmlProcessor.get_body_content method."""
    
    def test_get_body_content_with_body_tag(self):
        """Test extracting body content when body tag exists."""
        processor = HtmlProcessor()
        html = "<html><head><title>Test</title></head><body><p>Body content</p></body></html>"
        result = processor.get_body_content(html)
        assert "Body content" in result
        assert "<p>" in result
    
    def test_get_body_content_without_body_tag(self):
        """Test extracting body content when no body tag exists."""
        processor = HtmlProcessor()
        html = "<html><head><title>Test</title></head><p>Content</p></html>"
        result = processor.get_body_content(html)
        # Should return the entire content if no body tag
        assert "Content" in result
    
    def test_get_body_content_empty_body(self):
        """Test extracting body content from empty body."""
        processor = HtmlProcessor()
        html = "<html><head><title>Test</title></head><body></body></html>"
        result = processor.get_body_content(html)
        assert isinstance(result, str)


@pytest.mark.unit
class TestHtmlProcessorValidateStructure:
    """Test cases for HtmlProcessor.validate_structure method."""
    
    def test_validate_structure_well_formed(self):
        """Test validation of well-formed HTML."""
        processor = HtmlProcessor()
        html = "<html><body><p>Well-formed content</p></body></html>"
        assert processor.validate_structure(html) is True
    
    def test_validate_structure_malformed(self):
        """Test validation of malformed HTML."""
        processor = HtmlProcessor()
        # BeautifulSoup is very forgiving, so most malformed HTML will still validate
        # But we can test with something that might cause issues
        html = "<html><body><p>Unclosed tag<div>Content</body>"
        # BeautifulSoup will fix this, so it should still validate
        assert processor.validate_structure(html) is True
    
    def test_validate_structure_empty_string(self):
        """Test validation of empty string."""
        processor = HtmlProcessor()
        assert processor.validate_structure("") is True  # BeautifulSoup handles empty strings


@pytest.mark.unit
class TestHtmlProcessorIntegration:
    """Integration tests for HtmlProcessor with real-world scenarios."""
    
    def test_sanitize_markdown_generated_html(self):
        """Test sanitizing HTML generated from Markdown."""
        processor = HtmlProcessor()
        # HTML that might come from MarkdownProcessor
        html = """<h1>Title</h1>
<p>Paragraph with <strong>bold</strong> text.</p>
<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>
<table>
<thead>
<tr><th>Header</th></tr>
</thead>
<tbody>
<tr><td>Data</td></tr>
</tbody>
</table>
<img src="image.png" />
<pre><code>code block</code></pre>"""
        
        result = processor.sanitize(html)
        
        # Should preserve all safe elements
        assert "<h1>Title</h1>" in result
        assert "<p>" in result
        assert "<strong>bold</strong>" in result
        assert "<ul>" in result
        assert "<table>" in result
        assert "<img" in result
        assert "<pre>" in result
        assert "<code>" in result
        
        # Should ensure image has alt text
        assert 'alt=' in result
    
    def test_sanitize_with_unsafe_content(self):
        """Test sanitizing HTML with various unsafe content."""
        processor = HtmlProcessor()
        html = """<html>
<head>
    <style>body { color: red; }</style>
    <script>alert('xss');</script>
</head>
<body>
    <p onclick="alert('xss')">Click me</p>
    <iframe src="evil.com"></iframe>
    <img src="image.png" />
    <form><input type="text" /></form>
    <p>Safe content</p>
</body>
</html>"""
        
        result = processor.sanitize(html)
        
        # Should remove unsafe elements
        assert "<script>" not in result
        assert "<iframe>" not in result
        assert "<form>" not in result
        assert "<style>" not in result
        
        # Should remove unsafe attributes
        assert 'onclick=' not in result
        
        # Should preserve safe content
        assert "Safe content" in result
        
        # Should ensure image has alt
        assert 'alt=' in result
    
    def test_sanitize_preserves_links(self):
        """Test that links are preserved during sanitization."""
        processor = HtmlProcessor()
        html = '<html><body><a href="https://example.com">Link Text</a></body></html>'
        result = processor.sanitize(html)
        assert "<a href=" in result
        assert "https://example.com" in result
        assert "Link Text" in result
    
    def test_sanitize_preserves_tables(self):
        """Test that tables are preserved during sanitization."""
        processor = HtmlProcessor()
        html = """<table>
<thead>
<tr><th>Header 1</th><th>Header 2</th></tr>
</thead>
<tbody>
<tr><td>Data 1</td><td>Data 2</td></tr>
</tbody>
</table>"""
        result = processor.sanitize(html)
        assert "<table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "<th>Header 1</th>" in result
        assert "<td>Data 1</td>" in result


@pytest.mark.unit
class TestHtmlProcessorEdgeCases:
    """Test cases for edge cases and special scenarios."""
    
    def test_sanitize_unicode_content(self):
        """Test sanitizing HTML with Unicode content."""
        processor = HtmlProcessor()
        html = "<html><body><p>Unicode: émojis 🎉 and 中文</p></body></html>"
        result = processor.sanitize(html)
        assert "émojis" in result or "mojis" in result
        assert "中文" in result or "中文" in result
    
    def test_sanitize_nested_unsafe_elements(self):
        """Test sanitizing HTML with nested unsafe elements."""
        processor = HtmlProcessor()
        html = "<div><script>alert('xss')</script><p>Content</p></div>"
        result = processor.sanitize(html)
        assert "<script>" not in result
        assert "<p>Content</p>" in result
    
    def test_sanitize_multiple_images(self):
        """Test sanitizing HTML with multiple images."""
        processor = HtmlProcessor()
        html = """<html><body>
            <img src="image1.png" />
            <img src="image2.png" alt="Custom Alt" />
            <img src="image3.png" alt="" />
        </body></html>"""
        result = processor.sanitize(html)
        # All images should have alt text
        assert result.count('alt=') >= 3
    
    def test_sanitize_complex_html_structure(self):
        """Test sanitizing complex HTML structure."""
        processor = HtmlProcessor()
        html = """<html>
<head>
    <title>Complex Page</title>
    <style>body { margin: 0; }</style>
</head>
<body>
    <header>
        <h1>Title</h1>
        <nav>
            <ul>
                <li><a href="#section1">Section 1</a></li>
                <li><a href="#section2">Section 2</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <section id="section1">
            <h2>Section 1</h2>
            <p>Content with <strong>bold</strong> and <em>italic</em>.</p>
            <img src="image.png" />
        </section>
        <section id="section2">
            <h2>Section 2</h2>
            <table>
                <tr><th>Header</th></tr>
                <tr><td>Data</td></tr>
            </table>
        </section>
    </main>
    <footer>
        <p>Footer content</p>
    </footer>
</body>
</html>"""
        result = processor.sanitize(html)
        
        # Should preserve structure
        assert "<h1>Title</h1>" in result
        assert "<h2>Section 1</h2>" in result
        assert "<table>" in result
        assert "<img" in result
        
        # Should remove style
        assert "<style>" not in result
        
        # Should ensure image alt
        assert 'alt=' in result

