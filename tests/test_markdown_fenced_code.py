"""Code comments in fenced examples are not report headings."""

import pytest

from gpt_researcher import GPTResearcher


@pytest.fixture(scope="module")
def researcher():
    return GPTResearcher(query="Report post-processing", verbose=False)


@pytest.fixture(params=["```", "~~~"])
def report(request):
    fence = request.param
    return f'''# Report

Introduction.

{fence}python
# This is a code comment
print("example")
{fence}

## Findings

Actual findings.
'''


def test_headers_ignore_fenced_code(researcher, report):
    assert researcher.extract_headers(report) == [
        {
            "level": 1,
            "text": "Report",
            "children": [{"level": 2, "text": "Findings"}],
        }
    ]


def test_sections_keep_code_in_its_owning_section(researcher, report):
    sections = researcher.extract_sections(report)
    assert [section["section_title"] for section in sections] == ["Report", "Findings"]
    assert '# This is a code comment\nprint("example")' in sections[0]["written_content"]
    assert sections[1]["written_content"] == "Actual findings."


def test_table_of_contents_omits_code_comments(researcher, report):
    assert researcher.table_of_contents(report) == (
        "## Table of Contents\n\n- Report\n    - Findings\n"
    )
