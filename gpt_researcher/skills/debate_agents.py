"""Debate-Style Multi-Agent System

This module implements a debate-style pipeline with Pro/Con agents and a Judge agent
for structured argumentation and synthesis of research findings.
"""

from __future__ import annotations

import asyncio
import json

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Coroutine

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.skills.fact_extractor import Fact, FactDatabase


@dataclass
class Evidence:
    """Represents a piece of evidence supporting an argument."""

    claim: str
    supporting_facts: list[Fact]
    strength: float  # 0.0-1.0
    source_count: int
    evidence_type: str  # 'statistical', 'expert_opinion', 'case_study', 'research'

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "supporting_facts": [fact.to_dict() for fact in self.supporting_facts]}


@dataclass
class Argument:
    """Represents a structured argument with evidence."""

    position: str  # 'pro' or 'con'
    main_claim: str
    evidence_list: list[Evidence]
    confidence: float
    agent_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "evidence_list": [evidence.to_dict() for evidence in self.evidence_list]}


@dataclass
class Verdict:
    """Represents the judge's final verdict."""

    topic: str
    pro_arguments: list[Argument]
    con_arguments: list[Argument]
    synthesis: str
    verdict_summary: str
    confidence_assessment: dict[str, float]
    key_facts: list[Fact]
    recommendations: list[str]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "pro_arguments": [arg.to_dict() for arg in self.pro_arguments],
            "con_arguments": [arg.to_dict() for arg in self.con_arguments],
            "key_facts": [fact.to_dict() for fact in self.key_facts],
        }


class DebateAgent:
    """Base class for debate agents (Pro/Con)."""

    def __init__(self, agent_id: str, position: str, llm_provider: GenericLLMProvider, cfg):
        self.agent_id = agent_id
        self.position = position  # 'pro' or 'con'
        self.llm_provider = llm_provider
        self.cfg = cfg

    async def build_argument(self, topic: str, fact_db: FactDatabase, relevant_facts: list[Fact]) -> Argument:
        """Build an argument for the given position using available facts."""

        # Filter facts that support this position
        supporting_evidence = await self._identify_supporting_evidence(topic, relevant_facts)

        # Generate main claim
        main_claim = await self._generate_main_claim(topic, supporting_evidence)

        # Calculate confidence based on evidence strength
        confidence = self._calculate_argument_confidence(supporting_evidence)

        return Argument(
            position=self.position,
            main_claim=main_claim,
            evidence_list=supporting_evidence,
            confidence=confidence,
            agent_id=self.agent_id,
            created_at=datetime.now().isoformat(),
        )

    async def _identify_supporting_evidence(
        self,
        topic: str,
        facts: list[Fact],
    ) -> list[Evidence]:
        """Identify and group facts that support this agent's position."""

        evidence_prompt: str = f"""
Analyze the following facts and identify evidence that supports the {self.position.upper()} position for: {topic}

Facts to analyze:
{self._format_facts_for_prompt(facts)}

For each piece of supporting evidence, provide:
1. A clear claim statement
2. The supporting facts (reference by index)
3. Strength assessment (0.0-1.0)
4. Evidence type (statistical, expert_opinion, case_study, research)

Focus on:
- Concrete, verifiable evidence
- Multiple sources when possible
- Strong logical connections to the position
- Quantitative data when available

Return as JSON array:
[
    {{
        "claim": "Clear statement of what this evidence proves",
        "supporting_fact_indices": [0, 2, 5],
        "strength": 0.85,
        "evidence_type": "statistical"
    }}
]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": evidence_prompt}])

            evidence_data: list[dict[str, Any]] = json.loads(response)
            evidence_list: list[Evidence] = []

            for item in evidence_data:
                supporting_facts: list[Fact] = [facts[i] for i in item.get("supporting_fact_indices", []) if i < len(facts)]

                evidence = Evidence(
                    claim=item.get("claim", ""),
                    supporting_facts=supporting_facts,
                    strength=float(item.get("strength", 0.5)),
                    source_count=len(set(fact.source_url for fact in supporting_facts)),
                    evidence_type=item.get("evidence_type", "research"),
                )
                evidence_list.append(evidence)

            return evidence_list

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: create basic evidence from high-confidence facts
            return self._fallback_evidence_creation(facts)

    def _fallback_evidence_creation(self, facts: list[Fact]) -> list[Evidence]:
        """Fallback method to create evidence when LLM parsing fails."""
        evidence_list: list[Evidence] = []

        # Group facts by subject
        fact_groups: dict[str, list[Fact]] = {}
        for fact in facts:
            if fact.confidence > 0.6:  # Only use high-confidence facts
                subject: str = fact.subject.lower()
                if subject not in fact_groups:
                    fact_groups[subject] = []
                fact_groups[subject].append(fact)

        # Create evidence from fact groups
        for subject, subject_facts in fact_groups.items():
            if len(subject_facts) >= 2:  # Need multiple facts for evidence
                evidence = Evidence(
                    claim=f"Evidence regarding {subject}",
                    supporting_facts=subject_facts,
                    strength=sum(f.confidence for f in subject_facts) / len(subject_facts),
                    source_count=len(set(f.source_url for f in subject_facts)),
                    evidence_type="research",
                )
                evidence_list.append(evidence)

        return evidence_list

    async def _generate_main_claim(self, topic: str, evidence: list[Evidence]) -> str:
        """Generate the main claim for this argument."""

        evidence_summary: str = "\n".join([f"- {ev.claim} (strength: {ev.strength:.2f})" for ev in evidence])

        claim_prompt: str = f"""
