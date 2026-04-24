import aiofiles
import logging
import urllib
import mistune
import os
from pathlib import Path

from gpt_researcher.research_run_store import get_outputs_dir

logger = logging.getLogger(__name__)


def _output_path(filename: str, suffix: str) -> Path:
    output_dir = get_outputs_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{filename[:60]}.{suffix}"

async def write_to_file(filename: str, text: str) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
        filename (str): The filename to write to.
        text (str): The text to write.
    """
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)

    # Convert text to UTF-8, replacing any problematic characters
    text_utf8 = text.encode('utf-8', errors='replace').decode('utf-8')

    async with aiofiles.open(filename, "w", encoding='utf-8') as file:
        await file.write(text_utf8)

async def write_text_to_md(text: str, filename: str = "") -> str:
    """Writes text to a Markdown file and returns the file path.

    Args:
        text (str): Text to write to the Markdown file.

    Returns:
        str: The file path of the generated Markdown file.
    """
    file_path = _output_path(filename, "md")
    await write_to_file(str(file_path), text)
    return urllib.parse.quote(str(file_path))

def _preprocess_images_for_pdf(text: str) -> str:
    """Convert web image URLs to absolute file paths for PDF generation.
    
    Transforms /outputs/images/... URLs to absolute file:// paths that
    weasyprint can resolve.
    """
    import re
    
    base_path = os.path.abspath(".")
    
    # Pattern to find markdown images with /outputs/ URLs
    def replace_image_url(match):
        alt_text = match.group(1)
        url = match.group(2)
        
        # Convert /outputs/... to absolute path
        if url.startswith("/outputs/"):
            abs_path = os.path.join(base_path, url.lstrip("/"))
            return f"![{alt_text}]({abs_path})"
        return match.group(0)
    
    # Match ![alt text](/outputs/images/...)
    pattern = r'!\[([^\]]*)\]\((/outputs/[^)]+)\)'
    return re.sub(pattern, replace_image_url, text)


async def write_md_to_pdf(text: str, filename: str = "") -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated PDF.
    """
    file_path = _output_path(filename, "pdf")

    try:
        # Resolve css path relative to this backend module to avoid
        # dependency on the current working directory.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, "styles", "pdf_styles.css")
        
        # Preprocess image URLs for PDF compatibility
        processed_text = _preprocess_images_for_pdf(text)
        
        # Set base_url to current directory for resolving any remaining relative paths
        base_url = os.path.abspath(".")

        from md2pdf.core import md2pdf
        md2pdf(str(file_path),
               md_content=processed_text,
               # md_file_path=f"{file_path}.md",
               css_file_path=css_path,
               base_url=base_url)
        logger.info(f"PDF report written to {file_path}")
    except Exception as e:
        logger.error(f"Error in converting Markdown to PDF: {e}")
        return ""

    encoded_file_path = urllib.parse.quote(str(file_path))
    return encoded_file_path

async def write_md_to_word(text: str, filename: str = "") -> str:
    """Converts Markdown text to a DOCX file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated DOCX.
    """
    file_path = _output_path(filename, "docx")

    try:
        from docx import Document
        from htmldocx import HtmlToDocx
        # Convert report markdown to HTML
        html = mistune.html(text)
        # Create a document object
        doc = Document()
        # Convert the html generated from the report to document format
        HtmlToDocx().add_html_to_document(html, doc)

        # Saving the docx document to file_path
        doc.save(str(file_path))

        logger.info(f"DOCX report written to {file_path}")

        encoded_file_path = urllib.parse.quote(str(file_path))
        return encoded_file_path

    except Exception as e:
        logger.error(f"Error in converting Markdown to DOCX: {e}")
        return ""
