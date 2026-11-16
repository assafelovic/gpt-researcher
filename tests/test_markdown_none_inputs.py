"""Regression: markdown helpers must not crash on None/empty inputs."""

from __future__ import annotations

from gpt_researcher.actions.markdown_processing import (
    add_references,
    extract_headers,
    extract_sections,
    table_of_contents,
)


def test_extract_headers_none_and_empty():
    assert extract_headers(None) == []
    assert extract_headers("") == []


def test_extract_sections_none_and_empty():
    assert extract_sections(None) == []
    assert extract_sections("") == []


def test_table_of_contents_none():
    assert table_of_contents(None) == ""


def test_add_references_none_report_or_urls():
    assert add_references(None, set()) == "\n\n\n## References\n\n"
    assert add_references("body", None) == "body"
    assert "## References" in add_references("body", {"https://a.example"})


def test_extract_headers_real_markdown():
    md = "# Title\n\n## Section\n\ntext"
    headers = extract_headers(md)
    assert headers
    assert headers[0]["level"] == 1


def test_report_headings_ignore_shell_comments_in_fenced_code():
    report = """## Setup

```sh
# Example comment
echo hello
```

## Results

Done.
"""

    assert table_of_contents(report) == "## Table of Contents\n\n- Setup\n- Results\n"
    assert extract_sections(report) == [
        {"section_title": "Setup", "written_content": "# Example comment\necho hello"},
        {"section_title": "Results", "written_content": "Done."},
    ]
