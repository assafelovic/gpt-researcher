"""
Integrity audit: is every input counted, and counted once?
----------------------------------------------------------
Reads run archives and their latest score records; calls no model and writes
nothing but its own report. Each check either compares two counts that must
agree, or measures what a limit cut, so a formula that is right on paper is
not fed partial input without anyone noticing (the kind of bug where chunk
splitting swallowed whole pages into the chunk before them).

Status of a check:
  ok    the counts agree / nothing was cut
  note  something is left out by design; the amount is reported
  warn  something was lost or cut that the scores may feel; read the detail
  fail  two counts that must agree do not: a counting bug

Usage:
    python -m evals.research_eval.integrity RUNS/*.json --results-dir RESULTS
    python -m evals.research_eval.integrity RUNS/*.json --results-dir RESULTS --json integrity.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from .archive import RETRIEVAL_SPANS, RunArchive, normalize_url
from .citation_audit import (AUDIT_VERSION, MIN_UNCITED_CHARS, PASSAGE_CHARS, audited_paragraphs,
                             citation_units)
from .metrics.generation.common import REPORT_CHARS, report_text, word_count
from .metrics.retrieval.query import DecompositionTreeQuality
from .report_parser import (_BARE_URL, REFERENCES_HEADING, body_paragraphs, cited_urls,
                            report_ending)
from .scoring import RESULTS_DIR

STATUSES = ("ok", "note", "warn", "fail")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
_MD_LINK = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?(https?://(?:[^()\s<>]|\([^()\s]*\))+)>?"
                      r"(?:\s+\"[^\"]*\")?\s*\)")
TEXT_TOLERANCE = 0.03       # parsed body words may differ from the raw text by this share
CUT_WARN = 0.05             # a limit that cuts more than this share of its input is a warn


def _check(cid: str, name: str, status: str, summary: str, **detail) -> dict:
    assert status in STATUSES
    return {"id": cid, "name": name, "status": status, "summary": summary, "detail": detail}


# --- report parsing ------------------------------------------------------------

def _raw_body(markdown_text: str) -> tuple[list[str], list[str], list[str]]:
    """(body lines, heading lines in the body, lines under references sub-headings).

    The references section runs from its heading to the next heading of the
    same or a higher level, as `report_text` reads it."""
    body, headings, ref_subs = [], [], []
    skip_level, in_sub = 0, False
    for line in markdown_text.splitlines():
        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            if skip_level and level > skip_level:
                in_sub = True
                ref_subs.append(line)
                continue
            skip_level = level if REFERENCES_HEADING.match(m.group(2).strip()) else 0
            in_sub = False
            if not skip_level:
                headings.append(line)
            continue
        if skip_level:
            if in_sub:
                ref_subs.append(line)
            continue
        body.append(line)
    return body, headings, ref_subs


def _raw_urls(lines: list[str]) -> list[str]:
    """Every link and bare URL in these lines, as written (one entry per occurrence)."""
    out = []
    for line in lines:
        out.extend(m.group(2) for m in _MD_LINK.finditer(line))
        rest = _MD_LINK.sub(lambda m: " " if m.group(1).strip() == m.group(2) else m.group(1), line)
        out.extend(u.rstrip(".;:") for u in _BARE_URL.findall(rest))
    return out


def report_checks(archive: RunArchive) -> list[dict]:
    md = archive.report_markdown
    parsed = archive.report
    paras = body_paragraphs(parsed)
    out = []

    # R1: every link in the body is a parsed citation, and nothing else is.
    body, headings, ref_subs = _raw_body(md)
    raw = {normalize_url(u) for u in _raw_urls(body)}
    got = {normalize_url(u) for u in cited_urls(parsed)}
    in_headings = {normalize_url(u) for u in _raw_urls(headings)}
    lost, extra = sorted(raw - got), sorted(got - raw)
    occurrences = sum(len(c["offsets"]) for p in paras for c in p["citations"])
    status = "fail" if lost or extra else "ok"
    out.append(_check("R1", "body links = parsed citations", status,
                      f"{len(raw)} distinct URLs in the body text, {len(got)} parsed"
                      + (f"; {len(lost)} not parsed" if lost else "")
                      + (f"; {len(extra)} parsed but not in the body" if extra else ""),
                      raw_urls=len(raw), parsed_urls=len(got), not_parsed=lost, not_in_body=extra,
                      raw_occurrences=len(_raw_urls(body)), parsed_occurrences=occurrences,
                      links_in_headings=sorted(in_headings)))

    # R2: the parsed paragraphs hold the body's text, once.
    text, _ = report_text(archive, limit=10 ** 9)
    raw_words = sum(word_count(l) for l in text.splitlines() if not _HEADING.match(l))
    parsed_words = sum(word_count(re.sub(r"https?://\S+", "", p["text"])) for p in paras)
    ratio = parsed_words / raw_words if raw_words else 1.0
    status = "ok" if abs(ratio - 1) <= TEXT_TOLERANCE else "fail"
    out.append(_check("R2", "body words parsed", status,
                      f"{parsed_words} of {raw_words} body words in parsed paragraphs ({ratio:.1%})",
                      raw_words=raw_words, parsed_words=parsed_words, ratio=round(ratio, 4)))

    # R3: what the citation audit leaves out, and why.
    audited = {p["para_id"] for p in audited_paragraphs(archive)}
    reasons: dict[str, list[dict]] = {}
    for p in paras:
        if p["para_id"] in audited:
            continue
        why = p["type"] if p["type"] in ("code", "toc") else f"uncited, under {MIN_UNCITED_CHARS} chars"
        reasons.setdefault(why, []).append({"para_id": p["para_id"], "text": p["text"][:120],
                                            "words": word_count(p["text"])})
    left = sum(x["words"] for k, v in reasons.items() if k != "toc" for x in v)
    share = left / parsed_words if parsed_words else 0.0
    out.append(_check("R3", "paragraphs left out of the citation audit",
                      "warn" if share > CUT_WARN else ("note" if reasons else "ok"),
                      f"{len(audited)} of {len(paras)} paragraphs audited; left out: "
                      + (", ".join(f"{len(v)} {k}" for k, v in reasons.items()) or "none")
                      + f" ({share:.1%} of body words, tables of contents aside)",
                      audited=len(audited), paragraphs=len(paras), left_out=reasons,
                      words_left_out=left, share=round(share, 4)))

    # R4: links under a sub-heading of References are references, not body citations.
    sub_links = _raw_urls(ref_subs)
    as_body = sorted({normalize_url(u) for u in sub_links} & got - raw)
    out.append(_check("R4", "references section read as references",
                      "fail" if as_body else ("note" if ref_subs else "ok"),
                      (f"{len(sub_links)} links under sub-headings of References, "
                       f"{len(as_body)} of them read as body citations" if ref_subs
                       else "no sub-headings under References"),
                      lines_under_sub_headings=len(ref_subs), read_as_body=as_body[:20]))

    # R5: the report is whole (the writer did not stop part-way).
    end = report_ending(md)
    out.append(_check("R5", "report complete", "ok" if end["complete"] else "warn",
                      "ends cleanly" if end["complete"] else
                      f"cut off: {', '.join(end['signals'])}; last line: {end['last_line'][-80:]!r}",
                      **end))
    return out


# --- trace and material ----------------------------------------------------------

def trace_checks(archive: RunArchive, raw_data: dict) -> list[dict]:
    out = []
    chunks = archive.chunks
    referenced, missing = set(), []
    for s in archive.spans:
        for cid in s["attributes"].get("chunk_ids") or []:
            if s["name"] in RETRIEVAL_SPANS:
                referenced.add(cid)
            if cid not in chunks:
                missing.append({"span_id": s["span_id"], "chunk_id": cid})
    out.append(_check("T1", "span chunk ids exist", "fail" if missing else "ok",
                      f"{len(missing)} chunk ids point at no chunk" if missing
                      else f"{len(referenced)} chunk ids, all present", missing=missing[:20]))

    orphans = [cid for cid in chunks if cid not in referenced]
    out.append(_check("T2", "every chunk belongs to a search step", "warn" if orphans else "ok",
                      f"{len(orphans)} chunks no search step returned (never counted)" if orphans
                      else f"{len(chunks)} chunks, each from a search step",
                      orphans=orphans[:20]))

    swallowed = [cid for cid, c in chunks.items()
                 if re.search(r"\nSource: [^\n]*\nTitle: ", c.get("content") or "")]
    out.append(_check("T3", "no page swallowed by the chunk before it",
                      "fail" if swallowed else ("note" if archive.chunks_resplit else "ok"),
                      (f"{len(swallowed)} chunks still hold another page's header" if swallowed else
                       f"{archive.chunks_resplit} chunks repaired on load" if archive.chunks_resplit
                       else "no chunk holds another page's header"),
                      swallowed=swallowed[:20], repaired_on_load=archive.chunks_resplit,
                      chunks_in_file=len(raw_data.get("chunks") or {}), chunks_after_repair=len(chunks)))

    unattributed = [cid for cid in archive.retrieved_chunk_ids if not chunks[cid].get("url")]
    warnings = Counter(w for s in archive.spans for w in s["attributes"].get("parse_warnings") or [])
    out.append(_check("T4", "chunks with a source URL", "note" if unattributed else "ok",
                      f"{len(unattributed)} retrieved chunks have no URL (cannot be cited)"
                      if unattributed else "every retrieved chunk has a URL",
                      unattributed=len(unattributed),
                      chars=sum(len(chunks[c]["content"]) for c in unattributed),
                      context_parse_warnings=dict(warnings)))

    failed = archive.failed_deep_steps
    lost = len(archive.retrieved_chunk_ids) - len(archive.writer_chunk_ids)
    out.append(_check("T5", "deep steps whose material was dropped", "note" if failed else "ok",
                      f"{len(failed)} failed deep steps; {lost} chunks never reached the writer"
                      if failed else "no failed deep steps",
                      failed_steps=[{"span_id": s["span_id"], "query": s["attributes"].get("query", "")[:120],
                                     "error": s["attributes"].get("process_error")} for s in failed],
                      chunks_lost=lost))
    return out


# --- what the judge was shown --------------------------------------------------

def prompt_checks(archive: RunArchive, record: dict | None) -> list[dict]:
    out = []
    text, _ = report_text(archive, limit=10 ** 9)
    over = len(text) - REPORT_CHARS
    out.append(_check("W1", "whole report fits the judge prompt", "warn" if over > 0 else "ok",
                      f"report body {len(text)} chars, limit {REPORT_CHARS}"
                      + (f": the last {over} chars are not seen" if over > 0 else ""),
                      chars=len(text), limit=REPORT_CHARS))

    limit = DecompositionTreeQuality.PATH_CHARS
    long = [q for d in archive.decompositions if d.child_queries
            for q in archive.query_path(d.span_id)[:-1] if len(" ".join(q.split())) > limit]
    out.append(_check("W2", "tree-quality path entries shown whole", "note" if long else "ok",
                      f"{len(long)} ancestor queries cut to {limit} chars (the parent itself is shown whole)"
                      if long else "every path entry shown whole",
                      cut=len(long), longest=max((len(q) for q in long), default=0)))

    if record is None:
        return out
    paragraphs = (record.get("citation_audit") or {}).get("paragraphs") or []
    shown = {cid for p in paragraphs for s in p["sources"] + p.get("independent", [])
             for cid in s["chunk_ids"]}
    total = sum(len(archive.chunks[c]["content"]) for c in shown if c in archive.chunks)
    cut = sum(max(0, len(archive.chunks[c]["content"]) - PASSAGE_CHARS) for c in shown if c in archive.chunks)
    share = cut / total if total else 0.0
    out.append(_check("W3", "audit passages shown whole", "warn" if share > CUT_WARN else
                      ("note" if cut else "ok"),
                      f"{cut} of {total} chars of shown passages cut at {PASSAGE_CHARS} ({share:.1%})",
                      chars_shown=total, chars_cut=cut, share=round(share, 4),
                      passages_cut=sum(len(archive.chunks[c]["content"]) > PASSAGE_CHARS
                                       for c in shown if c in archive.chunks)))

    hidden = total_cited = 0
    for p in paragraphs:
        if p["mode"] != "cited":
            continue
        first = {cid for s in p["sources"] for cid in s["chunk_ids"]}
        for s in p["sources"]:
            cids = archive.chunks_by_url.get(normalize_url(s["url"]), [])
            total_cited += len(cids)
            hidden += sum(c not in first for c in cids)
    share = hidden / total_cited if total_cited else 0.0
    out.append(_check("W4", "cited pages' chunks shown in the first audit call",
                      "note" if hidden else "ok",
                      f"{hidden} of {total_cited} chunks of cited pages left to the recheck pool ({share:.1%})",
                      hidden=hidden, chunks_of_cited_pages=total_cited, share=round(share, 4)))

    qr = (record.get("metrics") or {}).get("query_relevance") or {}
    per_query = (qr.get("details") or {}).get("per_query") or []
    urls_total = sum(q.get("urls_total", 0) for q in per_query)
    urls_shown = sum(q.get("urls_shown", 0) for q in per_query)
    if per_query:
        out.append(_check("W5", "query-relevance material: every URL shown",
                          "ok" if urls_shown == urls_total else "note",
                          f"{urls_shown} of {urls_total} URLs shown across {len(per_query)} steps",
                          urls_shown=urls_shown, urls_total=urls_total))
    return out


# --- the citation audit as recorded --------------------------------------------------

def audit_checks(archive: RunArchive, record: dict) -> list[dict]:
    audit = record.get("citation_audit")
    if audit is None:
        return [_check("A0", "citation audit recorded", "note", "no citation audit in the record")]
    out = []
    paragraphs = audit["paragraphs"]
    if audit.get("version") != AUDIT_VERSION:
        out.append(_check("A0", "citation audit version", "warn",
                          f"record has audit v{audit.get('version')}, code is v{AUDIT_VERSION}"))
    parsed = {p["para_id"]: p for p in body_paragraphs(archive.report)}
    expected = [p["para_id"] for p in audited_paragraphs(archive)]
    ids = [p["para_id"] for p in paragraphs]
    dup = sorted(k for k, n in Counter(ids).items() if n > 1)
    missing, unknown = sorted(set(expected) - set(ids)), sorted(set(ids) - set(expected))
    out.append(_check("A1", "every audited paragraph judged once",
                      "fail" if dup or missing or unknown else "ok",
                      f"{len(ids)} audit entries for {len(expected)} paragraphs"
                      + (f"; missing {missing}" if missing else "") + (f"; twice {dup}" if dup else "")
                      + (f"; not in the report {unknown}" if unknown else ""),
                      missing=missing, duplicated=dup, unknown=unknown))

    errors = [{"para_id": p["para_id"], "error": p["error"]} for p in paragraphs if p.get("error")]
    out.append(_check("A2", "judge answered every paragraph", "fail" if errors else "ok",
                      f"{len(errors)} paragraphs dropped from every audit metric (judge error)"
                      if errors else "no judge errors", errors=errors))

    judged = [p for p in paragraphs if not p.get("error")]
    nonfact_cited = [p for p in judged if p["kind"] == "non_factual" and p["mode"] == "cited"]
    pairs = sum(len(s["citations"]) for p in nonfact_cited for s in p["sentences"])
    out.append(_check("A3", "cited paragraphs judged non-factual", "note" if nonfact_cited else "ok",
                      f"{len(nonfact_cited)} cited paragraphs had no claims: their {pairs} citations "
                      f"count in no citation metric" if nonfact_cited else "none",
                      paragraphs=[p["para_id"] for p in nonfact_cited], citations=pairs))

    # A4: the audit's sources are exactly the paragraph's citations, each once.
    mismatch, twice, found_wrong = [], [], []
    for p in judged:
        if p["mode"] != "cited" or p["para_id"] not in parsed:
            continue
        want = {normalize_url(c["url"]) for c in parsed[p["para_id"]]["citations"]}
        have = [normalize_url(s["url"]) for s in p["sources"] if s.get("cited", True)]
        if set(have) != want:
            mismatch.append({"para_id": p["para_id"], "missing": sorted(want - set(have)),
                             "extra": sorted(set(have) - want)})
        twice += [{"para_id": p["para_id"], "url": u} for u, n in Counter(have).items() if n > 1]
        found_wrong += [{"para_id": p["para_id"], "url": s["url"]} for s in p["sources"]
                        if s["found"] != (normalize_url(s["url"]) in archive.chunks_by_url)]
    out.append(_check("A4", "audit sources = the paragraph's citations",
                      "fail" if mismatch or found_wrong else ("warn" if twice else "ok"),
                      f"{len(mismatch)} paragraphs with other sources than they cite, "
                      f"{len(twice)} pages shown twice under two spellings, "
                      f"{len(found_wrong)} wrong 'retrieved' flags",
                      mismatch=mismatch, shown_twice=twice, found_wrong=found_wrong))

    # A5: claims point at items of their paragraph; claim checks are the cited facts.
    stray, check_gap = [], []
    for p in judged:
        if p["para_id"] not in parsed or p["kind"] != "factual":
            continue
        units = citation_units(parsed[p["para_id"]])
        cited_units = {i for i, u in enumerate(units, 1) if u["urls"]}
        expect = 0
        for c in p["claims"]:
            refs = []
            for x in c.get("sentences") or []:
                try:
                    refs.append(int(x))
                except (TypeError, ValueError):
                    pass
            if refs and not any(1 <= n <= len(units) for n in refs):
                stray.append({"para_id": p["para_id"], "claim": c["claim"][:120], "sentences": refs,
                              "items": len(units)})
            if c.get("type", "fact") == "fact" and p["mode"] == "cited" and cited_units \
                    and (not refs or any(n in cited_units for n in refs)):
                expect += 1
        if p["mode"] == "cited" and expect != len(p["claim_checks"]):
            check_gap.append({"para_id": p["para_id"], "expected": expect, "recorded": len(p["claim_checks"])})
    out.append(_check("A5", "claims tied to their items", "fail" if check_gap else ("warn" if stray else "ok"),
                      f"{len(stray)} claims name items the paragraph does not have (counted as uncited); "
                      f"{len(check_gap)} paragraphs whose claim checks do not match their cited facts",
                      stray=stray[:20], claim_check_gap=check_gap))

    # A6: the same fact claims in every metric's denominator.
    facts = [c for p in judged if p["kind"] == "factual" for c in p["claims"]
             if c.get("type", "fact") == "fact"]
    no_verdict = [c["claim"][:120] for c in facts if c.get("faith_score", c.get("score")) is None]
    m = record.get("metrics") or {}
    recall = (m.get("citation_recall") or {}).get("details") or {}
    faith = (m.get("faithfulness") or {}).get("details") or {}
    rows = {"audit": len(facts), "citation_recall.factual_claims": recall.get("factual_claims"),
            "faithfulness.fact_claims (+ claims without a verdict)":
                None if faith.get("fact_claims") is None else faith["fact_claims"] + len(no_verdict)}
    known = {k: v for k, v in rows.items() if v is not None}
    status = "fail" if len(set(known.values())) > 1 else ("warn" if no_verdict else "ok")
    out.append(_check("A6", "fact claims counted alike", status,
                      ", ".join(f"{k} {v}" for k, v in known.items())
                      + (f"; {len(no_verdict)} without a usable verdict" if no_verdict else ""),
                      counts=rows, without_verdict=no_verdict[:20]))

    # A7: every fact the first call did not support went to the recheck.
    todo = [(p["para_id"], c) for p in judged if p.get("independent") for c in p["claims"]
            if c.get("type", "fact") == "fact" and c.get("verdict") != "supported"]
    unchecked = [{"para_id": pid, "claim": c["claim"][:120]} for pid, c in todo
                 if "elsewhere_verdict" not in c]
    out.append(_check("A7", "unsupported facts rechecked", "warn" if unchecked else "ok",
                      f"{len(todo) - len(unchecked)} of {len(todo)} rechecked", unchecked=unchecked[:20]))
    return out


# --- metric results ----------------------------------------------------------------

def metric_checks(record: dict) -> list[dict]:
    m = record.get("metrics") or {}
    skipped = {k: r["skipped"] for k, r in m.items() if r.get("skipped")}
    judge_errors = {k: (r.get("llm") or {}).get("error_messages") or (r.get("llm") or {}).get("errors")
                    for k, r in m.items() if (r.get("llm") or {}).get("errors")}
    out = [_check("M1", "metrics ran", "warn" if judge_errors else ("note" if skipped else "ok"),
                  f"{len(m) - len(skipped)} of {len(m)} metrics have a value"
                  + (f"; judge errors in {sorted(judge_errors)}" if judge_errors else ""),
                  skipped=skipped, judge_errors=judge_errors)]

    # Items a judge reply skipped: dropped from a denominator, or scored as none.
    gaps = {}
    d = lambda k: (m.get(k) or {}).get("details") or {}
    if d("topic_relevance"):
        gaps["topic_relevance: paragraphs without a verdict"] = \
            d("topic_relevance").get("paragraphs", 0) - d("topic_relevance").get("judged", 0)
    if d("query_relevance").get("per_query"):
        gaps["query_relevance: steps without a score"] = \
            sum(q.get("score") is None for q in d("query_relevance")["per_query"])
    if d("decomposition_tree_quality").get("per_parent"):
        gaps["decomposition_tree_quality: parents without a score"] = \
            sum(q.get("score") is None for q in d("decomposition_tree_quality")["per_parent"])
        gaps["decomposition_tree_quality: children without a verdict"] = \
            sum(q.get("unanswered_children") or 0 for q in d("decomposition_tree_quality")["per_parent"]
                if q.get("score") is not None)
        gaps["decomposition_tree_quality: parent aspects without an answer"] = \
            sum(q.get("unanswered_aspects") or 0 for q in d("decomposition_tree_quality")["per_parent"]
                if q.get("score") is not None)
    if "unanswered" in d("subquery_redundancy"):
        gaps["subquery_redundancy: query-tree nodes without a verdict"] = len(d("subquery_redundancy")["unanswered"])
    for k in ("comprehensiveness", "material_coverage"):
        if "unanswered" in d(k):
            gaps[f"{k}: key points the reply skipped (scored none)"] = d(k)["unanswered"]
    if "unknown_verdicts" in d("faithfulness"):
        gaps["faithfulness: claims without a usable verdict"] = d("faithfulness")["unknown_verdicts"]
    bad = {k: v for k, v in gaps.items() if v}
    out.append(_check("M2", "judge replies cover every item", "warn" if bad else "ok",
                      ", ".join(f"{k} {v}" for k, v in bad.items()) or "every item has a verdict",
                      gaps=gaps))
    return out


# --- driver ---------------------------------------------------------------------

def latest_record(run_id: str, results_dir: str | Path) -> dict | None:
    files = sorted(Path(results_dir, run_id).glob("*.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def check_run(path: str | Path, results_dir: str | Path | None = RESULTS_DIR) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    archive = RunArchive(raw)
    record = latest_record(archive.run_id, results_dir) if results_dir else None
    checks = report_checks(archive) + trace_checks(archive, raw) + prompt_checks(archive, record)
    if record is not None:
        checks += audit_checks(archive, record) + metric_checks(record)
    return {"run_id": archive.run_id, "mode": (archive.meta.get("config") or {}).get("mode"),
            "record": record.get("scorer_version") if record else None, "checks": checks}


def summarize(runs: list[dict]) -> str:
    lines = []
    for r in runs:
        counts = Counter(c["status"] for c in r["checks"])
        lines.append(f"== {r['run_id']} [{r['mode']}] record {r['record'] or '(none)'}: "
                     + ", ".join(f"{counts[s]} {s}" for s in STATUSES if counts[s]))
        for c in r["checks"]:
            if c["status"] != "ok":
                lines.append(f"   {c['status']:<4} {c['id']} {c['name']}: {c['summary']}")
    by_check: dict[str, Counter] = {}
    for r in runs:
        for c in r["checks"]:
            by_check.setdefault(f"{c['id']} {c['name']}", Counter())[c["status"]] += 1
    lines.append(f"\n== {len(runs)} runs, per check")
    for name, cnt in by_check.items():
        lines.append(f"   {name:<52} " + ", ".join(f"{cnt[s]} {s}" for s in STATUSES if cnt[s]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archives", nargs="+")
    ap.add_argument("--results-dir", default=str(RESULTS_DIR),
                    help="score records (latest per run is read); '' to check archives only")
    ap.add_argument("--json", default="", help="write every check with its detail here")
    args = ap.parse_args(argv)
    runs = [check_run(p, args.results_dir or None) for p in args.archives]
    print(summarize(runs))
    if args.json:
        Path(args.json).write_text(json.dumps(runs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n-> {args.json}")
    return 1 if any(c["status"] == "fail" for r in runs for c in r["checks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
