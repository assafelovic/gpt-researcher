"""Fact Extractor Module

This module implements structured fact extraction from scraped content using OpenIE-style
extraction to pull out concrete facts, triples, numbers, and bullet-point metrics.
"""

from __future__ import annotations

import asyncio
import json
import re

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Iterator, List

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider


@dataclass
class Fact:
    """Represents a structured fact extracted from content."""

    subject: str
    predicate: str
    object: str
    confidence: float
    source_url: str
    source_title: str
    context: str
    fact_type: str  # 'triple', 'metric', 'statistic', 'claim'
    extracted_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return f"{self.subject} {self.predicate} {self.object}"


class FactDatabase:
    """In-memory database for storing and querying extracted facts."""

    def __init__(self):
        self.facts: list[Fact] = []
        self._subject_index: dict[str, list[int]] = {}
        self._predicate_index: dict[str, list[int]] = {}
        self._source_index: dict[str, list[int]] = {}

    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the database and update indices."""
        fact_id: int = len(self.facts)
        self.facts.append(fact)

        # Update indices
        self._add_to_index(self._subject_index, fact.subject.lower(), fact_id)
        self._add_to_index(self._predicate_index, fact.predicate.lower(), fact_id)
        self._add_to_index(self._source_index, fact.source_url, fact_id)

    def _add_to_index(
        self,
        index: dict[str, list[int]],
        key: str,
        fact_id: int,
    ) -> None:
        """Helper to add fact ID to an index."""
        if key not in index:
            index[key] = []
        index[key].append(fact_id)

    def get_facts_by_subject(
        self,
        subject: str,
    ) -> list[Fact]:
        """Get all facts with a specific subject."""
        fact_ids: list[int] = self._subject_index.get(subject.lower(), [])
        return [self.facts[i] for i in fact_ids]

    def get_facts_by_predicate(self, predicate: str) -> List[Fact]:
        """Get all facts with a specific predicate."""
        fact_ids: list[int] = self._predicate_index.get(predicate.lower(), [])
        return [self.facts[i] for i in fact_ids]

    def get_facts_by_source(self, source_url: str) -> List[Fact]:
        """Get all facts from a specific source."""
        fact_ids: list[int] = self._source_index.get(source_url, [])
        return [self.facts[i] for i in fact_ids]

    def search_facts(
        self,
        query: str,
        min_confidence: float = 0.5,
    ) -> list[Fact]:
        """Search facts by query string."""
        query_lower: str = query.lower()
        matching_facts: list[Fact] = []

        for fact in self.facts:
            if fact.confidence < min_confidence:
                continue

            # Check if query matches any part of the fact
            fact_text: str = f"{fact.subject} {fact.predicate} {fact.object} {fact.context}".lower()
            if query_lower in fact_text:
                matching_facts.append(fact)

        # Sort by confidence
        return sorted(matching_facts, key=lambda f: f.confidence, reverse=True)

    def get_all_facts(
        self,
        min_confidence: float = 0.0,
    ) -> list[Fact]:
        """Get all facts above minimum confidence threshold."""
        return [f for f in self.facts if f.confidence >= min_confidence]

    def get_fact_summary(self) -> dict[str, Any]:
        """Get summary statistics about the fact database."""
        return {
            "total_facts": len(self.facts),
            "fact_types": {fact_type: len([f for f in self.facts if f.fact_type == fact_type]) for fact_type in set(f.fact_type for f in self.facts)},
            "sources": len(set(f.source_url for f in self.facts)),
            "avg_confidence": sum(f.confidence for f in self.facts) / len(self.facts) if self.facts else 0,
        }


class FactExtractor:
    """Extracts structured facts from scraped content using LLM-based OpenIE."""

    def __init__(self, llm_provider: GenericLLMProvider, cfg):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: Config = cfg
        self.fact_db: FactDatabase = FactDatabase()

    async def extract_facts_from_content(self, content: Dict[str, Any]) -> List[Fact]:
        """Extract facts from a single piece of scraped content."""
        if not content.get("raw_content"):
            return []

        text: str = content["raw_content"]
        url: str = content.get("url", "")
        title: str = content.get("title", "")

        # Split content into chunks for processing
        chunks: list[str] = self._chunk_text(text, max_chunk_size=2000)
        all_facts: list[Fact] = []

        for chunk in chunks:
            facts: list[Fact] = await self._extract_facts_from_chunk(chunk, url, title)
            all_facts.extend(facts)

        # Add facts to database
        for fact in all_facts:
            self.fact_db.add_fact(fact)

        return all_facts

    def _chunk_text(
        self,
        text: str,
        max_chunk_size: int = 2000,
    ) -> list[str]:
        """Split text into manageable chunks for fact extraction."""
        # Split by paragraphs first
        paragraphs: list[str] = text.split("\n\n")
        chunks: list[str] = []
        current_chunk: str = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _extract_facts_from_chunk(
        self,
        text: str,
        source_url: str,
        source_title: str,
    ) -> list[Fact]:
        """Extract facts from a text chunk using LLM."""

        extraction_prompt = f"""
