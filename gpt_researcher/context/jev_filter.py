"""Relevance filtering of scraped content with TypeSafe's Jev model.

The embeddings pipeline in ``compression.py`` keeps the chunks whose vectors
are closest to the query. Cosine similarity measures topical closeness, not
whether a passage helps answer the question, so on-topic filler ranks as
high as the passage with the answer.

``JevContextCompressor`` asks the question directly instead: every chunk is
scored by Jev on a four-level usefulness rubric, and the best-scoring chunks
become the context. It keeps the embeddings pipeline's candidates (same
splitter, same per-page cap) and output budget, so the two differ only in
how chunks are chosen. No embedding model or vector math is involved.

API: https://docs.typesafe.ai/api
"""

import asyncio
import logging
import os
import weakref
from dataclasses import dataclass

import httpx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..prompts import PromptFamily
from .retriever import SearchAPIRetriever

logger = logging.getLogger(__name__)

JEV_API_URL = "https://api.typesafe.ai/v1/systemone"
#: USD per million input tokens; output tokens are free.
JEV_INPUT_PRICE_PER_MTOK = 0.042

RELEVANCE_LEVELS = [
    "Unrelated to the question",
    "Same topic, but does not help answer the question",
    "Partially answers the question or gives useful supporting facts",
    "Directly answers the question with specific facts",
]

# One shared limit per event loop: sub-queries run concurrently, and each
# compressor would otherwise open its own full-width pool. Keyed by loop
# because an asyncio.Semaphore is bound to the first loop that waits on it.
_SEMAPHORES: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = weakref.WeakKeyDictionary()


def _concurrency() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    if loop not in _SEMAPHORES:
        _SEMAPHORES[loop] = asyncio.Semaphore(int(os.environ.get("JEV_CONCURRENCY", "64")))
    return _SEMAPHORES[loop]


class JevError(RuntimeError):
    """Jev could not score the chunks (missing key, API or network failure)."""


@dataclass
class ScoredChunk:
    document: Document
    score: float
    position: int


class JevClient:
    """Minimal async client for the System One endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout: float = 30.0, max_retries: int = 3):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not self.api_key:
            raise JevError("TYPESAFE_API_KEY is not set")
        self.model = model or os.environ.get("JEV_MODEL", "jev-latest")
        self.timeout = timeout
        self.max_retries = max_retries
        self.input_tokens = 0

    def session(self) -> httpx.AsyncClient:
        """HTTP session shared by one batch of scoring calls."""
        return httpx.AsyncClient()

    async def score_relevance(self, client: httpx.AsyncClient, query: str, passage: str) -> float:
        """Probability-weighted usefulness of ``passage`` for ``query``, in [0, 3]."""
        payload = {
            "state": passage,
            "model": self.model,
            "questions": {
                "usefulness": {
                    "type": "score",
                    "instructions": f"How useful is this passage for answering the question: {query}",
                    "criteria": RELEVANCE_LEVELS,
                }
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(self.max_retries + 1):
            async with _concurrency():
                try:
                    response = await client.post(JEV_API_URL, json=payload, headers=headers, timeout=self.timeout)
                except httpx.HTTPError as exc:
                    error = exc
                else:
                    if response.status_code == 200:
                        try:
                            body = response.json()
                            score = float(body["answers"]["usefulness"]["score"])
                        except (ValueError, KeyError, TypeError) as exc:
                            raise JevError(f"Unexpected Jev response: {response.text[:200]}") from exc
                        self.input_tokens += body.get("usage", {}).get("input_tokens", 0)
                        return score
                    error = JevError(f"HTTP {response.status_code}: {response.text[:200]}")
                    # Only overload and rate limiting are worth retrying.
                    if response.status_code not in (429, 529):
                        raise error
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * 2 ** attempt)
        raise JevError(f"Jev request failed after {self.max_retries + 1} attempts: {error}")

    @property
    def cost(self) -> float:
        return self.input_tokens / 1_000_000 * JEV_INPUT_PRICE_PER_MTOK


class JevContextCompressor:
    """Selects the most useful chunks of scraped pages by asking Jev.

    Same interface as ``ContextCompressor``: ``documents`` are scraper dicts
    with ``raw_content``, ``url`` and ``title``.
    """

    def __init__(
        self,
        documents,
        max_results: int = 5,
        min_score: float | None = None,
        prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
        client: JevClient | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ):
        self.documents = documents
        self.chunk_size = chunk_size or int(os.environ.get("JEV_CHUNK_SIZE", "1000"))
        self.max_results = max_results
        if min_score is None:
            min_score = float(os.environ.get("JEV_MIN_SCORE", "1.5"))
        self.min_score = min_score
        self.prompt_family = prompt_family
        self.client = client or JevClient()

    def _chunks(self) -> list[Document]:
        pages = SearchAPIRetriever(pages=self.documents).invoke("")
        splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_size // 10)
        return [chunk for chunk in splitter.split_documents(pages) if chunk.page_content.strip()]

    async def rank(self, query: str) -> list[ScoredChunk]:
        """Every chunk with its Jev score, best first (ties keep page order)."""
        chunks = self._chunks()
        async with self.client.session() as http:
            scores = await asyncio.gather(
                *[self.client.score_relevance(http, query, chunk.page_content) for chunk in chunks]
            )
        ranked = [ScoredChunk(chunk, score, i) for i, (chunk, score) in enumerate(zip(chunks, scores))]
        return sorted(ranked, key=lambda c: (-c.score, c.position))

    async def async_get_context(self, query: str, max_results: int = 5, cost_callback=None) -> str:
        # Same shortcut as ContextCompressor: little content needs no filtering.
        total_chars = sum(len(str(doc.get("raw_content") or "")) for doc in self.documents)
        if total_chars < int(os.environ.get("COMPRESSION_THRESHOLD", "8000")) and len(self.documents) <= max_results:
            docs = [
                Document(
                    page_content=doc.get("raw_content") or "",
                    metadata={"title": doc.get("title") or "", "source": doc.get("source") or doc.get("url") or ""},
                )
                for doc in self.documents[:max_results]
            ]
            return self.prompt_family.pretty_print_docs(docs, max_results)

        ranked = await self.rank(query)
        if cost_callback:
            cost_callback(self.client.cost)
        selected = [c.document for c in ranked if c.score >= self.min_score][:max_results]
        return self.prompt_family.pretty_print_docs(selected, max_results)
