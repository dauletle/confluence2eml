"""MIME message generation for EML file creation.

This module provides functionality to create MIME email messages and
serialize them to .eml format for email clients.
"""

import logging
import mimetypes
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MimeGeneratorError(Exception):
    """Base exception for MimeGenerator errors."""
    pass


class MimeGenerator:
    """Generator for creating MIME email messages and EML files.
    
    This class handles the creation of email messages using Python's
    email.message.EmailMessage class. It supports:
    - HTML and plain text content
    - Basic multipart message structure
    - Serialization to .eml format
    
    Example:
        >>> generator = MimeGenerator()
        >>> msg = generator.create_message(
        ...     subject="Test Email",
        ...     html_content="<h1>Hello</h1><p>World</p>",
        ...     plain_text="Hello World"
        ... )
        >>> generator.save_to_file(msg, "output.eml")
    """
    
    def __init__(
        self,
        default_from: Optional[str] = None,
        default_to: Optional[str] = None
    ):
        """Initialize the MimeGenerator.
        
        Args:
            default_from: Default 'From' address for messages
                         (default: "confluence-exporter@localhost")
            default_to: Default 'To' address for messages
                      (default: "user@localhost")
        """
        self.default_from = default_from or "confluence-exporter@localhost"
        self.default_to = default_to or "user@localhost"
        
        logger.debug(
            f"MimeGenerator initialized: from={self.default_from}, to={self.default_to}"
        )
    
    def create_message(
        self,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
        from_addr: Optional[str] = None,
        to_addr: Optional[str] = None,
        date: Optional[str] = None
    ) -> EmailMessage:
        """Create an EmailMessage with HTML and optional plain text content.
        
        Args:
            subject: Email subject line
            html_content: HTML content for the email body
            plain_text: Optional plain text fallback content.
                       If not provided, a simple text version is generated
                       from HTML by stripping tags.
            from_addr: 'From' email address (default: uses default_from)
            to_addr: 'To' email address (default: uses default_to)
            date: Email date (default: current date/time)
            
        Returns:
            EmailMessage object ready for serialization
            
        Raises:
            MimeGeneratorError: If message creation fails
            
        Example:
            >>> generator = MimeGenerator()
            >>> msg = generator.create_message(
            ...     subject="Test",
            ...     html_content="<h1>Hello</h1>"
            ... )
            >>> assert msg['Subject'] == "Test"
        """
        try:
            logger.debug("Creating EmailMessage...")
            logger.debug(f"Subject: {subject}")
            
            # Create the message
            msg = EmailMessage()
            
            # Set headers
            msg['Subject'] = subject
            msg['From'] = from_addr or self.default_from
            msg['To'] = to_addr or self.default_to
            msg['Date'] = date or formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='confluence-export')
            
            # Generate plain text if not provided
            if plain_text is None:
                plain_text = self._html_to_plain_text(html_content)
            
            # Set plain text as the primary content
            msg.set_content(plain_text)
            
            # Add HTML as an alternative
            msg.add_alternative(html_content, subtype='html')
            
            logger.debug("EmailMessage created successfully")
            logger.debug(f"Message is multipart: {msg.is_multipart()}")
            logger.debug(f"Content type: {msg.get_content_type()}")
            
            return msg
            
        except Exception as e:
            error_msg = f"Failed to create EmailMessage: {e}"
            logger.error(error_msg, exc_info=True)
            raise MimeGeneratorError(error_msg) from e
    
    def _html_to_plain_text(self, html_content: str) -> str:
        """Convert HTML to plain text by stripping tags.
        
        This is a simple implementation. For production use, consider
        using a library like html2text or BeautifulSoup for better
        conversion.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Plain text version of the HTML
        """
        import re
        
        # Remove script and style content
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Replace common block elements with newlines
        html_content = re.sub(r'</(p|div|h[1-6]|li|tr|br)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities (basic)
        html_content = html_content.replace('&nbsp;', ' ')
        html_content = html_content.replace('&amp;', '&')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&quot;', '"')
        html_content = html_content.replace('&#39;', "'")
        
        # Clean up whitespace
        html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)  # Multiple newlines to double
        html_content = html_content.strip()
        
        return html_content
    
    def save_to_file(
        self,
        message: EmailMessage,
        filepath: str,
        encoding: str = 'utf-8'
    ) -> Path:
        """Save an EmailMessage to a .eml file.
        
        Args:
            message: EmailMessage object to serialize
            filepath: Path where the .eml file should be saved
            encoding: File encoding (default: 'utf-8')
            
        Returns:
            Path to the saved file
            
        Raises:
            MimeGeneratorError: If file cannot be written
            
        Example:
            >>> generator = MimeGenerator()
            >>> msg = generator.create_message("Test", "<h1>Hello</h1>")
            >>> path = generator.save_to_file(msg, "output.eml")
            >>> assert path.exists()
        """
        try:
            file_path = Path(filepath)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Saving EmailMessage to file: {file_path}")
            
            # Serialize the message to bytes
            message_bytes = message.as_bytes()
            
            # Write to file
            file_path.write_bytes(message_bytes)
            
            logger.info(f"EML file saved successfully: {file_path}")
            logger.debug(f"File size: {file_path.stat().st_size} bytes")
            
            return file_path
            
        except Exception as e:
            error_msg = f"Failed to save EML file: {e}"
            logger.error(error_msg, exc_info=True)
            raise MimeGeneratorError(error_msg) from e
    
    def create_and_save(
        self,
        subject: str,
        html_content: str,
        output_path: str,
        plain_text: Optional[str] = None,
        from_addr: Optional[str] = None,
        to_addr: Optional[str] = None
    ) -> Path:
        """Create a message and save it to a file in one step.
        
        This is a convenience method that combines create_message and save_to_file.
        
        Args:
            subject: Email subject line
            html_content: HTML content for the email body
            output_path: Path where the .eml file should be saved
            plain_text: Optional plain text fallback content
            from_addr: 'From' email address
            to_addr: 'To' email address
            
        Returns:
            Path to the saved file
            
        Raises:
            MimeGeneratorError: If message creation or file saving fails
        """
        msg = self.create_message(
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
            from_addr=from_addr,
            to_addr=to_addr
        )
        return self.save_to_file(msg, output_path)

