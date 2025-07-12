"""Fluff Classifier Module

This module implements a classifier to identify and flag "fluff" content - vague,
non-factual, or low-quality text that should be rejected or replaced with
bulletized, citation-backed statements.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
import json
import re

from dataclasses import dataclass
from enum import Enum
from typing import Any

from gpt_researcher.llm_provider import GenericLLMProvider


class ContentQuality(Enum):
    """Content quality levels."""

    HIGH = "high"  # Concrete, factual, well-sourced
    MEDIUM = "medium"  # Some facts but could be improved
    LOW = "low"  # Vague, speculative, or unsupported
    FLUFF = "fluff"  # Should be rejected/rewritten


@dataclass
class ContentAssessment:
    """Assessment of content quality."""

    text: str
    quality: ContentQuality
    confidence: float
    issues: list[str]
    suggestions: list[str]
    factual_density: float  # Ratio of factual statements to total content
    citation_count: int
    vague_language_score: float  # 0.0-1.0, higher = more vague

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "quality": self.quality.value,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "factual_density": self.factual_density,
            "citation_count": self.citation_count,
            "vague_language_score": self.vague_language_score,
        }


class FluffClassifier:
    """Classifier for identifying and flagging low-quality content."""

    def __init__(self, llm_provider: GenericLLMProvider, cfg: dict[str, Any]):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: dict[str, Any] = cfg

        # Patterns for identifying fluff
        self.vague_patterns: list[str] = [
            r"\b(?:some|many|several|various|numerous|often|sometimes|generally|usually|typically|likely|probably|possibly|potentially|arguably)\b",
            r"\b(?:it seems|it appears|one might|could be|may be|might be|tends to|appears to)\b",
            r"\b(?:in general|for the most part|to some extent|in many cases|in some cases)\b",
            r"\b(?:relatively|fairly|quite|rather|somewhat|pretty|very|extremely|incredibly)\b",
            r"\b(?:significant|substantial|considerable|notable|remarkable|impressive|important)\b(?!\s+(?:increase|decrease|change|difference|improvement|reduction))",
        ]

        self.speculation_patterns: list[str] = [
            r"\b(?:believe|think|feel|suppose|assume|imagine|expect|hope|wish|wonder)\b",
            r"\b(?:should|would|could|might|may|will likely|probably will|expected to)\b",
            r"\b(?:it is believed|it is thought|it is assumed|it is expected|it is hoped)\b",
        ]

        self.filler_patterns: list[str] = [
            r"\b(?:basically|essentially|fundamentally|ultimately|obviously|clearly|certainly|definitely|undoubtedly)\b",
            r"\b(?:of course|needless to say|it goes without saying|as we all know|as everyone knows)\b",
            r"\b(?:in fact|actually|really|truly|indeed|surely|certainly)\b(?!\s+(?:\d+|measured|documented|proven))",
        ]

    async def assess_content_quality(self, text: str, citations: list[str] | None = None) -> ContentAssessment:
        """Assess the quality of content and identify issues."""

        # Basic metrics
        citation_count: int = len(citations) if citations else self._count_citations(text)
        vague_language_score: float = self._calculate_vague_language_score(text)
        factual_density: float = await self._calculate_factual_density(text)

        # LLM-based assessment
        llm_assessment: dict[str, Any] = await self._llm_quality_assessment(text)

        # Combine assessments
        quality, confidence, issues, suggestions = self._combine_assessments(text, citation_count, vague_language_score, factual_density, llm_assessment)

        return ContentAssessment(
            text=text,
            quality=quality,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            factual_density=factual_density,
            citation_count=citation_count,
            vague_language_score=vague_language_score,
        )

    def _count_citations(self, text: str) -> int:
        """Count citations in text using common citation patterns."""
        citation_patterns: list[str] = [
            r"\[\d+\]",  # [1], [2], etc.
            r"\(\d{4}\)",  # (2023), (2024), etc.
            r"\([^)]*\d{4}[^)]*\)",  # (Author, 2023), (Smith et al., 2024)
            r"https?://[^\s]+",  # URLs
            r"doi:\s*[\w\./\-]+",  # DOI references
        ]

        total_citations = 0
        for pattern in citation_patterns:
            total_citations += len(re.findall(pattern, text, re.IGNORECASE))

        return total_citations

    def _calculate_vague_language_score(
        self,
        text: str,
    ) -> float:
        """Calculate how much vague language is present in the text."""
        word_count: int = len(text.split())
        if word_count == 0:
            return 0.0

        vague_matches = 0
        for pattern_list in [self.vague_patterns, self.speculation_patterns, self.filler_patterns]:
            for pattern in pattern_list:
                vague_matches += len(re.findall(pattern, text, re.IGNORECASE))

        return min(vague_matches / word_count, 1.0)

    async def _calculate_factual_density(self, text: str) -> float:
        """Calculate the density of factual statements in the text."""

        factual_prompt: str = f"""
Analyze the following text and identify factual statements vs. opinions, speculation, or vague claims.

Text to analyze:
'''{text}'''

Count:
1. Factual statements (concrete, verifiable claims with specific details)
2. Total sentences

