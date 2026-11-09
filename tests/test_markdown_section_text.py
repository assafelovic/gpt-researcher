"""Section extraction must return readable text rather than HTML entities."""

import pytest

from gpt_researcher.actions.markdown_processing import extract_sections


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("R&D uses A & B.", "R&D uses A & B."),
        ("Use `a < b` and `x > y`.", "Use a < b and x > y."),
        ("An escaped `'<tag>'` stays visible.", "An escaped '<tag>' stays visible."),
        ("**GPT**-4 improves *text*.", "GPT-4 improves text."),
        ("A &#8804; B &amp; C.", "A ≤ B & C."),
    ],
)
def test_section_content_preserves_readable_text(source, expected):
    sections = extract_sections(f"## Results\n\n{source}")
    assert sections == [{"section_title": "Results", "written_content": expected}]


def test_section_title_is_plain_text():
    sections = extract_sections("## **Research** &amp; Development\n\nBody.")
    assert sections[0]["section_title"] == "Research & Development"


def test_adjacent_html_blocks_keep_word_boundaries():
    sections = extract_sections("## Results\n\n<p>First block.</p><p>Second block.</p>")
    assert sections[0]["written_content"].split() == [
        "First", "block.", "Second", "block."
    ]
