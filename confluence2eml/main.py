#!/usr/bin/env python3
"""Main entry point for Confluence to EML Exporter.

This script provides a command-line interface for converting Confluence pages
to self-contained email files (.EML format).
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from confluence2eml.core.client import ConfluenceClient, URLResolver, ConfluenceClientError
from confluence2eml.core.html_processor import HtmlProcessor, HtmlProcessorError
from confluence2eml.core.css_inliner import CssInliner, CssInlinerError
from confluence2eml.core.image_processor import ImageProcessor, ImageProcessorError
from confluence2eml.core.markdown_processor import MarkdownProcessor, MarkdownProcessorError
from confluence2eml.core.mime_generator import MimeGenerator, MimeGeneratorError
from confluence2eml.core.utils import generate_markdown_filename, save_markdown_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_credentials(args):
    """Extract Confluence credentials from CLI arguments or environment variables.
    
    Args:
        args: Parsed argparse arguments
        
    Returns:
        tuple: (user, token) credentials
        
    Raises:
        ValueError: If credentials are not provided
    """
    user = args.user or os.getenv('CONFLUENCE_USER')
    token = args.token or os.getenv('CONFLUENCE_TOKEN')
    
    if not user:
        raise ValueError(
            "Confluence user must be provided via --user argument or "
            "CONFLUENCE_USER environment variable"
        )
    
    if not token:
        raise ValueError(
            "Confluence token must be provided via --token argument or "
            "CONFLUENCE_TOKEN environment variable"
        )
    
    return user, token


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Convert Atlassian Confluence pages to self-contained "
                    "Microsoft Outlook email files (.EML format)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables for authentication
  export CONFLUENCE_USER="your_email@example.com"
  export CONFLUENCE_TOKEN="your_api_token"
  confluence2eml --url "https://company.atlassian.net/wiki/..." --output "export.eml"
  
  # Using CLI arguments for authentication
  confluence2eml \\
    --url "https://company.atlassian.net/wiki/..." \\
    --output "export.eml" \\
    --user "your_email@example.com" \\
    --token "your_api_token"
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='The full Confluence page URL to export'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        type=str,
        help='Filepath to save the final .eml file (e.g., "export.eml")'
    )
    
    parser.add_argument(
        '--user',
        help='Confluence email address. Best practice: use env var CONFLUENCE_USER'
    )
    
    parser.add_argument(
        '--token',
        help='Confluence API token. Best practice: use env var CONFLUENCE_TOKEN'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    return parser.parse_args()


def extract_url_info(url: str) -> Tuple[str, str]:
    """Extract page ID and base URL from Confluence URL.
    
    Args:
        url: Full Confluence page URL
        
    Returns:
        Tuple of (page_id, base_url)
        
    Raises:
        ConfluenceClientError: If URL is invalid
    """
    page_id = URLResolver.extract_page_id(url)
    base_url = URLResolver.extract_base_url(url)
    logger.info(f"Extracted page ID: {page_id}")
    logger.debug(f"Base URL: {base_url}")
    return page_id, base_url


def fetch_page_content(client: ConfluenceClient, page_id: str) -> Dict:
    """Fetch page content from Confluence.
    
    Args:
        client: Initialized ConfluenceClient
        page_id: Confluence page ID
        
    Returns:
        Dictionary containing page content and metadata
        
    Raises:
        ConfluenceClientError: If page cannot be fetched
    """
    logger.info("Extracting page content from Confluence...")
    page_content = client.get_page_content(page_id)
    page_title = page_content.get('title', 'Unknown')
    logger.info(f"Successfully extracted content for page: {page_title}")
    logger.debug(f"Markdown content length: {len(page_content.get('markdown', ''))} characters")
    return page_content


def save_markdown_output(page_content: Dict, eml_output_path: Path) -> Path:
    """Save Markdown content to file.
    
    The Markdown file is always saved before processing. The filename
    is automatically generated from the page title.
    
    Args:
        page_content: Page content dictionary with 'markdown' and 'title' keys
        eml_output_path: Path to the EML output file (used to determine output directory)
        
    Returns:
        Path to the saved Markdown file
        
    Raises:
        OSError: If file cannot be written
    """
    output_dir = eml_output_path.parent if eml_output_path.parent != Path('.') else None
    markdown_path = generate_markdown_filename(page_content.get('title', 'Unknown'), output_dir)
    
    logger.info(f"Saving Markdown file: {markdown_path}")
    saved_path = save_markdown_file(
        content=page_content.get('markdown', ''),
        filepath=markdown_path
    )
    logger.info(f"Markdown file saved successfully: {saved_path}")
    return saved_path


def convert_to_html(markdown_content: str) -> str:
    """Convert Markdown content to HTML.
    
    Args:
        markdown_content: Markdown content as string
        
    Returns:
        HTML content as string
        
    Raises:
        MarkdownProcessorError: If conversion fails
    """
    logger.info("Converting Markdown to HTML...")
    markdown_processor = MarkdownProcessor()
    html_content = markdown_processor.convert(markdown_content)
    logger.info(f"Successfully converted Markdown to HTML ({len(html_content)} characters)")
    return html_content


def prepare_html_for_email(html_content: str, base_url: str) -> str:
    """Prepare HTML for email by sanitizing and inlining CSS.
    
    This function combines HTML sanitization and CSS inlining into a
    single step, as they are always performed together in the pipeline.
    
    Args:
        html_content: HTML content to prepare
        base_url: Base URL for CSS inlining (URL absolutization)
        
    Returns:
        Prepared HTML with sanitized content and inlined CSS
        
    Raises:
        HtmlProcessorError: If sanitization fails
        CssInlinerError: If CSS inlining fails
    """
    # Sanitize HTML for email compatibility
    logger.info("Sanitizing HTML for email compatibility...")
    html_processor = HtmlProcessor()
    sanitized_html = html_processor.sanitize(html_content)
    logger.info(f"Successfully sanitized HTML ({len(sanitized_html)} characters)")
    
    # Inline CSS for email compatibility
    logger.info("Inlining CSS styles for email compatibility...")
    css_inliner = CssInliner(base_url=base_url)
    inlined_html = css_inliner.inline(sanitized_html, wrap_with_css=True)
    logger.info(f"Successfully inlined CSS ({len(inlined_html)} characters)")
    
    return inlined_html


def embed_images_in_html(html_content: str, base_url: str, user: str, token: str) -> Tuple[str, List]:
    """Process images in HTML and embed them as CIDs.
    
    Args:
        html_content: HTML content with image tags
        base_url: Confluence base URL for image downloads
        user: Confluence username for authentication
        token: Confluence API token for authentication
        
    Returns:
        Tuple of (processed_html, embedded_images):
        - processed_html: HTML with src attributes rewritten to use cid:
        - embedded_images: List of ImageData objects for attachment
        
    Raises:
        ImageProcessorError: If image processing fails
    """
    logger.info("Processing images and embedding as CIDs...")
    image_processor = ImageProcessor(
        base_url=base_url,
        user=user,
        token=token
    )
    try:
        processed_html, embedded_images = image_processor.process_images(html_content)
        logger.info(
            f"Successfully processed images: {len(embedded_images)} image(s) embedded, "
            f"output HTML length: {len(processed_html)} characters"
        )
        return processed_html, embedded_images
    finally:
        image_processor.close()


def validate_output_path(output_path: str) -> Path:
    """Validate and prepare output path for EML file.
    
    Args:
        output_path: Path string for the output EML file
        
    Returns:
        Path object for the output file
        
    Raises:
        ValueError: If path is invalid or not writable
        OSError: If directory cannot be created
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not os.access(path.parent, os.W_OK):
        raise ValueError(f"Cannot write to output directory: {path.parent}")
    
    return path


