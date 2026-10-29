"""Unit tests for evals/research_eval: tracing, chunks, archive, report parser, cache, judge."""

import asyncio
import json

import pytest

from evals.research_eval.archive import RunArchive, build_archive, normalize_url, save_archive
from evals.research_eval.cache import EvalCache
from evals.research_eval.chunks import split_context
from evals.research_eval.judge import Embedder, Judge, parse_json_response
from evals.research_eval.report_parser import cited_urls, parse_report, report_sentences
from evals.research_eval.tracing import Tracer


# --- tracing ---------------------------------------------------------------

async def test_span_parent_follows_context_and_isolates_gathered_tasks():
    tr = Tracer()

    async def child(name):
        with tr.span("child", name=name) as sp:
            await asyncio.sleep(0)
            with tr.span("grandchild", name=name) as g:
                await asyncio.sleep(0)
                assert g.parent_id == sp.span_id
            return sp

    with tr.span("root") as root:
        a, b = await asyncio.gather(child("a"), child("b"))
    assert a.parent_id == b.parent_id == root.span_id
    grand = {s.attributes["name"]: s.parent_id for s in tr.spans if s.name == "grandchild"}
    assert grand == {"a": a.span_id, "b": b.span_id}
    assert Tracer.current() is None


def test_span_records_errors_and_restores_current():
    tr = Tracer()
    with pytest.raises(ValueError):
        with tr.span("boom"):
            raise ValueError("bad")
    assert tr.spans[0].status == "error" and "bad" in tr.spans[0].error
    assert Tracer.current() is None


# --- chunks ----------------------------------------------------------------

def test_split_context_default_format():
    text = ("Source: https://a.com/x\nTitle: A\nContent: first line\nsecond line\n\n"
            "Source: https://b.com\nTitle: None\nContent: other\n")
    chunks, warnings = split_context(text)
    assert warnings == []
    assert [(c["url"], c["title"], c["content"]) for c in chunks] == [
        ("https://a.com/x", "A", "first line\nsecond line"), ("https://b.com", None, "other")]
    again, _ = split_context(text)
    assert [c["id"] for c in again] == [c["id"] for c in chunks]


def test_split_context_unrecognised_text_is_kept_and_flagged():
    chunks, warnings = split_context("an MCP answer\n\n*Source: Foo (https://f.com)*")
    assert len(chunks) == 1 and chunks[0]["url"] is None
    assert warnings == ["unrecognised_context_format"]
    assert split_context("") == ([], [])


# --- archive ---------------------------------------------------------------

def _archive_dict():
    return build_archive(meta={"run_id": "r", "question_id": "q", "query": "core"},
                         spans=[], chunks={}, report_markdown="")


def test_archive_is_write_once_and_version_checked(tmp_path):
    p = save_archive(_archive_dict(), tmp_path / "r.json")
    assert RunArchive.load(p).run_id == "r"
    with pytest.raises(FileExistsError):
        save_archive(_archive_dict(), p)
    bad = _archive_dict() | {"schema_version": "0.9"}
    with pytest.raises(ValueError):
        RunArchive(bad)


def test_normalize_url():
    assert normalize_url("HTTPS://Example.com/a/#frag") == normalize_url("https://example.com/a")
    assert normalize_url("http://www.example.com/a") == normalize_url("https://example.com/a/")
    assert normalize_url("https://example.com/a?x=1") != normalize_url("https://example.com/a")


# --- report parser -----------------------------------------------------------

REPORT = """# EU crypto rules

Intro text before sections ([Reuters](https://reuters.com/a)).

## Licensing

MiCA requires licences for issuers, see [ESMA](https://esma.europa.eu/mica/). A second sentence long enough to count.

- point one https://bare.example.com/x.
- point two

#### Deep heading

| a | b |
|---|---|
| 1 | 2 |

## References

- [Reuters](https://reuters.com/a)
- https://never-cited.org/
"""


