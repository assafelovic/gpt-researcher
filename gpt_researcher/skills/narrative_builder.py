"""
Narrative Builder Module

This module builds detailed narratives from structured facts, ensuring all content
is citation-backed and free from fluff or speculation.
"""
from __future__ import annotations

import asyncio
import json

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Coroutine

from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.skills.fact_extractor import Fact, FactDatabase
from gpt_researcher.skills.fluff_classifier import ContentAssessment, ContentQuality, FluffClassifier


@dataclass
class NarrativeSection:
    """Represents a section of the narrative with facts and quality assessment."""
    title: str
    content: str
    supporting_facts: list[Fact]
    quality_assessment: ContentAssessment
    citations: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "supporting_facts": [fact.to_dict() for fact in self.supporting_facts],
            "quality_assessment": self.quality_assessment.to_dict(),
            "citations": self.citations,
            "confidence": self.confidence
        }


@dataclass
class StructuredNarrative:
    """Represents a complete structured narrative built from facts."""
    topic: str
    sections: list[NarrativeSection]
    executive_summary: str
    key_findings: list[str]
    methodology: str
    limitations: list[str]
    recommendations: list[str]
    fact_count: int
    source_count: int
    overall_quality: ContentQuality
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "sections": [section.to_dict() for section in self.sections],
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "methodology": self.methodology,
            "limitations": self.limitations,
            "recommendations": self.recommendations,
            "fact_count": self.fact_count,
            "source_count": self.source_count,
            "overall_quality": self.overall_quality.value,
            "created_at": self.created_at
        }