Based on the following evidence, generate a clear, concise main claim for the {self.position.upper()} position on: {topic}

Evidence available:
{evidence_summary}

Requirements:
- One clear, declarative statement
- Directly addresses the topic
- Supported by the available evidence
- Avoids overgeneralization
- Maximum 2 sentences

Return only the main claim, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": claim_prompt}])
        except Exception:
            # Fallback claim
            return f"The evidence supports a {self.position} position on {topic}"
        else:
            return response.strip()

    def _calculate_argument_confidence(self, evidence: list[Evidence]) -> float:
        """Calculate overall confidence in the argument."""
        if not evidence:
            return 0.0

        # Weight by evidence strength and source diversity
        total_strength: float = sum(ev.strength for ev in evidence)
        avg_strength: float = total_strength / len(evidence)

        # Bonus for multiple sources
        unique_sources: int = len(set(fact.source_url for ev in evidence for fact in ev.supporting_facts))
        source_bonus: float = min(unique_sources * 0.1, 0.3)

        return min(avg_strength + source_bonus, 1.0)

    def _format_facts_for_prompt(self, facts: list[Fact]) -> str:
        """Format facts for inclusion in prompts."""
        formatted: list[str] = []
        for i, fact in enumerate(facts):
            formatted.append(
                f"{i}. {fact.subject} {fact.predicate} {fact.object} "
                f"(confidence: {fact.confidence:.2f}, source: {fact.source_title})"
            )
        return "\n".join(formatted)


class ProAgent(DebateAgent):
    """Agent that argues for the positive/supporting side."""

    def __init__(
        self,
        llm_provider: GenericLLMProvider,
        cfg: Config,
    ):
        super().__init__("pro_agent", "pro", llm_provider, cfg)


class ConAgent(DebateAgent):
    """Agent that argues for the negative/opposing side."""

    def __init__(
        self,
        llm_provider: GenericLLMProvider,
        cfg: Config,
    ):
        super().__init__("con_agent", "con", llm_provider, cfg)