Extract structured facts from the following text. For each fact, identify:
1. Subject (who/what the fact is about)
2. Predicate (the relationship or action)
3. Object (what the subject relates to)
4. Fact type (triple, metric, statistic, claim)
5. Confidence (0.0-1.0 based on how certain/verifiable the fact is)

Focus on:
- Concrete, verifiable statements
- Numbers, statistics, and metrics
- Clear relationships between entities
- Factual claims with evidence

Avoid:
- Opinions or subjective statements
- Vague or ambiguous claims
- Speculation or hypotheticals

Text to analyze:
{text}

Return the facts as a JSON array with this structure:
[
  {{
    "subject": "entity or topic",
    "predicate": "relationship or action",
    "object": "related entity or value",
    "fact_type": "triple|metric|statistic|claim",
    "confidence": 0.85,
    "context": "surrounding context for the fact"
  }}
]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                stream=False,
            )

            # Parse JSON response
            facts_data: list[dict[str, Any]] = json.loads(response)
            facts: list[Fact] = []

            for fact_data in facts_data:
                fact = Fact(
                    subject=fact_data.get("subject", ""),
                    predicate=fact_data.get("predicate", ""),
                    object=fact_data.get("object", ""),
                    confidence=float(fact_data.get("confidence", 0.5)),
                    source_url=source_url,
                    source_title=source_title,
                    context=fact_data.get("context", ""),
                    fact_type=fact_data.get("fact_type", "claim"),
                    extracted_at=datetime.now().isoformat(),
                )
                facts.append(fact)

            return facts

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing JSON response: {e.__class__.__name__}: {e}")
            # Fallback to regex-based extraction for numbers and simple facts
            return self._fallback_extraction(text, source_url, source_title)

    def _fallback_extraction(
        self,
        text: str,
        source_url: str,
        source_title: str,
    ) -> list[Fact]:
        """Fallback fact extraction using regex patterns."""
        facts: list[Fact] = []

        # Extract numerical facts
        number_patterns: list[str] = [
            r"(\w+(?:\s+\w+)*)\s+(?:is|are|was|were|costs?|measures?)\s+(\$?[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|percent|%|dollars?|euros?|pounds?))?)",
            r"(\w+(?:\s+\w+)*)\s+(?:increased|decreased|grew|fell|rose|dropped)\s+(?:by\s+)?(\d+(?:\.\d+)?(?:\s*(?:percent|%)))",
            r"(\w+(?:\s+\w+)*)\s+(?:has|have)\s+(\d+(?:,\d{3})*(?:\s+(?:users|customers|employees|members|people)))",
        ]

        for pattern in number_patterns:
            matches: Iterator[re.Match[str]] = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                subject: str = match.group(1).strip()
                object_val: str = match.group(2).strip()

                fact = Fact(
                    subject=subject,
                    predicate=(
                        "has_value"
                        if any(word in pattern for word in ["is", "are", "costs", "measures"])
                        else "changed_by"
                    ),
                    object=object_val,
                    confidence=0.7,
                    source_url=source_url,
                    source_title=source_title,
                    context=match.group(0),
                    fact_type="metric",
                    extracted_at=datetime.now().isoformat(),
                )
                facts.append(fact)

        return facts

    async def extract_facts_from_sources(self, sources: list[dict[str, Any]]) -> list[Fact]:
        """Extract facts from multiple sources concurrently."""
        tasks: list[Any] = [self.extract_facts_from_content(source) for source in sources]
        results: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)

        all_facts: list[Fact] = []
        for result in results:
            if isinstance(result, list):
                all_facts.extend(result)

        return all_facts

    def get_fact_database(self) -> FactDatabase:
        """Get the fact database instance."""
        return self.fact_db

    def export_facts(
        self,
        format: str = "json",
    ) -> str:
        """Export facts in specified format."""
        facts_data: list[dict[str, Any]] = [fact.to_dict() for fact in self.fact_db.get_all_facts()]

        if format == "json":
            return json.dumps(facts_data, indent=2)
        elif format == "csv":
            import csv
            import io

            output: io.StringIO = io.StringIO()
            if facts_data:
                writer: csv.DictWriter = csv.DictWriter(output, fieldnames=facts_data[0].keys())
                writer.writeheader()
                writer.writerows(facts_data)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