Return as JSON:
{{
  "factual_statements": <number>,
  "total_sentences": <number>,
  "factual_density": <factual_statements / total_sentences>
}}

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": factual_prompt}])

            result: dict[str, Any] = json.loads(response)
            return float(result.get("factual_density", 0.0))

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: simple heuristic
            sentences: list[str] = re.split(r"[.!?]+", text)
            factual_indicators: list[str] = [
                r"\d+(?:\.\d+)?(?:\s*(?:percent|%|million|billion|thousand|dollars|euros))?",
                r"\b(?:according to|research shows|study found|data indicates|statistics show)\b",
                r"\b(?:measured|documented|recorded|observed|reported|published)\b",
            ]

            factual_count: int = 0
            for sentence in sentences:
                for pattern in factual_indicators:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        factual_count += 1
                        break

            return factual_count / max(len(sentences), 1)

    async def _llm_quality_assessment(self, text: str) -> dict[str, Any]:
        """Use LLM to assess content quality."""

        assessment_prompt: str = f"""
Assess the quality of the following text for a research report. Identify specific issues and provide improvement suggestions.

Text to assess:
{text}

Evaluate based on:
1. Specificity vs. vagueness
2. Factual content vs. speculation
3. Evidence and citations
4. Clarity and precision
5. Actionable information

Provide assessment as JSON:
{{
  "quality_score": <0.0-1.0>,
  "primary_issues": ["issue1", "issue2", ...],
  "improvement_suggestions": ["suggestion1", "suggestion2", ...],
  "is_fluff": <true/false>,
  "reasoning": "Brief explanation of assessment"
}}

Only return valid JSON, no additional text, no backticks, literally NOTHING else except VALID JSON."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": assessment_prompt}])

            return json.loads(response)

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback assessment
            return {
                "quality_score": 0.5,
                "primary_issues": ["Unable to assess"],
                "improvement_suggestions": ["Review for specificity and citations"],
                "is_fluff": False,
                "reasoning": "Fallback assessment due to parsing error",
            }

    def _combine_assessments(
        self,
        text: str,
        citation_count: int,
        vague_language_score: float,
        factual_density: float,
        llm_assessment: dict[str, Any],
    ) -> tuple[ContentQuality, float, list[str], list[str]]:
        """Combine different assessment metrics into final quality rating."""

        issues: list[str] = []
        suggestions: list[str] = []

        # Calculate base quality score
        quality_score: float = 0.0

        # Citation factor (0.0-0.3)
        citation_factor: float = min(citation_count * 0.1, 0.3)
        quality_score += citation_factor

        # Factual density factor (0.0-0.4)
        quality_score += factual_density * 0.4

        # Vague language penalty (0.0-0.3 penalty)
        vague_penalty: float = vague_language_score * 0.3
        quality_score -= vague_penalty

        # LLM assessment factor (0.0-0.3)
        llm_score: float = llm_assessment.get("quality_score", 0.5)
        quality_score += llm_score * 0.3

        # Normalize to 0.0-1.0
        quality_score = max(0.0, min(1.0, quality_score))

        # Determine quality level
        if llm_assessment.get("is_fluff", False) or quality_score < 0.3:
            quality = ContentQuality.FLUFF
        elif quality_score < 0.5:
            quality = ContentQuality.LOW
        elif quality_score < 0.7:
            quality = ContentQuality.MEDIUM
        else:
            quality = ContentQuality.HIGH

        # Collect issues
        if citation_count == 0:
            issues.append("No citations or references found")
            suggestions.append("Add citations to support claims")

        if vague_language_score > 0.3:
            issues.append("High use of vague language")
            suggestions.append("Replace vague terms with specific details")

        if factual_density < 0.4:
            issues.append("Low factual content density")
            suggestions.append("Include more concrete facts and data")

        # Add LLM-identified issues
        issues.extend(llm_assessment.get("primary_issues", []))
        suggestions.extend(llm_assessment.get("improvement_suggestions", []))

        confidence: float = quality_score

        return quality, confidence, issues, suggestions

    async def assess_paragraph_list(
        self,
        paragraphs: list[str],
        citations: list[list[str]] | None = None,
    ) -> list[ContentAssessment]:
        """Assess quality of multiple paragraphs concurrently."""

        tasks: list[Coroutine[Any, Any, ContentAssessment]] = []
        for i, paragraph in enumerate(paragraphs):
            paragraph_citations: list[str] | None = citations[i] if citations and i < len(citations) else None
            tasks.append(self.assess_content_quality(paragraph, paragraph_citations))

        results: list[ContentAssessment | Exception] = await asyncio.gather(*tasks, return_exceptions=True)

        assessments: list[ContentAssessment] = []
        for result in results:
            if isinstance(result, ContentAssessment):
                assessments.append(result)
            else:
                # Create fallback assessment for failed cases
                assessments.append(
                    ContentAssessment(
                        text="",
                        quality=ContentQuality.LOW,
                        confidence=0.0,
                        issues=["Assessment failed"],
                        suggestions=["Manual review required"],
                        factual_density=0.0,
                        citation_count=0,
                        vague_language_score=1.0,
                    )
                )

        return assessments

    async def improve_content(
        self,
        text: str,
        assessment: ContentAssessment,
    ) -> str:
        """Generate improved version of low-quality content."""

        if assessment.quality in [ContentQuality.HIGH, ContentQuality.MEDIUM]:
            return text  # Already good quality

        improvement_prompt: str = f"""