class JudgeAgent:
    """Judge agent that synthesizes arguments and provides a verdict."""

    def __init__(
        self,
        llm_provider: GenericLLMProvider,
        cfg: Config,
    ):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: Config = cfg

    async def synthesize_verdict(
        self,
        topic: str,
        pro_arguments: list[Argument],
        con_arguments: list[Argument],
        fact_db: FactDatabase,
    ) -> Verdict:
        """Synthesize arguments and provide a balanced verdict."""

        # Extract key facts from all arguments
        key_facts: list[Fact] = self._extract_key_facts(pro_arguments + con_arguments)

        # Generate synthesis
        synthesis: str = await self._generate_synthesis(topic, pro_arguments, con_arguments)

        # Generate verdict summary
        verdict_summary: str = await self._generate_verdict_summary(topic, pro_arguments, con_arguments, synthesis)

        # Assess confidence in each position
        confidence_assessment: dict[str, float] = self._assess_position_confidence(pro_arguments, con_arguments)

        # Generate recommendations
        recommendations: list[str] = await self._generate_recommendations(topic, synthesis, confidence_assessment)

        return Verdict(
            topic=topic,
            pro_arguments=pro_arguments,
            con_arguments=con_arguments,
            synthesis=synthesis,
            verdict_summary=verdict_summary,
            confidence_assessment=confidence_assessment,
            key_facts=key_facts,
            recommendations=recommendations,
            created_at=datetime.now().isoformat(),
        )

    def _extract_key_facts(self, arguments: list[Argument]) -> list[Fact]:
        """Extract the most important facts from all arguments."""
        all_facts: list[Fact] = []
        for arg in arguments:
            for evidence in arg.evidence_list:
                all_facts.extend(evidence.supporting_facts)

        # Remove duplicates and sort by confidence
        unique_facts: dict[str, Fact] = {}
        for fact in all_facts:
            key: str = f"{fact.subject}_{fact.predicate}_{fact.object}"
            if key not in unique_facts or fact.confidence > unique_facts[key].confidence:
                unique_facts[key] = fact

        # Return top facts sorted by confidence
        sorted_facts: list[Fact] = sorted(unique_facts.values(), key=lambda f: f.confidence, reverse=True)
        return sorted_facts[:10]  # Top 10 facts

    async def _generate_synthesis(self, topic: str, pro_arguments: list[Argument], con_arguments: list[Argument]) -> str:
        """Generate a balanced synthesis of all arguments."""

        pro_summary: str = self._summarize_arguments(pro_arguments)
        con_summary: str = self._summarize_arguments(con_arguments)

        synthesis_prompt: str = f"""
Provide a balanced, objective synthesis of the following arguments about: {topic}

PRO ARGUMENTS:
{pro_summary}

CON ARGUMENTS:
{con_summary}

Requirements:
- Objective, balanced analysis
- Acknowledge strengths and weaknesses of both sides
- Identify areas of agreement and disagreement
- Highlight the most compelling evidence
- Avoid taking a definitive stance
- Focus on facts and evidence quality
- 3-4 paragraphs maximum

Provide a comprehensive synthesis that helps readers understand the full picture."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": synthesis_prompt}])
            return response.strip()
        except Exception:
            return f"Analysis of arguments regarding {topic} shows evidence on both sides."

    async def _generate_verdict_summary(
        self,
        topic: str,
        pro_arguments: list[Argument],
        con_arguments: list[Argument],
        synthesis: str,
    ) -> str:
        """Generate a concise verdict summary."""

        verdict_prompt: str = f"""
Based on the following synthesis, provide a concise verdict summary for: {topic}

Synthesis:
{synthesis}

Requirements:
- 2-3 sentences maximum
- Clear, actionable conclusion
- Acknowledge uncertainty where appropriate
- Focus on the strongest evidence
- Avoid absolute statements unless evidence is overwhelming

Provide a balanced verdict summary."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": verdict_prompt}])
            return response.strip()
        except Exception:
            return f"The evidence presents valid points on both sides of {topic}."

    def _assess_position_confidence(
        self,
        pro_arguments: list[Argument],
        con_arguments: list[Argument],
    ) -> dict[str, float]:
        """Assess confidence in each position based on argument quality."""

        def calculate_position_strength(arguments: list[Argument]) -> float:
            if not arguments:
                return 0.0

            total_confidence: float = sum(arg.confidence for arg in arguments)
            avg_confidence: float = total_confidence / len(arguments)

            # Factor in evidence diversity
            total_evidence: int = sum(len(arg.evidence_list) for arg in arguments)
            evidence_bonus: float = min(total_evidence * 0.05, 0.2)

            return min(avg_confidence + evidence_bonus, 1.0)

        pro_strength: float = calculate_position_strength(pro_arguments)
        con_strength: float = calculate_position_strength(con_arguments)

        return {"pro_confidence": pro_strength, "con_confidence": con_strength, "overall_certainty": abs(pro_strength - con_strength)}

    async def _generate_recommendations(
        self,
        topic: str,
        synthesis: str,
        confidence_assessment: dict[str, float],
    ) -> list[str]:
        """Generate actionable recommendations based on the analysis."""

        recommendations_prompt: str = f"""
Based on the analysis of {topic}, provide 3-5 specific, actionable recommendations.

Synthesis:
{synthesis}

Confidence Assessment:
- Pro position confidence: {confidence_assessment.get('pro_confidence', 0):.2f}
- Con position confidence: {confidence_assessment.get('con_confidence', 0):.2f}
- Overall certainty: {confidence_assessment.get('overall_certainty', 0):.2f}

Requirements:
- Specific, actionable recommendations
- Consider the confidence levels
- Address areas of uncertainty
- Suggest further research if needed
- Focus on practical next steps

Return as a JSON array of recommendation strings:
["recommendation 1", "recommendation 2", ...]

Only return valid JSON, no additional text."""

        try:
            response: str = await self.llm_provider.get_chat_response(messages=[{"role": "user", "content": recommendations_prompt}])
            return json.loads(response)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback recommendations
            return [f"Further research needed on {topic}", "Consider multiple perspectives when making decisions", "Monitor for new evidence and developments"]

    def _summarize_arguments(self, arguments: list[Argument]) -> str:
        """Summarize a list of arguments for prompt inclusion."""
        if not arguments:
            return "No arguments provided."

        summaries = []
        for i, arg in enumerate(arguments, 1):
            evidence_count = len(arg.evidence_list)
            summaries.append(f"{i}. {arg.main_claim} " f"(confidence: {arg.confidence:.2f}, evidence pieces: {evidence_count})")

        return "\n".join(summaries)


