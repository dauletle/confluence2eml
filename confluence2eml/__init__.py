"""Confluence to EML Exporter Package.

A Python utility that converts Atlassian Confluence pages into
self-contained Microsoft Outlook email files (.EML format).
"""

__version__ = "0.1.0"

# Import main components for easy access
from confluence2eml.client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    URLResolver,
)

__all__ = [
    'ConfluenceClient',
    'ConfluenceClientError',
    'ConfluenceAuthenticationError',
    'ConfluencePageNotFoundError',
    'URLResolver',
]
