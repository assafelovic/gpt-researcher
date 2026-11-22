"""Headings in the TOC must be the same readable text as section titles."""

import pytest

from gpt_researcher.actions.markdown_processing import (
    extract_headers,
    extract_sections,
    table_of_contents,
)


@pytest.mark.parametrize(
    ("source", "title"),
    [
        ("## Results\n\nBody.", "Results"),
        ("## **Results**\n\nBody.", "Results"),
        ("## *Discussion*\n\nBody.", "Discussion"),
        ("## Research &amp; Development\n\nBody.", "Research & Development"),
        ("## [API guide](https://example.com/api)\n\nBody.", "API guide"),
        ("## `status_code`\n\nBody.", "status_code"),
        ("## A &#8804; B &amp; C.\n\nBody.", "A ≤ B & C."),
    ],
)
def test_header_text_matches_section_title(source, title):
    headers = extract_headers(source)
    sections = extract_sections(source)
    assert headers[0]["text"] == title
    assert sections[0]["section_title"] == title
    assert f"- {title}\n" in table_of_contents(source)
    assert "<" not in table_of_contents(source)


def test_nested_formatted_headers_keep_plain_text():
    source = "# **Report**\n\n## [Findings](https://example.com)\n\nActual findings."
    assert extract_headers(source) == [
        {
            "level": 1,
            "text": "Report",
            "children": [{"level": 2, "text": "Findings"}],
        }
    ]
    assert table_of_contents(source) == (
        "## Table of Contents\n\n- Report\n    - Findings\n"
    )
