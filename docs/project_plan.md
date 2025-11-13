# Confluence-to-Email Exporter: Architectural Blueprint and Development Plan

## Executive Analysis: System Architecture and Core Decisions

This report outlines the complete architectural design and project development plan for a Python utility that converts Atlassian Confluence pages into self-contained Microsoft Outlook email files. The system is designed to be robust, maintainable, and platform-independent, addressing the complexities of Confluence API interaction, HTML processing, and MIME email generation.

**Key Architectural Decision**: This project leverages the existing [`confluence-markdown-exporter`](https://github.com/Spenhouet/confluence-markdown-exporter) library to handle all Confluence API interactions, authentication, URL resolution, and content extraction. This significantly simplifies the project scope, allowing us to focus on the email generation pipeline (Markdown/HTML to EML conversion).

## High-Level System Data Flow

The system is architected as a multi-stage data processing pipeline. This modular design isolates concerns, enhances testability, and clarifies the flow of data from input URL to output file.

1. **Ingestion**: The tool is initiated via a Command-Line Interface (CLI), accepting a target Confluence Page URL as a required argument.

2. **Content Extraction (via confluence-markdown-exporter)**: The `confluence-markdown-exporter` library handles:
   - URL parsing and resolution to `page_id`
   - Authentication with Confluence API (supports API tokens and PATs)
   - Content retrieval from Confluence (handles both v1 and v2 APIs)
   - Conversion to Markdown format
   - Image and attachment metadata extraction

3. **Markdown File Saving**: The raw Markdown content is always saved to a file before processing. The filename is automatically generated from the Confluence page title. This ensures:
   - The intermediate Markdown file is always available for reference or further processing
   - Users can debug the conversion process by examining the Markdown
   - The Markdown file can be used independently of the email generation
   - Both outputs (Markdown and EML) are produced as part of the tool's core functionality

4. **Markdown to HTML Conversion**: The Markdown content is converted to HTML using a Markdown processor (e.g., `markdown` or `markdown2`). This provides a clean HTML representation of the Confluence page content.

5. **Transformation (HTML Sanitation)**: The HTML is sanitized using BeautifulSoup. Interactive UI elements (e.g., "Edit," "Like," comment sections) are removed using `.decompose()` based on a predefined list of CSS classes.

6. **Transformation (CSS Inlining)**: The sanitized HTML is processed by the premailer library. This critical step solves two problems: 1) It inlines all CSS rules from `<style>` blocks into style attributes on individual HTML elements, ensuring compatibility with email clients. 2) It converts all relative URLs (e.g., `/download/...`) into absolute URLs.

7. **Transformation (Image Embedding)**: An ImageProcessor parses the inlined HTML. It finds all `<img>` tags, downloads the image data from its absolute URL, generates a unique Content-ID (CID) for it, and rewrites the HTML `src` attribute to point to this `cid:`.

8. **Generation (MIME Construction)**: A MimeGenerator module constructs a `multipart/related` EmailMessage object. It adds the final, rewritten HTML as the body, attaches the downloaded images as related parts with their corresponding CIDs, and attaches all other files (PDFs, DOCX, etc.) from the attachment manifest as standard email attachments.

9. **Output**: The tool produces two output files:
   - **Markdown file**: Saved in step 3, with filename automatically generated from the Confluence page title
   - **EML file**: The completed EmailMessage object is serialized and written to the local filesystem as a `.eml` file, as specified by the user's `--output` flag

## Primary Architectural Decision: .EML vs. .MSG Format

The query specifies the output should be ".EML or .MSG, depending on what is easier." An analysis of these formats reveals this is not a choice of preference but of technical feasibility. The .EML format is the only viable path for a pure, standalone Python application.

### Analysis of .EML (Recommended Path)

The .EML format is a robust, open, and well-defined standard. It is essentially a text file that stores a complete email message, including its headers, body, and attachments, formatted according to the MIME (Multipurpose Internet Mail Extensions) specification (RFC 822 and RFC 5322).

- **Standard Library Support**: Python's standard library is explicitly designed to create these files. The modern `email.message.EmailMessage` class and its related `email.mime` subclasses provide a comprehensive API for building complex MIME structures, including the `multipart/related` type needed for embedded images.

- **Generation and Portability**: Creating the final file is trivial. An EmailMessage object can be serialized to bytes and written directly to a file. The resulting .eml file is platform-independent and can be opened by a vast array of email clients, including Microsoft Outlook, Apple Mail, and Thunderbird.

