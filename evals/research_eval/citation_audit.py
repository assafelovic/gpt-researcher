"""
Citation audit: which source passages each part of the report rests on.
-----------------------------------------------------------------------
Shared by the generation metrics (ALCE citation recall / precision, effective
citations, faithfulness) and by the retrieval side's `citation_utilization`,
which reads `used_chunk_ids` for its chunk-level view. One judge call per
paragraph does all of it, so running several of these metrics costs the same
as running one: the audit is memoised on the ScoringContext and every call is
in the judge cache.

Per paragraph the judge sees:
  sentences  numbered, each with the sources it links to (placed by link
             position, `report_parser.cited_sentences`);
  material   for a paragraph with citations, the passages of its cited URLs
             (the retrieved chunks of each URL that best match the paragraph,
             BM25-weighted, within a budget); a cited URL that was never
             retrieved is shown as unavailable. For a paragraph without
             citations, the best-matching passages from everything retrieved.
and returns:
  kind       factual | non_factual (opinion, transition: no claims judged)
  claims     the paragraph's factual claims, each with a 6-level verdict and
             the passage ids it rests on (-> chunk ids)
  sentences  for each citing sentence, whether its sources together support it,
             and per source whether it alone supports it and whether the others
             would without it (ALCE's two conditions for an irrelevant citation)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from string import ascii_lowercase
from typing import TYPE_CHECKING

from gpt_researcher.context.lexical import tokenize

from .archive import normalize_url
from .metrics.lexical import idf_table, weighted_overlap
from .prompts import PARAGRAPH_AUDIT
from .report_parser import body_paragraphs, cited_sentences

if TYPE_CHECKING:
    from .archive import RunArchive
    from .judge import JudgeResponse
    from .metrics.base import ScoringContext

# Bump when the audit's material or unit logic changes (prompt changes bump the
# prompt version instead); every metric that reads the audit carries it in its
# version, so the scorer version changes and old results are not overwritten.
AUDIT_VERSION = "6"

# Faithfulness points per verdict (eval-design/generation-metrics.md §3.2 B).
VERDICT_SCORES = {"supported": 1.0, "inferred_a": 0.5, "inferred_b": 0.4, "inferred_c": 0.3,
                  "unsupported": 0.0, "contradicted": -1.0}

MIN_UNCITED_CHARS = 80      # shorter uncited paragraphs are headings-in-disguise or transitions
PASSAGE_CHARS = 1200        # one chunk shown to the judge
SOURCE_PASSAGES = 12        # chunks shown per cited URL: most pages fit whole
MATERIAL_CHARS = 24000      # per paragraph, shared by its cited URLs
UNCITED_PASSAGES = 4        # BM25 top-k for paragraphs without citations
UNAVAILABLE = "(not available: the agent never retrieved this URL)"


@dataclass
class ParagraphAudit:
    para_id: str
    heading_path: list[str]
    mode: str                                   # cited | uncited
    sentences: list[dict]                       # [{"text", "urls"}]
    sources: list[dict]                         # [{"n", "url", "found", "passages": [{"id", "chunk_id"}]}]
    response: "JudgeResponse | None" = None
    kind: str | None = None                     # factual | non_factual
    claims: list[dict] = field(default_factory=list)
    sentence_checks: list[dict] = field(default_factory=list)
    error: str | None = None
    table: bool = False                         # rows are units; citations belong to the table

    def to_dict(self) -> dict:
        return {"para_id": self.para_id, "heading_path": self.heading_path, "mode": self.mode,
                "kind": self.kind, "claims": self.claims, "sentences": self.sentence_checks,
                "sources": [{"n": s["n"], "url": s["url"], "found": s["found"],
                             "chunk_ids": [p["chunk_id"] for p in s["passages"]]}
                            for s in self.sources],
                "error": self.error}


@dataclass
class CitationAudit:
    paragraphs: list[ParagraphAudit]

    @property
    def responses(self) -> list["JudgeResponse"]:
        return [p.response for p in self.paragraphs if p.response is not None]

    @property
    def judged(self) -> list[ParagraphAudit]:
        return [p for p in self.paragraphs if p.error is None]

    @property
    def used_chunk_ids(self) -> set[str]:
        """Chunks some claim rests on (supported or inferred)."""
        return {cid for p in self.judged for c in p.claims if (c["score"] or 0) > 0
                for cid in c["chunk_ids"]}

    @property
    def sentence_checks(self) -> list[dict]:
        return [s for p in self.judged for s in p.sentence_checks]

    @property
    def citations(self) -> list[dict]:
        """Judged citations for precision and effective-citation counts.

        A sentence-URL pair each, except in tables: a table's source line
        cites the whole table, so every row carries every URL. There each URL
        counts once per table, precise / effective when it is so for any row
        (`sentence` lists the rows). Recall still counts each row.
        """
        out, tables = [], {}
        for s in self.sentence_checks:
            if not s["judged"]:
                continue
            for c in s["citations"]:
                if not s.get("table"):
                    out.append({"para_id": s["para_id"], "sentence": s["sentence"],
                                "supported": s["supported"], **c})
                    continue
                key = (s["para_id"], c["url"])
                if key not in tables:
                    tables[key] = {"para_id": s["para_id"], "sentence": [], "supported": False,
                                   "url": c["url"], "found": c["found"],
                                   "precise": False, "effective": False}
                    out.append(tables[key])
                t = tables[key]
                t["sentence"].append(s["sentence"])
                t["supported"] |= s["supported"]
                t["precise"] |= c["precise"]
                t["effective"] |= c["effective"]
        return out


async def citation_audit(archive: "RunArchive", ctx: "ScoringContext") -> CitationAudit:
    memo, key = ctx.archive_memo(archive), "citation_audit"
    if key not in memo:
        memo[key] = await _run(archive, ctx)
    return memo[key]


def audited_paragraphs(archive: "RunArchive") -> list[dict]:
    """Body paragraphs worth auditing: not code or a table of contents; uncited
    ones only if substantial."""
    return [p for p in body_paragraphs(archive.report) if p["type"] not in ("code", "toc")
            and (p["citations"] or len(p["text"]) >= MIN_UNCITED_CHARS)]


def material_idf(archive: "RunArchive", ctx: "ScoringContext") -> dict[str, float]:
    memo, key = ctx.archive_memo(archive), "material_idf"
    if key not in memo:
        memo[key] = idf_table([archive.chunks[c]["content"] for c in archive.retrieved_chunk_ids])
    return memo[key]


def _rank(text: str, chunk_ids: list[str], archive: "RunArchive", idf: dict) -> list[str]:
    scored = [(weighted_overlap(text, set(tokenize(archive.chunks[c]["content"])), idf), i, c)
              for i, c in enumerate(chunk_ids)]
    return [c for _, _, c in sorted(scored, key=lambda x: (-x[0], x[1]))]


def _candidates(archive: "RunArchive", sents: list[dict], text: str, cids: list[str],
                idf: dict) -> list[str]:
    """A source's chunks in the order to show them: first the best chunk for
    each sentence in turn (a long source is often cited for several facts that
    sit in different chunks), then the rest by match with the whole paragraph."""
    if len(cids) <= 1:
        return list(cids)
    out: list[str] = []
    for s in sents:
        best = _rank(s["text"], cids, archive, idf)[0]
        if best not in out:
            out.append(best)
    out.extend(c for c in _rank(text, cids, archive, idf) if c not in out)
    return out


def citation_units(paragraph: dict, scope: str = "preceding") -> list[dict]:
    """The paragraph split into the units a citation vouches for.

    scope "sentence" (strict ALCE): each sentence alone.
    scope "preceding" (default): a citation also covers the uncited sentences
    right before it, back to the previous citation. gpt-researcher's writer is
    told to cite "at the end of the sentence or paragraph", and in practice
    puts one citation group at the end of a paragraph; scoring only the last
    sentence would judge the citation on its conclusion and ignore the facts it
    was given for. Uncited sentences after the last citation stay on their own.
    """
    sents = cited_sentences(paragraph) or [{"text": paragraph["text"], "urls": []}]
    if paragraph.get("type") == "table":
        # A table is cited once, on the line under it, for all its rows. Each row
        # is a statement of its own, so each data row is a unit carrying the
        # table's citations; judging the whole table as one unit fails it as soon
        # as any of its rows is not fully supported. The header row states nothing.
        urls = list(dict.fromkeys(u for s in sents for u in s["urls"]))
        rows = [[c.strip() for c in r.strip(" |").split("|")]
                for r in paragraph["text"].split("\n") if "|" in r]
        if len(rows) < 2:
            return [{"text": " | ".join(r), "urls": urls, "sentences": 1} for r in rows]
        header, body = rows[0], rows[1:]
        # "Date: 30 June 2024 | Change: ..." so each row reads as a statement.
        return [{"text": " | ".join(f"{h}: {c}" if h else c for h, c in zip(header + [""] * len(r), r)),
                 "urls": urls, "sentences": 1} for r in body if any(r)]
    if scope == "sentence":
        return sents
    units, pending = [], []
    for s in sents:
        if s["urls"]:
            units.append({"text": " ".join([p["text"] for p in pending] + [s["text"]]),
                          "urls": s["urls"], "sentences": len(pending) + 1})
            pending = []
        else:
            pending.append(s)
    return units + pending


def prepare(archive: "RunArchive", paragraph: dict, idf: dict,
            scope: str = "preceding") -> ParagraphAudit:
    sents = citation_units(paragraph, scope)
    urls = list(dict.fromkeys(u for s in sents for u in s["urls"]))
    sources: list[dict] = []
    if urls:
        mode = "cited"
        per_source = max(2 * PASSAGE_CHARS, MATERIAL_CHARS // len(urls))
        for n, url in enumerate(urls, 1):
            cids = archive.chunks_by_url.get(normalize_url(url), [])
            picked, used = [], 0
            for cid in _candidates(archive, cited_sentences(paragraph), paragraph["text"],
                                   cids, idf)[:SOURCE_PASSAGES]:
                size = min(len(archive.chunks[cid]["content"]), PASSAGE_CHARS)
                if picked and used + size > per_source:
                    break
                picked.append(cid)
                used += size
            sources.append({"n": n, "url": url, "found": bool(cids),
                            "passages": [{"id": f"{n}{ascii_lowercase[i]}", "chunk_id": c}
                                         for i, c in enumerate(picked)]})
    else:
        mode = "uncited"
        top = _rank(paragraph["text"], archive.retrieved_chunk_ids, archive, idf)[:UNCITED_PASSAGES]
        sources = [{"n": n, "url": archive.chunks[c].get("url"), "found": True,
                    "passages": [{"id": f"{n}a", "chunk_id": c}]} for n, c in enumerate(top, 1)]
    return ParagraphAudit(paragraph["para_id"], [], mode, sents, sources,
                          table=paragraph.get("type") == "table")


def render(archive: "RunArchive", pa: ParagraphAudit) -> str:
    num = {s["url"]: s["n"] for s in pa.sources}
    lines = []
    for i, s in enumerate(pa.sentences, 1):
        cites = ", ".join(f"[{num[u]}]" for u in s["urls"] if u in num)
        lines.append(f"{i}. {s['text']}" + (f"  (cites: {cites})" if cites else ""))
    blocks = []
    if pa.mode == "uncited":
        blocks.append("(The paragraph cites nothing. These are the retrieved passages that "
                      "match it best.)")
    for s in pa.sources:
        header = f"Source [{s['n']}] {s['url'] or 'unknown source'}"
        if not s["found"]:
            blocks.append(f"{header}\n{UNAVAILABLE}")
            continue
        for p in s["passages"]:
            text = archive.chunks[p["chunk_id"]]["content"][:PASSAGE_CHARS]
            blocks.append(f"{header} passage {p['id']}:\n{text}")
    if not pa.sources:
        blocks.append("(no material)")
    return PARAGRAPH_AUDIT.render(question=archive.query, sentences="\n".join(lines),
                                  material="\n\n".join(blocks))


def interpret(pa: ParagraphAudit) -> None:
    """Fill kind / claims / sentence_checks from the judge response."""
    r = pa.response
    if r is None or not isinstance(r.parsed, dict):
        pa.error = (r.error if r else None) or "no usable judge response"
        return
    data = r.parsed
    pa.kind = data.get("kind") if data.get("kind") in ("factual", "non_factual") else "factual"
    passage_chunk = {p["id"]: p["chunk_id"] for s in pa.sources for p in s["passages"]}
    for c in data.get("claims") or [] if pa.kind == "factual" else []:
        if not isinstance(c, dict):
            continue
        verdict = str(c.get("verdict", "")).strip().lower()
        pa.claims.append({
            "claim": c.get("claim", ""), "verdict": verdict, "score": VERDICT_SCORES.get(verdict),
            "sentences": c.get("sentences") or [],
            "chunk_ids": [passage_chunk[str(x)] for x in c.get("passages") or []
                          if str(x) in passage_chunk],
            "evidence": c.get("evidence", "")})

    by_n = {}
    for s in data.get("sentences") or []:
        if isinstance(s, dict):
            try:
                by_n[int(s.get("sentence"))] = s
            except (TypeError, ValueError):
                continue
    url_of = {s["n"]: s for s in pa.sources}
    num = {s["url"]: s["n"] for s in pa.sources}
    for i, sent in enumerate(pa.sentences, 1):
        if not sent["urls"]:
            continue
        got = by_n.get(i, {})
        cites = {}
        for c in got.get("citations") or []:
            try:
                cites[int(c.get("source"))] = c
            except (TypeError, ValueError, AttributeError):
                continue
        found_any = any(url_of[num[u]]["found"] for u in sent["urls"])
        # A sentence whose sources were never retrieved cannot be supported by them.
        supported = bool(got.get("supported")) if found_any else False
        judged = found_any is False or "supported" in got
        checks = []
        for u in sent["urls"]:
            src = url_of[num[u]]
            c = cites.get(src["n"], {})
            alone = bool(c.get("alone")) and src["found"]
            rest = bool(c.get("rest_suffice")) and len(sent["urls"]) > 1
            checks.append({"url": u, "found": src["found"], "alone": alone, "rest_suffice": rest})
        _alce(supported, checks)
        pa.sentence_checks.append({"para_id": pa.para_id, "sentence": i, "text": sent["text"],
                                   "judged": judged, "supported": supported, "citations": checks,
                                   "table": pa.table})


def _alce(supported: bool, checks: list[dict]) -> None:
    """ALCE precision per citation, as in its reference implementation.

    Not jointly supported -> no citation of the sentence is precise. One
    citation -> precise iff supported. Several -> a citation is irrelevant only
    when it does not support the sentence alone AND the rest still do.
    A citation counts as effective (supported) when it supports the sentence
    alone, or is the single citation of a supported sentence.
    """
    for c in checks:
        if not supported:
            c["precise"] = False
        elif len(checks) == 1:
            c["precise"] = True
        else:
            c["precise"] = c["alone"] or not c["rest_suffice"]
        c["effective"] = c["alone"] or (supported and len(checks) == 1)


async def _run(archive: "RunArchive", ctx: "ScoringContext") -> CitationAudit:
    idf = material_idf(archive, ctx)
    paragraphs = audited_paragraphs(archive)
    heading = {p["para_id"]: s["heading_path"] for s in archive.report["sections"]
               for p in s["paragraphs"]}
    audits = []
    for p in paragraphs:
        pa = prepare(archive, p, idf, ctx.option("citation_scope", "preceding"))
        pa.heading_path = heading.get(p["para_id"], [])
        audits.append(pa)

    async def ask(pa: ParagraphAudit) -> None:
        pa.response = await ctx.judge.ask(PARAGRAPH_AUDIT.id, PARAGRAPH_AUDIT.version,
                                          render(archive, pa))
        interpret(pa)

    await ctx.gather(ask(pa) for pa in audits)
    return CitationAudit(audits)


