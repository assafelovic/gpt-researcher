"""Retrieval metrics (eval-design/retrieval-metrics.md): query, source, efficiency."""

from .efficiency import CitationUtilization, QueryRelevance, RetrievalOverlap
from .query import (DecompositionCoverage, DecompositionTreeQuality, PlanAdherence,
                    SubqueryRedundancy)
from .source import SourceAuthority, SourceDiversity

RETRIEVAL_METRICS = (
    # A. query
    DecompositionCoverage, SubqueryRedundancy, DecompositionTreeQuality, PlanAdherence,
    # B. source
    SourceAuthority, SourceDiversity,
    # C. efficiency
    CitationUtilization, QueryRelevance, RetrievalOverlap,
)
