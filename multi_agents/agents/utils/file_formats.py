from __future__ import annotations

import os
import urllib
import urllib.parse
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import mistune

if TYPE_CHECKING:
    import logging

    from docx.document import Document

from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


async def write_to_file_async(
    filename: os.PathLike | str,
    text: str,
) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
        filename (str): The filename to write to.
        text (str): The text to write.
    """
    file_path = Path(os.path.expandvars(os.path.normpath(filename))).absolute()
    # Convert text to UTF-8, replacing any problematic characters
    text_utf8 = text.encode("utf-8", errors="replace").decode("utf-8")

    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.write(text_utf8)
    logger.info(f"Report written to '{file_path}'")


async def write_md_to_word(
    text: str,
    path: os.PathLike | str,
) -> str:
    """Converts Markdown text to a DOCX file and returns the file path.

    Args:
        text (str): Markdown text to convert.
        path (os.PathLike | str): The path to save the DOCX file.

    Returns:
        str: The encoded file path of the generated DOCX.
    """
    task = uuid.uuid4().hex
    file_path = Path(os.path.normpath(path), task).with_suffix(".docx").absolute()

    try:
        from docx import Document
        from htmldocx import HtmlToDocx

        # Convert report markdown to HTML
        html: str | list[dict[str, Any]] = mistune.html(text)
        # Create a document object
        doc: Document = Document()
        # Convert the html generated from the report to document format
        HtmlToDocx().add_html_to_document(html, doc)

        # Saving the docx document to file_path
        doc.save(str(file_path))

        print(f"Report written to {file_path}")

        return urllib.parse.quote(f"{file_path}.docx")

    except Exception as e:
        print(f"Error in converting Markdown to DOCX: {e}")
        return ""


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
    text_utf8 = text.encode("utf-8", errors="replace").decode("utf-8")

    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(text_utf8)


async def write_text_to_md(
    text: str,
    path: os.PathLike | str,
) -> str:
    """Writes text to a Markdown file and returns the file path.

    Args:
        text (str): Text to write to the Markdown file.

    Returns:
        str: The file path of the generated Markdown file.
    """
    task = uuid.uuid4().hex
    file_path = Path(os.path.normpath(path), task).with_suffix(".md").absolute()
    await write_to_file_async(file_path, text)
    logger.info(f"Markdown report written to '{file_path}'")
    return urllib.parse.quote(str(file_path))


async def write_md_to_pdf(
    text: str,
    path: os.PathLike | str,
) -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated PDF.
    """
    task = uuid.uuid4().hex
    md_file_path = Path(os.path.normpath(path), task).with_suffix(".md").absolute()
    pdf_file_path = md_file_path.with_suffix(".pdf")

    try:
        # Moved imports to inner function to avoid known import errors with gobject-2.0
        from md2pdf.core import md2pdf

        md2pdf(
            pdf_file_path,
            md_content=text,
            md_file_path=md_file_path,
            css_file_path="./multi_agents/skills/utils/pdf_styles.css",  # Updated path
            base_url=None,
        )
    except Exception as e:
        logger.exception(f"Error occurred while converting Markdown to PDF: {e.__class__.__name__}: {e}")
        return text
    else:
        logger.info(f"PDF report written to '{pdf_file_path}'")
        return urllib.parse.quote(str(pdf_file_path))
