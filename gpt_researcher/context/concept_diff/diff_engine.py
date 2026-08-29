"""Concept-Diff Engine for GPT Researcher.

Filters scraped web text into dense, high-signal diff payloads by discarding
redundant background fluff, recording novel assertions, and highlighting conflicting facts.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from .extractor import FactExtractor
from .knowledge_graph import FactAssertion, SessionKnowledgeGraph

logger = logging.getLogger(__name__)


class ConceptDiffEngine:
    """Core gatekeeper middleware for reducing token bloat during web ingestion."""

    def __init__(
        self,
        graph: Optional[SessionKnowledgeGraph] = None,
        extractor: Optional[FactExtractor] = None,
        llm_model: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        cost_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.graph = graph or SessionKnowledgeGraph()
        self.extractor = extractor or FactExtractor(
            llm_model=llm_model,
            llm_provider=llm_provider,
            llm_kwargs=llm_kwargs,
            cost_callback=cost_callback,
        )
        self.raw_words_processed: int = 0
        self.payload_words_emitted: int = 0
        self.total_discarded_facts: int = 0
        self.total_added_facts: int = 0
        self.total_conflicts_detected: int = 0

    async def process_observation(
        self,
        raw_text: str,
        source_url: str = "",
        source_title: str = "",
    ) -> str:
        """Process raw scraped text into a compact Concept-Diff markdown payload.

        Args:
            raw_text: Full raw scraped text from the web source.
            source_url: URL of the web page.
            source_title: Title of the web page.

        Returns:
            A dense markdown string containing novel facts, metric variances,
            and source citation metadata.
        """
        if not raw_text or not raw_text.strip():
            return "*No content retrieved from search tool observation.*"

        raw_word_count = len(raw_text.split())
        self.raw_words_processed += raw_word_count

        facts = await self.extractor.extract_facts(
            raw_text=raw_text,
            source_url=source_url,
            source_title=source_title,
        )

        discarded_facts: List[FactAssertion] = []
        added_facts: List[FactAssertion] = []
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]] = []

        for fact in facts:
            if self.graph.is_exact_duplicate(fact):
                discarded_facts.append(fact)
                self.total_discarded_facts += 1
                continue

            existing_conflict = self.graph.find_conflict(fact)
            if existing_conflict:
                conflicting_facts.append((fact, existing_conflict))
                self.graph.add_fact(fact)
                self.total_conflicts_detected += 1
                continue

            self.graph.add_fact(fact)
            added_facts.append(fact)
            self.total_added_facts += 1

        payload_text = self._build_diff_payload_markdown(
            source_url=source_url,
            source_title=source_title,
            raw_word_count=raw_word_count,
            added_facts=added_facts,
            conflicting_facts=conflicting_facts,
            discard_count=len(discarded_facts),
        )

        payload_word_count = len(payload_text.split())
        self.payload_words_emitted += payload_word_count
        return payload_text

    def _build_diff_payload_markdown(
        self,
        source_url: str,
        source_title: str,
        raw_word_count: int,
        added_facts: List[FactAssertion],
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]],
        discard_count: int,
    ) -> str:
        payload_lines: List[str] = []

        title_str = source_title or source_url or "Web Source"
        payload_lines.append(f"### 🌐 CONCEPT DIFF PAYLOAD: [{title_str}]")
        if source_url:
            payload_lines.append(f"**URL**: {source_url}")

        reduction_pct = 0
        output_est = min(len(added_facts), 15) * 8 + len(conflicting_facts) * 20 + 25
        if raw_word_count > 0:
            reduction_pct = max(0, int((1 - (output_est / raw_word_count)) * 100))

        payload_lines.append(
            f"> ⚡ **Gatekeeper Summary**: Processed {raw_word_count} words | "
            f"Discarded {discard_count} redundant facts (~{reduction_pct}% fluff removed)\n"
        )

        if added_facts:
            payload_lines.append("#### 🟢 NEW FACTS ADDED:")
            sorted_facts = sorted(added_facts, key=lambda f: f.is_numeric, reverse=True)[:15]
            for f in sorted_facts:
                metric_tag = " 📊" if f.is_numeric else ""
                payload_lines.append(f"- **{f.subject}** → *{f.predicate}*: `{f.object_val}`{metric_tag}")
            payload_lines.append("")

        if conflicting_facts:
            payload_lines.append("#### ⚠️ CONFLICTS DETECTED:")
            for inc, ex in conflicting_facts[:5]:
                payload_lines.append(
                    f"- **{inc.subject} [{inc.predicate}]**: Current claims **'{inc.object_val}'**, "
                    f"contradicting prior **'{ex.object_val}'**."
                )
            payload_lines.append("")

        if not added_facts and not conflicting_facts:
            payload_lines.append(
                "> ℹ️ *All content in this source was redundant background fluff. Zero new assertions.*"
            )

        return "\n".join(payload_lines)

    def get_telemetry(self) -> Dict[str, Any]:
        """Return token and word reduction telemetry statistics."""
        reduction_pct = 0.0
        if self.raw_words_processed > 0:
            savings = self.raw_words_processed - self.payload_words_emitted
            reduction_pct = max(0.0, round((savings / self.raw_words_processed) * 100, 2))

        return {
            "raw_words_processed": self.raw_words_processed,
            "payload_words_emitted": self.payload_words_emitted,
            "word_reduction_pct": reduction_pct,
            "total_discarded_facts": self.total_discarded_facts,
            "total_added_facts": self.total_added_facts,
            "total_conflicts_detected": self.total_conflicts_detected,
            "knowledge_graph_stats": self.graph.get_stats(),
        }
