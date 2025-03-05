from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any

import markdown

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_formatted_logger(__name__)


def extract_headers(
    markdown_text: str,
) -> list[dict[str, Any]]:
    """Extract headers from markdown text.

    Args:
        markdown_text (str): The markdown text to process.

    Returns:
        list[dict[str, Any]]: A list of dictionaries representing the header structure.
    """
    headers: list[dict[str, Any]] = []
    parsed_md: str = markdown.markdown(markdown_text)
    lines: list[str] = parsed_md.split("\n")

    stack: list[dict[str, Any]] = []
    for line in lines:
        if line.startswith("<h") and len(line) > 2 and line[2].isdigit():
            level = int(line[2])
            header_text = line[line.index(">") + 1 : line.rindex("<")]

            while stack and stack[-1]["level"] >= level:
                stack.pop()

            header = {
                "level": level,
                "text": header_text,
            }
            if stack:
                children: list[dict[str, Any]] = stack[-1].setdefault("children", [])
                children.append(header)
            else:
                headers.append(header)

            stack.append(header)

    return headers


def extract_sections(
    markdown_text: str,
) -> list[dict[str, str]]:
    """Extract all written sections from subtopic report.

    Args:
        markdown_text (str): Subtopic report text.

    Returns:
        list[dict[str, str]]: List of sections, each section is a dictionary containing
        'section_title' and 'written_content'.
    """
    sections: list[dict[str, str]] = []
    parsed_md: str = markdown.markdown(markdown_text)

    pattern: str = r"<h\d>(.*?)</h\d>(.*?)(?=<h\d>|$)"
    matches: list[tuple[str, str]] = re.findall(pattern, parsed_md, re.DOTALL)

    for title, content in matches:
        clean_content = re.sub(r"<.*?>", "", content).strip()
        if clean_content:
            sections.append(
                {
                    "section_title": title.strip(),
                    "written_content": clean_content,
                }
            )

    return sections


def table_of_contents(
    markdown_text: str,
) -> str:
    """Generate a table of contents for the given markdown text.

    Args:
        markdown_text (str): The markdown text to process.

    Returns:
        str: The generated table of contents.
    """

    def generate_table_of_contents(
        headers: list[dict[str, Any]],
        indent_level: int = 0,
    ) -> str:
        toc: str = ""
        for header in headers:
            toc += " " * (indent_level * 4) + "- " + header["text"] + "\n"
            if "children" in header:
                toc += generate_table_of_contents(header["children"], indent_level + 1)
        return toc

    try:
        headers: list[dict[str, Any]] = extract_headers(markdown_text)
        toc: str = "## Table of Contents\n\n" + generate_table_of_contents(headers)
    except Exception as e:
        logger.exception("table_of_contents Exception : ", e)
        return markdown_text
    else:
        return toc


def add_references(
    report_markdown: str,
    visited_urls: set[str],
) -> str:
    """Add references to the markdown report.

    Args:
        report_markdown (str): The existing markdown report.
        visited_urls (set): A set of URLs that have been visited during research.

    Returns:
        str: The updated markdown report with added references.
    """
    try:
        url_markdown: str = "\n\n\n## References\n\n"
        url_markdown += "".join(f"- [{url}]({url})\n" for url in visited_urls)
        updated_markdown_report = report_markdown + url_markdown
    except Exception as e:
        logger.exception(
            f"Encountered exception in adding source urls : {e.__class__.__name__}: {e}"
        )
        return report_markdown
    else:
        return updated_markdown_report
