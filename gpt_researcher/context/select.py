"""Turns pages of text into LLM context, the same way everywhere.

Research sub-queries (scraped pages) and report chat (the finished report)
both call ``select_context``. ``CONTEXT_FILTER`` picks how chunks are chosen:

  auto        jev when TYPESAFE_API_KEY is set, otherwise keyword
  jev         TypeSafe's Jev scores each chunk's usefulness (needs a key)
  keyword     BM25 keyword ranking: local, no API, no model, no embeddings
  embeddings  embedding similarity (needs an embedding provider)
  none        no filtering: every page, in full

Anything that fails degrades to ``keyword``, so no mode can leave a run
without context. Benchmarks: ``evals/context_filter``.
"""

import logging
import os
from typing import Callable

from langchain_core.documents import Document

from ..prompts import PromptFamily
from .jev_filter import JevContextCompressor, JevError
from .lexical import LexicalContextCompressor
from .retriever import SearchAPIRetriever

logger = logging.getLogger(__name__)

CONTEXT_FILTERS = ("auto", "jev", "keyword", "embeddings", "none")

#: Keyword chunks must score at least this fraction of the best chunk, and
#: up to this many are kept. Chosen by evals/context_filter: the threshold
#: is what beats embeddings; plain top-10 BM25 loses to them.
KEYWORD_RELATIVE_THRESHOLD = float(os.environ.get("KEYWORD_RELATIVE_THRESHOLD", "0.5"))
KEYWORD_MAX_RESULTS = int(os.environ.get("KEYWORD_MAX_RESULTS", "25"))


def resolve_context_filter(setting: str | None) -> str:
    """The filter to use; ``auto`` means Jev when a TypeSafe key is set, else keyword."""
    mode = (setting or "auto").strip().lower()
    if mode not in CONTEXT_FILTERS:
        logger.warning(f"Unknown CONTEXT_FILTER {setting!r}; expected one of {CONTEXT_FILTERS}. Using 'auto'.")
        mode = "auto"
    if mode == "auto":
        return "jev" if os.environ.get("TYPESAFE_API_KEY") else "keyword"
    return mode


def _as_documents(pages: list[dict]) -> list[Document]:
    return SearchAPIRetriever(pages=pages).invoke("")


def _describe(chosen: list[tuple[Document, float | None]], whole_pages: bool = False) -> list[dict]:
    """Where each chosen chunk sits in its (capped) page; never the text itself."""
    selected = []
    for rank, (doc, score) in enumerate(chosen, 1):
        start = 0 if whole_pages else doc.metadata.get("start_index")
        selected.append({
            "url": doc.metadata.get("source"),
            "rank": rank,
            "start": start if isinstance(start, int) and start >= 0 else None,
            "length": len(doc.page_content),
            "score": None if score is None else float(score),
        })
    return selected


async def select_context(
    query: str,
    pages: list[dict],
    cfg,
    *,
    max_results: int = 10,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    cost_callback: Callable[[float], None] | None = None,
    embeddings: Callable[[], object] | None = None,
    on_selected: Callable[[dict], None] | None = None,
) -> str:
    """Context for ``query`` from ``pages`` (dicts with ``raw_content``, ``url``, ``title``).

    ``embeddings`` is a zero-argument factory, called only in embeddings mode,
    so nothing builds an embedding model unless that mode is chosen.

    ``on_selected``, if given, is called once with a description of the choice:
    the filter requested and the one that ran, why it fell back, and the URL,
    rank, offsets and score of each chunk in the context (no page text). It
    never changes the context, and its failures are logged, not raised.
    """
    requested = getattr(cfg, "context_filter", None) or "auto"
    mode = resolve_context_filter(requested)
    prompt_family = prompt_family or PromptFamily
    fallback_reason = None
    docs: list[Document] = []

    def done(context: str, used: str, source=None) -> str:
        """Report what ``source`` (a compressor, or None for whole pages) chose."""
        if on_selected:
            try:
                whole_pages = source is None
                chosen = [(d, None) for d in docs] if whole_pages else source.selected
                on_selected({
                    "filter": requested, "filter_used": used, "fallback_reason": fallback_reason,
                    "candidate_pages": len(pages), "candidate_chunks": getattr(source, "candidate_chunks", None),
                    "context_chars": len(context), "selected": _describe(chosen, whole_pages),
                })
            except Exception as e:  # noqa: BLE001 - reporting must never affect the context
                logger.debug(f"Context selection callback failed: {type(e).__name__}")
        return context

    if mode == "none":
        docs = _as_documents(pages)
        return done(prompt_family.pretty_print_docs(docs), "none")

    # Little content needs no filtering, whatever the mode.
    total_chars = sum(len(str(p.get("raw_content") or "")) for p in pages)
    if total_chars < int(os.environ.get("COMPRESSION_THRESHOLD", "8000")) and len(pages) <= max_results:
        docs = _as_documents(pages)[:max_results]
        return done(prompt_family.pretty_print_docs(docs, max_results), "shortcut")

    if mode == "jev":
        try:
            jev = JevContextCompressor(documents=pages, prompt_family=prompt_family)
            context = await jev.async_get_context(query=query, max_results=max_results, cost_callback=cost_callback)
            return done(context, "jev", jev)
        except JevError as e:
            logger.warning(f"Jev context filter unavailable ({e}); using keyword ranking")
            fallback_reason = type(e).__name__

    if mode == "embeddings":
        try:
            from .compression import ContextCompressor

            compressor = ContextCompressor(
                documents=pages,
                embeddings=embeddings() if embeddings else None,
                similarity_threshold=getattr(cfg, "similarity_threshold", None),
                prompt_family=prompt_family,
            )
            context = await compressor.async_get_context(query=query, max_results=max_results, cost_callback=cost_callback)
            return done(context, "embeddings", compressor)
        except Exception as e:
            logger.warning(f"Embedding context filter unavailable ({e}); using keyword ranking")
            fallback_reason = type(e).__name__

    keyword = LexicalContextCompressor(
        documents=pages, relative_threshold=KEYWORD_RELATIVE_THRESHOLD, prompt_family=prompt_family,
    )
    context = await keyword.async_get_context(query, KEYWORD_MAX_RESULTS)
    return done(context, "keyword", keyword)
