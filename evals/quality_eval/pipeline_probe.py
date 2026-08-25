"""
Pipeline Probe — per-stage instrumentation for the research pipeline.
--------------------------------------------------------------------
Every metric in this suite scores the pipeline's OUTPUT, so a low score says a
report is weak without saying which stage weakened it. This module records what
each stage was handed and what it passed on, turning one end-to-end number into
a funnel that can be read stage by stage.

    plan        query           -> sub-queries
    search      sub-queries     -> URLs
    scrape      URLs            -> pages          (anti-bot defences bite here)
    compress    pages           -> chunks         (similarity filter, then top-N)
    write       context         -> report

The recording logic (`PipelineTrace`) is pure and separately testable; the
patching (`PipelineProbe`) only feeds it. Patches are applied to the running
test process and reverted on exit — the library itself is never modified, the
same approach benchmark.py already uses to recover multi-agent source URLs.

Because the hooks sit below the orchestration layer, the probe works unchanged
for both the single-agent and multi-agent workflows.

Usage:
    with PipelineProbe() as probe:
        context = await researcher.conduct_research()
        report  = await researcher.write_report()
    print(probe.trace.funnel())
    sources = probe.trace.scraped_urls      # what the writer could actually read
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Recording  (pure — no imports from gpt_researcher, unit-testable offline)
# ---------------------------------------------------------------------------

@dataclass
class PipelineTrace:
    """What each stage received and produced during one research run."""

    subqueries:   list[str]  = field(default_factory=list)
    searches:     list[dict] = field(default_factory=list)
    scrapes:      list[dict] = field(default_factory=list)
    compressions: list[dict] = field(default_factory=list)
    context_len:  int = 0

    # --- recording -------------------------------------------------------

    def record_search(self, proposed: list[str], accepted: list[str]) -> None:
        """One search's results, before and after de-duplication.

        The pipeline drops URLs it has already seen before anything is scraped,
        so every later stage sees disjoint sets by construction — measuring
        overlap downstream can only ever return zero. This is the one place the
        redundancy is still visible: a sub-query whose results were all seen
        already spent a search slot and returned nothing new.
        """
        self.searches.append({
            "proposed": len(proposed or []),
            "accepted": len(accepted or []),
            "duplicate": len(proposed or []) - len(accepted or []),
        })

    def record_scrape(self, urls_in: list[str], pages_out: list[dict]) -> None:
        """One scrape batch: which URLs were attempted, which came back."""
        got = [p.get("url") or p.get("source") or "" for p in pages_out]
        self.scrapes.append({
            "urls_in":   list(urls_in or []),
            "urls_out":  [u for u in got if u],
            "chars_out": sum(len(str(p.get("raw_content", "") or "")) for p in pages_out or []),
        })

    def record_compression(self, subquery: str, pages_in: list[dict],
                           chars_out: int, *, docs_after_filter: int | None = None,
                           top_n: int | None = None) -> None:
        """One compression call: the corpus in, the context out.

        `docs_after_filter` / `top_n` describe the second, less visible cut:
        the similarity filter decides which chunks qualify, then only the first
        `top_n` of them survive. When more chunks qualify than top_n admits, the
        count cap is what is actually binding, not the similarity threshold.
        """
        chars_in = sum(len(str(p.get("raw_content", "") or "")) for p in pages_in or [])
        threshold = int(os.environ.get("COMPRESSION_THRESHOLD", "8000"))
        self.compressions.append({
            "subquery":          subquery,
            "pages_in":          len(pages_in or []),
            "chars_in":          chars_in,
            "chars_out":         chars_out,
            "docs_after_filter": docs_after_filter,
            "top_n":             top_n,
            # Mirrors ContextCompressor.async_get_context's fast-path predicate.
            "fast_path":         chars_in < threshold and len(pages_in or []) <= 10,
        })

    # --- derived ---------------------------------------------------------

    @property
    def attempted_urls(self) -> list[str]:
        return [u for s in self.scrapes for u in s["urls_in"]]

    @property
    def scraped_urls(self) -> list[str]:
        """URLs that actually produced content.

        This is the honest denominator for source-quality metrics. `visited_urls`
        counts everything the retriever proposed, including pages that never
        loaded, so scoring it credits the pipeline for sources the writer never
        read — and since the strictest bot defences sit in front of the most
        authoritative publishers, that credit is not evenly distributed.
        """
        seen, out = set(), []
        for s in self.scrapes:
            for u in s["urls_out"]:
                if u not in seen:
                    seen.add(u)
                    out.append(u)
        return out

    @property
    def failed_urls(self) -> list[str]:
        got = set(self.scraped_urls)
        seen, out = set(), []
        for u in self.attempted_urls:
            if u not in got and u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def funnel(self) -> dict:
        """Stage-by-stage volumes and retention rates."""
        attempted = len(self.attempted_urls)
        scraped   = len(self.scraped_urls)
        proposed  = sum(s["proposed"] for s in self.searches)
        duplicate = sum(s["duplicate"] for s in self.searches)
        chars_in  = sum(c["chars_in"] for c in self.compressions)
        chars_out = sum(c["chars_out"] for c in self.compressions)
        capped    = [c for c in self.compressions
                     if c.get("docs_after_filter") is not None
                     and c.get("top_n") is not None
                     and c["docs_after_filter"] > c["top_n"]]
        return {
            "subqueries":        len(self.subqueries),
            "urls_proposed":     proposed,
            "urls_duplicate":    duplicate,
            # Share of search results already seen by an earlier query — how
            # much of the retrieval budget the planner spent on ground it had
            # already covered.
            "search_overlap":    round(duplicate / proposed, 3) if proposed else None,
            "urls_attempted":    attempted,
            "urls_scraped":      scraped,
            "scrape_rate":       round(scraped / attempted, 3) if attempted else None,
            "scraped_chars":     chars_in,
            "context_chars":     chars_out,
            "compression_rate":  round(chars_out / chars_in, 3) if chars_in else None,
            "compress_calls":    len(self.compressions),
            "fast_path_calls":   sum(c["fast_path"] for c in self.compressions),
            # How often the top-N cap, not the similarity threshold, did the cutting
            "top_n_capped_calls": len(capped),
        }


# ---------------------------------------------------------------------------
# Patching
# ---------------------------------------------------------------------------

class PipelineProbe:
    """Context manager that wires a PipelineTrace to the pipeline's seams.

    Patches are process-local and reverted in __exit__, including on error.
    Nesting two probes is not supported — the inner one would record into the
    outer one's patches.
    """

    def __init__(self) -> None:
        self.trace = PipelineTrace()
        self._restore: list = []

    def __enter__(self) -> "PipelineProbe":
        # Imported here so the module stays importable without the runtime
        # installed (unit tests exercise PipelineTrace alone).
        from gpt_researcher.skills.researcher import ResearchConductor
        from gpt_researcher.skills.browser import BrowserManager
        from gpt_researcher.skills.context_manager import ContextManager
        from gpt_researcher.prompts import PromptFamily

        trace = self.trace
        orig_plan     = ResearchConductor.plan_research
        orig_browse   = BrowserManager.browse_urls
        orig_dedupe   = ResearchConductor._get_new_urls
        orig_compress = ContextManager.get_similar_content_by_query
        orig_pretty   = PromptFamily.pretty_print_docs

        # pretty_print_docs runs inside compression; this box ferries the doc
        # count from there out to the enclosing compression record.
        last_cut: dict = {}

        async def plan(self, *a, **k):
            out = await orig_plan(self, *a, **k)
            trace.subqueries = list(out) if out else []
            return out

        async def browse(self, urls, *a, **k):
            pages = await orig_browse(self, urls, *a, **k)
            trace.record_scrape(urls, pages or [])
            return pages

        async def dedupe(self, url_set_input, *a, **k):
            proposed = list(url_set_input or [])
            accepted = await orig_dedupe(self, url_set_input, *a, **k)
            trace.record_search(proposed, accepted or [])
            return accepted

        def pretty(docs, top_n=None):
            last_cut["docs"] = len(docs or [])
            last_cut["top_n"] = top_n
            return orig_pretty(docs, top_n)

        async def compress(self, query, pages, *a, **k):
            last_cut.clear()
            ctx = await orig_compress(self, query, pages, *a, **k)
            trace.record_compression(
                query, pages or [], len(str(ctx or "")),
                docs_after_filter=last_cut.get("docs"), top_n=last_cut.get("top_n"))
            return ctx

        ResearchConductor.plan_research = plan
        ResearchConductor._get_new_urls = dedupe
        BrowserManager.browse_urls = browse
        ContextManager.get_similar_content_by_query = compress
        PromptFamily.pretty_print_docs = staticmethod(pretty)
        self._restore = [
            (ResearchConductor, "plan_research", orig_plan),
            (ResearchConductor, "_get_new_urls", orig_dedupe),
            (BrowserManager, "browse_urls", orig_browse),
            (ContextManager, "get_similar_content_by_query", orig_compress),
            (PromptFamily, "pretty_print_docs", staticmethod(orig_pretty)),
        ]
        return self

    def __exit__(self, *exc) -> None:
        for owner, name, original in self._restore:
            setattr(owner, name, original)
        self._restore = []
        return None
