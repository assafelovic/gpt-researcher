"""Perturbation test tooling for evals/research_eval: each defect lands where
intended, the originals are untouched, and the report reads directions right."""

import json
import re
from pathlib import Path

import pytest

from evals.research_eval.archive import RunArchive
from evals.research_eval.perturb import (PERTURBATIONS, make, report, split_report, threshold,
                                         verdict)

SEED = Path(__file__).parent.parent / "evals" / "research_eval" / "seeds" / "v0" / "q001_default" / "archive.json"
LINK = re.compile(r"\[[^\]]*\]\((https?://[^)]*)\)")


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    out = tmp_path_factory.mktemp("perturb")
    before = SEED.read_bytes()
    manifest = json.loads(make([str(SEED)], str(out)).read_text())
    assert SEED.read_bytes() == before                      # the original is never touched
    return out, manifest


def load(out, run_id):
    return json.loads((out / f"{run_id}.json").read_text())


def body(data):
    return "\n".join(split_report(data["report"]["markdown"])[0])


def test_make_writes_every_perturbation_with_its_own_run_id(made):
    out, manifest = made
    run = manifest["runs"][0]
    names = [p["name"] for p in run["perturbations"] if not p.get("skipped")]
    assert names == list(PERTURBATIONS)
    base = load(out, run["base"])
    src = json.loads(SEED.read_text())
    assert base["report"] == src["report"] and base["spans"] == src["spans"]
    for p in run["perturbations"]:
        d = load(out, p["run_id"])
        assert d["meta"]["run_id"] == p["run_id"] != src["meta"]["run_id"]
        assert d["meta"]["question_id"] == "q001"           # key points still found
        assert p["expected"] and set(p["expected"].values()) <= {"up", "down"}
        assert d != src


def test_report_perturbations_change_the_report_as_intended(made):
    out, manifest = made
    run_id = manifest["runs"][0]["run_id"]
    base = load(out, run_id + "__base")
    p = lambda name: load(out, f"{run_id}__{name}")
    assert not LINK.search(body(p("strip_links")))
    assert LINK.search("\n".join(split_report(p("strip_links")["report"]["markdown"])[1]))   # references kept
    swapped = p("swap_citations")
    mapping = swapped["meta"]["perturbation_mapping"]
    assert mapping and all(a != b for a, b in mapping.items())
    retrieved = set(RunArchive(base).chunks_by_url)
    from evals.research_eval.archive import normalize_url
    assert all(normalize_url(u) in retrieved for u in mapping.values())   # still real pages
    nums = p("alter_numbers")
    assert nums["meta"]["perturbation_changed"] > 10
    assert LINK.findall(body(nums)) == LINK.findall(body(base))           # links untouched
    assert body(base).count("##") > body(p("drop_half_sections")).count("##")
    assert "Sourdough" in body(p("insert_off_topic"))
    assert "clueless bureaucrats" in body(p("insert_toxic_biased"))
    scrambled = body(p("scramble_structure"))
    assert not re.search(r"^#{2,6} ", scrambled, re.M) and scrambled.startswith("# ")
    facts = body(p("facts_only"))
    assert len(facts) < len(body(base)) and re.search(r"^- ", facts, re.M)


async def test_trace_perturbations_change_the_trace_as_intended(made):
    from evals.research_eval.cache import EvalCache
    from evals.research_eval.metrics.base import ScoringContext
    from evals.research_eval.metrics.retrieval.query import PlanAdherence
    out, manifest = made
    run_id = manifest["runs"][0]["run_id"]
    dup = RunArchive(load(out, f"{run_id}__duplicate_subqueries"))
    plan = next(d for d in dup.decompositions if d.kind == "plan")
    q0 = plan.child_queries[0]
    assert all(q0 in q for q in plan.child_queries)
    # executed steps were renamed with their plan: still all delivered
    r = await PlanAdherence().score(dup, ScoringContext(cache=EvalCache(":memory:")))
    assert r.value == 1.0
    off = RunArchive(load(out, f"{run_id}__irrelevant_material"))
    assert any(u.startswith("offtopic-") for u in off.chunks_by_url)


def _write_result(results, run_id, values):
    d = results / run_id
    d.mkdir(parents=True)
    (d / "v.json").write_text(json.dumps({"run_id": run_id, "metrics": {
        m: {"value": v, "skipped": None} for m, v in values.items()}}))


def test_report_judges_direction_against_the_noise(tmp_path):
    manifest = {"runs": [{"run_id": "r", "base": "r__base", "noise": "r__noise", "perturbations": [
        {"name": "strip_links", "run_id": "r__strip_links",
         "expected": {"citation_recall": "down", "citation_coverage": "down"}},
        {"name": "insert_toxic_biased", "run_id": "r__insert_toxic_biased",
         "expected": {"toxicity": "up"}}]}]}
    (tmp_path / "m.json").write_text(json.dumps(manifest))
    res = tmp_path / "results"
    _write_result(res, "r__base", {"citation_recall": 0.8, "citation_coverage": 1.0, "toxicity": 0.0,
                                   "readability": 0.7})
    _write_result(res, "r__noise", {"citation_recall": 0.75, "citation_coverage": 1.0, "toxicity": 0.0,
                                    "readability": 0.7})
    _write_result(res, "r__strip_links", {"citation_recall": 0.72, "citation_coverage": 0.0,
                                          "readability": 0.4})
    _write_result(res, "r__insert_toxic_biased", {"toxicity": 0.0})
    rows, side = report(str(tmp_path / "m.json"), str(res))
    got = {(r["perturbation"], r["metric"]): r["verdict"] for r in rows}
    # recall fell 0.08 but the judge alone moved it 0.05: not beyond 2 x noise
    assert got[("strip_links", "citation_recall")] == "weak"
    assert got[("strip_links", "citation_coverage")] == "pass"
    assert got[("insert_toxic_biased", "toxicity")] == "FAIL"     # did not move
    assert [s["metric"] for s in side] == ["readability"]
    assert verdict("down", 0.5, 0.6, 0.03) == "FAIL" and verdict("up", 0.0, 0.05, 0.03) == "pass"
    assert threshold("effective_citations", 12.0, None) == pytest.approx(1.2)
