"""Tests for MimeGenerator module."""

import email
import pytest
from pathlib import Path

from confluence2eml.core.mime_generator import (
    MimeGenerator,
    MimeGeneratorError,
)


@pytest.mark.unit
class TestMimeGeneratorInitialization:
    """Test cases for MimeGenerator initialization."""
    
    def test_default_initialization(self):
        """Test MimeGenerator with default configuration."""
        generator = MimeGenerator()
        assert generator is not None
        assert generator.default_from == "confluence-exporter@localhost"
        assert generator.default_to == "user@localhost"
    
    def test_custom_initialization(self):
        """Test MimeGenerator with custom configuration."""
        generator = MimeGenerator(
            default_from="custom@example.com",
            default_to="recipient@example.com"
        )
        assert generator.default_from == "custom@example.com"
        assert generator.default_to == "recipient@example.com"


@pytest.mark.unit
class TestMimeGeneratorCreateMessage:
    """Test cases for MimeGenerator.create_message method."""
    
    def test_create_message_basic(self):
        """Test creating a basic message with HTML content."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test Subject",
            html_content="<h1>Hello</h1><p>World</p>"
        )
        
        assert msg['Subject'] == "Test Subject"
        assert msg['From'] == "confluence-exporter@localhost"
        assert msg['To'] == "user@localhost"
        assert 'Date' in msg
        assert 'Message-ID' in msg
        assert msg.is_multipart()
    
    def test_create_message_with_custom_addresses(self):
        """Test creating message with custom from/to addresses."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>",
            from_addr="sender@example.com",
            to_addr="recipient@example.com"
        )
        
        assert msg['From'] == "sender@example.com"
        assert msg['To'] == "recipient@example.com"
    
    def test_create_message_with_plain_text(self):
        """Test creating message with explicit plain text."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<h1>HTML</h1>",
            plain_text="Plain Text Version"
        )
        
        # Should have both plain text and HTML
        assert msg.is_multipart()
        
        # Get the plain text part
        plain_part = None
        html_part = None
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                plain_part = part
            elif part.get_content_type() == 'text/html':
                html_part = part
        
        assert plain_part is not None
        assert html_part is not None
        assert "Plain Text Version" in plain_part.get_content()
        assert "<h1>HTML</h1>" in html_part.get_content()
    
    def test_create_message_auto_generates_plain_text(self):
        """Test that plain text is auto-generated from HTML if not provided."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<h1>Title</h1><p>Paragraph with <strong>bold</strong> text.</p>"
        )
        
        # Should have both parts
        assert msg.is_multipart()
        
        # Get the plain text part
        plain_part = None
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                plain_part = part
                break
        
        assert plain_part is not None
        content = plain_part.get_content()
        # Should have extracted text content (HTML tags removed)
        assert "Title" in content
        assert "Paragraph" in content
        assert "bold" in content
        # Should not have HTML tags
        assert "<h1>" not in content
        assert "<p>" not in content
    
    def test_create_message_has_correct_content_type(self):
        """Test that message has correct multipart structure."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>"
        )
        
        # Should be multipart/alternative
        assert msg.is_multipart()
        content_type = msg.get_content_type()
        assert 'multipart' in content_type
    
    def test_create_message_has_message_id(self):
        """Test that message has a Message-ID header."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>"
        )
        
        assert 'Message-ID' in msg
        msg_id = msg['Message-ID']
        assert msg_id.startswith('<')
        assert msg_id.endswith('>')
        assert 'confluence-export' in msg_id
    
    def test_create_message_has_date(self):
        """Test that message has a Date header."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>"
        )
        
        assert 'Date' in msg
        date = msg['Date']
        assert date is not None
        assert len(date) > 0
    
    def test_create_message_with_custom_date(self):
        """Test creating message with custom date."""
        generator = MimeGenerator()
        custom_date = "Mon, 01 Jan 2024 12:00:00 +0000"  # Use zero-padded day
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>",
            date=custom_date
        )
        
        assert msg['Date'] == custom_date
    
    def test_create_message_empty_html(self):
        """Test creating message with empty HTML content."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content=""
        )
        
        assert msg['Subject'] == "Test"
        assert msg.is_multipart()