class DebatePipeline:
    """Orchestrates the debate-style research pipeline."""

    def __init__(
        self,
        llm_provider: GenericLLMProvider,
        cfg: Config,
    ):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: Config = cfg
        self.pro_agent: ProAgent = ProAgent(llm_provider, cfg)
        self.con_agent: ConAgent = ConAgent(llm_provider, cfg)
        self.judge_agent: JudgeAgent = JudgeAgent(llm_provider, cfg)

    async def run_debate(
        self,
        topic: str,
        fact_db: FactDatabase,
        min_confidence: float = 0.5,
    ) -> Verdict:
        """Run the complete debate pipeline."""

        # Get relevant facts for the topic
        relevant_facts: list[Fact] = fact_db.search_facts(topic, min_confidence)

        if not relevant_facts:
            raise ValueError(f"No relevant facts found for topic: {topic}")

        # Run agents concurrently
        pro_task: Coroutine[Any, Any, Argument] = self.pro_agent.build_argument(topic, fact_db, relevant_facts)
        con_task: Coroutine[Any, Any, Argument] = self.con_agent.build_argument(topic, fact_db, relevant_facts)

        pro_argument, con_argument = await asyncio.gather(pro_task, con_task)

        # Judge synthesizes the arguments
        verdict: Verdict = await self.judge_agent.synthesize_verdict(topic, [pro_argument], [con_argument], fact_db)

        return verdict

    def export_debate_results(
        self,
        verdict: Verdict,
        format: str = "json",
    ) -> str:
        """Export debate results in specified format."""
        if format == "json":
            return json.dumps(verdict.to_dict(), indent=2)
        elif format == "markdown":
            return self._format_verdict_as_markdown(verdict)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _format_verdict_as_markdown(
        self,
        verdict: Verdict,
    ) -> str:
        """Format verdict as markdown report."""
        md: str = f"""# Debate Analysis: {verdict.topic}

## Verdict Summary
{verdict.verdict_summary}

## Synthesis
{verdict.synthesis}

## Arguments

### Pro Position
**Main Claim:** {verdict.pro_arguments[0].main_claim if verdict.pro_arguments else 'No pro arguments'}
**Confidence:** {verdict.pro_arguments[0].confidence:.2f if verdict.pro_arguments else 'N/A'}

### Con Position
**Main Claim:** {verdict.con_arguments[0].main_claim if verdict.con_arguments else 'No con arguments'}
**Confidence:** {verdict.con_arguments[0].confidence:.2f if verdict.con_arguments else 'N/A'}

## Confidence Assessment
- Pro Position: {verdict.confidence_assessment.get('pro_confidence', 0):.2f}
- Con Position: {verdict.confidence_assessment.get('con_confidence', 0):.2f}
- Overall Certainty: {verdict.confidence_assessment.get('overall_certainty', 0):.2f}

## Recommendations"""
        for i, rec in enumerate(verdict.recommendations, 1):
            md += f"{i}. {rec}\n"

        md += "\n## Key Facts\n"
        for i, fact in enumerate(verdict.key_facts[:5], 1):
            md += f"{i}. {fact.subject} {fact.predicate} {fact.object} (confidence: {fact.confidence:.2f})\n"

        return md
