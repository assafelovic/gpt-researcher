"""Metric registry. Retrieval metrics live in `retrieval/`, generation metrics
(plus toxicity / bias) in `generation/`."""

from .base import Metric, MetricResult, ScoringContext  # noqa: F401


def all_metrics() -> list[Metric]:
    from .generation import GENERATION_METRICS
    from .retrieval import RETRIEVAL_METRICS
    return [m() for m in RETRIEVAL_METRICS + GENERATION_METRICS]