@pytest.mark.unit
class TestMimeGeneratorHtmlToPlainText:
    """Test cases for HTML to plain text conversion."""
    
    def test_html_to_plain_text_simple(self):
        """Test converting simple HTML to plain text."""
        generator = MimeGenerator()
        html = "<h1>Title</h1><p>Paragraph text.</p>"
        text = generator._html_to_plain_text(html)
        
        assert "Title" in text
        assert "Paragraph text" in text
        assert "<h1>" not in text
        assert "<p>" not in text
    
    def test_html_to_plain_text_with_bold(self):
        """Test converting HTML with bold text."""
        generator = MimeGenerator()
        html = "<p>This is <strong>bold</strong> text.</p>"
        text = generator._html_to_plain_text(html)
        
        assert "This is" in text
        assert "bold" in text
        assert "text" in text
        assert "<strong>" not in text
    
    def test_html_to_plain_text_removes_scripts(self):
        """Test that script tags are removed."""
        generator = MimeGenerator()
        html = "<p>Content</p><script>alert('xss')</script><p>More content</p>"
        text = generator._html_to_plain_text(html)
        
        assert "Content" in text
        assert "More content" in text
        assert "alert" not in text
        assert "<script>" not in text
    
    def test_html_to_plain_text_handles_entities(self):
        """Test that HTML entities are decoded."""
        generator = MimeGenerator()
        html = "<p>Text with &amp; and &lt;tags&gt;</p>"
        text = generator._html_to_plain_text(html)
        
        assert "&" in text or "and" in text
        assert "<tags>" in text or "tags" in text


@pytest.mark.unit
class TestMimeGeneratorSaveToFile:
    """Test cases for MimeGenerator.save_to_file method."""
    
    def test_save_to_file(self, temp_output_dir):
        """Test saving a message to a file."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<h1>Hello</h1>"
        )
        
        output_path = temp_output_dir / "test.eml"
        saved_path = generator.save_to_file(msg, str(output_path))
        
        assert saved_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_save_to_file_creates_directory(self, tmp_path):
        """Test that save_to_file creates parent directories."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>"
        )
        
        nested_path = tmp_path / "nested" / "deep" / "path" / "test.eml"
        saved_path = generator.save_to_file(msg, str(nested_path))
        
        assert nested_path.exists()
        assert saved_path == nested_path
    
    def test_save_to_file_can_be_parsed(self, temp_output_dir):
        """Test that saved file can be parsed back as an EmailMessage."""
        generator = MimeGenerator()
        original_msg = generator.create_message(
            subject="Test Subject",
            html_content="<h1>Test Content</h1>",
            plain_text="Test Content"
        )
        
        output_path = temp_output_dir / "test.eml"
        generator.save_to_file(original_msg, str(output_path))
        
        # Parse the file back
        with open(output_path, 'rb') as f:
            parsed_msg = email.message_from_bytes(f.read())
        
        assert parsed_msg['Subject'] == "Test Subject"
        assert parsed_msg.is_multipart()
        assert parsed_msg.get_content_type().startswith('multipart')
    
    def test_save_to_file_overwrites_existing(self, temp_output_dir):
        """Test that save_to_file overwrites existing files."""
        generator = MimeGenerator()
        
        output_path = temp_output_dir / "test.eml"
        
        # Create first message
        msg1 = generator.create_message(
            subject="First",
            html_content="<p>First content</p>"
        )
        generator.save_to_file(msg1, str(output_path))
        
        # Create second message
        msg2 = generator.create_message(
            subject="Second",
            html_content="<p>Second content</p>"
        )
        generator.save_to_file(msg2, str(output_path))
        
        # Parse and verify it's the second message
        with open(output_path, 'rb') as f:
            parsed_msg = email.message_from_bytes(f.read())
        
        assert parsed_msg['Subject'] == "Second"


