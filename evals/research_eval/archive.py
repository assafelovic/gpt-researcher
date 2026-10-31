"""
Run archive: the frozen record of one research run.
---------------------------------------------------
One JSON file per run, written once by the runner and only read afterwards.
It holds raw facts (spans, chunks, report text, config, cost) and never scores;
scoring reads an archive and writes results elsewhere, so metrics, prompts and
judges can change without re-running the agent.

`RunArchive` wraps the loaded JSON and builds the derived views metrics use:
the span tree, the query tree's decompositions and retrieval units, the URL ->
chunk index, and the parsed report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"

# Spans that issue a search and receive material.
RETRIEVAL_SPANS = ("sub_query", "initial_results")


def build_archive(*, meta: dict, spans: list[dict], chunks: dict[str, dict],
                  report_markdown: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": meta,
        "spans": spans,
        "chunks": chunks,
        "report": {"markdown": report_markdown or ""},
    }


def save_archive(archive: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"run archives are immutable; {path} already exists")
    path.write_text(json.dumps(archive, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


@dataclass(frozen=True)
class Decomposition:
    """One parent query and the child queries it was split into."""
    span_id: str
    kind: str                 # plan | deep_plan | deep_level | subtopics
    parent_query: str
    child_queries: list[str]


@dataclass(frozen=True)
class RetrievalUnit:
    """One search step and the chunks that reached the context from it."""
    span_id: str
    kind: str                 # sub_query | initial_results
    query: str
    chunk_ids: list[str]
    proposed_urls: list[str]
    new_urls: list[str]
    is_core_query: bool


class RunArchive:
    def __init__(self, data: dict) -> None:
        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ValueError(f"unsupported archive schema_version {version!r}")
        self.data = data

    @classmethod
    def load(cls, path: str | Path) -> "RunArchive":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    # --- raw ---------------------------------------------------------------

    @property
    def meta(self) -> dict:
        return self.data["meta"]

    @property
    def run_id(self) -> str:
        return self.meta["run_id"]

    @property
    def question_id(self) -> str | None:
        return self.meta.get("question_id")

    @property
    def query(self) -> str:
        return self.meta.get("query") or ""

    @property
    def spans(self) -> list[dict]:
        return self.data["spans"]

    @property
    def chunks(self) -> dict[str, dict]:
        return self.data["chunks"]

    @property
    def report_markdown(self) -> str:
        return self.data["report"]["markdown"]

    # --- tree ----------------------------------------------------------------

    @cached_property
    def span_by_id(self) -> dict[str, dict]:
        return {s["span_id"]: s for s in self.spans}

    @cached_property
    def children(self) -> dict[str | None, list[dict]]:
        out: dict[str | None, list[dict]] = {}
        for s in self.spans:
            out.setdefault(s["parent_id"], []).append(s)
        return out

    def descendants(self, span_id: str) -> list[dict]:
        out, stack = [], list(self.children.get(span_id, []))
        while stack:
            s = stack.pop()
            out.append(s)
            stack.extend(self.children.get(s["span_id"], []))
        return out

    def subtree_chunk_ids(self, span_id: str) -> list[str]:
        own = self.span_by_id[span_id]["attributes"].get("chunk_ids", [])
        ids = list(own)
        for s in self.descendants(span_id):
            ids.extend(s["attributes"].get("chunk_ids", []))
        return ids

    # --- query tree views --------------------------------------------------

    @cached_property
    def decompositions(self) -> list[Decomposition]:
        out = []
        for s in self.spans:
            a = s["attributes"]
            kids = {
                "plan": a.get("sub_queries"),
                "deep_plan": a.get("questions"),
                "deep_level": [q.get("query") for q in a.get("serp_queries") or []],
                "subtopics": a.get("subtopics"),
            }.get(s["name"])
            if kids:
                out.append(Decomposition(s["span_id"], s["name"], a.get("query") or "",
                                         [k for k in kids if k]))
        return out

    @cached_property
    def retrieval_units(self) -> list[RetrievalUnit]:
        out = []
        for s in self.spans:
            if s["name"] not in RETRIEVAL_SPANS:
                continue
            a = s["attributes"]
            out.append(RetrievalUnit(
                span_id=s["span_id"], kind=s["name"], query=a.get("query") or "",
                chunk_ids=list(a.get("chunk_ids") or []),
                proposed_urls=list(a.get("proposed_urls") or []),
                new_urls=list(a.get("new_urls") or []),
                is_core_query=bool(a.get("is_core_query")) or s["name"] == "initial_results",
            ))
        return out

    def query_layer(self, span_id: str) -> int:
        """Depth of a search step in the query tree (0 = the run's question).

        Each researcher adds a layer: its own query and initial search sit at
        the researcher's depth, its planned sub-queries one deeper. A detailed
        report's subtopic researchers (`parent_query` set) run beside the main
        one in the trace but are its children, so they start at layer 1.
        """
        span = self.span_by_id[span_id]
        researchers, cur = [], span
        while cur is not None:
            if cur["name"] == "research":
                researchers.append(cur)
            cur = self.span_by_id.get(cur["parent_id"])
        layer = max(len(researchers) - 1, 0)
        if researchers and researchers[-1]["attributes"].get("parent_query"):
            layer += 1
        own = span["attributes"].get("query", "").strip()
        is_root = bool(researchers) and own == researchers[0]["attributes"].get("query", "").strip()
        if span["name"] == "sub_query" and not is_root:
            layer += 1
        return layer

    def query_path(self, span_id: str) -> list[str]:
        """Queries from the run's question down to this span's own query.

        One entry per distinct query on the span's ancestor chain (researcher,
        deep-research level, plan, ...), consecutive repeats folded; starts
        with the run's question even where the trace starts a new root (a
        detailed report's subtopic researchers).
        """
        chain, cur = [], self.span_by_id.get(span_id)
        while cur is not None:
            q = (cur["attributes"].get("query") or "").strip()
            if q:
                chain.append(q)
            cur = self.span_by_id.get(cur["parent_id"])
        path = [self.query.strip()]
        for q in reversed(chain):
            if q != path[-1]:
                path.append(q)
        return path

    @cached_property
    def issued_subqueries(self) -> list[str]:
        """Distinct queries actually searched, excluding the run's core query.

        A nested researcher's own root query (a deep-research SERP query, a
        detailed-report subtopic) is a sub-query of the run and is kept.
        """
        seen, out = {self.query.strip()}, []
        for u in self.retrieval_units:
            if u.kind == "sub_query" and u.query.strip() not in seen:
                seen.add(u.query.strip())
                out.append(u.query)
        return out

    # --- material views ----------------------------------------------------

    @cached_property
    def retrieved_chunk_ids(self) -> list[str]:
        """Every chunk that reached the context, once, in first-seen order."""
        seen, out = set(), []
        for u in self.retrieval_units:
            for cid in u.chunk_ids:
                if cid not in seen and cid in self.chunks:
                    seen.add(cid)
                    out.append(cid)
        return out

    @cached_property
    def chunks_by_url(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for cid in self.retrieved_chunk_ids:
            url = self.chunks[cid].get("url")
            if url:
                out.setdefault(normalize_url(url), []).append(cid)
        return out

    @cached_property
    def retrieved_urls(self) -> list[str]:
        """Distinct source URLs of the retrieved chunks."""
        seen, out = set(), []
        for cid in self.retrieved_chunk_ids:
            url = self.chunks[cid].get("url")
            if url and normalize_url(url) not in seen:
                seen.add(normalize_url(url))
                out.append(url)
        return out

    @cached_property
    def report(self) -> dict[str, Any]:
        from .report_parser import parse_report
        return parse_report(self.report_markdown, self.chunks_by_url)


def normalize_url(url: str) -> str:
    """Comparison key for URLs.

    Ignores what a writer commonly changes when citing a page it read: the
    scheme (http/https), a leading "www.", a trailing slash and the fragment.
    """
    from urllib.parse import urlsplit
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return url.strip()
    host = p.netloc.lower().removeprefix("www.")
    key = host + p.path.rstrip("/")
    return f"{key}?{p.query}" if p.query else key
