from __future__ import annotations

import os
import urllib.parse

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import mistune

from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException
from gpt_researcher.utils.logger import get_formatted_logger
from markdown_it import MarkdownIt

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_formatted_logger("gpt_researcher")

MAX_FILENAME_LENGTH: int = 60


async def write_to_file(
    filepath: os.PathLike | str,
    text: str,
    encoding: str = "utf-8",
) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
    ----
        filepath (os.PathLike | str): The filepath to write to.
        text (str): The text to write.
        encoding (str): The encoding to use.
    """
    # Convert text to UTF-8, replacing any problematic characters
    text_utf8 = str(text).encode(encoding, errors="replace").decode(encoding)

    filepath = os.path.abspath(os.path.normpath(filepath))
    async with aiofiles.open(filepath, "w", encoding=encoding) as file:
        await file.write(text_utf8)


async def write_text_to_md(
    text: str,
    filename: str = "",
    output_dir: os.PathLike | str = "outputs",
) -> str:
    """Writes text to a Markdown file and returns the file path.

    Args:
    ----
        text (str): Text to write to the Markdown file.
        filename (str): Base filename to use
        output_dir (os.PathLike | str): Directory to save the Markdown file

    Returns:
    -------
        str: The file path of the generated Markdown file.
    """
    file_path = os.path.join(output_dir, f"{filename[:MAX_FILENAME_LENGTH]}.md")
    await write_to_file(file_path, text)
    return urllib.parse.quote(file_path)


async def write_md_to_pdf(
    text: str,
    filename: str = "",
    output_dir: os.PathLike | str = "outputs",
    css_file_path: os.PathLike | str = "./frontend/pdf_styles.css",
    text_size: int = 11,
    font_family: str = "helvetica",
) -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
    ----
        text (str): Markdown text to convert
        filename (str): Base filename to use
        output_dir (os.PathLike | str): Directory to save the PDF file
        css_file_path (os.PathLike | str): Path to the CSS file
        text_size (int): Text size
        font_family (str): Font family

    Returns:
    -------
        str: The encoded file path of the generated PDF
    """
    file_path = os.path.join(output_dir, f"{filename[:MAX_FILENAME_LENGTH]}.pdf")

    try:
        # Convert markdown to HTML
        md = MarkdownIt()
        html = md.render(text)

        # Apply CSS styles
        css_file_path = Path(os.path.normpath(css_file_path))
        css = css_file_path.read_text()

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font(font_family, size=text_size)

        # Add CSS styles to the PDF
        try:
            pdf.write_html(f"<style>{css}</style>{html}")
        except FPDFUnicodeEncodingException:
            logger.warning("FPDFUnicodeEncodingException: Removing unicode characters due to FPDF limitations.")
            pdf.add_page()
            pdf.set_font(font_family, size=text_size)
            pdf.write_html(f"<style>{css}</style>{html}".encode("ascii", errors="replace").decode("ascii"))

        # Save PDF
        pdf.output(file_path)

        logger.debug(f"Report written to '{file_path}' with styles from '{css_file_path}'")

    except Exception as e:
        logger.exception(f"Error in converting Markdown to PDF! {e.__class__.__name__}: {e}")
        return ""

    return urllib.parse.quote(file_path)


async def write_md_to_word(
    text: str,
    filename: str = "",
    output_dir: os.PathLike | str = "outputs",
) -> str:
    """Converts Markdown text to a DOCX file and returns the file path.

    Args:
    ----
        text (str): Markdown text to convert.
        filename (str): Base filename to use
        output_dir (os.PathLike | str): Directory to save the DOCX file

    Returns:
    -------
        str: The encoded file path of the generated DOCX.
    """
    file_path = os.path.join(output_dir, f"{filename[:MAX_FILENAME_LENGTH]}.docx")

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
        logger.exception(f"Error in converting Markdown to DOCX! {e.__class__.__name__}: {e}")
        return ""