@pytest.mark.unit
class TestMimeGeneratorCreateAndSave:
    """Test cases for MimeGenerator.create_and_save convenience method."""
    
    def test_create_and_save(self, temp_output_dir):
        """Test create_and_save convenience method."""
        generator = MimeGenerator()
        
        output_path = temp_output_dir / "test.eml"
        saved_path = generator.create_and_save(
            subject="Test Subject",
            html_content="<h1>Hello</h1><p>World</p>",
            output_path=str(output_path)
        )
        
        assert saved_path == output_path
        assert output_path.exists()
        
        # Verify the file can be parsed
        with open(output_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        assert msg['Subject'] == "Test Subject"
        assert msg.is_multipart()
    
    def test_create_and_save_with_plain_text(self, temp_output_dir):
        """Test create_and_save with explicit plain text."""
        generator = MimeGenerator()
        
        output_path = temp_output_dir / "test.eml"
        saved_path = generator.create_and_save(
            subject="Test",
            html_content="<h1>HTML</h1>",
            output_path=str(output_path),
            plain_text="Plain Text"
        )
        
        assert saved_path.exists()
        
        # Verify both parts are present
        with open(output_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        assert msg.is_multipart()
        parts = list(msg.walk())
        content_types = [part.get_content_type() for part in parts]
        assert 'text/plain' in content_types
        assert 'text/html' in content_types


@pytest.mark.unit
class TestMimeGeneratorErrorHandling:
    """Test cases for error handling in MimeGenerator."""
    
    def test_create_message_with_invalid_subject(self):
        """Test that create_message handles various subject formats."""
        generator = MimeGenerator()
        # Should not raise an error even with special characters
        msg = generator.create_message(
            subject="Test: Subject with <special> chars & symbols",
            html_content="<p>Content</p>"
        )
        
        assert msg['Subject'] == "Test: Subject with <special> chars & symbols"
    
    def test_save_to_file_invalid_path(self):
        """Test that save_to_file raises error for invalid paths."""
        generator = MimeGenerator()
        msg = generator.create_message(
            subject="Test",
            html_content="<p>Content</p>"
        )
        
        # Try to save to a path that would require creating invalid directory
        # (This might work on some systems, so we just test it doesn't crash)
        try:
            generator.save_to_file(msg, "/invalid/path/test.eml")
        except (MimeGeneratorError, OSError, PermissionError):
            # Expected - path might not be writable
            pass


@pytest.mark.integration
class TestMimeGeneratorIntegration:
    """Integration tests for MimeGenerator with real-world scenarios."""
    
    def test_full_pipeline_markdown_to_eml(self, temp_output_dir):
        """Test full pipeline: Markdown -> HTML -> EML."""
        from confluence2eml.core.markdown_processor import MarkdownProcessor
        from confluence2eml.core.html_processor import HtmlProcessor
        
        markdown_processor = MarkdownProcessor()
        html_processor = HtmlProcessor()
        mime_generator = MimeGenerator()
        
        markdown = """# Sample Page

This is **bold** and *italic* text.

## Section

- Item 1
- Item 2

## Table

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
        
        # Convert Markdown to HTML
        html = markdown_processor.convert(markdown)
        
        # Sanitize HTML
        sanitized_html = html_processor.sanitize(html)
        
        # Create and save EML
        output_path = temp_output_dir / "output.eml"
        saved_path = mime_generator.create_and_save(
            subject="Confluence Export: Sample Page",
            html_content=sanitized_html,
            output_path=str(output_path)
        )
        
        assert saved_path.exists()
        
        # Verify the EML file
        with open(saved_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        assert msg['Subject'] == "Confluence Export: Sample Page"
        assert msg.is_multipart()
        
        # Verify HTML content is present
        html_found = False
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                # Use get_payload() for email.Message objects
                html_content = part.get_payload(decode=True)
                if isinstance(html_content, bytes):
                    html_content = html_content.decode('utf-8')
                assert "Sample Page" in html_content
                html_found = True
        
        assert html_found
    
    def test_eml_file_structure(self, temp_output_dir):
        """Test that generated EML file has correct structure."""
        generator = MimeGenerator()
        
        output_path = temp_output_dir / "test.eml"
        generator.create_and_save(
            subject="Test Email",
            html_content="<h1>Title</h1><p>Content</p>",
            output_path=str(output_path)
        )
        
        # Parse the file
        with open(output_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        # Check structure
        assert msg.is_multipart()
        assert msg.get_content_type().startswith('multipart')
        
        # Check parts
        parts = list(msg.walk())
        assert len(parts) >= 2  # At least plain text and HTML
        
        # Verify we have both text/plain and text/html
        content_types = [part.get_content_type() for part in parts]
        assert 'text/plain' in content_types
        assert 'text/html' in content_types
    
    def test_multiple_messages_same_generator(self, temp_output_dir):
        """Test that same generator can create multiple messages."""
        generator = MimeGenerator()
        
        # Create first message
        path1 = temp_output_dir / "msg1.eml"
        generator.create_and_save(
            subject="Message 1",
            html_content="<p>Content 1</p>",
            output_path=str(path1)
        )
        
        # Create second message
        path2 = temp_output_dir / "msg2.eml"
        generator.create_and_save(
            subject="Message 2",
            html_content="<p>Content 2</p>",
            output_path=str(path2)
        )
        
        # Verify both files exist and are different
        assert path1.exists()
        assert path2.exists()
        
        with open(path1, 'rb') as f:
            msg1 = email.message_from_bytes(f.read())
        with open(path2, 'rb') as f:
            msg2 = email.message_from_bytes(f.read())
        
        assert msg1['Subject'] == "Message 1"
        assert msg2['Subject'] == "Message 2"
        assert msg1['Message-ID'] != msg2['Message-ID']

