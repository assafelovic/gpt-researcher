"""Generation metrics (eval-design/generation-metrics.md): writing quality,
citations, hallucination, plus toxicity / bias (§3.5)."""

from .citation import CitationCoverage, CitationPrecision, CitationRecall, EffectiveCitations
from .hallucination import FactGrounding, Faithfulness
from .safety import Bias, Toxicity
from .writing import (Comprehensiveness, Insight, InstructionFollowing, Readability,
                      TopicRelevance)

GENERATION_METRICS = (
    # A. writing quality
    Comprehensiveness, Insight, Readability, InstructionFollowing, TopicRelevance,
    # B. citations
    CitationRecall, CitationPrecision, CitationCoverage, EffectiveCitations,
    # C. hallucination
    Faithfulness, FactGrounding,
    # other
    Toxicity, Bias,
)
