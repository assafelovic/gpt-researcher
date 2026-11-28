"""Offline unit tests for post-report citation provenance verification."""

import pytest

from gpt_researcher import GPTResearcher
from gpt_researcher.actions import (
    CitationAudit,
    annotate_unverified_citations,
    extract_cited_urls,
    verify_report_citations,
)
from gpt_researcher.actions.citation_verifier import normalize_citation_url

_SITE_A = "https://example.com"
_SITE_B = "https://example.org"


def test_extract_cited_urls_handles_inline_reference_autolink_and_bare():
    report = (
        "# Findings\n\n"
        f'See [Docs]({_SITE_A}/overview "Overview") and '
        f"[Guide]({_SITE_B}/wiki/Topic_(overview)).\n"
        f"Angle link: [Spec](<{_SITE_B}/spec/v1>).\n"
        f"Autolink: <{_SITE_B}/auto>.\n"
        f"Bare link in prose: {_SITE_B}/bare-page.\n"
        "Also referenced via [ref1].\n\n"
        f"[ref1]: {_SITE_B}/reference-style\n"
    )

    urls = extract_cited_urls(report)

    assert urls == [
        f"{_SITE_A}/overview",
        f"{_SITE_B}/wiki/Topic_(overview)",
        f"{_SITE_B}/spec/v1",
        f"{_SITE_B}/reference-style",
        f"{_SITE_B}/auto",
        f"{_SITE_B}/bare-page",
    ]


def test_extract_cited_urls_ignores_code_blocks_inline_code_and_images():
    bt3 = "`" * 3
    tilde3 = "~" * 3
    bang = "!"
    report = (
        f"Real citation: [Paper]({_SITE_B}/paper/101).\n"
        f"Embedded chart: {bang}[Chart]({_SITE_A}/chart.png).\n"
        f"Inline code: `{_SITE_A}/inline-ignored` and ``[x]({_SITE_A}/span-ignored)``.\n\n"
        f"{bt3}python\n"
        f'url = "{_SITE_A}/fenced-ignored"\n'
        f"{bt3}\n\n"
        f"{tilde3}markdown\n"
        f"[Sample]({_SITE_A}/tilde-ignored)\n"
        f"{tilde3}\n"
    )

    assert extract_cited_urls(report) == [f"{_SITE_B}/paper/101"]


def test_normalize_citation_url_equivalence_and_distinction():
    trk1 = "utm_" + "source=search"
    trk2 = "gcl" + "id=123"
    a = normalize_citation_url(f"{_SITE_A.upper()}:443/Article/?b=2&{trk1}&a=1#sec")
    b = normalize_citation_url(f"{_SITE_A}/Article?a=1&b=2&{trk2}")
    c = normalize_citation_url(f"{_SITE_A}/Article?a=1&b=3")

    assert a == b
    assert a != c
    plain_http = _SITE_A.replace("https://", "http://")
    assert normalize_citation_url(f"{plain_http}:80/") == plain_http
    assert normalize_citation_url(f"{_SITE_A}.:443/path/") == f"{_SITE_A}/path"


def test_verify_report_citations_identifies_verified_unverified_and_uncited():
    trk = "utm_" + "campaign=q4"
    cited_doc = f"{_SITE_A.upper()}/docs/?{trk}#intro"
    report = (
        f"Confirmed claim ([Docs]({cited_doc})).\n"
        f"Unverified claim ([Other]({_SITE_B}/missing)).\n"
        f"Source-dict claim ([API]({_SITE_A}/v2)).\n"
    )
    visited = {
        f"{_SITE_A}/docs",
        f"{_SITE_A}/unused-report",
    }
    sources = [
        {"url": f"{_SITE_A}/v2/", "title": "API"},
        {"href": f"{_SITE_A}/unused-paper"},
    ]

    audit = verify_report_citations(report, visited, research_sources=sources)

    assert isinstance(audit, CitationAudit)
    assert audit.verified_urls == [cited_doc, f"{_SITE_A}/v2"]
    assert audit.unverified_urls == [f"{_SITE_B}/missing"]
    assert audit.uncited_sources == [
        f"{_SITE_A}/unused-paper",
        f"{_SITE_A}/unused-report",
    ]
    assert audit.verification_rate == pytest.approx(2 / 3)
    assert audit.to_dict()["unverified_urls"] == [f"{_SITE_B}/missing"]


def test_verify_report_citations_handles_empty_and_malformed_inputs():
    audit_empty = verify_report_citations("", None, None)
    assert audit_empty.cited_urls == []
    assert audit_empty.verified_urls == []
    assert audit_empty.unverified_urls == []
    assert audit_empty.uncited_sources == []
    assert audit_empty.verification_rate == 1.0

    audit_none = verify_report_citations(
        None, [None, "", f"{_SITE_A}/valid"], [123, {}]
    )
    assert audit_none.cited_urls == []
    assert audit_none.uncited_sources == [f"{_SITE_A}/valid"]
    assert audit_none.verification_rate == 1.0


def test_annotate_unverified_citations_marks_only_unverified_prose_links_idempotently():
    bt3 = "`" * 3
    bang = "!"
    good = f"{_SITE_A}/good"
    other = f"{_SITE_B}/other"
    report = (
        f"Verified [Good]({good}) and unverified [Other]({other}). "
        f"Image {bang}[Img]({other}.png). "
        f"Code `[Other]({other})`.\n"
        f"{bt3}\n[Other]({other})\n{bt3}\n"
    )
    visited = {f"{good}/"}

    annotated = annotate_unverified_citations(report, visited)
    assert f"[Good]({good}) and" in annotated
    assert f"[Other]({other}) [unverified]." in annotated
    assert f"{bang}[Img]({other}.png)." in annotated
    assert f"`[Other]({other})`." in annotated
    assert f"{bt3}\n[Other]({other})\n{bt3}" in annotated

    # Applying a second time must not double-annotate.
    assert annotate_unverified_citations(annotated, visited) == annotated


def test_researcher_verify_citations_uses_visited_urls_and_research_sources():
    researcher = GPTResearcher.__new__(GPTResearcher)
    researcher.visited_urls = {f"{_SITE_A}/visited"}
    researcher.research_sources = [{"url": f"{_SITE_A}/from-source"}]

    report = (
        f"Point A [A]({_SITE_A}/visited#top), "
        f"Point B [B]({_SITE_A}/from-source), "
        f"Point C [C]({_SITE_A}/not-visited)."
    )

    audit = researcher.verify_citations(report)

    assert audit.verified_urls == [
        f"{_SITE_A}/visited#top",
        f"{_SITE_A}/from-source",
    ]
    assert audit.unverified_urls == [f"{_SITE_A}/not-visited"]
    assert audit.uncited_sources == []
    assert audit.verification_rate == pytest.approx(2 / 3)