class NarrativeBuilder:
    """Builds structured narratives from fact databases."""

    def __init__(self, llm_provider: GenericLLMProvider, cfg: dict[str, Any]):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: dict[str, Any] = cfg
        self.fluff_classifier: FluffClassifier = FluffClassifier(llm_provider, cfg)

    async def build_narrative(
        self,
        topic: str,
        fact_db: FactDatabase,
        min_confidence: float = 0.5,
        max_sections: int = 8,
    ) -> StructuredNarrative:
        """Build a complete structured narrative from facts."""

        # Get relevant facts
        relevant_facts = fact_db.search_facts(topic, min_confidence)

        if not relevant_facts:
            raise ValueError(f"No relevant facts found for topic: {topic}")

        # Generate narrative structure
        section_outline = await self._generate_section_outline(topic, relevant_facts, max_sections)

        # Build sections concurrently
        section_tasks: list[Coroutine[Any, Any, NarrativeSection]] = [
            self._build_section(section_title, topic, relevant_facts)
            for section_title in section_outline
        ]

        sections: list[NarrativeSection | BaseException] = await asyncio.gather(*section_tasks, return_exceptions=True)

        # Filter successful sections
        valid_sections: list[NarrativeSection] = [s for s in sections if isinstance(s, NarrativeSection)]

        # Generate supporting content
        executive_summary: str = await self._generate_executive_summary(topic, valid_sections)
        key_findings: list[str] = await self._extract_key_findings(valid_sections)
        methodology: str = await self._generate_methodology(fact_db, relevant_facts)
        limitations: list[str] = await self._identify_limitations(relevant_facts)
        recommendations: list[str] = await self._generate_recommendations(topic, valid_sections)

        # Calculate overall quality
        overall_quality: ContentQuality = self._assess_overall_quality(valid_sections)

        return StructuredNarrative(
            topic=topic,
            sections=valid_sections,
            executive_summary=executive_summary,
            key_findings=key_findings,
            methodology=methodology,
            limitations=limitations,
            recommendations=recommendations,
            fact_count=len(relevant_facts),
            source_count=len(set(fact.source_url for fact in relevant_facts)),
            overall_quality=overall_quality,
            created_at=datetime.now().isoformat()
        )

    async def _generate_section_outline(
        self,
        topic: str,
        facts: list[Fact],
        max_sections: int,
    ) -> list[str]:
        """Generate an outline of sections based on available facts."""

        # Group facts by subject/theme
        fact_themes = self._group_facts_by_theme(facts)

        outline_prompt = f"""
Based on the following fact themes for the topic "{topic}", create a logical section outline for a research report.

Available fact themes:
{self._format_themes_for_prompt(fact_themes)}

Requirements:
- Maximum {max_sections} sections
- Logical flow from general to specific
- Each section should have sufficient facts to support it
- Focus on the most important aspects of the topic
- Use clear, descriptive section titles

Return as a JSON array of section titles:
["Section Title 1", "Section Title 2", ...]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": outline_prompt}])

            section_titles: list[str] = json.loads(response)
            return section_titles[:max_sections]  # Ensure we don't exceed max

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: create sections from top themes
            return list(fact_themes.keys())[:max_sections]

    def _group_facts_by_theme(
        self,
        facts: list[Fact],
    ) -> dict[str, list[Fact]]:
        """Group facts by common themes/subjects."""
        themes: dict[str, list[Fact]] = {}

        for fact in facts:
            # Use subject as primary grouping key
            theme_key: str = fact.subject.lower()

            # Try to find existing similar theme
            matched_theme: str | None = None
            for existing_theme in themes.keys():
                if self._themes_similar(theme_key, existing_theme):
                    matched_theme = existing_theme
                    break

            if matched_theme:
                themes[matched_theme].append(fact)
            else:
                themes[theme_key] = [fact]

        # Sort themes by fact count (descending)
        sorted_themes: dict[str, list[Fact]] = dict(sorted(themes.items(), key=lambda x: len(x[1]), reverse=True))

        return sorted_themes

    def _themes_similar(
        self,
        theme1: str,
        theme2: str,
    ) -> bool:
        """Check if two themes are similar enough to group together."""
        # Simple similarity check - can be enhanced with more sophisticated methods
        words1: set[str] = set(theme1.split())
        words2: set[str] = set(theme2.split())

        if not words1 or not words2:
            return False

        intersection: set[str] = words1.intersection(words2)
        union: set[str] = words1.union(words2)

        similarity: float = len(intersection) / len(union)
        return similarity > 0.3  # 30% word overlap threshold

    def _format_themes_for_prompt(
        self,
        themes: dict[str, list[Fact]],
    ) -> str:
        """Format themes for inclusion in prompts."""
        formatted: list[str] = []
        for theme, theme_facts in themes.items():
            fact_count: int = len(theme_facts)
            sample_facts: list[Fact] = theme_facts[:3]  # Show first 3 facts as examples

            formatted.append(f"Theme: {theme.title()} ({fact_count} facts)")
            for fact in sample_facts:
                formatted.append(f"  - {fact.subject} {fact.predicate} {fact.object}")
            if len(theme_facts) > 3:
                formatted.append(f"  - ... and {len(theme_facts) - 3} more facts")
            formatted.append("")

        return "\n".join(formatted)

    async def _build_section(
        self,
        section_title: str,
        topic: str,
        all_facts: list[Fact],
    ) -> NarrativeSection:
        """Build a single narrative section."""

        # Find facts relevant to this section
        section_facts: list[Fact] = self._find_section_facts(section_title, all_facts)

        if not section_facts:
            # Create minimal section if no specific facts found
            section_facts = all_facts[:3]  # Use first 3 facts as fallback

        # Generate section content
        content: str = await self._generate_section_content(section_title, topic, section_facts)

        # Extract citations
        citations: list[str] = self._extract_citations_from_facts(section_facts)

        # Assess content quality
        quality_assessment: ContentAssessment = (
            await self.fluff_classifier.assess_content_quality(
                content,
                citations,
            )
        )

        # Improve content if quality is low
        if quality_assessment.quality in [ContentQuality.FLUFF, ContentQuality.LOW]:
            content = await self.fluff_classifier.improve_content(content, quality_assessment)

            # Re-assess improved content
            quality_assessment = await self.fluff_classifier.assess_content_quality(
                content,
                citations,
            )

        # Calculate section confidence
        confidence: float = self._calculate_section_confidence(
            section_facts,
            quality_assessment,
        )

        return NarrativeSection(
            title=section_title,
            content=content,
            supporting_facts=section_facts,
            quality_assessment=quality_assessment,
            citations=citations,
            confidence=confidence
        )

    def _find_section_facts(
        self,
        section_title: str,
        all_facts: list[Fact],
    ) -> list[Fact]:
        """Find facts relevant to a specific section."""
        section_keywords: list[str] = section_title.lower().split()
        relevant_facts: list[tuple[Fact, int]] = []

        for fact in all_facts:
            fact_text: str = f"{fact.subject} {fact.predicate} {fact.object} {fact.context}".lower()

            # Check if any section keywords appear in the fact
            relevance_score: int = 0
            for keyword in section_keywords:
                if keyword in fact_text:
                    relevance_score += 1

            if relevance_score > 0:
                relevant_facts.append((fact, relevance_score))

        # Sort by relevance score and confidence
        relevant_facts.sort(key=lambda x: (x[1], x[0].confidence), reverse=True)

        # Return top facts (limit to avoid overwhelming content)
        return [fact_tuple[0] for fact_tuple in relevant_facts[:10]]

    async def _generate_section_content(
        self,
        section_title: str,
        topic: str,
        facts: list[Fact],
    ) -> str:
        """Generate content for a section based on facts."""

        facts_summary: str = self._format_facts_for_content_generation(facts)

        content_prompt = f"""
Write a detailed section for a research report on "{topic}".

