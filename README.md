# Confluence to EML Exporter

A Python utility that converts Atlassian Confluence pages into self-contained Microsoft Outlook email files (.EML format). The tool extracts Confluence page content, converts it to HTML, embeds images, and generates a professional email file that can be opened in Outlook, Apple Mail, Thunderbird, and other email clients.

## Features

- **Confluence Integration**: Extracts content from Confluence pages using the `confluence-markdown-exporter` library
- **Dual Output**: Always produces both a Markdown file and an EML file
- **High-Fidelity Conversion**: Preserves formatting, tables, lists, and other Confluence elements
- **Image Embedding**: Automatically downloads and embeds images as CID attachments for offline viewing
- **Attachment Support**: Includes all page attachments (PDFs, DOCX, etc.) as email attachments
- **Email Client Compatible**: Uses CSS inlining and email-friendly HTML for maximum compatibility
- **Platform Independent**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.7 or higher
- Access to a Confluence instance (Cloud or Server)
- Confluence API token or Personal Access Token (PAT)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd confluence2eml
```

### 2. Install Dependencies

Using pip:

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

### Required Dependencies

- `confluence-markdown-exporter` - Confluence API client and content extraction
- `markdown` - Markdown to HTML conversion
- `beautifulsoup4` - HTML parsing and sanitization
- `premailer` - CSS inlining for email compatibility
- `requests` - HTTP client for downloading images and attachments

## Configuration

### Authentication

The tool requires authentication to access your Confluence instance. You can provide credentials in two ways:

#### Option 1: Environment Variables (Recommended)

Set the following environment variables:

**On macOS/Linux:**

```bash
export CONFLUENCE_USER="your_email@example.com"
export CONFLUENCE_TOKEN="your_api_token"
export CONFLUENCE_URL="https://yourcompany.atlassian.net"  # Optional, can be inferred from URL
```

**On Windows (Command Prompt):**

```cmd
set CONFLUENCE_USER=your_email@example.com
set CONFLUENCE_TOKEN=your_api_token
set CONFLUENCE_URL=https://yourcompany.atlassian.net
```

**On Windows (PowerShell):**

```powershell
$env:CONFLUENCE_USER="your_email@example.com"
$env:CONFLUENCE_TOKEN="your_api_token"
$env:CONFLUENCE_URL="https://yourcompany.atlassian.net"
```

> **Note:** Environment variables set in a terminal session are temporary and will be lost when you close the terminal. To make them persistent, add them to your shell profile (`.bashrc`, `.zshrc`, etc. on macOS/Linux) or set them as system/user environment variables on Windows.

#### Option 2: Command-Line Arguments

Provide credentials directly via CLI flags (see Usage section below).

### Getting an API Token

We recommend creating an **API token with scopes** for enhanced security. This allows you to grant only the minimum permissions needed for the tool to function.

#### Recommended: Create an API Token with Scopes

1. Log in to [Atlassian Account Security Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Select **"Create API token" with scopes**
3. Give your API token a descriptive name (e.g., "Confluence2EML Exporter")
4. Select an **expiration date** (1 to 365 days)
5. Select **Confluence** as the app
6. Select the following **scopes** (minimum required permissions):
   - **View** - Read Confluence page content
   - **Download** - Download attachments and images from pages
7. Select **Create**
8. **Copy the token immediately** - you won't be able to view it again after this step
9. Save the token securely (e.g., in a password manager)

> **Note:** The tool only requires read and download permissions. It does not modify, create, or delete any Confluence content, so write or delete permissions are not needed.

#### Alternative: Create an API Token Without Scopes

If you need to use an app that doesn't currently support API tokens with scopes, you can create a token without scopes:

1. Log in to [Atlassian Account Security Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Select **"Create API token"** (without scopes)
3. Give your API token a descriptive name
4. Select an expiration date (1 to 365 days)
5. Select **Create**
6. Copy and save the token securely

> **Security Note:** API tokens with scopes are more secure as they follow the principle of least privilege. For more information, see the [Atlassian documentation on managing API tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).

## Usage

### Running the Script

You can run the script in two ways:

**Option 1: Using the installed command (if installed with `pip install -e .`):**

```bash
confluence2eml --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