Improve the following text to make it more factual, specific, and citation-worthy for a research report.

Original text:
{text}

Issues identified:
{', '.join(assessment.issues)}

Requirements for improvement:
- Replace vague language with specific details
- Convert opinions to factual statements where possible
- Structure as bullet points if appropriate
- Indicate where citations are needed with [CITATION NEEDED]
- Remove speculation and filler words
- Focus on concrete, verifiable information

Return only the improved text, no additional commentary."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": improvement_prompt}])

            return response.strip()

        except Exception:
            # Fallback: basic cleanup
            return self._basic_content_cleanup(text)

    def _basic_content_cleanup(self, text: str) -> str:
        """Basic cleanup of content when LLM improvement fails."""

        # Remove common filler phrases
        cleanup_patterns: list[tuple[str, str]] = [
            (r"\b(?:basically|essentially|fundamentally|ultimately)\s+", ""),
            (r"\b(?:obviously|clearly|certainly|definitely)\s+", ""),
            (r"\b(?:of course|needless to say)\s*,?\s*", ""),
            (r"\s+", " "),  # Multiple spaces to single space
        ]

        cleaned_text: str = text
        for pattern, replacement in cleanup_patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)

        return cleaned_text.strip()

    def filter_high_quality_content(
        self,
        assessments: list[ContentAssessment],
        min_quality: ContentQuality = ContentQuality.MEDIUM,
    ) -> list[str]:
        """Filter content to only include high-quality pieces."""

        quality_order: dict[ContentQuality, int] = {
            ContentQuality.FLUFF: 0,
            ContentQuality.LOW: 1,
            ContentQuality.MEDIUM: 2,
            ContentQuality.HIGH: 3,
        }

        min_level: int = quality_order[min_quality]

        filtered_content: list[str] = []
        for assessment in assessments:
            if quality_order[assessment.quality] >= min_level:
                filtered_content.append(assessment.text)

        return filtered_content

    def generate_quality_report(
        self,
        assessments: list[ContentAssessment],
    ) -> dict[str, Any]:
        """Generate a summary report of content quality."""

        if not assessments:
            return {"error": "No assessments provided"}

        quality_counts: dict[str, int] = {quality.value: 0 for quality in ContentQuality}
        total_issues: list[str] = []
        avg_factual_density: float = 0.0
        avg_citation_count: float = 0.0
        avg_vague_score: float = 0.0

        for assessment in assessments:
            quality_counts[assessment.quality.value] += 1
            total_issues.extend(assessment.issues)
            avg_factual_density += assessment.factual_density
            avg_citation_count += assessment.citation_count
            avg_vague_score += assessment.vague_language_score

        total_assessments: int = len(assessments)

        # Calculate percentages
        quality_percentages: dict[str, float] = {quality: (count / total_assessments) * 100 for quality, count in quality_counts.items()}

        # Most common issues
        issue_counts: dict[str, int] = {}
        for issue in total_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        common_issues: list[tuple[str, int]] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_content_pieces": total_assessments,
            "quality_distribution": quality_percentages,
            "quality_counts": quality_counts,
            "average_factual_density": avg_factual_density / total_assessments,
            "average_citation_count": avg_citation_count / total_assessments,
            "average_vague_language_score": avg_vague_score / total_assessments,
            "most_common_issues": [{"issue": issue, "count": count} for issue, count in common_issues],
            "recommendations": self._generate_quality_recommendations(quality_percentages, common_issues),
        }

    def _generate_quality_recommendations(
        self,
        quality_percentages: dict[str, float],
        common_issues: list[tuple[str, int]],
    ) -> list[str]:
        """Generate recommendations based on quality analysis."""

        recommendations: list[str] = []

        fluff_percentage: float = quality_percentages.get("fluff", 0)
        low_percentage: float = quality_percentages.get("low", 0)

        if fluff_percentage > 20:
            recommendations.append("High amount of fluff content detected. Consider rewriting or removing low-quality sections.")

        if low_percentage > 30:
            recommendations.append("Many sections have low quality. Focus on adding specific facts and citations.")

        if quality_percentages.get("high", 0) < 30:
            recommendations.append("Increase high-quality content by adding more concrete facts and evidence.")

        # Issue-specific recommendations
        issue_recommendations: dict[str, str] = {
            "No citations or references found": "Add citations and references to support all claims",
            "High use of vague language": "Replace vague terms with specific, measurable details",
            "Low factual content density": "Include more concrete facts, statistics, and data points",
        }

        for issue, count in common_issues:
            if issue in issue_recommendations:
                recommendations.append(issue_recommendations[issue])

        return recommendations[:5]  # Limit to top 5 recommendations