def generate_eml_file(
    html_content: str,
    page_title: str,
    output_path: Path,
    embedded_images: Optional[List] = None
) -> Path:
    """Generate and save EML file with HTML content and embedded images.
    
    Args:
        html_content: Final HTML content with CID references
        page_title: Confluence page title for email subject
        output_path: Path where EML file should be saved
        embedded_images: Optional list of ImageData objects to attach
        
    Returns:
        Path to the saved EML file
        
    Raises:
        MimeGeneratorError: If EML generation fails
    """
    logger.info("Generating EML file...")
    mime_generator = MimeGenerator()
    
    email_subject = f"Confluence Export: {page_title}"
    plain_text = mime_generator._html_to_plain_text(html_content)
    
    eml_path = mime_generator.create_and_save(
        subject=email_subject,
        html_content=html_content,
        output_path=str(output_path),
        plain_text=plain_text,
        images=embedded_images if embedded_images else None
    )
    logger.info(f"Successfully generated EML file: {eml_path}")
    return eml_path


def print_success_summary(markdown_path: Optional[Path], eml_path: Optional[Path]) -> None:
    """Print summary of successfully created output files.
    
    Args:
        markdown_path: Path to saved Markdown file (if any)
        eml_path: Path to saved EML file (if any)
    """
    logger.info("=" * 60)
    logger.info("Export process completed successfully!")
    logger.info("=" * 60)
    logger.info("Output files:")
    if markdown_path:
        logger.info(f"  ✓ Markdown: {markdown_path}")
    if eml_path:
        logger.info(f"  ✓ EML: {eml_path}")
        logger.info(f"    File size: {eml_path.stat().st_size:,} bytes")
    logger.info("=" * 60)


