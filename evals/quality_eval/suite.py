"""
Metric suite — concrete BaseMetric implementations + the evaluate() entry point.
--------------------------------------------------------------------------------
Each class is a thin wrapper over a function in metrics.py, standardizing I/O
into a MetricResult (score is always higher = better; raw detail kept in
`breakdown`). Keeping the raw functions separate means the existing unit tests
and perturbation checks remain valid — this layer only standardizes structure
and attaches the concept-alignment metadata (group / aligned_with).

Concept ontology (see quality_eval/README.md):
    Faithfulness      → unsupported_claim            (aligns RAGAS Faithfulness)
    Answer Relevancy  → subtopic_coverage            (aligns RAGAS answer relevancy)
    Source Quality    → source_authority, diversity  (autonomous-agent extension)
    Citation          → citation_faithfulness        (aligns ALCE citation precision)
"""

from __future__ import annotations

from evals.quality_eval import metrics as m
from evals.quality_eval.base import BaseMetric, EvalSample, MetricResult, Group


# ---------------------------------------------------------------------------
# Citation  (aligns ALCE citation precision — structural)
# ---------------------------------------------------------------------------

class CitationFaithfulnessMetric(BaseMetric):
    name         = "citation_faithfulness"
    group        = Group.CITATION
    aligned_with = "ALCE citation precision (structural)"
    needs_llm    = False

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        raw   = m.citation_faithfulness(sample.report, sample.sources, context=sample.context)
        score = raw.get("citation_faithfulness")
        return MetricResult(
            name=self.name, group=self.group, aligned_with=self.aligned_with,
            score=score,
            reason=("no References section to compare against" if score is None
                    else f"{len(raw['listed_only_domains'])} listed-only (decorative) refs"),
            breakdown=raw,
        )


# ---------------------------------------------------------------------------
# Source Quality  (autonomous-agent extension)
# ---------------------------------------------------------------------------

class SourceDiversityMetric(BaseMetric):
    name         = "source_diversity"
    group        = Group.SOURCE_QUALITY
    aligned_with = "extension (autonomous agent)"
    needs_llm    = False

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        raw = m.source_diversity(sample.sources)
        return MetricResult(
            name=self.name, group=self.group, aligned_with=self.aligned_with,
            score=raw["diversity_ratio"],
            reason=f"{raw['unique_domains']}/{raw['total_sources']} unique domains, entropy={raw['domain_entropy']}",
            breakdown=raw,
        )


class SourceAuthorityMetric(BaseMetric):
    name         = "source_authority"
    group        = Group.SOURCE_QUALITY
    aligned_with = "extension (autonomous agent)"
    needs_llm    = True   # optional: falls back to the rule table without a grader

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        raw = await m.source_authority(sample.sources, grader_model=grader_model)
        return MetricResult(
            name=self.name, group=self.group, aligned_with=self.aligned_with,
            score=raw["avg_authority_score"],
            reason=f"avg authority over {len(raw['breakdown'])} domains",
            breakdown=raw,
        )


# ---------------------------------------------------------------------------
# Answer Relevancy  (aligns RAGAS answer relevancy — impl measures completeness)
# ---------------------------------------------------------------------------

class SubtopicCoverageMetric(BaseMetric):
    name         = "subtopic_coverage"
    group        = Group.ANSWER_RELEVANCY
    aligned_with = "RAGAS answer relevancy (measures completeness)"
    needs_llm    = True

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        raw   = await m.subtopic_coverage(sample.query, sample.report, grader_model)
        score = raw.get("subtopic_coverage_rate")
        if score is None:
            return MetricResult.skip(self, raw.get("error", "coverage unavailable"))
        return MetricResult(
            name=self.name, group=self.group, aligned_with=self.aligned_with,
            score=score,
            reason=f"{len(raw['covered'])}/{len(raw['expected_subtopics'])} subtopics covered",
            breakdown=raw,
        )


# ---------------------------------------------------------------------------
# Faithfulness  (aligns RAGAS Faithfulness)
# ---------------------------------------------------------------------------

class UnsupportedClaimMetric(BaseMetric):
    name         = "unsupported_claim"
    group        = Group.FAITHFULNESS
    aligned_with = "RAGAS Faithfulness"
    needs_llm    = True

    async def measure(self, sample: EvalSample, grader_model=None) -> MetricResult:
        if not sample.context:
            return MetricResult.skip(self, "no source context available")
        raw   = await m.unsupported_claim(sample.report, sample.context, grader_model)
        score = raw.get("avg_claim_score")
        if score is None:
            return MetricResult.skip(self, raw.get("error", "scoring failed"))
        return MetricResult(
            name=self.name, group=self.group, aligned_with=self.aligned_with,
            score=score,   # higher = more faithful; unsupported_rate is in breakdown
            reason=f"{raw['unsupported_count']}/{raw['total_claims']} claims unsupported",
            breakdown=raw,
        )


# ---------------------------------------------------------------------------
# Registry + entry point
# ---------------------------------------------------------------------------

def default_metrics(run_subtopic: bool = True, run_unsupported: bool = True) -> list[BaseMetric]:
    """Zero-cost metrics always; the two LLM metrics gated by flags (ordered cheap→expensive)."""
    suite: list[BaseMetric] = [
        CitationFaithfulnessMetric(),
        SourceDiversityMetric(),
        SourceAuthorityMetric(),
    ]
    if run_subtopic:
        suite.append(SubtopicCoverageMetric())
    if run_unsupported:
        suite.append(UnsupportedClaimMetric())
    return suite


async def evaluate(sample: EvalSample, metrics: list[BaseMetric], grader_model=None) -> list[MetricResult]:
    """Run each metric on the sample. A metric failure becomes a skipped
    MetricResult rather than aborting the whole evaluation (DeepEval-style)."""
    results: list[MetricResult] = []
    for metric in metrics:
        try:
            results.append(await metric.measure(sample, grader_model))
        except Exception as e:
            results.append(MetricResult.skip(metric, f"{type(e).__name__}: {e}"))
    return results
