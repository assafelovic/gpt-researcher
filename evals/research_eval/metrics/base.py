"""
Metric interface and the context metrics share.
-----------------------------------------------
A metric reads one RunArchive and returns one MetricResult. It never writes to
the archive and never aggregates with other metrics: results are listed per
metric, with no overall score.

Rule metrics only read the archive. LLM / embedding metrics go through
`ScoringContext.judge` / `.embedder`, which cache every call, and record which
prompts they used and how many calls hit the cache.
"""

from __future__ import annotations

import asyncio
import weakref
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Iterable, TypeVar

if TYPE_CHECKING:
    from ..archive import RunArchive
    from ..cache import EvalCache
    from ..judge import Embedder, Judge, JudgeResponse
    from ..prompts import Prompt

T = TypeVar("T")


@dataclass
class MetricResult:
    name: str
    category: str
    version: str
    value: float | None
    higher_is_better: bool = True
    details: dict[str, Any] = field(default_factory=dict)
    skipped: str | None = None           # reason, when the metric could not run
    llm: dict[str, Any] | None = None    # judge model, prompts, calls, cache hits

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScoringContext:
    cache: "EvalCache"
    judge: "Judge | None" = None          # None -> LLM metrics are skipped
    embedder: "Embedder | None" = None    # None -> embedding metrics are skipped
    key_points_dir: Path | None = None    # frozen, human-reviewed key points
    max_concurrency: int = 4
    options: dict[str, Any] = field(default_factory=dict)
    _memo: dict[Any, Any] = field(default_factory=dict)
    _per_archive: "weakref.WeakKeyDictionary" = field(default_factory=weakref.WeakKeyDictionary)

    def archive_memo(self, archive: "RunArchive") -> dict[Any, Any]:
        """Results several metrics share within one scoring of one archive
        (e.g. the citation audit). Scoring the archive again starts afresh, so
        each scoring reports its own API calls and cache hits."""
        return self._per_archive.setdefault(archive, {})

    def option(self, name: str, default: Any) -> Any:
        return self.options.get(name, default)

    async def gather(self, aws: Iterable[Awaitable[T]]) -> list[T]:
        sem = asyncio.Semaphore(self.max_concurrency)

        async def run(a: Awaitable[T]) -> T:
            async with sem:
                return await a

        return await asyncio.gather(*(run(a) for a in aws))


class Metric:
    name: str = ""
    category: str = ""
    version: str = "1"
    higher_is_better: bool = True
    uses_llm: bool = False
    uses_embeddings: bool = False
    prompts: tuple["Prompt", ...] = ()

    async def score(self, archive: "RunArchive", ctx: ScoringContext) -> MetricResult:
        raise NotImplementedError

    # --- helpers -------------------------------------------------------------

    def result(self, value: float | None, **details: Any) -> MetricResult:
        return MetricResult(self.name, self.category, self.version, value,
                            self.higher_is_better, details)

    def skip(self, reason: str, **details: Any) -> MetricResult:
        r = self.result(None, **details)
        r.skipped = reason
        return r

    def llm_record(self, ctx: ScoringContext, responses: list["JudgeResponse"]) -> dict:
        errors = [r.error for r in responses if r.error is not None]
        record = {
            "judge_model": ctx.judge.model if ctx.judge else None,
            "prompts": {p.id: {"version": p.version, "hash": p.hash} for p in self.prompts},
            # requests = judge requests made by the metric; api_calls = the
            # ones that reached the model (the rest were replayed from cache).
            "requests": len(responses),
            "cache_hits": sum(r.cache_hit for r in responses),
            "api_calls": sum(not r.cache_hit for r in responses),
            "errors": len(errors),
        }
        if errors:
            # What went wrong (429, timeout, unparseable reply), not just how often.
            record["error_messages"] = sorted({e[:300] for e in errors})
        return record


def rounded(x: float | None, nd: int = 3) -> float | None:
    return None if x is None else round(x, nd)
