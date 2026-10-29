"""
A. Writing quality: comprehensiveness, insight, readability, instruction
following, topic relevance (eval-design/generation-metrics.md §2).
All scores are absolute; nothing is compared with a reference report.
"""

from __future__ import annotations

import re

from gpt_researcher.context.lexical import tokenize

from ...archive import RunArchive, normalize_url
from ...citation_audit import material_idf
from ...key_points import get_key_points
from ...prompts import (COMPREHENSIVENESS, KEY_POINTS, QUALITY_RUBRIC, QUALITY_SCORE,
                        TOPIC_RELEVANCE)
from ...report_parser import body_paragraphs, cited_urls
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import weighted_overlap
from .common import batches, body_word_count, paragraph_plain, report_text

COVERAGE_POINTS = {"full": 1.0, "partial": 0.5, "none": 0.0}


class Comprehensiveness(Metric):
    """Share of the question's key points the report covers.

        value = (full + 0.5 * partial) / K

    One judge call maps every key point to the report (the same key points as
    the retrieval metrics). No embedding pre-pass: on the retrieval side the
    embedding mapping got 3 of 8 points wrong.

    `details.omitted_but_retrieved` flags uncovered points that some retrieved
    chunk seems to discuss (BM25-weighted share of the point's terms found in
    the chunk >= 0.6): a writing omission rather than a retrieval gap. It is a
    lexical hint, not judged.
    """

    name, category = "comprehensiveness", "generation.writing"
    uses_llm = True
    prompts = (COMPREHENSIVENESS, KEY_POINTS)
    HINT = 0.6

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        if not body_paragraphs(archive.report):
            return self.skip("empty report")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        text, truncated = report_text(archive)
        r = await ctx.judge.ask(COMPREHENSIVENESS.id, COMPREHENSIVENESS.version,
                                COMPREHENSIVENESS.render(
                                    question=archive.query, report=text,
                                    key_points="\n".join(f"{i}. {p}" for i, p in enumerate(points, 1))))
        got = {}
        for e in (r.parsed or {}).get("points", []) if isinstance(r.parsed, dict) else []:
            try:
                got[int(e["point"])] = e
            except (KeyError, TypeError, ValueError):
                continue
        if not got:
            res = self.skip("judge call failed", key_points=provenance, error=r.error)
            res.llm = self.llm_record(ctx, [r])
            return res

        idf = material_idf(archive, ctx)
        chunk_terms = [(c, set(tokenize(archive.chunks[c]["content"]))) for c in archive.retrieved_chunk_ids]
        threshold = ctx.option("omission_hint", self.HINT)
        per_point, total = [], 0.0
        for i, p in enumerate(points, 1):
            cov = str(got.get(i, {}).get("coverage", "none")).lower()
            cov = cov if cov in COVERAGE_POINTS else "none"
            total += COVERAGE_POINTS[cov]
            entry = {"key_point": p, "coverage": cov, "evidence": got.get(i, {}).get("evidence", "")}
            if cov == "none" and chunk_terms:
                best = max(((weighted_overlap(p, t, idf), c) for c, t in chunk_terms), key=lambda x: x[0])
                entry["retrieved_hint"] = {"best_overlap": round(best[0], 3), "chunk_id": best[1],
                                           "url": archive.chunks[best[1]].get("url")}
            per_point.append(entry)
        omitted = [e["key_point"] for e in per_point
                   if e.get("retrieved_hint", {}).get("best_overlap", 0) >= threshold]
        res = self.result(rounded(total / len(points)), key_points=provenance,
                          per_point=per_point, omitted_but_retrieved=omitted,
                          report_truncated=truncated)
        res.llm = self.llm_record(ctx, [r])
        return res