def handle_error(error: Exception, context: str) -> None:
    """Handle errors with appropriate logging and exit.
    
    Args:
        error: Exception that occurred
        context: Description of what operation was being performed
    """
    logger.error(f"{context}: {error}")
    if isinstance(error, (ConfluenceClientError, MarkdownProcessorError, 
                          HtmlProcessorError, CssInlinerError, ImageProcessorError, 
                          MimeGeneratorError)):
        # Known errors - don't print full traceback
        sys.exit(1)
    else:
        # Unexpected errors - print full traceback
        logger.error(f"Unexpected error: {error}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI application.
    
    This function orchestrates the complete Confluence-to-EML conversion
    pipeline. It follows the Step Down Rule, with high-level operations
    calling lower-level functions that hide implementation details.
    """
    try:
        # Parse and validate command-line arguments
        args = parse_arguments()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Starting Confluence to EML export process")
        logger.info(f"URL: {args.url}")
        logger.info(f"Output: {args.output}")
        
        # Get authentication credentials
        try:
            user, token = get_credentials(args)
            logger.debug("Credentials retrieved successfully")
        except ValueError as e:
            handle_error(e, "Authentication failed")
        
        # Extract page information from URL
        try:
            page_id, base_url = extract_url_info(args.url)
        except ConfluenceClientError as e:
            handle_error(e, "Invalid Confluence URL")
        
        # Initialize Confluence client and fetch page content
        try:
            client = ConfluenceClient(base_url=base_url, user=user, token=token)
            logger.debug("Confluence client initialized successfully")
            page_content = fetch_page_content(client, page_id)
        except ConfluenceClientError as e:
            handle_error(e, "Failed to fetch page content")
        except Exception as e:
            handle_error(e, "Failed to initialize Confluence client")
        
        page_title = page_content.get('title', 'Unknown')
        
        # Save Markdown file (always done before processing)
        try:
            eml_output_path = Path(args.output)
            markdown_path = save_markdown_output(page_content, eml_output_path)
        except Exception as e:
            handle_error(e, "Failed to save Markdown file")
        
        # Convert Markdown to HTML
        try:
            html_content = convert_to_html(page_content.get('markdown', ''))
        except MarkdownProcessorError as e:
            handle_error(e, "Failed to convert Markdown to HTML")
        except Exception as e:
            handle_error(e, "Unexpected error during Markdown conversion")
        
        # Prepare HTML for email (sanitize and inline CSS)
        try:
            prepared_html = prepare_html_for_email(html_content, base_url)
        except (HtmlProcessorError, CssInlinerError) as e:
            handle_error(e, "Failed to prepare HTML for email")
        except Exception as e:
            handle_error(e, "Unexpected error during HTML preparation")
        
        # Process and embed images
        try:
            final_html, embedded_images = embed_images_in_html(
                prepared_html, base_url, user, token
            )
        except ImageProcessorError as e:
            handle_error(e, "Failed to process images")
        except Exception as e:
            handle_error(e, "Unexpected error during image processing")
        
        # Validate output path
        try:
            output_path = validate_output_path(args.output)
        except (OSError, ValueError) as e:
            handle_error(e, "Invalid output path")
        
        # Generate and save EML file
        try:
            eml_path = generate_eml_file(
                final_html, page_title, output_path, embedded_images
            )
        except MimeGeneratorError as e:
            handle_error(e, "Failed to generate EML file")
        except Exception as e:
            handle_error(e, "Unexpected error during EML generation")
        
        # Print success summary
        print_success_summary(markdown_path, eml_path)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

