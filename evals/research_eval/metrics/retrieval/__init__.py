"""Retrieval metrics (eval-design/retrieval-metrics.md): query, source, efficiency."""

from .efficiency import SourceUtilization, QueryRelevance, RetrievalOverlap
from .query import (DecompositionCoverage, DecompositionTreeQuality, PlanAdherence,
                    SubqueryRedundancy)
from .source import MaterialCoverage, SourceAuthority, SourceDiversity, SourceRecency

RETRIEVAL_METRICS = (
    # A. query
    DecompositionCoverage, SubqueryRedundancy, DecompositionTreeQuality, PlanAdherence,
    # B. source
    SourceAuthority, SourceDiversity, SourceRecency, MaterialCoverage,
    # C. efficiency
    SourceUtilization, QueryRelevance, RetrievalOverlap,
)
