"""Generation metrics: writing quality, citations, hallucination, plus
toxicity / bias."""

from .citation import CitationCoverage, CitationPrecision, CitationRecall, EffectiveCitations
from .hallucination import ContradictedParagraphs, FactGrounding, Faithfulness
from .safety import Bias, Toxicity
from .writing import (Comprehensiveness, Insight, InstructionFollowing, Readability,
                      TopicRelevance)

GENERATION_METRICS = (
    # writing quality: what the report says and how it reads
    Comprehensiveness, Insight, Readability, Toxicity, Bias, TopicRelevance,
    # writing authority: whether it follows the brief and rests on its sources
    InstructionFollowing, CitationRecall, CitationPrecision, CitationCoverage,
    EffectiveCitations, FactGrounding, Faithfulness, ContradictedParagraphs,
)
