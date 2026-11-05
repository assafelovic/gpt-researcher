"""Integrity audit for evals/research_eval: a clean run passes every check, and
each kind of lost or double count is caught by the check meant for it."""

import json
from pathlib import Path

import pytest

from evals.research_eval.integrity import check_run, main
from evals.research_eval.metrics import all_metrics
from evals.research_eval.report_parser import parse_report
from evals.research_eval.scoring import save_results, score_archive

from .test_research_eval_generation import REPORT, ScriptedJudge, make_archive  # noqa: F401
from .test_research_eval_generation import ctx  # noqa: F401  (fixture)

SEEDS = Path(__file__).parent.parent / "evals" / "research_eval" / "seeds" / "v0"


def statuses(result):
    return {c["id"]: c["status"] for c in result["checks"]}


def write(tmp_path, archive, name="run.json"):
    path = tmp_path / name
    path.write_text(json.dumps(archive.data), encoding="utf-8")
    return path


@pytest.mark.parametrize("mode", ["default", "detailed", "deep"])
def test_seed_archives_have_no_counting_gaps(mode):
    r = check_run(next(SEEDS.glob(f"*_{mode}")) / "archive.json", results_dir=None)
    s = statuses(r)
    assert not {k for k, v in s.items() if v in ("warn", "fail")}, r["checks"]
    assert {"R1", "R2", "R5", "T1", "T2", "T3", "W1"} <= set(s)


async def scored(tmp_path, ctx, archive):
    # The scripted judge answers the generation prompts and subquery_redundancy's;
    # the other retrieval metrics it runs are rule-based.
    metrics = [m for m in all_metrics() if not m.uses_embeddings
               and (m.category.startswith("generation") or not m.uses_llm
                    or m.name == "subquery_redundancy")]
    record = await score_archive(archive, metrics, ctx)
    save_results(record, tmp_path / "results")
    return check_run(write(tmp_path, archive), tmp_path / "results"), record


async def test_scored_run_accounts_for_every_paragraph_and_claim(tmp_path, ctx):
    r, record = await scored(tmp_path, ctx, make_archive())
    s = statuses(r)
    for cid in ("A1", "A2", "A4", "A5", "A6", "A7", "R1", "R2", "R4", "R5"):
        assert s[cid] == "ok", next(c for c in r["checks"] if c["id"] == cid)
    a6 = next(c for c in r["checks"] if c["id"] == "A6")
    assert len(set(v for v in a6["detail"]["counts"].values() if v is not None)) == 1
    assert s["M1"] in ("ok", "note") and s["M2"] == "ok"


async def test_judge_errors_and_unanswered_items_are_flagged(tmp_path, ctx):
    _, record = await scored(tmp_path, ctx, make_archive())
    m = record["metrics"]
    m["topic_relevance"]["details"]["judged"] -= 1                          # a paragraph got no verdict
    m["insight"]["llm"]["errors"] = 1
    m["subquery_redundancy"]["details"]["unanswered"] = ["q"]
    save_results({**record, "scorer_version": "zz-later"}, tmp_path / "results")
    r = check_run(write(tmp_path, make_archive()), tmp_path / "results")
    s = statuses(r)
    assert s["M1"] == "warn" and s["M2"] == "warn"
    m2 = next(c for c in r["checks"] if c["id"] == "M2")
    assert m2["detail"]["gaps"]["subquery_redundancy: query-tree nodes without a verdict"] == 1


async def test_dropped_or_duplicated_audit_paragraphs_fail(tmp_path, ctx):
    archive = make_archive()
    _, record = await scored(tmp_path, ctx, archive)
    paras = record["citation_audit"]["paragraphs"]
    record["citation_audit"]["paragraphs"] = paras[1:] + paras[-1:]       # one lost, one twice
    record["metrics"]["citation_recall"]["details"]["factual_claims"] += 1
    paras[-1]["error"] = "unparseable reply"
    save_results({**record, "scorer_version": "zz-later"}, tmp_path / "results")
    r = check_run(write(tmp_path, archive), tmp_path / "results")
    assert r["record"] == "zz-later"                                        # latest record read
    s = statuses(r)
    assert s["A1"] == "fail" and s["A2"] == "fail" and s["A6"] == "fail"


def test_archive_counting_problems_are_caught(tmp_path):
    archive = make_archive(REPORT.replace(
        "## References\n", "## References\n\n### Sources we read\n\n- [Extra](https://extra.org/a)\n"))
    data = archive.data
    first = next(iter(data["chunks"]))
    data["chunks"]["c-orphan"] = {"url": "https://orphan.org", "title": "o", "content": "never searched",
                                  "jev_score": None}
    data["chunks"]["c-glued"] = {"url": "https://a.org", "title": "a",
                                 "content": "text\nSource: https://b.org\nTitle: B", "jev_score": None}
    data["spans"][1]["attributes"]["chunk_ids"] += ["c-missing", "c-glued"]
    data["report"]["markdown"] = data["report"]["markdown"].replace(
        "## Outlook\n\nOverall, diversifying suppliers looks like the sensible path for manufacturers going forward.",
        "## Outlook\n\nOverall, diversifying suppliers is **the")
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    s = statuses(check_run(path, results_dir=None))
    assert s["T1"] == "fail" and s["T2"] == "warn" and s["T3"] == "fail"
    assert s["R5"] == "warn"
    # References sub-headings stay references: their links are not body citations.
    assert s["R4"] == "note" and s["R1"] == "ok"
    assert first in data["chunks"]
    assert main([str(path), "--results-dir", ""]) == 1                       # a fail sets the exit code


def test_references_sub_headings_stay_references():
    parsed = parse_report("# T\n\n## A\n\nText ([a](https://a.com)).\n\n## References\n\n"
                          "### Academic\n\n- [b](https://b.com)\n\n### News\n\n- [c](https://c.com)\n")
    assert parsed["references"] == ["https://b.com", "https://c.com"]
    assert [p["text"] for s in parsed["sections"] for p in s["paragraphs"]] == ["Text (a)."]
