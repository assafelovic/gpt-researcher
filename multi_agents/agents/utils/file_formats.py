from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.parse
from contextlib import suppress

import aiofiles
import mistune


async def write_to_file(
    filename: str,
    text: str,
) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
        filename (str): The filename to write to.
        text (str): The text to write.
    """
    # Ensure text is a string
    text = str(text)

    # Convert text to UTF-8, replacing any problematic characters
    text_utf8: str = str(text).encode("utf-8", errors="replace").decode("utf-8")

    async with aiofiles.open(filename.replace(" ", "_"), "w", encoding="utf-8") as file:
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
    file_path: str = f"outputs/{filename[:60]}.md"
    await write_to_file(file_path, text)
    return urllib.parse.quote(file_path)


async def write_md_to_pdf(
    text: str,
    filename: str = "",
) -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated PDF.
    """
    file_path: str = f"outputs/{filename[:60]}.pdf"

    # Method 1: Try md2pdf (original approach)
    try:
        from md2pdf.core import md2pdf

        md2pdf(
            file_path,
            md_content=text,
            # md_file_path=f"{file_path}.md",
            css_file_path="./frontend/pdf_styles.css",
            base_url=None,
        )
        print(f"Report written to '{file_path}' using md2pdf")
        encoded_file_path: str = urllib.parse.quote(file_path)
        return encoded_file_path
    except Exception as e:
        print(f"md2pdf failed: {e.__class__.__name__}: {e}")
        print("Attempting fallback methods...")

    # Method 2: Try weasyprint command directly
    try:
        success: bool = await _weasyprint_subprocess_fallback(text, file_path)
        if success:
            print(f"Report written to '{file_path}' using weasyprint subprocess")
            encoded_file_path: str = urllib.parse.quote(file_path)
            return encoded_file_path
    except Exception as e:
        print(f"WeasyPrint subprocess failed: {e.__class__.__name__}: {e}")

    # Method 3: Try python -m weasyprint
    try:
        success = await _python_weasyprint_fallback(text, file_path)
        if success:
            print(f"Report written to '{file_path}' using python -m weasyprint")
            encoded_file_path: str = urllib.parse.quote(file_path)
            return encoded_file_path
    except Exception as e:
        print(f"Python module weasyprint failed: {e.__class__.__name__}: {e}")

    # Method 4: Try weasyprint Python API directly
    try:
        success = await _weasyprint_api_fallback(text, file_path)
        if success:
            print(f"Report written to '{file_path}' using WeasyPrint API")
            encoded_file_path: str = urllib.parse.quote(file_path)
            return encoded_file_path
    except Exception as e:
        print(f"WeasyPrint API failed: {e.__class__.__name__}: {e}")

    print("All PDF generation methods failed")
    return ""


async def _weasyprint_subprocess_fallback(
    markdown_text: str,
    output_path: str,
) -> bool:
    """Try using weasyprint command directly via subprocess."""
    # Check if weasyprint command is available
    if not shutil.which("weasyprint"):
        raise FileNotFoundError("weasyprint command not found in PATH")

    # Convert markdown to HTML
    html_content: str = str(mistune.html(markdown_text))

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as temp_html:
        temp_html.write(html_content)
        temp_html_path: str = temp_html.name

    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build weasyprint command
        cmd: list[str] = ["weasyprint"]

        # Add CSS file if it exists
        if os.path.exists("./frontend/pdf_styles.css"):
            cmd.extend(["--stylesheet", "./frontend/pdf_styles.css"])

        # Add input and output files
        cmd.extend([temp_html_path, output_path])

        # Execute command
        _result: subprocess.CompletedProcess[bytes] = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,  # 60 second timeout
        )

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    finally:
        # Clean up temporary file
        with suppress(Exception):
            os.unlink(temp_html_path)


async def _python_weasyprint_fallback(markdown_text: str, output_path: str) -> bool:
    """Try using python -m weasyprint via subprocess."""
    # Convert markdown to HTML
    html_content: str = str(mistune.html(markdown_text))

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as temp_html:
        temp_html.write(str(html_content))
        temp_html_path: str = temp_html.name

    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build python -m weasyprint command
        cmd: list[str] = ["python", "-m", "weasyprint"]

        # Add CSS file if it exists
        if os.path.exists("./frontend/pdf_styles.css"):
            cmd.extend(["--stylesheet", "./frontend/pdf_styles.css"])

        # Add input and output files
        cmd.extend([temp_html_path, output_path])

        # Execute command
        _result: subprocess.CompletedProcess[bytes] = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,  # 60 second timeout
        )

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    finally:
        # Clean up temporary file
        with suppress(Exception):
            os.unlink(temp_html_path)


async def _weasyprint_api_fallback(markdown_text: str, output_path: str) -> bool:
    """Try using WeasyPrint Python API directly."""
    try:
        from weasyprint import CSS, HTML  # pyright: ignore[reportMissingImports]

        # Convert markdown to HTML
        html_content: str = str(mistune.html(markdown_text))

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create HTML object
        html_doc: HTML = HTML(string=html_content)

        # Prepare stylesheets
        stylesheets: list[CSS] = []
        if os.path.exists("./frontend/pdf_styles.css"):
            with open("./frontend/pdf_styles.css", "r", encoding="utf-8") as css_file:
                css_content: str = css_file.read()
                stylesheets.append(CSS(string=css_content))

        # Generate PDF
        html_doc.write_pdf(output_path, stylesheets=stylesheets)

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    except ImportError:
        raise ImportError("WeasyPrint not available for direct API usage")


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
    file_path: str = f"outputs/{filename[:60]}.docx"

    try:
        from docx import Document
        from htmldocx import HtmlToDocx

        # Convert report markdown to HTML
        html: str = str(mistune.html(text))
        # Create a document object
        doc = Document()
        # Convert the html generated from the report to document format
        HtmlToDocx().add_html_to_document(html, doc)

        # Saving the docx document to file_path
        doc.save(file_path)

        print(f"Report (Word Document) written to '{file_path}'")

        encoded_file_path: str = urllib.parse.quote(file_path)
        return encoded_file_path

    except Exception as e:
        print(f"Error in converting Markdown to DOCX: {e.__class__.__name__}: {e}")
        return ""
