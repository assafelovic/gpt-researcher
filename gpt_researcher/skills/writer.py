from typing import Dict, Optional
import json
import os
import logging

from ..utils.llm import construct_subtopics
from ..utils.costs import estimate_token_usage
from ..actions import (
    stream_output,
    generate_report,
    generate_draft_section_titles,
    write_report_introduction,
    write_conclusion
)
from ..actions.markdown_processing import (
    sanitize_citation_links,
    canonicalize_intext_citations,
    prune_unsupported_citation_claims,
)


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports based on research data."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.research_params = {
            "query": self.researcher.query,
            "agent_role_prompt": self.researcher.cfg.agent_role or self.researcher.role,
            "report_type": self.researcher.report_type,
            "report_source": self.researcher.report_source,
            "tone": self.researcher.tone,
            "websocket": self.researcher.websocket,
            "cfg": self.researcher.cfg,
            "headers": self.researcher.headers,
        }

    async def write_report(self, existing_headers: list = [], relevant_written_contents: list = [], ext_context=None, custom_prompt="") -> str:
        """
        Write a report based on existing headers and relevant contents.

        Args:
            existing_headers (list): List of existing headers.
            relevant_written_contents (list): List of relevant written contents.
            ext_context (Optional): External context, if any.
            custom_prompt (str): Custom prompt for the report.

        Returns:
            str: The generated report.
        """
        # send the selected images prior to writing report
        research_images = self.researcher.get_research_images()
        if research_images:
            await stream_output(
                "images",
                "selected_images",
                json.dumps(research_images),
                self.researcher.websocket,
                True,
                research_images
            )

        context = ext_context or self.researcher.context
        allowed_urls = set()
        try:
            allowed_urls = set(getattr(self.researcher, "visited_urls", set()) or set())
        except Exception:
            allowed_urls = set()

        # Add an allow-list of sources into the prompt context to reduce hallucinated citations.
        if allowed_urls and _env_bool("INCLUDE_ALLOWED_SOURCES_IN_CONTEXT", True):
            limit = int(os.getenv("ALLOWED_SOURCES_LIMIT", "200"))
            allowed_list = list(allowed_urls)[: max(0, limit)]
            allowed_block = (
                "\n\nALLOWED_SOURCES (cite ONLY these URLs; do NOT invent papers/authors/domains; "
                "if you cannot support a claim with these sources, omit the claim):\n"
                + "\n".join(f"- {u}" for u in allowed_list)
            )
            context = f"{context}{allowed_block}"

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_report",
                f"✍️ Writing report for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        report_params = self.research_params.copy()
        report_params["context"] = context
        report_params["custom_prompt"] = custom_prompt

        if self.researcher.report_type == "subtopic_report":
            report_params.update({
                "main_topic": self.researcher.parent_query,
                "existing_headers": existing_headers,
                "relevant_written_contents": relevant_written_contents,
                "cost_callback": self.researcher.add_costs,
            })
        else:
            report_params["cost_callback"] = self.researcher.add_costs

        report = await generate_report(**report_params, **self.researcher.kwargs)
        report = sanitize_citation_links(report, allowed_urls=allowed_urls if allowed_urls else None)
        report = canonicalize_intext_citations(report, allowed_urls=allowed_urls if allowed_urls else None)
        # Optional stricter guard: drop uncited "study found X%" style hallucination sentences
        if _env_bool("STRICT_CITATIONS", True):
            report = prune_unsupported_citation_claims(report)

        # Token/cost snapshot right after markdown is produced (helps debugging accounting gaps)
        try:
            log_subtopic = _env_bool("LOG_TOKEN_USAGE_SUBTOPIC", False)
            should_log = _env_bool("LOG_TOKEN_USAGE_SNAPSHOT", True) and (
                log_subtopic or self.researcher.report_type != "subtopic_report"
            )
            if should_log:
                total_usage = self.researcher.get_token_usage()
                total_cost = self.researcher.get_costs()
                # Estimate the report's own size in tokens (rough, but good sanity check)
                report_est = estimate_token_usage("", report or "", model=self.researcher.cfg.smart_llm_model)
                snapshot = {
                    "phase": "report_generated",
                    "report_type": self.researcher.report_type,
                    "model": self.researcher.cfg.smart_llm_model,
                    "report_chars": len(report or ""),
                    "report_bytes": len((report or "").encode("utf-8")),
                    "report_estimated_tokens": report_est,
                    "total_token_usage": total_usage,
                    "total_costs": total_cost,
                }
                logger.info(f"TOKEN_USAGE_SNAPSHOT: {json.dumps(snapshot, ensure_ascii=False)}")
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "token_usage_snapshot",
                        json.dumps(snapshot, ensure_ascii=False),
                        self.researcher.websocket,
                        True,
                        snapshot,
                    )
        except Exception as e:
            logger.debug(f"Failed to log token usage snapshot: {e}")

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "report_written",
                f"📝 Report written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return report

    async def write_report_conclusion(self, report_content: str, research_gap: str = "") -> str:
        """
        Write the conclusion for the report.

        Args:
            report_content (str): The content of the report.
            research_gap (str): Identified research gap.

        Returns:
            str: The generated conclusion.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_conclusion",
                f"✍️ Writing conclusion for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        conclusion = await write_conclusion(
            query=self.researcher.query,
            context=report_content,
            config=self.researcher.cfg,
            agent_role_prompt=self.researcher.cfg.agent_role or self.researcher.role,
            cost_callback=self.researcher.add_costs,
            websocket=self.researcher.websocket,
            prompt_family=self.researcher.prompt_family,
            research_gap=research_gap,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "conclusion_written",
                f"📝 Conclusion written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return conclusion

    async def write_introduction(self, research_gap: str = ""):
        """Write the introduction section of the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_introduction",
                f"✍️ Writing introduction for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        introduction = await write_report_introduction(
            query=self.researcher.query,
            context=self.researcher.context,
            agent_role_prompt=self.researcher.cfg.agent_role or self.researcher.role,
            config=self.researcher.cfg,
            websocket=self.researcher.websocket,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            research_gap=research_gap,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "introduction_written",
                f"📝 Introduction written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return introduction

    async def write_research_gap(self):
        """Write the research gap section of the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_research_gap",
                f"🕵️ Writing research gap section for '{self.researcher.query}'...",
                self.researcher.websocket,
            )
            
        from ..actions.report_generation import write_research_gap
        
        gap_section = await write_research_gap(
            query=self.researcher.query,
            context=self.researcher.context,
            config=self.researcher.cfg,
            websocket=self.researcher.websocket,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_gap_written",
                f"📝 Research gap section written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return gap_section

    async def get_subtopics(self):
        """Retrieve subtopics for the research."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_subtopics",
                f"🌳 Generating subtopics for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        subtopics = await construct_subtopics(
            task=self.researcher.query,
            data=self.researcher.context,
            config=self.researcher.cfg,
            subtopics=self.researcher.subtopics,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subtopics_generated",
                f"📊 Subtopics generated for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return subtopics

    async def get_draft_section_titles(self, current_subtopic: str):
        """Generate draft section titles for the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_draft_sections",
                f"📑 Generating draft section titles for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        draft_section_titles = await generate_draft_section_titles(
            query=self.researcher.query,
            current_subtopic=current_subtopic,
            context=self.researcher.context,
            role=self.researcher.cfg.agent_role or self.researcher.role,
            websocket=self.researcher.websocket,
            config=self.researcher.cfg,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "draft_sections_generated",
                f"🗂️ Draft section titles generated for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return draft_section_titles