async def quality_scores(archive: RunArchive, ctx: ScoringContext) -> dict:
    """Rubric (once per question, cached) + one scoring call for insight and readability."""
    memo, key = ctx.archive_memo(archive), "quality_scores"
    if key in memo:
        return memo[key]
    out: dict = {"responses": [], "error": None, "dims": {}}
    rub = await ctx.judge.ask(QUALITY_RUBRIC.id, QUALITY_RUBRIC.version,
                              QUALITY_RUBRIC.render(question=archive.query))
    out["responses"].append(rub)
    criteria = []
    if isinstance(rub.parsed, dict):
        for dim, prefix in (("insight", "I"), ("readability", "R")):
            items = [c for c in rub.parsed.get(dim) or [] if isinstance(c, dict)]
            for j, c in enumerate(items, 1):
                try:
                    w = max(0.0, float(c.get("weight", 0)))
                except (TypeError, ValueError):
                    w = 0.0
                criteria.append({"id": f"{prefix}{j}", "dimension": dim,
                                 "criterion": c.get("criterion", ""),
                                 "description": c.get("description", ""), "weight": w})
    if not criteria:
        out["error"] = "rubric generation failed: " + (rub.error or "no criteria")
        memo[key] = out
        return out
    text, truncated = report_text(archive)
    listing = "\n".join(f"{c['id']} [{c['dimension']}] {c['criterion']}: {c['description']}"
                        for c in criteria)
    sc = await ctx.judge.ask(QUALITY_SCORE.id, QUALITY_SCORE.version,
                             QUALITY_SCORE.render(question=archive.query, criteria=listing, report=text))
    out["responses"].append(sc)
    scores = {}
    for e in (sc.parsed or {}).get("scores", []) if isinstance(sc.parsed, dict) else []:
        try:
            scores[str(e["id"]).strip()] = (max(0.0, min(10.0, float(e["score"]))), e.get("evidence", ""))
        except (KeyError, TypeError, ValueError):
            continue
    for dim in ("insight", "readability"):
        rows = []
        for c in criteria:
            if c["dimension"] != dim:
                continue
            s, ev = scores.get(c["id"], (None, ""))
            rows.append({**c, "score": s, "evidence": ev})
        scored = [r for r in rows if r["score"] is not None]
        wsum = sum(r["weight"] for r in scored)
        if scored and wsum <= 0:      # weights missing: treat criteria equally
            for r in scored:
                r["weight"] = 1.0
            wsum = len(scored)
        value = sum(r["weight"] * r["score"] for r in scored) / wsum / 10 if scored else None
        out["dims"][dim] = {"value": value, "criteria": rows, "report_truncated": truncated}
    if not scores:
        out["error"] = "scoring call failed: " + (sc.error or "no scores")
    memo[key] = out
    return out


class _RubricDimension(Metric):
    """RACE-style rubric score on an absolute 0-10 scale, normalised to [0, 1].

    The rubric (3-5 weighted criteria per dimension) is generated once per
    question and cached; insight and readability are scored in the same call.
        value = sum(weight * score) / sum(weight) / 10
    """

    category = "generation.writing"
    uses_llm = True
    prompts = (QUALITY_RUBRIC, QUALITY_SCORE)
    dimension = ""

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        if not body_paragraphs(archive.report):
            return self.skip("empty report")
        q = await quality_scores(archive, ctx)
        dim = q["dims"].get(self.dimension)
        if not dim or dim["value"] is None:
            res = self.skip(q["error"] or "no scored criteria")
        else:
            res = self.result(rounded(dim["value"]), criteria=dim["criteria"],
                              report_truncated=dim["report_truncated"])
        res.llm = {**self.llm_record(ctx, q["responses"]), "shared": "quality_scores"}
        return res


class Insight(_RubricDimension):
    __doc__ = _RubricDimension.__doc__
    name, dimension = "insight", "insight"


class Readability(_RubricDimension):
    __doc__ = _RubricDimension.__doc__
    name, dimension = "readability", "readability"


_TOC = re.compile(r"^\s*(table of contents|contents|目录)\s*$", re.I)


