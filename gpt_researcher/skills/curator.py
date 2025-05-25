from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions import stream_output
from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class SourceCurator:
    """Ranks sources and curates data based on their relevance, credibility and reliability."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher
        self.cfg: Config = researcher.cfg

    async def curate_sources(
        self,
        source_data: list,
        max_results: int = 10,
    ) -> list:
        """Rank sources based on research data and guidelines.

        Args:
            query: The research query/task
            source_data: List of source documents to rank
            max_results: Maximum number of top sources to return

        Returns:
            list: Ranked list of source URLs with reasoning
        """
        print(f"\n\nCurating {len(source_data)} sources: {source_data}")
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_plan",
                "⚖️ Evaluating and curating sources by credibility and relevance...",
                self.researcher.websocket,
            )

        response: str = ""
        try:
            response = await create_chat_completion(
                model=self.researcher.cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": f"{self.researcher.role}"},
                    {"role": "user", "content": self.researcher.prompt_family.curate_sources(self.researcher.query, source_data, max_results)},
                ],
                temperature=0.2,
                max_tokens=8000,
                llm_provider=self.researcher.cfg.smart_llm_provider,
                llm_kwargs=self.researcher.cfg.llm_kwargs,
                cost_callback=self.researcher.add_costs,
                cfg=self.researcher.cfg,
            )

            # Extract JSON from markdown code blocks if present
            from gpt_researcher.utils.llm import extract_json_from_markdown
            clean_response = extract_json_from_markdown(response)

            # Validate the response before parsing
            from gpt_researcher.utils.llm import validate_llm_response
            validated_response = validate_llm_response(clean_response, "Source curation")

            curated_sources: list[dict[str, Any]] = json.loads(validated_response)
            print(f"\n\nFinal Curated sources {len(curated_sources)} sources: {curated_sources}")

            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🏅 Verified and ranked top {len(curated_sources)} most reliable sources",
                    self.researcher.websocket,
                )

            return curated_sources

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error in curate_sources from LLM response: {response}! {e.__class__.__name__}: {e}")
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🚫 Source verification failed: {response}! {e.__class__.__name__}: {e}",
                    self.researcher.websocket,
                )
            # Return original sources instead of failing completely
            return source_data
        except Exception as e:
            print(f"Unexpected error in curate_sources: {e.__class__.__name__}: {e}")
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🚫 Source curation failed unexpectedly: {e.__class__.__name__}: {e}",
                    self.researcher.websocket,
                )
            # Return original sources instead of failing completely
            return source_data