### Analysis of .MSG (Rejected Path)

The .MSG format, in contrast, is a proprietary, complex binary format developed by Microsoft. It is based on the OLE (Object Linking and Embedding) compound file structure.

- **Lack of Writing Libraries**: A thorough review of the Python ecosystem reveals a critical gap: while numerous libraries exist to read and extract data from .MSG files (e.g., extract-msg, outlook-msg, msglite), there are no well-maintained, pure-Python libraries that provide a public API for writing or creating new .MSG files from scratch.

- **Community Confirmation**: This gap is a known and significant bottleneck. Community discussions confirm that developers attempting this task have been unable to find a functional writing library. The complexity of the binary OLE format makes implementing the specification manually an unreasonable and high-risk development effort.

- **The win32com Misconception**: The only "solution" commonly found for writing .MSG files in Python involves using the `win32com.client` library. This is not a viable solution for a standalone tool; it is a Windows-only automation script that drives a locally installed instance of the Microsoft Outlook application. This approach is fragile, platform-dependent, and fails entirely on Linux, macOS, or any server environment where Outlook is not installed.

### Decision and Recommendation

The "easier" path is also the only architecturally sound and professional path. **The project will exclusively target the .EML format.** This decision eliminates a major technical roadblock, simplifies the architecture, and ensures the final utility is robust, portable, and maintainable.

## Phase 1: Integration with confluence-markdown-exporter

### Leveraging Existing Library

