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


async def select_context(
    query: str,
    pages: list[dict],
    cfg,
    *,
    max_results: int = 10,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    cost_callback: Callable[[float], None] | None = None,
    embeddings: Callable[[], object] | None = None,
) -> str:
    """Context for ``query`` from ``pages`` (dicts with ``raw_content``, ``url``, ``title``).

    ``embeddings`` is a zero-argument factory, called only in embeddings mode,
    so nothing builds an embedding model unless that mode is chosen.
    """
    mode = resolve_context_filter(getattr(cfg, "context_filter", None))
    prompt_family = prompt_family or PromptFamily

    if mode == "none":
        return prompt_family.pretty_print_docs(_as_documents(pages))

    # Little content needs no filtering, whatever the mode.
    total_chars = sum(len(str(p.get("raw_content") or "")) for p in pages)
    if total_chars < int(os.environ.get("COMPRESSION_THRESHOLD", "8000")) and len(pages) <= max_results:
        return prompt_family.pretty_print_docs(_as_documents(pages)[:max_results], max_results)

    if mode == "jev":
        try:
            return await JevContextCompressor(documents=pages, prompt_family=prompt_family).async_get_context(
                query=query, max_results=max_results, cost_callback=cost_callback)
        except JevError as e:
            logger.warning(f"Jev context filter unavailable ({e}); using keyword ranking")

    if mode == "embeddings":
        try:
            from .compression import ContextCompressor

            return await ContextCompressor(
                documents=pages,
                embeddings=embeddings() if embeddings else None,
                similarity_threshold=getattr(cfg, "similarity_threshold", None),
                prompt_family=prompt_family,
            ).async_get_context(query=query, max_results=max_results, cost_callback=cost_callback)
        except Exception as e:
            logger.warning(f"Embedding context filter unavailable ({e}); using keyword ranking")

    return await LexicalContextCompressor(
        documents=pages, relative_threshold=KEYWORD_RELATIVE_THRESHOLD, prompt_family=prompt_family,
    ).async_get_context(query, KEYWORD_MAX_RESULTS)
