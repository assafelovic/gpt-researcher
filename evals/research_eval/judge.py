"""
Judge and embedding clients for the scoring layer, both cached.
--------------------------------------------------------------
`Judge` sends a versioned rubric prompt to the judge model (evals/judge.py
picks and builds it) and returns the parsed JSON. Responses are cached by
hash(model + prompt id/version + full prompt + parameters), so rescoring an
archive replays the same verdicts. Each call reports whether it hit the cache
so results can record it.

`Embedder` embeds texts through gpt-researcher's own provider layer
(`EMBEDDING`, default openai:text-embedding-3-small), one vector per text,
cached by model + text.

Both accept injected backends so tests run offline.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .cache import EvalCache, stable_hash


@dataclass
class JudgeResponse:
    parsed: Any               # parsed JSON, or None when parsing failed
    raw: str
    cache_hit: bool
    prompt_id: str
    prompt_version: str
    error: str | None = None


def parse_json_response(text: str) -> Any:
    """Parse JSON from an LLM reply, tolerating code fences and surrounding prose."""
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_, close in (("{", "}"), ("[", "]")):
        i, j = text.find(open_), text.rfind(close)
        if i != -1 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON object in judge response")


PARSE_RETRIES = 1       # extra calls when a reply holds no usable JSON


class Judge:
    """Cached rubric judge. `complete` is an async str -> str backend."""

    def __init__(self, cache: EvalCache, *, model: str | None = None,
                 complete: Callable[[str], Awaitable[str]] | None = None,
                 salt: str = "", max_calls: int | None = None) -> None:
        """`salt` keys the cache apart (asks again what the plain cache already
        holds, e.g. to measure the judge's own spread); `max_calls` caps
        uncached calls: past it, ask() returns an error instead of calling."""
        from evals.judge import judge_model_name
        self.cache = cache
        self.model = model or judge_model_name()
        self._complete = complete
        self.salt = salt
        self.max_calls = max_calls
        self.refused = 0            # calls not made because max_calls was reached
        self.prompt_chars = 0       # characters sent in uncached calls
        self.calls = 0
        self.cache_hits = 0
        self.input_tokens = 0       # summed from the provider's usage metadata,
        self.output_tokens = 0      # uncached calls only (reasoning tokens included)

    async def _call(self, prompt: str) -> str:
        if self._complete is None:
            from evals.judge import make_judge
            llm = make_judge(self.model)

            async def complete(p: str) -> str:
                resp = await llm.ainvoke(p)
                self._add_usage(getattr(resp, "usage_metadata", None))
                return resp.content if isinstance(resp.content, str) else str(resp.content)

            self._complete = complete
        return await self._complete(prompt)

    def _add_usage(self, usage: dict | None) -> None:
        if usage:
            self.input_tokens += int(usage.get("input_tokens") or 0)
            self.output_tokens += int(usage.get("output_tokens") or 0)

    def usage(self) -> dict:
        return {"model": self.model, "calls": self.calls, "cache_hits": self.cache_hits,
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "prompt_chars": self.prompt_chars, "refused": self.refused}

    async def ask(self, prompt_id: str, prompt_version: str, prompt: str,
                  **params: Any) -> JudgeResponse:
        key = stable_hash(self.model, prompt_id, prompt_version, prompt, params)
        if self.salt:
            key = stable_hash(key, self.salt)
        cached = self.cache.get("llm", key)
        if cached is not None:
            self.cache_hits += 1
            return JudgeResponse(cached["parsed"], cached["raw"], True, prompt_id, prompt_version)
        for attempt in range(1 + PARSE_RETRIES):
            if self.max_calls is not None and self.calls >= self.max_calls:
                self.refused += 1
                return JudgeResponse(None, "", False, prompt_id, prompt_version,
                                     error=f"call budget reached ({self.max_calls} calls)")
            self.calls += 1
            self.prompt_chars += len(prompt)
            try:
                raw = await self._call(prompt)
            except Exception as e:
                return JudgeResponse(None, "", False, prompt_id, prompt_version,
                                     error=f"{type(e).__name__}: {e}")
            try:
                parsed = parse_json_response(raw)
            except ValueError as e:
                # Unparseable replies (empty, cut off) are not cached; ask again.
                error = str(e) + (f" (after {attempt + 1} attempts)" if attempt else "")
                continue
            self.cache.put("llm", key, {"parsed": parsed, "raw": raw})
            return JudgeResponse(parsed, raw, False, prompt_id, prompt_version)
        return JudgeResponse(None, raw, False, prompt_id, prompt_version, error=error)


class Embedder:
    """Cached embeddings. `embed` is an async list[str] -> list[list[float]] backend."""

    def __init__(self, cache: EvalCache, *, model: str | None = None,
                 embed: Callable[[list[str]], Awaitable[list[list[float]]]] | None = None) -> None:
        self.cache = cache
        self._embed = embed
        self.model = model or self._default_model()
        self.calls = 0

    @staticmethod
    def _default_model() -> str:
        from gpt_researcher.config import Config
        cfg = Config()
        return f"{cfg.embedding_provider}:{cfg.embedding_model}"

    async def _backend(self, texts: list[str]) -> list[list[float]]:
        if self._embed is None:
            from gpt_researcher.config import Config
            from gpt_researcher.memory import Memory
            cfg = Config()
            provider, model = self.model.split(":", 1)
            emb = Memory(provider, model, **cfg.embedding_kwargs).get_embeddings()

            async def embed(ts: list[str]) -> list[list[float]]:
                return await emb.aembed_documents(ts)

            self._embed = embed
        return await self._embed(texts)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        keys = [stable_hash(self.model, t) for t in texts]
        out: list[list[float] | None] = [self.cache.get("embedding", k) for k in keys]
        missing = [i for i, v in enumerate(out) if v is None]
        if missing:
            self.calls += 1
            vecs = await self._backend([texts[i] for i in missing])
            for i, v in zip(missing, vecs):
                out[i] = list(v)
                self.cache.put("embedding", keys[i], out[i])
        return out  # type: ignore[return-value]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