**Option 2: Using Python module (recommended for development):**

```bash
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

**On Windows:**

```cmd
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

### Basic Usage (with Environment Variables)

If you've set environment variables (see Configuration section above):

**On macOS/Linux:**

```bash
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

**On Windows (Command Prompt):**

```cmd
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

**On Windows (PowerShell):**

```powershell
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml"
```

### With Explicit Credentials

If you prefer to provide credentials directly via command-line arguments:

**On macOS/Linux:**

```bash
python -m confluence2eml.main \
  --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" \
  --output "export.eml" \
  --user "your_email@example.com" \
  --token "your_api_token"
```

**On Windows (Command Prompt):**

```cmd
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml" --user "your_email@example.com" --token "your_api_token"
```

**On Windows (PowerShell):**

```powershell
python -m confluence2eml.main --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title" --output "export.eml" --user "your_email@example.com" --token "your_api_token"
```

### Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--url` | Yes | The full Confluence page URL to export |
| `--output` | Yes | Filepath to save the final .eml file (e.g., `export.eml`) |
| `--user` | No* | Confluence email address. Required if not set via `CONFLUENCE_USER` environment variable |
| `--token` | No* | Confluence API token. Required if not set via `CONFLUENCE_TOKEN` environment variable |

\* At least one authentication method (environment variables or CLI arguments) must be provided.

## Output Files

The tool always produces two output files:

1. **Markdown File** (`.md`): 
   - Contains the raw Markdown content extracted from Confluence
   - Filename is automatically generated from the Confluence page title
   - Useful for reference, debugging, or further processing

2. **EML File** (`.eml`):
   - Self-contained email file with embedded images and attachments
   - Can be opened directly in Outlook, Apple Mail, Thunderbird, and other email clients
   - Filename specified via `--output` flag

## How It Works

1. **Content Extraction**: Uses `confluence-markdown-exporter` to fetch page content from Confluence API
2. **Markdown Saving**: Saves the extracted Markdown content to a file
3. **HTML Conversion**: Converts Markdown to HTML with proper formatting
4. **HTML Sanitization**: Removes unsafe elements and ensures email compatibility
5. **CSS Inlining**: Inlines all CSS styles for email client compatibility
6. **Image Embedding**: Downloads images and embeds them as CID attachments
7. **Attachment Processing**: Downloads and attaches all page attachments
8. **EML Generation**: Creates a multipart/related MIME message with HTML body, embedded images, and attachments

## Examples

### Export a Single Page

**On macOS/Linux:**

```bash
python -m confluence2eml.main \
  --url "https://company.atlassian.net/wiki/spaces/ENG/pages/789012/API+Documentation" \
  --output "api_docs.eml"
```

**On Windows:**

```cmd
python -m confluence2eml.main --url "https://company.atlassian.net/wiki/spaces/ENG/pages/789012/API+Documentation" --output "api_docs.eml"
```

This will create:
- `api_docs.eml` - The email file
- `API Documentation.md` - The Markdown file (automatically generated from the Confluence page title)

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:
- Verify your API token is correct
- Ensure your email address matches your Confluence account
- Check that environment variables are set correctly:
  - **On macOS/Linux:** Use `echo $CONFLUENCE_USER` to verify
  - **On Windows (Command Prompt):** Use `echo %CONFLUENCE_USER%` to verify
  - **On Windows (PowerShell):** Use `echo $env:CONFLUENCE_USER` to verify

### URL Format Issues

The tool supports both URL formats:
- Page ID format: `.../pages/viewpage.action?pageId=123456789`
- Pretty URLs: `.../display/SPACEKEY/Page+Title`

### Missing Images or Attachments

- Ensure you have proper permissions to access the Confluence page
- Check that images and attachments are accessible via the API
- Verify your authentication credentials have sufficient permissions

## Development

### Running Tests

```bash
pytest
```

### Running with Coverage

```bash
pytest --cov=confluence2eml --cov-report=html
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

For more information about the MIT License, visit: https://opensource.org/licenses/MIT

## Contributing

[Add contribution guidelines if applicable]

## Acknowledgments

This project leverages the [`confluence-markdown-exporter`](https://github.com/Spenhouet/confluence-markdown-exporter) library for Confluence API interactions.

