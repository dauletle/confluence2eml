#!/usr/bin/env python3
"""Main entry point for Confluence to EML Exporter.

This script provides a command-line interface for converting Confluence pages
to self-contained email files (.EML format).
"""

import argparse
import logging
import os
import sys

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


def main():
    """Main entry point for the CLI application."""
    try:
        args = parse_arguments()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Starting Confluence to EML export process")
        logger.info(f"URL: {args.url}")
        logger.info(f"Output: {args.output}")
        
        # Get credentials
        try:
            user, token = get_credentials(args)
            logger.debug("Credentials retrieved successfully")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        
        # TODO: Phase 3 - Library Integration and Content Extraction
        # This will be implemented in Sprint 0, Phase 3
        logger.info("Content extraction not yet implemented")
        logger.info("This is a placeholder for Sprint 0, Phase 1 setup")
        
        logger.info("Export process completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