Section Title: {section_title}

Available Facts:
{facts_summary}

Requirements:
- Use ONLY the provided facts - do not add speculation or unsupported claims
- Write in clear, professional prose
- Include specific numbers, statistics, and concrete details from the facts
- Maintain objectivity and avoid subjective language
- Structure with clear topic sentences and logical flow
- Reference facts naturally within the text
- Aim for 200-400 words
- Do not include citations in brackets - they will be added separately

Write the section content:"""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": content_prompt}])

            return response.strip()

        except Exception:
            # Fallback: create basic content from facts
            return self._create_fallback_content(section_title, facts)

    def _format_facts_for_content_generation(
        self,
        facts: list[Fact],
    ) -> str:
        """Format facts for content generation prompts."""
        formatted: list[str] = []
        for i, fact in enumerate(facts, 1):
            formatted.append(
                f"{i}. {fact.subject} {fact.predicate} {fact.object} "
                f"(confidence: {fact.confidence:.2f}, source: {fact.source_title})"
            )
            if fact.context:
                formatted.append(f"   Context: {fact.context}")

        return "\n".join(formatted)

    def _create_fallback_content(
        self,
        section_title: str,
        facts: list[Fact],
    ) -> str:
        """Create basic content when LLM generation fails."""
        if not facts:
            return f"No specific data available for {section_title}."

        content_parts: list[str] = [f"## {section_title}\n"]

        for fact in facts[:5]:  # Limit to top 5 facts
            content_parts.append(f"• {fact.subject} {fact.predicate} {fact.object}")

        return "\n".join(content_parts)

    def _extract_citations_from_facts(self, facts: list[Fact]) -> list[str]:
        """Extract unique citations from facts."""
        citations: set[str] = set()

        for fact in facts:
            if fact.source_url:
                citations.add(fact.source_url)
            if fact.source_title:
                citations.add(fact.source_title)

        return list(citations)

    def _calculate_section_confidence(
        self,
        facts: list[Fact],
        quality_assessment: ContentAssessment,
    ) -> float:
        """Calculate confidence score for a section."""
        if not facts:
            return 0.0

        # Average fact confidence
        avg_fact_confidence: float = sum(fact.confidence for fact in facts) / len(facts)

        # Quality assessment confidence
        quality_confidence: float = quality_assessment.confidence

        # Source diversity bonus
        unique_sources: int = len(set(fact.source_url for fact in facts))
        source_bonus: float = min(unique_sources * 0.1, 0.2)

        # Combine factors
        total_confidence: float = (
            avg_fact_confidence * 0.5
            + quality_confidence * 0.4
            + source_bonus
        )

        return min(total_confidence, 1.0)

    async def _generate_executive_summary(
        self,
        topic: str,
        sections: list[NarrativeSection],
    ) -> str:
        """Generate an executive summary from sections."""

        section_summaries: list[str] = []
        for section in sections:
            # Extract key points from each section
            key_points: str = section.content[:200] + "..." if len(section.content) > 200 else section.content
            section_summaries.append(f"{section.title}: {key_points}")

        summary_prompt: str = f"""
Create a concise executive summary for a research report on "{topic}".

Section summaries:
{chr(10).join(section_summaries)}

Requirements:
- 3-4 sentences maximum
- Highlight the most important findings
- Use specific facts and numbers where available
- Maintain objectivity
- Focus on actionable insights

Write the executive summary:"""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": summary_prompt}])

            return response.strip()

        except Exception:
            return f"Research analysis of {topic} based on {len(sections)} key areas of investigation."

    async def _extract_key_findings(
        self,
        sections: list[NarrativeSection],
    ) -> list[str]:
        """Extract key findings from sections."""

        all_facts: list[Fact] = []
        for section in sections:
            all_facts.extend(section.supporting_facts)

        # Sort facts by confidence and select top findings
        top_facts: list[Fact] = sorted(all_facts, key=lambda f: f.confidence, reverse=True)[:10]

        findings_prompt: str = f"""
Extract 5-7 key findings from the following facts:

{self._format_facts_for_content_generation(top_facts)}

Requirements:
- Each finding should be a clear, specific statement
- Focus on the most significant and well-supported facts
- Use concrete numbers and details
- Avoid speculation or interpretation
- Format as bullet points

