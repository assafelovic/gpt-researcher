"""
Per-question key points: the K aspects a good answer must cover.
-----------------------------------------------------------------
Generated once per question and shared by every run of it (decomposition
coverage, query relevance, and later the generation metrics). Lookup order:

  1. a frozen file `<key_points_dir>/<question_id>.json` ({"key_points": [...]}),
     reviewed by a person and versioned with the dataset;
  2. the SQLite cache, keyed by question_id + prompt version + judge model;
  3. one judge call, whose result is cached.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .cache import stable_hash
from .prompts import KEY_POINTS

if TYPE_CHECKING:
    from .archive import RunArchive
    from .metrics.base import ScoringContext


async def get_key_points(archive: "RunArchive", ctx: "ScoringContext") -> tuple[list[str] | None, dict]:
    """Returns (key_points or None, provenance)."""
    qid = archive.question_id or "q-" + stable_hash(archive.query)[:12]
    memo_key = ("key_points", qid)
    if memo_key in ctx._memo:
        return ctx._memo[memo_key]

    out: tuple[list[str] | None, dict]
    frozen = ctx.key_points_dir / f"{qid}.json" if ctx.key_points_dir else None
    if frozen is not None and frozen.exists():
        points = json.loads(frozen.read_text(encoding="utf-8"))["key_points"]
        out = (points, {"source": "frozen", "path": str(frozen)})
    elif ctx.judge is None:
        out = (None, {"source": "unavailable", "reason": "no frozen key points and no judge"})
    else:
        key = stable_hash(qid, KEY_POINTS.version, ctx.judge.model)
        cached = ctx.cache.get("question", key)
        if cached is not None:
            out = (cached, {"source": "cache", "prompt_version": KEY_POINTS.version,
                            "judge_model": ctx.judge.model})
        else:
            resp = await ctx.judge.ask(KEY_POINTS.id, KEY_POINTS.version,
                                       KEY_POINTS.render(question=archive.query))
            points = (resp.parsed or {}).get("key_points") if isinstance(resp.parsed, dict) else None
            points = [str(p).strip() for p in points or [] if str(p).strip()]
            if points:
                ctx.cache.put("question", key, points)
                out = (points, {"source": "judge", "prompt_version": KEY_POINTS.version,
                                "judge_model": ctx.judge.model, "cache_hit": resp.cache_hit})
            else:
                out = (None, {"source": "failed", "error": resp.error or "empty key point list"})
    ctx._memo[memo_key] = out
    return out
