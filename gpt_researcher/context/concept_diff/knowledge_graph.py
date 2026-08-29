"""In-memory Session Knowledge Graph for GPT Researcher Concept-Diff Ingestion.

Tracks atomic facts and metric assertions learned across research sources during
a session to detect exact duplicate fluff and surface numeric/factual conflicts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class FactAssertion:
    """An atomic factual claim or metric extracted from a web source.

    Attributes:
        subject: Normalized entity or topic name.
        predicate: Relationship, verb, or property name.
        object_val: Target entity, stat, status, or numerical value.
        is_numeric: Whether object_val contains numbers, metrics, or dates.
        source_url: URL of the origin source.
        source_title: Title of the source web page.
        context_snippet: Original sentence context for citation and verification.
    """

    subject: str
    predicate: str
    object_val: str
    is_numeric: bool = False
    source_url: str = ""
    source_title: str = ""
    context_snippet: str = ""

    def canonical_key(self) -> str:
        """Normalized string hash key for exact duplicate matching."""
        s = re.sub(r"\W+", "", self.subject.lower())
        p = re.sub(r"\W+", "", self.predicate.lower())
        o = re.sub(r"\W+", "", self.object_val.lower())
        return f"{s}:{p}:{o}"

    def subject_predicate_key(self) -> str:
        """Key representing Subject + Predicate for conflict / variance checks."""
        s = re.sub(r"\W+", "", self.subject.lower())
        p = re.sub(r"\W+", "", self.predicate.lower())
        return f"{s}:{p}"


class SessionKnowledgeGraph:
    """Live in-memory state graph tracking all facts learned in a research session."""

    def __init__(self) -> None:
        self._exact_keys: Set[str] = set()
        self._sp_index: Dict[str, List[FactAssertion]] = {}
        self.facts: List[FactAssertion] = []
        self.entities: Set[str] = set()

    def is_exact_duplicate(self, fact: FactAssertion) -> bool:
        """Check if an exact identical fact has already been recorded."""
        return fact.canonical_key() in self._exact_keys

    def find_conflict(self, fact: FactAssertion) -> Optional[FactAssertion]:
        """Check if this fact contradicts an existing assertion on the same property.

        Returns the conflicting existing fact if found, otherwise None.
        """
        sp_key = fact.subject_predicate_key()
        if sp_key not in self._sp_index:
            return None

        for existing in self._sp_index[sp_key]:
            if existing.object_val.strip().lower() != fact.object_val.strip().lower():
                return existing
        return None

    def add_fact(self, fact: FactAssertion) -> bool:
        """Add a novel or conflicting fact to the session graph.

        Returns True if newly added, False if exact duplicate.
        """
        key = fact.canonical_key()
        if key in self._exact_keys:
            return False

        self._exact_keys.add(key)
        sp_key = fact.subject_predicate_key()
        if sp_key not in self._sp_index:
            self._sp_index[sp_key] = []
        self._sp_index[sp_key].append(fact)

        self.facts.append(fact)
        if fact.subject:
            self.entities.add(fact.subject)
        if fact.object_val:
            self.entities.add(fact.object_val)
        return True

    def get_stats(self) -> Dict[str, int]:
        """Return graph size and entity statistics."""
        return {
            "total_facts": len(self.facts),
            "total_entities": len(self.entities),
            "unique_subject_predicates": len(self._sp_index),
        }
