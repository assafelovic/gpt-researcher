"""Source curator skill for GPT Researcher.

This module provides the SourceCurator class that evaluates and ranks
research sources based on relevance, credibility, and reliability.
"""

from typing import Dict, List, Optional

import json_repair
from langchain_core.utils.json import parse_json_markdown

from ..actions import stream_output
from ..config.config import Config
from ..utils.llm import create_chat_completion


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

            # LLMs frequently wrap the JSON in ```json fences or add prose
            # despite the prompt's instructions, which plain json.loads cannot
            # parse. Recover the payload the same way the rest of the codebase
            # does (see actions/query_processing.py, multi_agents/agents/utils/
            # llms.py) so a well-formed-but-fenced response is not discarded.
            curated_sources = parse_json_markdown(response, parser=json_repair.loads)
            # json_repair never raises: on unusable output it returns "" or a
            # dict rather than a list. Guard so such a result still falls back
            # to the uncurated sources below instead of emptying the context.
            if not isinstance(curated_sources, list):
                raise ValueError(
                    f"expected a JSON list of sources, got "
                    f"{type(curated_sources).__name__}"
                )
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
