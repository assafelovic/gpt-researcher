"""
Lexical similarity built on gpt-researcher's BM25 tokenizer.
-----------------------------------------------------------
`weighted_overlap(a, b)` is the share of a's BM25 term weight (IDF, computed
over the given corpus) that also appears in b. It is BM25 with saturated term
frequency and no length normalisation, which makes it bounded in [0, 1] and
comparable across texts of very different length (a one-line query, a page
chunk). Terms common to the whole corpus get little weight, so siblings that
share only the core topic words do not look alike.
"""

from __future__ import annotations

import math

from gpt_researcher.context.lexical import tokenize


def idf_table(corpus: list[str]) -> dict[str, float]:
    docs = [set(tokenize(t)) for t in corpus]
    n = len(docs)
    df: dict[str, int] = {}
    for d in docs:
        for t in d:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((n - k + 0.5) / (k + 0.5) + 1) for t, k in df.items()}


def weighted_overlap(a: str, b: str | set[str], idf: dict[str, float]) -> float:
    ta = set(tokenize(a))
    tb = b if isinstance(b, set) else set(tokenize(b))
    default = max(idf.values(), default=1.0)
    total = sum(idf.get(t, default) for t in ta)
    if not total:
        return 0.0
    return sum(idf.get(t, default) for t in ta & tb) / total


def symmetric_overlap(a: str, b: str, idf: dict[str, float]) -> float:
    return (weighted_overlap(a, b, idf) + weighted_overlap(b, a, idf)) / 2