class InstructionFollowing(Metric):
    """Rule checks of the writer prompt's explicit requirements; value = passed / checks.

    min_words            body words >= the configured TOTAL_WORDS (archive config,
                         else option `min_words`, default 1200)
    single_title         exactly one level-1 heading
    clean_headings       a section heading exists, no level jumps, no content before it
    no_toc               no table-of-contents section
    references           a references section that lists links, without duplicates
    in_text_citations    the body carries hyperlinked citations
    cites_only_retrieved every URL cited in the body was retrieved by the agent
    """

    name, category = "instruction_following", "generation.writing"
    MIN_WORDS = 1200

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        parsed = archive.report
        if not body_paragraphs(parsed):
            return self.skip("empty report")
        w = parsed["parse_warnings"]
        cfg = archive.meta.get("config") or {}
        min_words = cfg.get("total_words") or ctx.option("min_words", self.MIN_WORDS)
        words = body_word_count(archive)
        cited = cited_urls(parsed)
        refs = [normalize_url(u) for u in parsed["references"]]
        not_retrieved = [u for u in cited if normalize_url(u) not in archive.chunks_by_url]
        headings = {h for s in parsed["sections"] for h in s["heading_path"]}
        checks = {
            "min_words": words >= min_words,
            "single_title": not ({"no_title", "multiple_titles"} & set(w)),
            "clean_headings": bool(headings) and not ({"heading_level_jump",
                                                        "content_before_first_heading"} & set(w)),
            "no_toc": not any(_TOC.match(h) for h in headings),
            "references": bool(refs) and len(set(refs)) == len(refs),
            "in_text_citations": bool(cited),
            "cites_only_retrieved": not not_retrieved,
        }
        return self.result(rounded(sum(checks.values()) / len(checks)), checks=checks,
                           words=words, min_words=min_words, parse_warnings=w,
                           duplicate_references=len(refs) - len(set(refs)),
                           cited_not_retrieved=not_retrieved)


class TopicRelevance(Metric):
    """Share of paragraphs that serve the core question (DeepEval AnswerRelevancy style).

    Batched judge calls (about 20k characters of paragraphs each) give yes / no /
    idk per paragraph; idk counts as relevant. value = (yes + idk) / judged.
    """

    name, category = "topic_relevance", "generation.writing"
    uses_llm = True
    prompts = (TOPIC_RELEVANCE,)
    BATCH_CHARS = 20000

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        paras = [p for p in body_paragraphs(archive.report) if p["type"] != "code"]
        if not paras:
            return self.skip("empty report")

        async def ask(batch):
            listing = "\n\n".join(f"{i}. {paragraph_plain(p)}" for i, p in enumerate(batch, 1))
            r = await ctx.judge.ask(TOPIC_RELEVANCE.id, TOPIC_RELEVANCE.version,
                                    TOPIC_RELEVANCE.render(question=archive.query, paragraphs=listing))
            return batch, r

        results = await ctx.gather(ask(b) for b in batches(paras, lambda p: len(p["text"]) + 8,
                                                           self.BATCH_CHARS))
        per_para, relevant, judged = [], 0, 0
        for batch, r in results:
            got = {}
            for e in (r.parsed or {}).get("verdicts", []) if isinstance(r.parsed, dict) else []:
                try:
                    got[int(e["paragraph"])] = e
                except (KeyError, TypeError, ValueError):
                    continue
            for i, p in enumerate(batch, 1):
                v = str(got.get(i, {}).get("verdict", "")).lower()
                if v not in ("yes", "no", "idk"):
                    v = None
                else:
                    judged += 1
                    relevant += v != "no"
                per_para.append({"para_id": p["para_id"], "verdict": v,
                                 "reason": got.get(i, {}).get("reason", "")})
        res = (self.result(rounded(relevant / judged), judged=judged, paragraphs=len(paras),
                           off_topic=[p for p in per_para if p["verdict"] == "no"], per_paragraph=per_para)
               if judged else self.skip("every judge call failed"))
        res.llm = self.llm_record(ctx, [r for _, r in results])
        return res
