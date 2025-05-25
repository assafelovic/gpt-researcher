"""Structured Research Pipeline

This module orchestrates the complete structured research pipeline, integrating
fact extraction, debate-style analysis, fluff classification, and narrative building.
"""

from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gpt_researcher.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.skills.debate_agents import DebatePipeline, Verdict
from gpt_researcher.skills.fact_extractor import Fact, FactDatabase, FactExtractor
from gpt_researcher.skills.fluff_classifier import ContentAssessment, ContentQuality, FluffClassifier
from gpt_researcher.skills.narrative_builder import NarrativeBuilder, StructuredNarrative


@dataclass
class ResearchResults:
    """Complete results from the structured research pipeline."""

    topic: str
    narrative: StructuredNarrative
    debate_verdict: Verdict | None
    fact_summary: dict[str, Any]
    quality_report: dict[str, Any]
    processing_time: float
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "narrative": self.narrative.to_dict(),
            "debate_verdict": self.debate_verdict.to_dict() if self.debate_verdict else None,
            "fact_summary": self.fact_summary,
            "quality_report": self.quality_report,
            "processing_time": self.processing_time,
            "created_at": self.created_at,
        }


class StructuredResearchPipeline:
    """Main orchestrator for the structured research pipeline."""

    def __init__(self, llm_provider: GenericLLMProvider, cfg):
        self.llm_provider: GenericLLMProvider = llm_provider
        self.cfg: Config = cfg

        # Initialize components
        self.fact_extractor = FactExtractor(llm_provider, cfg)
        self.debate_pipeline = DebatePipeline(llm_provider, cfg)
        self.fluff_classifier = FluffClassifier(llm_provider, cfg)
        self.narrative_builder = NarrativeBuilder(llm_provider, cfg)

    async def run_structured_research(
        self,
        topic: str,
        sources: list[dict[str, Any]],
        enable_debate: bool = True,
        min_confidence: float = 0.5,
        max_sections: int = 8,
    ) -> ResearchResults:
        """Run the complete structured research pipeline."""

        start_time: datetime = datetime.now()

        # Stage 1: Extract facts from sources
        print(f"🔍 Stage 1: Extracting facts from {len(sources)} sources...")
        facts: list[Fact] = await self.fact_extractor.extract_facts_from_sources(sources)
        fact_db: FactDatabase = self.fact_extractor.get_fact_database()

        print(f"✅ Extracted {len(facts)} facts")

        # Stage 2: Run debate analysis (optional)
        debate_verdict: Verdict | None = None
        if enable_debate and len(facts) >= 10:  # Need sufficient facts for debate
            print("⚖️ Stage 2: Running debate analysis...")
            try:
                debate_verdict = await self.debate_pipeline.run_debate(topic, fact_db, min_confidence)
                print("✅ Debate analysis completed")
            except Exception as e:
                print(f"⚠️ Debate analysis failed: {e.__class__.__name__}: {e}")
        else:
            print("⏭️ Stage 2: Skipping debate analysis (insufficient facts or disabled)")

        # Stage 3: Build structured narrative
        print("📝 Stage 3: Building structured narrative...")
        narrative: StructuredNarrative = await self.narrative_builder.build_narrative(topic, fact_db, min_confidence, max_sections)
        print(f"✅ Narrative built with {len(narrative.sections)} sections")

        # Stage 4: Generate quality reports
        print("📊 Stage 4: Generating quality reports...")
        fact_summary: dict[str, Any] = fact_db.get_fact_summary()

        # Assess quality of all narrative sections
        section_assessments: list[ContentAssessment] = [section.quality_assessment for section in narrative.sections]
        quality_report: dict[str, Any] = self.fluff_classifier.generate_quality_report(section_assessments)

        end_time: datetime = datetime.now()
        processing_time: float = (end_time - start_time).total_seconds()

        print(f"✅ Research pipeline completed in {processing_time:.2f} seconds")

        return ResearchResults(
            topic=topic,
            narrative=narrative,
            debate_verdict=debate_verdict,
            fact_summary=fact_summary,
            quality_report=quality_report,
            processing_time=processing_time,
            created_at=start_time.isoformat(),
        )

    async def run_fact_only_research(
        self,
        topic: str,
        sources: list[dict[str, Any]],
        min_confidence: float = 0.5,
    ) -> dict[str, Any]:
        """Run fact extraction only (faster, simpler pipeline)."""

        print(f"🔍 Extracting facts from {len(sources)} sources...")
        facts: list[Fact] = await self.fact_extractor.extract_facts_from_sources(sources)
        fact_db: FactDatabase = self.fact_extractor.get_fact_database()

        # Filter and organize facts
        relevant_facts: list[Fact] = fact_db.search_facts(topic, min_confidence)
        fact_summary: dict[str, Any] = fact_db.get_fact_summary()

        return {
            "topic": topic,
            "total_facts": len(facts),
            "relevant_facts": len(relevant_facts),
            "fact_summary": fact_summary,
            "top_facts": [fact.to_dict() for fact in relevant_facts[:20]],
            "sources_analyzed": len(sources),
        }

    async def improve_existing_content(
        self,
        content: str,
        citations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Improve existing content by removing fluff and enhancing quality."""

        print("📝 Analyzing content quality...")

        # Split content into paragraphs
        paragraphs: list[str] = [p.strip() for p in content.split("\n\n") if p.strip()]

        # Assess each paragraph
        assessments: list[ContentAssessment] = await self.fluff_classifier.assess_paragraph_list(paragraphs, [citations] * len(paragraphs) if citations else None)

        # Improve low-quality paragraphs
        improved_paragraphs: list[str] = []
        for i, (paragraph, assessment) in enumerate(zip(paragraphs, assessments)):
            if assessment.quality in [ContentQuality.FLUFF, ContentQuality.LOW]:
                print(f"🔧 Improving paragraph {i+1} (quality: {assessment.quality.value})")
                improved = await self.fluff_classifier.improve_content(paragraph, assessment)
                improved_paragraphs.append(improved)
            else:
                improved_paragraphs.append(paragraph)

        # Generate quality report
        quality_report: dict[str, Any] = self.fluff_classifier.generate_quality_report(assessments)

        return {
            "original_content": content,
            "improved_content": "\n\n".join(improved_paragraphs),
            "quality_report": quality_report,
            "improvements_made": sum(1 for a in assessments if a.quality in [ContentQuality.FLUFF, ContentQuality.LOW]),
        }

    def export_results(
        self,
        results: ResearchResults,
        format: str = "markdown",
    ) -> str:
        """Export research results in specified format."""

        if format == "markdown":
            return self._export_as_markdown(results)
        elif format == "json":
            return json.dumps(results.to_dict(), indent=2)
        elif format == "html":
            return self._export_as_html(results)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_as_markdown(self, results: ResearchResults) -> str:
        """Export results as comprehensive markdown report."""

        md_parts: list[str] = [
            f"# Structured Research Report: {results.topic}",
            "",
            f"*Generated: {results.created_at}*",
            f"*Processing time: {results.processing_time:.2f} seconds*",
            f"*Facts analyzed: {results.fact_summary['total_facts']}*",
            f"*Sources: {results.fact_summary['sources']}*",
            "",
            "---",
            "",
        ]

        # Add narrative
        narrative_md: str = self.narrative_builder.export_narrative(results.narrative, "markdown")
        md_parts.append(narrative_md)

        # Add debate analysis if available
        if results.debate_verdict:
            md_parts.extend(["", "---", "", "# Debate Analysis", ""])

            debate_md: str = self.debate_pipeline.export_debate_results(results.debate_verdict, "markdown")
            md_parts.append(debate_md)

        # Add quality report
        md_parts.extend(["", "---", "", "# Quality Assessment", "", "**Overall Quality Distribution:**"])

        for quality, percentage in results.quality_report["quality_distribution"].items():
            md_parts.append(f"- {quality.title()}: {percentage:.1f}%")

        md_parts.extend(
            [
                "",
                f"**Average Factual Density:** {results.quality_report['average_factual_density']:.2f}",
                f"**Average Citation Count:** {results.quality_report['average_citation_count']:.1f}",
                "",
                "**Recommendations for Improvement:**",
            ]
        )

        for rec in results.quality_report["recommendations"]:
            md_parts.append(f"- {rec}")

        # Add fact summary
        md_parts.extend(
            [
                "",
                "---",
                "",
                "# Fact Analysis Summary",
                "",
                f"**Total Facts Extracted:** {results.fact_summary['total_facts']}",
                f"**Unique Sources:** {results.fact_summary['sources']}",
                f"**Average Confidence:** {results.fact_summary['avg_confidence']:.2f}",
                "",
                "**Fact Types:**",
            ]
        )

        for fact_type, count in results.fact_summary["fact_types"].items():
            md_parts.append(f"- {fact_type.title()}: {count}")

        return "\n".join(md_parts)

    def _export_as_html(self, results: ResearchResults) -> str:
        """Export results as HTML report."""

        # Convert markdown to HTML (basic conversion)
        markdown_content: str = self._export_as_markdown(results)

        # Simple markdown to HTML conversion
        html_content: str = markdown_content.replace("\n# ", "\n<h1>").replace("# ", "<h1>")
        html_content = html_content.replace("</h1>", "</h1>")
        html_content = html_content.replace("\n## ", "\n<h2>").replace("## ", "<h2>")
        html_content = html_content.replace("</h2>", "</h2>")
        html_content = html_content.replace("\n### ", "\n<h3>").replace("### ", "<h3>")
        html_content = html_content.replace("</h3>", "</h3>")
        html_content = html_content.replace("\n- ", "\n<li>").replace("- ", "<li>")
        html_content = html_content.replace("\n\n", "</p><p>")
        html_content = html_content.replace("**", "<strong>").replace("**", "</strong>")
        html_content = html_content.replace("*", "<em>").replace("*", "</em>")

        html_template: str = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Research Report: {results.topic}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2C3E50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495E; border-bottom: 1px solid #BDC3C7; }}
        h3 {{ color: #7F8C8D; }}
        .quality-high {{ background-color: #D5F4E6; padding: 10px; border-radius: 5px; }}
        .quality-medium {{ background-color: #FFF3CD; padding: 10px; border-radius: 5px; }}
        .quality-low {{ background-color: #F8D7DA; padding: 10px; border-radius: 5px; }}
        .metadata {{ background-color: #F8F9FA; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        li {{ margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="metadata">
        <strong>Generated:</strong> {results.created_at}<br>
        <strong>Processing Time:</strong> {results.processing_time:.2f} seconds<br>
        <strong>Overall Quality:</strong> {results.narrative.overall_quality.value.title()}
    </div>

    <p>{html_content}</p>
</body>
</html>"""

        return html_template

    async def validate_pipeline(
        self,
        test_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Validate the pipeline with test data."""

        validation_results: dict[str, Any] = {"pipeline_status": "unknown", "components_tested": {}, "errors": [], "performance_metrics": {}}

        try:
            # Test fact extraction
            print("🧪 Testing fact extraction...")
            start_time: datetime = datetime.now()
            facts: list[Fact] = await self.fact_extractor.extract_facts_from_sources(test_sources[:2])
            fact_extraction_time: float = (datetime.now() - start_time).total_seconds()

            validation_results["components_tested"]["fact_extraction"] = {"status": "success", "facts_extracted": len(facts), "time_taken": fact_extraction_time}

            if len(facts) > 0:
                # Test fluff classification
                print("🧪 Testing fluff classification...")
                start_time: datetime = datetime.now()
                test_content: str = "This is a very important and significant development that could potentially impact many aspects of the industry in various ways."
                assessment: ContentAssessment = await self.fluff_classifier.assess_content_quality(test_content)
                fluff_classification_time: float = (datetime.now() - start_time).total_seconds()

                validation_results["components_tested"]["fluff_classification"] = {
                    "status": "success",
                    "quality_detected": assessment.quality.value,
                    "time_taken": fluff_classification_time,
                }

                # Test narrative building
                print("🧪 Testing narrative building...")
                start_time: datetime = datetime.now()
                fact_db: FactDatabase = self.fact_extractor.get_fact_database()
                narrative: StructuredNarrative = await self.narrative_builder.build_narrative("test topic", fact_db, min_confidence=0.3, max_sections=3)
                narrative_building_time: float = (datetime.now() - start_time).total_seconds()

                validation_results["components_tested"]["narrative_building"] = {
                    "status": "success",
                    "sections_created": len(narrative.sections),
                    "overall_quality": narrative.overall_quality.value,
                    "time_taken": narrative_building_time,
                }

                # Test debate pipeline if enough facts
                if len(facts) >= 5:
                    print("🧪 Testing debate pipeline...")
                    start_time: datetime = datetime.now()
                    try:
                        verdict: Verdict = await self.debate_pipeline.run_debate("test topic", fact_db, min_confidence=0.3)
                        debate_time: float = (datetime.now() - start_time).total_seconds()

                        validation_results["components_tested"]["debate_pipeline"] = {
                            "status": "success",
                            "verdict_generated": True,
                            "time_taken": debate_time,
                            "pro_arguments": len(verdict.pro_arguments),
                            "con_arguments": len(verdict.con_arguments),
                            "key_facts": len(verdict.key_facts),
                            "has_synthesis": bool(verdict.synthesis),
                            "has_verdict_summary": bool(verdict.verdict_summary),
                        }
                    except Exception as e:
                        validation_results["components_tested"]["debate_pipeline"] = {"status": "failed", "error": f"{e.__class__.__name__}: {e}"}
                        errors: list[str] = validation_results["errors"]
                        errors.append(f"Debate pipeline: {e.__class__.__name__}: {e}")

                validation_results["pipeline_status"] = "success"

            else:
                validation_results["pipeline_status"] = "partial_failure"
                errors = validation_results["errors"]
                errors.append("No facts extracted from test sources")

        except Exception as e:
            validation_results["pipeline_status"] = "failure"
            errors = validation_results["errors"]
            errors.append(f"Pipeline validation failed: {e.__class__.__name__}: {e}")

        # Calculate performance metrics
        total_time: float = sum(component.get("time_taken", 0) for component in validation_results["components_tested"].values() if isinstance(component, dict))

        validation_results["performance_metrics"] = {
            "total_validation_time": total_time,
            "components_successful": len([c for c in validation_results["components_tested"].values() if isinstance(c, dict) and c.get("status") == "success"]),
            "components_failed": len([c for c in validation_results["components_tested"].values() if isinstance(c, dict) and c.get("status") == "failed"]),
        }

        return validation_results

    def get_pipeline_status(self) -> dict[str, Any]:
        """Get current status and configuration of the pipeline."""

        return {
            "pipeline_version": "1.0.0",
            "components": {
                "fact_extractor": "FactExtractor with OpenIE-style extraction",
                "debate_pipeline": "Pro/Con agents with Judge synthesis",
                "fluff_classifier": "Multi-metric content quality assessment",
                "narrative_builder": "Structured narrative from facts",
            },
            "configuration": {
                "llm_model": getattr(self.cfg, "smart_llm_model", "unknown"),
                "fast_model": getattr(self.cfg, "fast_llm_model", "unknown"),
                "default_min_confidence": 0.5,
                "default_max_sections": 8,
            },
            "capabilities": [
                "Structured fact extraction from web content",
                "Debate-style multi-agent analysis",
                "Automatic fluff detection and removal",
                "Citation-backed narrative generation",
                "Quality assessment and improvement",
                "Multiple export formats (Markdown, JSON, HTML)",
            ],
        }
