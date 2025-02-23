from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from gpt_researcher.actions import stream_output
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import curate_sources as rank_sources_prompt

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher

logger = logging.getLogger(__name__)


class SourceCurator:
    """Ranks sources and curates data based on their relevance, credibility and reliability."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher
        self.llm_provider: GenericLLMProvider | None = None

    def _get_llm(self) -> GenericLLMProvider:
        """Get or create an LLM provider instance."""
        if self.llm_provider is None:
            self.llm_provider = GenericLLMProvider(
                self.researcher.cfg.SMART_LLM_PROVIDER,
                model=self.researcher.cfg.SMART_LLM_MODEL,
                temperature=self.researcher.cfg.TEMPERATURE,
            )
        return self.llm_provider

    async def curate_sources(
        self,
        source_data: list,
        max_results: int = 10,
    ) -> list:
        """
        Rank sources based on research data and guidelines.

        Args:
            query: The research query/task
            source_data: List of source documents to rank
            max_results: Maximum number of top sources to return

        Returns:
            str: Ranked list of source URLs with reasoning
        """
        logger.debug(f"\n\nCurating {len(source_data)} sources: {source_data}")
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_plan",
                "⚖️ Evaluating and curating sources by credibility and relevance...",
                self.researcher.websocket,
            )

        response: str = ""
        try:
            provider = self._get_llm()
            response = await provider.get_chat_response(
                messages=[
                    {
                        "role": "system",
                        "content": f"{self.researcher.agent_role}",
                    },
                    {
                        "role": "user",
                        "content": rank_sources_prompt(
                            self.researcher.query, source_data, max_results
                        ),
                    },
                ],
                stream=False,
            )

            if self.researcher.add_costs:
                from gpt_researcher.utils.costs import estimate_llm_cost
                llm_costs = estimate_llm_cost(
                    rank_sources_prompt(self.researcher.query, source_data, max_results),
                    response,
                )
                self.researcher.add_costs(llm_costs)

            curated_sources = json.loads(response)
            logger.info(f"\n\nFinal Curated sources {len(source_data)} sources: {curated_sources}")

            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🏅 Verified and ranked top {len(curated_sources)} most reliable sources",
                    self.researcher.websocket,
                )

            return curated_sources

        except Exception as e:
            logger.exception(f"Error in curate_sources from LLM response: {response}")
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🚫 Source verification failed: {str(e)}",
                    self.researcher.websocket,
                )
            return source_data
