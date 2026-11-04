"""Retrieval metrics (eval-design/retrieval-metrics.md): query, source, efficiency."""

from .efficiency import SourceUtilization, QueryRelevance, RetrievalOverlap
from .query import (DecompositionCoverage, DecompositionTreeQuality, PlanAdherence,
                    SubqueryRedundancy)
from .source import MaterialCoverage, SourceAuthority, SourceDiversity, SourceRecency

RETRIEVAL_METRICS = (
    # query quality: what the agent decided to search for
    DecompositionCoverage, SubqueryRedundancy, DecompositionTreeQuality,
    # source quality: the sources the report rests on
    SourceAuthority, SourceDiversity, SourceRecency,
    # retrieval quality: what the searches brought back and how it was used
    PlanAdherence, RetrievalOverlap, MaterialCoverage, QueryRelevance, SourceUtilization,
)
