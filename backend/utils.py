from __future__ import annotations

import logging
import urllib.parse

import aiofiles
import mistune
from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException
from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)


async def write_to_file(
    filename: str,
    text: str,
) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
        filename (str): The filename to write to.
        text (str): The text to write.
    """
    # Convert text to UTF-8, replacing any problematic characters
    text_utf8 = str(text).encode("utf-8", errors="replace").decode("utf-8")

    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(text_utf8)


async def write_text_to_md(
    text: str,
    filename: str = "",
) -> str:
    """Writes text to a Markdown file and returns the file path.

    Args:
        text (str): Text to write to the Markdown file.

    Returns:
        str: The file path of the generated Markdown file.
    """
    file_path = f"outputs/{filename[:60]}.md"
    await write_to_file(file_path, text)
    return urllib.parse.quote(file_path)


async def write_md_to_pdf(
    text: str,
    filename: str = "",
) -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
    ----
        text (str): Markdown text to convert
        filename (str): Base filename to use

    Returns:
    -------
        str: The encoded file path of the generated PDF
    """
    file_path = f"outputs/{filename[:60]}.pdf"

    try:
        # Convert markdown to HTML
        md = MarkdownIt()
        html = md.render(text)

        # Apply CSS styles
        css_file_path = "./frontend/pdf_styles.css"
        with open(css_file_path) as css_file:
            css = css_file.read()

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=11)

        # Add CSS styles to the PDF
        try:
           pdf.write_html(f"<style>{css}</style>{html}")
        except FPDFUnicodeEncodingException:
            logger.warning("FPDFUnicodeEncodingException: Removing unicode characters due to FPDF limitations.")
            pdf.add_page()
            pdf.set_font("helvetica", size=11)
            pdf.write_html(f"<style>{css}</style>{html}".encode("ascii", errors="replace").decode("ascii"))

        # Save PDF
        pdf.output(file_path)

        logger.debug(f"Report written to '{file_path}' with styles from '{css_file_path}'")

    except Exception as e:
        logger.exception(f"Error in converting Markdown to PDF: {e}")
        return ""

    return urllib.parse.quote(file_path)


async def write_md_to_word(
    text: str,
    filename: str = "",
) -> str:
    """Converts Markdown text to a DOCX file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated DOCX.
    """
    file_path = f"outputs/{filename[:60]}.docx"

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
        doc.save(file_path)

        logger.debug(f"Report written to {file_path}")

        return urllib.parse.quote(file_path)

    except Exception as e:
        logger.exception(f"Error in converting Markdown to DOCX: {e}")
        return ""