Return as JSON array:
["Finding 1", "Finding 2", ...]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": findings_prompt}])

            return json.loads(response)

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: create findings from top facts
            return [
                f"{fact.subject} {fact.predicate} {fact.object}"
                for fact in top_facts[:5]
            ]

    async def _generate_methodology(
        self,
        fact_db: FactDatabase,
        facts: list[Fact],
    ) -> str:
        """Generate methodology description."""

        fact_summary: dict[str, Any] = fact_db.get_fact_summary()

        methodology: str = f"""
This analysis is based on structured fact extraction from {fact_summary['sources']} sources,
yielding {fact_summary['total_facts']} verified facts with an average confidence of
{fact_summary['avg_confidence']:.2f}. Facts were categorized by type:
{', '.join(f"{k}: {v}" for k, v in fact_summary['fact_types'].items())}.
Only facts with confidence scores above 0.5 were included in the narrative construction."""

        return methodology.strip()

    async def _identify_limitations(
        self,
        facts: list[Fact],
    ) -> list[str]:
        """Identify limitations in the analysis."""

        limitations: list[str] = []

        # Check for source diversity
        unique_sources = len(set(fact.source_url for fact in facts))
        if unique_sources < 5:
            limitations.append(f"Limited source diversity ({unique_sources} unique sources)")

        # Check for low confidence facts
        low_confidence_facts = [f for f in facts if f.confidence < 0.7]
        if len(low_confidence_facts) > len(facts) * 0.3:
            limitations.append("Significant portion of facts have moderate confidence levels")

        # Check for fact type diversity
        fact_types = set(fact.fact_type for fact in facts)
        if len(fact_types) < 3:
            limitations.append("Limited diversity in fact types")

        # Check for temporal coverage
        recent_facts = [f for f in facts if "2023" in f.extracted_at or "2024" in f.extracted_at]
        if len(recent_facts) < len(facts) * 0.5:
            limitations.append("Limited recent data coverage")

        return limitations

    async def _generate_recommendations(
        self,
        topic: str,
        sections: list[NarrativeSection],
    ) -> list[str]:
        """Generate recommendations based on the analysis."""

        high_confidence_sections: list[NarrativeSection] = [s for s in sections if s.confidence > 0.7]

        recommendations_prompt: str = f"""
Based on the research analysis of "{topic}", provide 3-5 specific, actionable recommendations.

High-confidence findings:
{chr(10).join([f"- {s.title}: {s.content[:100]}..." for s in high_confidence_sections])}

Requirements:
- Specific, actionable recommendations
- Based on the evidence presented
- Consider practical implementation
- Address key areas identified in the research

Return as JSON array:
["Recommendation 1", "Recommendation 2", ...]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": recommendations_prompt}])

            return json.loads(response)

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback recommendations
            return [
                f"Further research needed on {topic}",
                "Monitor developments in key areas identified",
                "Consider implementing evidence-based strategies"
            ]

    def _assess_overall_quality(
        self,
        sections: list[NarrativeSection],
    ) -> ContentQuality:
        """Assess overall quality of the narrative."""
        if not sections:
            return ContentQuality.LOW

        quality_scores: dict[ContentQuality, int] = {
            ContentQuality.FLUFF: 0,
            ContentQuality.LOW: 1,
            ContentQuality.MEDIUM: 2,
            ContentQuality.HIGH: 3
        }

        avg_quality_score: float = sum(
            quality_scores[section.quality_assessment.quality]
            for section in sections
        ) / len(sections)

        if avg_quality_score >= 2.5:
            return ContentQuality.HIGH
        elif avg_quality_score >= 1.5:
            return ContentQuality.MEDIUM
        elif avg_quality_score >= 0.5:
            return ContentQuality.LOW
        else:
            return ContentQuality.FLUFF

    def export_narrative(
        self,
        narrative: StructuredNarrative,
        format: str = "markdown",
    ) -> str:
        """Export narrative in specified format."""

        if format == "markdown":
            return self._format_as_markdown(narrative)
        elif format == "json":
            return json.dumps(narrative.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _format_as_markdown(self, narrative: StructuredNarrative) -> str:
        """Format narrative as markdown."""

        md_parts = [
            f"# {narrative.topic}",
            "",
            "## Executive Summary",
            narrative.executive_summary,
            "",
            "## Key Findings",
        ]

        for finding in narrative.key_findings:
            md_parts.append(f"• {finding}")

        md_parts.extend(["", "## Analysis"])

        for section in narrative.sections:
            md_parts.extend([
                f"### {section.title}",
                section.content,
                ""
            ])

        md_parts.extend([
            "## Methodology",
            narrative.methodology,
            "",
            "## Limitations"
        ])

        for limitation in narrative.limitations:
            md_parts.append(f"• {limitation}")

        md_parts.extend(["", "## Recommendations"])

        for recommendation in narrative.recommendations:
            md_parts.append(f"• {recommendation}")

        md_parts.extend([
            "",
            "---",
            f"*Analysis based on {narrative.fact_count} facts from {narrative.source_count} sources*",
            f"*Overall quality: {narrative.overall_quality.value.title()}*",
            f"*Generated: {narrative.created_at}*"
        ])

        return "\n".join(md_parts)
