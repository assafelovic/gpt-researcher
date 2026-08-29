"""Concept-Diff Ingestion Gatekeeper for GPT Researcher.

Reduces web ingestion token bloat by extracting atomic facts, deduplicating
against a session knowledge graph, and generating compact diff payloads.
"""

from .diff_engine import ConceptDiffEngine
from .extractor import FactExtractor
from .knowledge_graph import FactAssertion, SessionKnowledgeGraph

__all__ = [
    "ConceptDiffEngine",
    "FactAssertion",
    "FactExtractor",
    "SessionKnowledgeGraph",
]
