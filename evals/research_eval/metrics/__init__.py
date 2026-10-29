"""Metric registry. Retrieval metrics live in `retrieval/`; generation metrics
will live in `generation/` and register the same way."""

from .base import Metric, MetricResult, ScoringContext  # noqa: F401


def all_metrics() -> list[Metric]:
    from .retrieval import RETRIEVAL_METRICS
    return [m() for m in RETRIEVAL_METRICS]
