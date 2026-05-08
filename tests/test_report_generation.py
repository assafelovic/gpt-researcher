from gpt_researcher.actions.report_generation import (
    _normalize_report_markdown,
    _report_needs_deterministic_fallback,
)


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