The [`confluence-markdown-exporter`](https://github.com/Spenhouet/confluence-markdown-exporter) library is a mature, well-maintained Python package that handles all the complex Confluence API interactions. By using this library, we eliminate the need to build:

- Custom Confluence API client
- URL parsing and resolution logic
- Authentication handling (supports both API tokens and Personal Access Tokens)
- Content extraction from Confluence (handles both v1 and v2 APIs)
- Markdown conversion from Confluence storage format

### Integration Approach

The tool will use `confluence-markdown-exporter` as a Python library (not just as a CLI tool). We'll need to:

1. **Import the library**: Use the library's internal modules to access Confluence content programmatically.

2. **URL Resolution**: The library already handles URL parsing and resolution. We'll extract the `page_id` from the input URL using the library's utilities or by parsing the URL ourselves if needed.

3. **Content Extraction**: Use the library's API to:
   - Authenticate with Confluence (credentials can be passed or read from environment variables)
   - Retrieve page content as Markdown
   - Get page metadata (title, attachments, etc.)

4. **Attachment Handling**: The library provides attachment information. We'll extract this metadata to download attachments later in the pipeline.

5. **Markdown File Saving**: The extracted Markdown content is always saved to a file before further processing. The filename is automatically generated from the Confluence page title. This ensures:
   - The intermediate Markdown file is always available for reference
   - Users can debug the conversion process by examining the Markdown
   - The Markdown file can be used independently (e.g., for version control, documentation, or other tools)
   - Both outputs (Markdown and EML) are produced as part of the tool's core functionality
   - Future enhancement: Re-run email generation from the saved Markdown without re-fetching from Confluence

### Authentication Configuration

The `confluence-markdown-exporter` library supports multiple authentication methods:
- API Tokens (via username/token)
- Personal Access Tokens (PAT)
- Environment variables or configuration files

Our tool will accept credentials via:
- CLI arguments (`--user`, `--token`)
- Environment variables (`CONFLUENCE_USER`, `CONFLUENCE_TOKEN`, `CONFLUENCE_URL`)
- Pass credentials directly to the library's API

### Note on Library API

Since `confluence-markdown-exporter` is primarily designed as a CLI tool, we may need to:
- Use it as a subprocess and parse its output, OR
- Import and use its internal modules directly if they expose a programmatic API

Research will be needed to determine the best integration approach. If the library doesn't expose a clean Python API, we can wrap its CLI functionality or contribute to the library to add programmatic access.

## Phase 2: Markdown to HTML Conversion

### Converting Markdown to HTML

The `confluence-markdown-exporter` library outputs content in Markdown format. To create an HTML email, we need to convert this Markdown to HTML.

**Library Selection**: The Python `markdown` library (or `markdown2`) will be used for this conversion. The `markdown` library is the standard Python implementation of Markdown and provides:

- Extensibility through extensions
- Support for tables, code blocks, and other Markdown features
- Clean HTML output

**Conversion Process**:

```python
import markdown

# Convert Markdown to HTML
html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code', 'codehilite'])
```

The Markdown content from `confluence-markdown-exporter` should already be clean and well-formatted, as the library handles Confluence-specific formatting conversions.

**Note on Markdown File Saving**: The Markdown content will have been saved to a file in Phase 1 (this is always done). The conversion process will use the in-memory Markdown content for processing. In the future, this could be extended to allow reading from a previously saved Markdown file (e.g., `--markdown-input` flag) to enable re-processing without re-fetching from Confluence.

## Phase 3: HTML Transformation and Email Client Preparation

### HTML Sanitation with BeautifulSoup

The HTML generated from Markdown should already be clean (no Confluence UI elements), but we'll still sanitize it to ensure no unwanted elements remain.

The `beautifulsoup4` library will be used to parse and clean the HTML. Since the content comes from Markdown (not raw Confluence HTML), we primarily need to:

1. Ensure proper HTML structure
2. Remove any potential unwanted elements
3. Prepare the HTML for CSS inlining

### HTML Sanitation: Cleaning and Validation

Since the HTML is generated from Markdown (which is already clean), the sanitation step is primarily for:

1. **Structure Validation**: Ensure the HTML is well-formed
2. **Security**: Remove any potentially unsafe elements (scripts, iframes, etc.)
3. **Email Compatibility**: Remove elements that email clients don't support well

BeautifulSoup provides methods to clean and validate HTML:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')

# Remove script and style tags (security)
for script in soup(["script", "style"]):
    script.decompose()

# Remove iframes (email clients often block these)
for iframe in soup.find_all("iframe"):
    iframe.decompose()

# Ensure all images have alt text for email compatibility
for img in soup.find_all("img"):
    if not img.get("alt"):
        img["alt"] = "Image"
```

This step ensures the HTML is safe and email-client-compatible before CSS inlining.

### CSS Inlining: The Key to Email Fidelity

This is a critical step for ensuring the visual fidelity of the final email. Most email clients, particularly Microsoft Outlook and Gmail, will strip `<style>` blocks and external `<link rel="stylesheet">` tags for security reasons.

The only reliable method for styling HTML email is to use inline `style` attributes on every individual HTML element (e.g., `<p style="color: #333; margin-top: 10px;">...`).

**Approach**: Since we're converting from Markdown (which doesn't include styles), we have two options:

1. **Add Basic CSS Styles**: Wrap the HTML in a `<style>` block with basic email-friendly CSS (typography, spacing, tables, etc.), then inline it.
2. **Direct Inlining**: Apply inline styles directly to elements based on their semantic meaning (headings, paragraphs, lists, etc.).

**Decision**: The architecture will use `premailer` with a predefined CSS stylesheet. This approach:

1. Wraps the Markdown-generated HTML with a `<style>` block containing email-friendly CSS
2. Uses premailer to inline all CSS rules as `style` attributes
3. Converts all relative URLs to absolute URLs (crucial for images and links)

The CSS stylesheet will include:
- Typography (font families, sizes, colors)
- Spacing (margins, padding)
- Table styling
- List styling
- Link styling
- Code block styling

This ensures the email looks professional and readable across different email clients.

## Phase 4: High-Fidelity .EML (MIME) Generation

### Constructing the multipart/related Message

To create an email where the HTML body can display images that are embedded within the email itself, the email's top-level MIME type must be `multipart/related`.

The modern Python 3 `email.message.EmailMessage` class will be used for this. It provides a clean, object-oriented API and handles the complexities of MIME construction automatically.

```python
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = "Confluence Export: " + page_title_from_api
msg['From'] = "confluence-exporter@company.com"
msg['To'] = "user@company.com"

# Add a plain-text fallback for email clients that do not support HTML
msg.set_content("This is a plain-text fallback for the HTML content.")
```

### Embedding Images via Content-ID (CID)

This is a critical step for creating a truly self-contained email. The `confluence-markdown-exporter` library includes images in the Markdown output as links. When converted to HTML, these become `<img>` tags with URLs pointing to Confluence.

The premailer step converts these to absolute URLs (e.g., `src="https://confluence.company.com/..."`). If left as-is, the email client would try to hotlink these images, which would fail if the user is offline or not logged into Confluence.

The solution is to download each image, embed it in the email, and use the Content-ID (CID) standard to link the HTML to the embedded image. This requires authentication with Confluence to download the images.

**Image Processing Pipeline:**

1. The premailer-processed HTML is passed to the ImageProcessor module and parsed again with BeautifulSoup: `img_soup = BeautifulSoup(inlined_html_string, 'html.parser')`.

2. A list of all image tags is generated: `images = img_soup.find_all('img')`.

3. A `cid_mappings` list is created to hold the image data and its corresponding CID.

4. The module iterates through each `img_tag` in the `images` list:
   a. The absolute URL is extracted: `img_url = img_tag['src']`.
   b. The image data is downloaded using the same authentication credentials used for `confluence-markdown-exporter`: `img_data = requests.get(img_url, auth=confluence_auth).content`.
   c. A unique Content-ID is generated: `cid = email.utils.make_msgid(domain="confluence-export")`. (This creates a string like `<12345.abcdef@confluence-export>`).
   d. The data is stored: `cid_mappings.append({'data': img_data, 'cid': cid, 'content_type': detect_image_type(img_data)})`.
   e. **HTML Rewriting**: The `<img>` tag in the BeautifulSoup object is modified in-place, changing its `src` to reference the CID: `img_tag['src'] = f'cid:{cid[1:-1]}'` (stripping the `<>` brackets for the src attribute).

5. After the loop, the final rewritten HTML is generated by serializing the `img_soup` object: `final_html_body = str(img_soup)`.

6. This final HTML is added to the EmailMessage as an "alternative" body: `msg.add_alternative(final_html_body, subtype='html')`.

7. Finally, the module iterates through the `cid_mappings` and attaches each image to the EmailMessage, specifying its unique CID. This crucial step links the `cid:` references in the HTML to the actual image data:
   ```python
   msg.add_attachment(img['data'], maintype='image', subtype='png', cid=img['cid'])
   ```

### Attaching Confluence Page Attachments

This step handles non-image attachments (PDFs, DOCX, ZIPs, etc.) that should appear as standard attachments in the user's email client.

The `confluence-markdown-exporter` library provides attachment metadata. We'll extract this information and download the attachments:

1. Extract attachment information from the library's output (filenames, download URLs).
2. Download each attachment: `attachment_data = requests.get(att['download_url'], auth=confluence_auth).content`.
3. Use the filename from the metadata.
4. Use Python's standard `mimetypes` library to guess the file's `maintype` and `subtype`.
5. Call `msg.add_attachment()` to add the file as a standard attachment.

**Note**: We need to distinguish between images (which are embedded via CID) and other file attachments (which are added as standard attachments). The `confluence-markdown-exporter` library should provide metadata to help with this distinction.

This completes the construction of the EmailMessage object, which now contains the styled HTML, the CID-embedded images, and the standard file attachments.

## Phase 5: Final Tool Packaging and Structure

### Building a Professional Command-Line Interface (CLI)

The tool will be operated via the command line. Python's standard `argparse` library provides a robust, professional way to build the CLI. It automatically handles argument parsing, type validation, and generating help messages.

The main script will be configured with the following arguments:

```python
import argparse

parser = argparse.ArgumentParser(description="Confluence Page to EML Exporter")
parser.add_argument("--url", required=True, 
                    help="The full Confluence page URL to export.")
parser.add_argument("--output", required=True, 
                    help="Filepath to save the final .eml file (e.g., 'export.eml').")
parser.add_argument("--user", 
                    help="Confluence email. Best practice: use env var CONFLUENCE_USER.")
parser.add_argument("--token", 
                    help="Confluence API token. Best practice: use env var CONFLUENCE_TOKEN.")
args = parser.parse_args()
```

### Project Configuration: pyproject.toml

To adhere to modern Python packaging standards, the project will be configured using a `pyproject.toml` file. This approach is superior to a simple `requirements.txt` file because it serves as a single, consolidated source of truth for all project metadata.

The `pyproject.toml` file will define:

- **[build-system]**: Specifies the build backend (e.g., setuptools).
- **[project]**: Contains project metadata like name, version, and authors.
- **[project.dependencies]**: A list of the core dependencies required for the tool to run (e.g., requests, beautifulsoup4, premailer).
- **[project.optional-dependencies]**: Defines extra dependencies for development, such as a `[dev]` group that includes pytest, pytest-cov, and pytest-mock. This allows for a reproducible development environment via `pip install .[dev]`.
- **[project.scripts]**: Defines the entry point for the CLI, linking a command (e.g., `confluence-export`) to the main function.

### Comprehensive Testing Strategy with pytest

A robust, professional tool requires a comprehensive test suite. The `pytest` framework will be used to test each component of the pipeline.

The testing strategy will be:

- **Unit Tests with Parametrization**: The URLResolver module will be heavily tested using `pytest.mark.parametrize` to feed it dozens of example Confluence URLs (pretty, pageId, with/without special characters) and assert that it always resolves the correct `page_id`.

- **Fixtures**: Sample API responses (JSON) and page content (HTML) will be saved as files in a `tests/fixtures/` directory. pytest fixtures will be used to load this data, keeping the test functions clean and readable.

- **Mocking**: The entire test suite will run without live network access. The `requests` library will be patched using `unittest.mock` (or `pytest-mock`). Tests for the ConfluenceClient will assert that `requests.get` was called with the correct URL, parameters, and authentication headers, and will return the pre-canned data from the fixtures.

- **End-to-End Pipeline Test**: A final test will validate the entire pipeline. It will:
  a. Provide a test URL to the main application entry point.
  b. (All requests calls will be mocked).
  c. Take the resulting .eml file.
  d. Parse the output file back into an EmailMessage object using `email.message_from_bytes`.
  e. Assert the following: `msg.is_multipart()` is `True`, `msg.get_content_type()` is `multipart/related`, the HTML part contains `cid:` references, and the number of attached files matches the expected count.

## Project Development and Execution Plan

### Recommended Technology Stack and Module Justification

The following table outlines the "Bill of Materials" for the project, justifying each technical choice.

**Table 1: Recommended Python Libraries and Justification**

| Library | Purpose | Justification |
|---------|---------|---------------|
| `confluence-markdown-exporter` | Confluence API Client & Content Extraction | Handles all Confluence API interactions: authentication, URL resolution, content retrieval, and Markdown conversion. Eliminates the need to build a custom Confluence client. |
| `markdown` | Markdown to HTML Conversion | Standard Python library for converting Markdown to HTML. Provides extensions for tables, code blocks, and other features needed for email formatting. |
| `beautifulsoup4` | HTML Parsing & Manipulation | Essential for HTML sanitization, security (removing scripts/iframes), and finding/manipulating <img> tags for CID embedding. |
| `premailer` | CSS Inliner & URL Absolutizer | Critically required for email client compatibility. Transforms <style> blocks into inline style attributes. Also converts all relative URLs to absolute URLs. |
| `requests` | HTTP Client | Used for downloading images and attachments from Confluence. Provides authentication support for protected resources. |
| `argparse` | Standard Lib CLI | Robust, standard library module for creating a professional, documented command-line interface with arguments (--url), help messages, and validation. |
| `email.message` | Standard Lib .EML Generation | Modern (Python 3+) standard library for creating complex MIME messages. Natively supports multipart/related structures, HTML alternatives (.add_alternative), and CID-embedded images (.add_attachment(cid=...)). |
| `logging` | Standard Lib Diagnostics | Required for providing debug/info/error messages (e.g., "Converting Markdown to HTML", "Downloading images..."). |
| `pytest` | Testing Framework | De-facto standard for Python testing. Enables fixtures for test data, parametrization for testing, and a rich ecosystem (e.g., pytest-mock, pytest-cov). |

### Project Roadmap: A 3-Sprint Scrum Development Plan

This project can be effectively executed in three two-week Scrum sprints, significantly simplified by leveraging the `confluence-markdown-exporter` library.

#### Sprint 0: Foundation and Library Integration (2 weeks)
**Goals**: Establish the project skeleton, set up development environment, and integrate with `confluence-markdown-exporter` library.

**Actions**:
**Phase 1: Project Setup and Configuration (Week 1, Days 1-3)**
- [x] **Design**: Design project structure, dependency management strategy, and development workflow
- [x] **Implementation**: Create `pyproject.toml` file defining all dependencies (`confluence-markdown-exporter`, `markdown`, `beautifulsoup4`, `premailer`, `requests`, `pytest`), set up project directory structure, configure development tools
- [x] **Testing**: Test project setup, verify dependencies install correctly, test development environment
- [x] **Review**: Review project structure, dependency configuration, and ensure development workflow is established

**Phase 2: Testing Infrastructure (Week 1, Days 4-5)**
- [ ] **Design**: Design pytest structure, test organization, and test coverage reporting strategy
- [ ] **Implementation**: Set up basic pytest structure, create test fixtures, set up test coverage reporting
- [ ] **Testing**: Test pytest framework, verify test discovery works, verify test coverage reporting
- [ ] **Review**: Review testing infrastructure and ensure it supports the development workflow

**Phase 3: Library Integration and Content Extraction (Week 2, Days 1-3)**
- [ ] **Design**: Design integration approach with `confluence-markdown-exporter`, authentication handling, and content extraction workflow
- [ ] **Implementation**: Implement library integration, create ConfluenceClient wrapper, implement authentication via CLI arguments and environment variables, implement content extraction from URL
- [ ] **Testing**: Test library integration with mocked API calls, test authentication mechanisms, test content extraction from various URL formats
- [ ] **Review**: Review library integration approach and ensure robust error handling

**Phase 4: Markdown File Saving (Week 2, Days 4-5)**
- [ ] **Design**: Design Markdown file saving mechanism with automatic filename generation from page title
- [ ] **Implementation**: Implement Markdown content saving to file, implement filename generation from Confluence page title, handle filename sanitization
- [ ] **Testing**: Test Markdown file saving with various page titles, test filename generation and sanitization, verify file output
- [ ] **Review**: Review Markdown saving implementation and ensure it works correctly as part of the output

**Deliverables**:
- Project structure with `pyproject.toml` and all dependencies configured
- Basic pytest structure and test coverage reporting in place
- Library integration with `confluence-markdown-exporter` working
- Authentication via CLI arguments and environment variables
- Markdown content extraction from Confluence URLs
- Markdown file saving with auto-generated filenames
- Integration tests for content extraction (mocked)

#### Sprint 1: Markdown to HTML and Basic .EML Generation (2 weeks)
**Goals**: Create a functional, end-to-end tool that converts Markdown to HTML and generates basic .eml files.

**Actions**:
**Phase 1: Markdown to HTML Conversion (Week 1, Days 1-3)**
- [ ] **Design**: Design MarkdownProcessor module architecture and HTML conversion workflow
- [ ] **Implementation**: Implement MarkdownProcessor module using `markdown` library, configure markdown extensions (tables, fenced_code, codehilite), implement conversion from Markdown to HTML
- [ ] **Testing**: Test Markdown to HTML conversion with various markdown content, test markdown extensions work correctly, verify HTML output quality
- [ ] **Review**: Review MarkdownProcessor implementation and ensure it handles all markdown features correctly

**Phase 2: HTML Sanitization (Week 1, Days 4-5)**
- [ ] **Design**: Design HtmlProcessor module for HTML sanitization and email compatibility
- [ ] **Implementation**: Implement HtmlProcessor module using BeautifulSoup, remove unsafe elements (scripts, iframes), ensure all images have alt text, validate HTML structure
- [ ] **Testing**: Test HTML sanitization with various HTML inputs, test security element removal, test email compatibility
- [ ] **Review**: Review HtmlProcessor implementation and ensure HTML is safe and email-client-compatible

**Phase 3: Basic EML Generation (Week 2, Days 1-3)**
- [ ] **Design**: Design MimeGenerator module architecture and EML file generation workflow
- [ ] **Implementation**: Implement MimeGenerator module using `email.message.EmailMessage`, create basic multipart message structure, implement HTML body addition, implement file serialization to .eml format
- [ ] **Testing**: Test EML file generation, verify file can be opened in email clients, test message structure
- [ ] **Review**: Review MimeGenerator implementation and ensure EML files are valid

**Phase 4: CLI Implementation (Week 2, Days 4-5)**
- [ ] **Design**: Design CLI interface with argparse, argument structure, and help messages
- [ ] **Implementation**: Implement argparse CLI with `--url`, `--output`, `--user`, `--token` arguments, implement argument validation, implement help messages and documentation
- [ ] **Testing**: Test CLI with various argument combinations, test error handling, test help messages, test end-to-end workflow
- [ ] **Review**: Review CLI implementation and ensure user-friendly interface

**Deliverables**:
- MarkdownProcessor module converting Markdown to HTML
- HtmlProcessor module sanitizing HTML for email compatibility
- MimeGenerator module creating basic .eml files
- Complete argparse CLI with all required arguments
- End-to-end workflow: URL → Markdown → HTML → EML
- Integration tests for complete pipeline
- Basic .eml files that open correctly in email clients

#### Sprint 2: High-Fidelity Styling and Embedded Images (2 weeks)
**Goals**: Implement CSS inlining and image embedding to create visually accurate emails that render correctly offline.

**Actions**:
**Phase 1: CSS Stylesheet Creation (Week 1, Days 1-2)**
- [ ] **Design**: Design email-friendly CSS stylesheet with typography, spacing, tables, lists, links, and code blocks
- [ ] **Implementation**: Create CSS stylesheet file with email-compatible styles, ensure styles work across email clients, test style compatibility
- [ ] **Testing**: Test CSS stylesheet with various HTML content, verify styles render correctly, test email client compatibility
- [ ] **Review**: Review CSS stylesheet and ensure professional appearance

**Phase 2: CSS Inlining with Premailer (Week 1, Days 3-5)**
- [ ] **Design**: Design CSS inlining workflow using premailer library
- [ ] **Implementation**: Integrate premailer library, implement HTML wrapping with CSS stylesheet, implement CSS inlining process, implement URL absolutization
- [ ] **Testing**: Test CSS inlining with various HTML content, verify inline styles are applied correctly, test URL absolutization, test email client rendering
- [ ] **Review**: Review CSS inlining implementation and ensure email client compatibility

**Phase 3: Image Processing and CID Embedding (Week 2, Days 1-4)**
- [ ] **Design**: Design ImageProcessor module for finding, downloading, and embedding images as CIDs
- [ ] **Implementation**: Implement ImageProcessor module, parse HTML for `<img>` tags, download images with authentication, generate unique Content-IDs (CIDs), rewrite HTML src attributes to use CIDs, attach images to EmailMessage with CIDs
- [ ] **Testing**: Test image finding and downloading, test CID generation and embedding, test image attachment to email, test email rendering with embedded images, test offline rendering
- [ ] **Review**: Review ImageProcessor implementation and ensure images are properly embedded

**Phase 4: Integration and Testing (Week 2, Day 5)**
- [ ] **Design**: Design integration testing for complete pipeline with images
- [ ] **Implementation**: Integrate ImageProcessor with existing pipeline, update MimeGenerator to handle CID images, test complete workflow
- [ ] **Testing**: Test complete pipeline end-to-end with images, verify email renders correctly in Outlook/Gmail offline, test with various image types and sizes
- [ ] **Review**: Review complete implementation and ensure high-fidelity email generation

**Deliverables**:
- Email-friendly CSS stylesheet
- CSS inlining functionality using premailer
- ImageProcessor module for CID embedding
- Complete pipeline with styled HTML and embedded images
- High-fidelity .eml files that render correctly offline
- Integration tests for image embedding
- Email client compatibility verified (Outlook, Gmail)

#### Sprint 3: Attachments and Final Polish (2 weeks)
**Goals**: Add file attachment support, finalize CLI, complete documentation, and achieve test coverage targets.

**Actions**:
**Phase 1: Attachment Processing (Week 1, Days 1-3)**
- [ ] **Design**: Design attachment extraction and processing workflow
- [ ] **Implementation**: Extract attachment metadata from `confluence-markdown-exporter` output, implement attachment downloading with authentication, distinguish between images and file attachments, implement attachment addition to EmailMessage
- [ ] **Testing**: Test attachment metadata extraction, test attachment downloading, test attachment addition to email, test email with various attachment types
- [ ] **Review**: Review attachment processing implementation and ensure all attachments are included

**Phase 2: CLI Finalization (Week 1, Days 4-5)**
- [ ] **Design**: Design final CLI improvements with complete help messages and robust error handling
- [ ] **Implementation**: Enhance CLI with complete help messages, improve error handling and user feedback, enhance environment variable support, add input validation
- [ ] **Testing**: Test CLI with various scenarios, test error handling, test help messages, test environment variable support
- [ ] **Review**: Review CLI implementation and ensure professional user experience

**Phase 3: Documentation and Testing (Week 2, Days 1-3)**
- [ ] **Design**: Design comprehensive documentation structure and testing strategy
- [ ] **Implementation**: Complete README.md with setup, configuration, and usage instructions, write user documentation, implement comprehensive test suite, achieve 80%+ test coverage with pytest-cov
- [ ] **Testing**: Test documentation completeness and accuracy, execute full test suite, verify test coverage meets targets
- [ ] **Review**: Review documentation and testing coverage, ensure quality standards are met

**Phase 4: Final Integration and Quality Assurance (Week 2, Days 4-5)**
- [ ] **Design**: Design final integration testing and quality assurance plan
- [ ] **Implementation**: Execute end-to-end integration tests, perform quality assurance review, fix any remaining issues, prepare for release
- [ ] **Testing**: Test complete application with all features, verify all acceptance criteria are met, test on different platforms
- [ ] **Review**: Review complete application and ensure it's ready for delivery

**Deliverables**:
- Attachment processing functionality
- Complete CLI with professional help messages
- Comprehensive README.md documentation
- Test coverage above 80%
- Fully-functional, tested, and documented CLI tool
- Complete .eml files with styled body, embedded images, and attachments
- Quality assurance validation
- Production-ready application

**Table 2: 3-Sprint Project Plan Summary**

| Sprint | Goals | Key Phases | Acceptance Criteria |
|--------|-------|------------|---------------------|
| Sprint 0 | Foundation & Library Integration | Project Setup, Testing Infrastructure, Library Integration, Markdown Saving | pytest passes; the tool can successfully extract Markdown content from a Confluence page URL; Markdown file is always saved as part of the output. |
| Sprint 1 | Markdown to HTML & Basic .EML | Markdown Conversion, HTML Sanitization, EML Generation, CLI Implementation | Both Markdown and .eml files are created from a URL. Fidelity is low (unstyled HTML but readable). |
| Sprint 2 | High-Fidelity Styling & Images | CSS Stylesheet, CSS Inlining, Image Embedding, Integration Testing | Generated .eml has CSS inlined and images embedded as CIDs. Renders correctly offline. |
| Sprint 3 | Attachments & Final Polish | Attachment Processing, CLI Finalization, Documentation, Quality Assurance | A fully-functional, tested, and documented CLI tool is delivered. Tool always produces both Markdown and .EML outputs. .EML includes styled body, embedded images, and all file attachments. |

## Concluding Architectural Recommendations

This report has detailed a complete and robust architecture for the Confluence-to-Email Exporter. The design is based on a series of critical, well-justified decisions.

- **Format: .EML Only**. The .MSG format is not technically viable for a standalone Python tool due to the lack of writing libraries. The .EML (MIME) format is an open standard with excellent support in Python's standard library.

- **Leveraging Existing Library: confluence-markdown-exporter**. Instead of building a custom Confluence API client from scratch, the project leverages the mature `confluence-markdown-exporter` library. This eliminates significant development effort and reduces maintenance burden, as the library already handles:
  - URL parsing and resolution
  - Authentication (API tokens and PATs)
  - Content extraction from both Confluence v1 and v2 APIs
  - Markdown conversion from Confluence storage format
  - Attachment metadata extraction

- **The Content Pipeline**: The core complexity of this tool is in the email generation pipeline. This multi-stage process—Extract Markdown → Save Markdown (always) → Convert to HTML → Sanitize HTML → Add CSS Styles → Inline CSS & Absolutize URLs → Embed Images via CID → Attach Files → Generate .EML—is designed to be a modular, testable, and robust assembly line. The tool always produces both outputs: a Markdown file and an EML file.

- **Reduced Scope**: By using `confluence-markdown-exporter`, the project scope is reduced from 4 sprints to 3 sprints, focusing development effort on the unique value proposition: converting Confluence content to high-fidelity email format.

This architecture, when executed via the provided 3-sprint plan, will produce a professional, maintainable, and highly effective utility that fully meets the project's requirements while minimizing development time and complexity.

## Future Enhancements (Post-MVP)

Once the core tool is complete, the modular architecture enables several potential future enhancements:

- **Batch Processing**: The argparse CLI could be enhanced to accept a text file (`--file-input`) containing a list of URLs, processing them in a batch.

- **Jira Integration**: The tool could be extended to not only save the .EML file but to also upload it as an attachment to a specified Jira issue using the Jira REST API.

- **GUI Wrapper**: A simple GUI (e.g., using Tkinter) could be built on top of this core library to make it accessible to non-technical users within the organization.