def test_parse_report_structure_citations_and_evidence():
    chunks_by_url = {normalize_url("https://esma.europa.eu/mica"): ["c1"]}
    r = parse_report(REPORT, chunks_by_url)
    assert r["title"] == "EU crypto rules"
    assert r["references"] == ["https://reuters.com/a", "https://never-cited.org/"]
    assert "heading_level_jump" in r["parse_warnings"]
    assert "no_references_section" not in r["parse_warnings"]

    paths = [s["heading_path"] for s in r["sections"]]
    assert paths == [["EU crypto rules"], ["EU crypto rules", "Licensing"],
                     ["EU crypto rules", "Licensing", "Deep heading"]]
    lic = r["sections"][1]["paragraphs"]
    assert [p["type"] for p in lic] == ["text", "list"]
    assert lic[0]["citations"] == [{"url": "https://esma.europa.eu/mica/", "anchor": "ESMA"}]
    assert lic[0]["evidence"] == [{"url": "https://esma.europa.eu/mica/", "found": True, "chunk_ids": ["c1"]}]
    assert lic[1]["citations"][0]["url"] == "https://bare.example.com/x"
    assert lic[1]["evidence"][0]["found"] is False
    assert r["sections"][2]["paragraphs"][0]["type"] == "table"
    # References list is not part of the body.
    assert "https://never-cited.org/" not in cited_urls(r)
    assert any(s.startswith("MiCA requires licences") for s in report_sentences(r))


def test_parse_report_flags_missing_parts():
    r = parse_report("Just text with no headings.")
    assert set(r["parse_warnings"]) >= {"no_title", "no_references_section",
                                       "content_before_first_heading"}
    assert parse_report("")["sections"] == []


# --- cache / judge / embedder ---------------------------------------------

def test_parse_json_response_tolerates_fences_and_prose():
    assert parse_json_response('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_response('Sure! {"a": [1]} done') == {"a": [1]}
    with pytest.raises(ValueError):
        parse_json_response("no json here")


async def test_judge_caches_by_full_input_and_skips_bad_replies(tmp_path):
    cache = EvalCache(tmp_path / "c.sqlite")
    replies = iter(['{"total": 3}', "garbage", '{"total": 5}'])
    calls = []

    async def complete(p):
        calls.append(p)
        return next(replies)

    j = Judge(cache, model="m", complete=complete)
    first = await j.ask("p", "1", "prompt A")
    second = await j.ask("p", "1", "prompt A")
    assert first.parsed == second.parsed == {"total": 3}
    assert (first.cache_hit, second.cache_hit) == (False, True)
    bad = await j.ask("p", "2", "prompt A")          # new version -> new key
    assert bad.parsed is None and bad.error
    retry = await j.ask("p", "2", "prompt A")        # unparseable reply was not cached
    assert retry.parsed == {"total": 5}
    assert len(calls) == 3

    # Survives reopening the file.
    cache.close()
    j2 = Judge(EvalCache(tmp_path / "c.sqlite"), model="m", complete=complete)
    assert (await j2.ask("p", "1", "prompt A")).cache_hit


async def test_judge_records_backend_errors():
    async def complete(p):
        raise RuntimeError("down")

    r = await Judge(EvalCache(":memory:"), model="m", complete=complete).ask("p", "1", "x")
    assert r.parsed is None and "down" in r.error


async def test_embedder_embeds_only_missing_texts():
    seen = []

    async def embed(texts):
        seen.append(list(texts))
        return [[float(len(t)), 1.0] for t in texts]

    e = Embedder(EvalCache(":memory:"), model="prov:m", embed=embed)
    assert await e.embed(["a", "bb"]) == [[1.0, 1.0], [2.0, 1.0]]
    assert await e.embed(["bb", "ccc"]) == [[2.0, 1.0], [3.0, 1.0]]
    assert seen == [["a", "bb"], ["ccc"]]
