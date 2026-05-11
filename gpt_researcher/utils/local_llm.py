"""Helpers for local OpenAI-compatible endpoints.

This module centralizes local endpoint detection and provides a tiny
deterministic embedding fallback for local models that do not expose a
dedicated embeddings endpoint.
"""

from __future__ import annotations

import hashlib
import math
import os
import re

try:
    import requests
except ImportError:  # pragma: no cover - requests is a direct dependency.
    requests = None

from langchain_core.embeddings import Embeddings

LOCAL_OPENAI_BASE_URL_CANDIDATES = (
    "http://127.0.0.1:8081/v1",
    "http://localhost:8081/v1",
    "http://host.docker.internal:8081/v1",
    "http://127.0.0.1:8080/v1",
    "http://localhost:8080/v1",
    "http://host.docker.internal:8080/v1",
)

LOCAL_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if "://" not in normalized:
        normalized = f"http://{normalized}"
    return normalized


def is_local_openai_base_url(base_url: str | None) -> bool:
    """Return True when the base URL points at localhost."""
    normalized = _normalize_base_url(base_url)
    if not normalized:
        return False
    return normalized.startswith("http://127.0.0.1") or normalized.startswith("http://localhost")


def detect_local_openai_base_url(timeout: float = 0.25) -> str | None:
    """Probe common localhost OpenAI-compatible endpoints."""
    configured = _normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    if configured:
        return configured

    if requests is None:
        return None

    for candidate in LOCAL_OPENAI_BASE_URL_CANDIDATES:
        try:
            response = requests.get(f"{candidate}/models", timeout=timeout)
            if response.ok:
                return candidate
        except Exception:
            continue
    return None


def resolve_openai_base_url() -> str | None:
    """Resolve a local or configured OpenAI-compatible base URL."""
    configured = _normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    if configured:
        return configured
    return detect_local_openai_base_url()


def resolve_ollama_base_url() -> str:
    """Resolve a local or configured Ollama base URL."""
    configured = _normalize_base_url(
        os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST")
    )
    if configured:
        return configured
    return LOCAL_OLLAMA_BASE_URL


def should_use_local_embedding_fallback(base_url: str | None = None) -> bool:
    """Decide whether embeddings should use the local hash fallback."""
    if os.getenv("USE_REAL_OPENAI_EMBEDDINGS", "").strip().lower() in {"1", "true", "yes"}:
        return False
    resolved = _normalize_base_url(base_url) or resolve_openai_base_url()
    return bool(resolved and is_local_openai_base_url(resolved))


class LocalHashEmbeddings(Embeddings):
    """Deterministic, dependency-free embeddings for local-only setups."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions
        self.model = "local-hash-embeddings"

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _vectorize(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)
