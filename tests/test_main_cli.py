"""Tests for main CLI module."""

import email
import os
import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from confluence2eml.core.client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
)
from confluence2eml.core.html_processor import HtmlProcessorError
from confluence2eml.core.markdown_processor import MarkdownProcessorError
from confluence2eml.core.mime_generator import MimeGeneratorError


@pytest.mark.unit
class TestCLIArgumentParsing:
    """Test cases for CLI argument parsing."""
    
    def test_parse_arguments_required_url(self):
        """Test that --url is required."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', ['confluence2eml', '--output', 'test.eml']):
            with pytest.raises(SystemExit):
                parse_arguments()
    
    def test_parse_arguments_required_output(self):
        """Test that --output is required."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', ['confluence2eml', '--url', 'https://example.com/wiki/pages/123']):
            with pytest.raises(SystemExit):
                parse_arguments()
    
    def test_parse_arguments_with_all_required(self):
        """Test parsing with all required arguments."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123',
            '--output', 'test.eml'
        ]):
            args = parse_arguments()
            
            assert args.url == 'https://example.com/wiki/pages/123'
            assert args.output == 'test.eml'
    
    def test_parse_arguments_with_optional_user_token(self):
        """Test parsing with optional user and token."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123',
            '--output', 'test.eml',
            '--user', 'user@example.com',
            '--token', 'token123'
        ]):
            args = parse_arguments()
            
            assert args.user == 'user@example.com'
            assert args.token == 'token123'
    
    def test_parse_arguments_verbose_flag(self):
        """Test parsing with verbose flag."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123',
            '--output', 'test.eml',
            '--verbose'
        ]):
            args = parse_arguments()
            
            assert args.verbose is True
    
    def test_parse_arguments_short_verbose_flag(self):
        """Test parsing with short verbose flag."""
        from confluence2eml.main import parse_arguments
        
        with patch.object(sys, 'argv', [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123',
            '--output', 'test.eml',
            '-v'
        ]):
            args = parse_arguments()
            
            assert args.verbose is True


@pytest.mark.unit
class TestCLICredentials:
    """Test cases for credential handling."""
    
    def test_get_credentials_from_args(self):
        """Test getting credentials from CLI arguments."""
        from confluence2eml.main import get_credentials
        
        class Args:
            user = 'user@example.com'
            token = 'token123'
        
        args = Args()
        user, token = get_credentials(args)
        
        assert user == 'user@example.com'
        assert token == 'token123'
    
    def test_get_credentials_from_env(self, monkeypatch):
        """Test getting credentials from environment variables."""
        from confluence2eml.main import get_credentials
        
        monkeypatch.setenv('CONFLUENCE_USER', 'env_user@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'env_token123')
        
        class Args:
            user = None
            token = None
        
        args = Args()
        user, token = get_credentials(args)
        
        assert user == 'env_user@example.com'
        assert token == 'env_token123'
    
    def test_get_credentials_args_override_env(self, monkeypatch):
        """Test that CLI arguments override environment variables."""
        from confluence2eml.main import get_credentials
        
        monkeypatch.setenv('CONFLUENCE_USER', 'env_user@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'env_token123')
        
        class Args:
            user = 'arg_user@example.com'
            token = 'arg_token123'
        
        args = Args()
        user, token = get_credentials(args)
        
        assert user == 'arg_user@example.com'
        assert token == 'arg_token123'
    
    def test_get_credentials_missing_user(self):
        """Test that missing user raises ValueError."""
        from confluence2eml.main import get_credentials
        
        class Args:
            user = None
            token = 'token123'
        
        args = Args()
        with pytest.raises(ValueError) as exc_info:
            get_credentials(args)
        
        assert 'user' in str(exc_info.value).lower()
    
    def test_get_credentials_missing_token(self):
        """Test that missing token raises ValueError."""
        from confluence2eml.main import get_credentials
        
        class Args:
            user = 'user@example.com'
            token = None
        
        args = Args()
        with pytest.raises(ValueError) as exc_info:
            get_credentials(args)
        
        assert 'token' in str(exc_info.value).lower()


@pytest.mark.unit
class TestCLIMainFunction:
    """Test cases for main() function."""
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    @patch('confluence2eml.main.MarkdownProcessor')
    @patch('confluence2eml.main.HtmlProcessor')
    @patch('confluence2eml.main.MimeGenerator')
    def test_main_successful_export(
        self,
        mock_mime_gen,
        mock_html_proc,
        mock_md_proc,
        mock_client,
        mock_url_resolver,
        temp_output_dir,
        monkeypatch
    ):
        """Test successful end-to-end export."""
        from confluence2eml.main import main
        
        # Setup mocks
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_page_content.return_value = {
            'markdown': '# Test Page\n\nContent here.',
            'title': 'Test Page',
            'attachments': []
        }
        mock_client.return_value = mock_client_instance
        
        mock_md_processor = MagicMock()
        mock_md_processor.convert.return_value = '<h1>Test Page</h1><p>Content here.</p>'
        mock_md_proc.return_value = mock_md_processor
        
        mock_html_processor = MagicMock()
        mock_html_processor.sanitize.return_value = '<h1>Test Page</h1><p>Content here.</p>'
        mock_html_proc.return_value = mock_html_processor
        
        mock_mime_gen_instance = MagicMock()
        mock_mime_gen_instance._html_to_plain_text.return_value = 'Test Page\n\nContent here.'
        mock_mime_gen_instance.create_and_save.return_value = Path(temp_output_dir / 'test.eml')
        mock_mime_gen.return_value = mock_mime_gen_instance
        
        # Set environment variables
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        # Mock sys.argv
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', str(temp_output_dir / 'test.eml')
        ]
        
        with patch.object(sys, 'argv', test_args):
            # Should not raise an exception
            try:
                main()
            except SystemExit as e:
                # SystemExit(0) is success
                assert e.code == 0
    
    @patch('confluence2eml.main.URLResolver')
    def test_main_invalid_url(self, mock_url_resolver, monkeypatch):
        """Test main() with invalid URL."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.side_effect = ConfluenceClientError("Invalid URL")
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'invalid-url',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    def test_main_authentication_error(
        self,
        mock_client,
        mock_url_resolver,
        monkeypatch
    ):
        """Test main() with authentication error."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client.side_effect = ConfluenceAuthenticationError("Authentication failed")
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    def test_main_page_not_found(
        self,
        mock_client,
        mock_url_resolver,
        monkeypatch
    ):
        """Test main() with page not found error."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_page_content.side_effect = ConfluencePageNotFoundError("Page not found")
        mock_client.return_value = mock_client_instance
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    @patch('confluence2eml.main.MarkdownProcessor')
    def test_main_markdown_conversion_error(
        self,
        mock_md_proc,
        mock_client,
        mock_url_resolver,
        monkeypatch
    ):
        """Test main() with Markdown conversion error."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_page_content.return_value = {
            'markdown': '# Test Page',
            'title': 'Test Page'
        }
        mock_client.return_value = mock_client_instance
        
        mock_md_proc.side_effect = MarkdownProcessorError("Markdown conversion failed")
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    @patch('confluence2eml.main.MarkdownProcessor')
    @patch('confluence2eml.main.HtmlProcessor')
    def test_main_html_sanitization_error(
        self,
        mock_html_proc,
        mock_md_proc,
        mock_client,
        mock_url_resolver,
        monkeypatch
    ):
        """Test main() with HTML sanitization error."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_page_content.return_value = {
            'markdown': '# Test Page',
            'title': 'Test Page'
        }
        mock_client.return_value = mock_client_instance
        
        mock_md_processor = MagicMock()
        mock_md_processor.convert.return_value = '<h1>Test</h1>'
        mock_md_proc.return_value = mock_md_processor
        
        mock_html_proc.side_effect = HtmlProcessorError("HTML sanitization failed")
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    @patch('confluence2eml.main.URLResolver')
    @patch('confluence2eml.main.ConfluenceClient')
    @patch('confluence2eml.main.MarkdownProcessor')
    @patch('confluence2eml.main.HtmlProcessor')
    @patch('confluence2eml.main.MimeGenerator')
    def test_main_eml_generation_error(
        self,
        mock_mime_gen,
        mock_html_proc,
        mock_md_proc,
        mock_client,
        mock_url_resolver,
        monkeypatch
    ):
        """Test main() with EML generation error."""
        from confluence2eml.main import main
        
        mock_url_resolver.extract_page_id.return_value = '123456'
        mock_url_resolver.extract_base_url.return_value = 'https://example.com'
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_page_content.return_value = {
            'markdown': '# Test Page',
            'title': 'Test Page'
        }
        mock_client.return_value = mock_client_instance
        
        mock_md_processor = MagicMock()
        mock_md_processor.convert.return_value = '<h1>Test</h1>'
        mock_md_proc.return_value = mock_md_processor
        
        mock_html_processor = MagicMock()
        mock_html_processor.sanitize.return_value = '<h1>Test</h1>'
        mock_html_proc.return_value = mock_html_processor
        
        mock_mime_gen.side_effect = MimeGeneratorError("EML generation failed")
        
        monkeypatch.setenv('CONFLUENCE_USER', 'test@example.com')
        monkeypatch.setenv('CONFLUENCE_TOKEN', 'test_token')
        
        test_args = [
            'confluence2eml',
            '--url', 'https://example.com/wiki/pages/123456',
            '--output', 'test.eml'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def test_cli_help_message(self):
        """Test that CLI help message is displayed."""
        result = subprocess.run(
            [sys.executable, '-m', 'confluence2eml.main', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'Confluence' in result.stdout
        assert '--url' in result.stdout
        assert '--output' in result.stdout
    
    def test_cli_missing_required_args(self):
        """Test that CLI exits with error when required args are missing."""
        result = subprocess.run(
            [sys.executable, '-m', 'confluence2eml.main'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert 'error' in result.stderr.lower() or 'required' in result.stderr.lower()

