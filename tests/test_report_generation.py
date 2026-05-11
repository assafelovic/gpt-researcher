from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

import gpt_researcher.actions.report_generation as report_generation
from gpt_researcher.actions.report_generation import (
    _normalize_context_text,
    _normalize_report_markdown,
    _report_needs_deterministic_fallback,
)
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.language import normalize_german_technical_terms, normalize_source_title, strip_source_boilerplate


def test_normalize_report_markdown_strips_prelude_and_adds_title_and_references():
    raw_report = """
$prelude$
Includes all source images, videos, and caption metadata.

## Overview
FastAPI and Flask are both widely used Python web frameworks.
"""

    cleaned = _normalize_report_markdown(
        raw_report,
        "Compare FastAPI and Flask",
        "Research context with a source URL: https://example.com/source",
        ["https://example.com/source"],
    )

    assert cleaned.startswith("# Compare FastAPI and Flask")
    assert "$prelude$" not in cleaned
    assert "Includes all source images" not in cleaned
    assert "## Overview" in cleaned
    assert "## References" in cleaned
    assert "https://example.com/source" in cleaned


def test_normalize_report_markdown_preserves_existing_h1():
    raw_report = "# Existing Title\n\nBody text."

    cleaned = _normalize_report_markdown(
        raw_report,
        "Ignored title",
        "",
        None,
    )

    assert cleaned.startswith("# Existing Title")


def test_normalize_report_markdown_strips_url_noise_after_title():
    noisy_url = "https://example.com/" + "a/" * 60
    raw_report = f"# Existing Title\n\n{noisy_url}\n\n## Overview\nBody text."

    cleaned = _normalize_report_markdown(
        raw_report,
        "Ignored title",
        "",
        None,
    )

    assert cleaned.startswith("# Existing Title")
    assert noisy_url not in cleaned
    assert "## Overview" in cleaned


def test_report_needs_deterministic_fallback_for_repetitive_body():
    repetitive = "只要有超多字数，就用什么图表，就用什么格式，就超会带超多链接的, never end vibes "
    raw_report = "# Existing Title\n\n" + repetitive * 10

    assert _report_needs_deterministic_fallback(raw_report)


def test_normalize_source_title_falls_back_to_domain_for_boilerplate_titles():
    title = "Learn Python, C++, App & AI Coding, Game Design & More."

    assert normalize_source_title(title, "https://example.com/course") == "example.com"


def test_strip_source_boilerplate_removes_promotional_leading_line():
    raw_content = """
Learn Python, C++, App & AI Coding, Game Design & More.
Become a Pro Coder in 18+ months.

In diesem Beitrag erfahren Sie mehr über Python-Webframeworks.
"""

    cleaned = strip_source_boilerplate(raw_content)

    assert "Learn Python" not in cleaned
    assert "Become a Pro Coder" not in cleaned
    assert "In diesem Beitrag erfahren Sie mehr über Python-Webframeworks." in cleaned


def test_pretty_print_docs_smooths_boilerplate_titles_and_content():
    doc = Document(
        page_content=(
            "Learn Python, C++, App & AI Coding, Game Design & More.\n"
            "In diesem Beitrag erfahren Sie mehr über Python-Webframeworks."
        ),
        metadata={
            "title": "Learn Python, C++, App & AI Coding, Game Design & More.",
            "source": "https://example.com/course",
        },
    )

    text = PromptFamily.pretty_print_docs([doc])

    assert "Learn Python" not in text
    assert "Title: example.com" in text
    assert "In diesem Beitrag erfahren Sie mehr über Python-Webframeworks." in text


def test_normalize_context_text_strips_document_metadata():
    raw_context = """
Source: https://example.com/source
Title: Example title
Content: Erstes Ergebnis.

Content: Zweites Ergebnis.
"""

    cleaned = _normalize_context_text(raw_context)

    assert "Source:" not in cleaned
    assert "Title:" not in cleaned
    assert "Content:" not in cleaned
    assert "Erstes Ergebnis." in cleaned
    assert "Zweites Ergebnis." in cleaned


def test_normalize_german_technical_terms_rewrites_common_loanwords_without_touching_code():
    raw_text = (
        "FastAPI vs Flask . Best Practices , Open Source - Projekte und Use Cases helfen beim Vergleich.\n"
        "```python\n"
        "print('FastAPI vs Flask')\n"
        "```\n"
    )

    cleaned = normalize_german_technical_terms(raw_text)

    assert "FastAPI gegenüber Flask." in cleaned
    assert "bewährte Vorgehensweisen" in cleaned
    assert "Open-Source-Projekte" in cleaned
    assert "Anwendungsfälle" in cleaned
    assert "print('FastAPI vs Flask')" in cleaned


@pytest.mark.asyncio
async def test_translate_final_report_normalizes_technical_loanwords(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        user_prompt = kwargs["messages"][1]["content"]
        return user_prompt.split("REPORT:\n", 1)[1]

    monkeypatch.setattr(report_generation, "create_chat_completion", fake_create_chat_completion)

    cfg = SimpleNamespace(
        smart_llm_model="model",
        smart_llm_provider="provider",
        smart_token_limit=256,
        llm_kwargs={},
        language="de",
    )

    report_markdown = (
        "# Bericht\n\n"
        "FastAPI vs Flask . Best Practices , Open Source - Projekte und Use Cases werden oft verglichen.\n"
        "```python\n"
        "print('FastAPI vs Flask')\n"
        "```\n\n"
        "## Verifikationsprüfung\n"
        "Best Practices bleiben erhalten.\n"
    )

    translated = await report_generation._translate_final_report(report_markdown, "de", cfg)

    assert "FastAPI gegenüber Flask" in translated
    assert "bewährte Vorgehensweisen bleiben erhalten." in translated
    assert "Open-Source-Projekte" in translated
    assert "Anwendungsfälle" in translated
    assert "print('FastAPI vs Flask')" in translated
    assert "Best Practices" not in translated
