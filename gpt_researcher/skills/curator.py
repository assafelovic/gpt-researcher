"""Source curator skill for GPT Researcher.

This module provides the SourceCurator class that evaluates and ranks
research sources based on relevance, credibility, and reliability.
"""

from typing import Dict, List, Optional

from ..actions import stream_output
from ..utils.json_parsing import parse_llm_json_response
from ..utils.llm import create_chat_completion


def _normalize_curated_sources(payload: object) -> list | None:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload

    if isinstance(payload, dict):
        for key in ("sources", "curated_sources", "results"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value

    if isinstance(payload, str):
        parsed = parse_llm_json_response(payload, expected_kind="any")
        if parsed is not None:
            normalized = _normalize_curated_sources(parsed)
            if normalized is not None:
                return normalized

    return None


class SourceCurator:
    """Ranks and curates sources based on relevance, credibility and reliability.

    This class uses LLM-based evaluation to assess research sources
    and select the most appropriate ones for report generation.

    Attributes:
        researcher: The parent GPTResearcher instance.
    """

    def __init__(self, researcher):
        """Initialize the SourceCurator.

        Args:
            researcher: The GPTResearcher instance that owns this curator.
        """
        self.researcher = researcher

    async def curate_sources(
        self,
        source_data: List,
        max_results: int = 10,
    ) -> List:
        """
        Rank sources based on research data and guidelines.

        Args:
            query: The research query/task
            source_data: List of source documents to rank
            max_results: Maximum number of top sources to return

        Returns:
            str: Ranked list of source URLs with reasoning
        """
        print(f"\n\nCurating {len(source_data)} sources: {source_data}")
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_plan",
                f"⚖️ Evaluating and curating sources by credibility and relevance...",
                self.researcher.websocket,
            )

        response = ""
        try:
            response = await create_chat_completion(
                model=self.researcher.cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": f"{self.researcher.role}"},
                    {"role": "user", "content": self.researcher.prompt_family.curate_sources(
                        self.researcher.query, source_data, max_results)},
                ],
                temperature=0.2,
                max_tokens=8000,
                llm_provider=self.researcher.cfg.smart_llm_provider,
                llm_kwargs=self.researcher.cfg.llm_kwargs,
                cost_callback=self.researcher.add_costs,
            )

            curated_sources = _normalize_curated_sources(response)
            if curated_sources is None:
                raise ValueError("LLM did not return a valid list of source objects")
            print(f"\n\nFinal Curated sources {len(source_data)} sources: {curated_sources}")

            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🏅 Verified and ranked top {len(curated_sources)} most reliable sources",
                    self.researcher.websocket,
                )

            return curated_sources

        except Exception as e:
            print(f"Error in curate_sources from LLM response: {response}")
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🚫 Source verification failed: {str(e)}",
                    self.researcher.websocket,
                )
            return source_data
