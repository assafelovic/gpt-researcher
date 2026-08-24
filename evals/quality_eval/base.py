"""
Evaluation framework abstractions.
----------------------------------
A thin, dependency-free layer that follows DeepEval's Metric / test-case design,
adapted for AUTONOMOUS-RESEARCH evaluation.

Key adaptation: `EvalSample` carries `sources` — the URLs the agent found itself.
RAG-oriented frameworks (RAGAS/DeepEval) assume the context is *given*, so they
have no place for source-level metrics. Every metric also declares the standard
concept it aligns with, so the suite doubles as a concept-ontology map:

    aligned with RAGAS / ALCE  →  Faithfulness, Answer Relevancy, Citation
    autonomous-agent extension →  Source Quality

Score convention: `MetricResult.score` is always "higher = better" (0–1) so
results aggregate and compare uniformly, regardless of the raw metric direction.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class Group:
    """Metric families. Three align with standard frameworks; one is an extension.

    Roadmap: with a semantic citation-precision metric (does a citation actually
    support its claim, ALCE-style) + a true answer-relevancy metric, the CITATION
    group can be promoted to a `Precision` family. Tracked as next step.
    """
    FAITHFULNESS     = "Faithfulness"       # aligns with RAGAS Faithfulness
    ANSWER_RELEVANCY = "Answer Relevancy"   # aligns with RAGAS answer relevancy (impl: completeness)
    SOURCE_QUALITY   = "Source Quality"     # extension: source reliability / variety
    CITATION         = "Citation"           # aligns with ALCE citation precision (structural)


@dataclass
class EvalSample:
    """One report to evaluate.

    `sources` (raw URLs the agent retrieved) is the field RAG frameworks lack and
    the reason source-level metrics can exist here. `reference` is an optional
    ground-truth answer, unused by the ground-truth-free metrics.
    """
    query:     str = ""
    report:    str = ""
    sources:   list[str] = field(default_factory=list)
    context:   str = ""
    reference: str | None = None


@dataclass
class MetricResult:
    """Uniform output for every metric — enables aggregation / compare / logging."""
    name:         str
    group:        str
    aligned_with: str                                # standard concept, or "extension"
    score:        float | None = None                # primary scalar, higher = better
    reason:       str = ""
    breakdown:    dict = field(default_factory=dict)  # full metric-specific detail
    skipped:      bool = False

    @classmethod
    def skip(cls, metric: "BaseMetric", reason: str) -> "MetricResult":
        return cls(name=metric.name, group=metric.group,
                   aligned_with=metric.aligned_with, score=None,
                   reason=reason, skipped=True)


class BaseMetric:
    """Follows DeepEval's BaseMetric shape: declare metadata + implement measure().

    Subclasses set the four class attributes and implement `measure()`, which
    wraps the underlying metric function (in metrics.py) and returns a
    MetricResult. Keeping the raw functions separate means the existing 35 unit
    tests and perturbation checks stay valid — this layer only standardizes I/O.
    """
    name:         str = ""
    group:        str = ""
    aligned_with: str = ""
    needs_llm:    bool = False

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        raise NotImplementedError
