from __future__ import annotations

import json
import logging

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions import stream_output
from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher

logger = logging.getLogger(__name__)

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

        # Check if source_data is empty or invalid, return immediately if so
        if not source_data:
            logger.warning("No source data provided to curate_sources")
            return []

        # If source_data is a string list, convert to list of dicts with raw_content
        if isinstance(source_data, list) and len(source_data) > 0 and isinstance(source_data[0], str):
            source_data = [{"raw_content": content, "url": "", "title": ""} for content in source_data]
            logger.info("Converted string list to dictionary list with raw_content key")

        # Check if source_data elements have the required keys
        required_keys: list[str] = ["raw_content"]
        if source_data and isinstance(source_data, list) and isinstance(source_data[0], dict):
            # Check if first item has the required keys
            if not all(k in source_data[0] for k in required_keys):
                logger.warning(f"Source data is missing required keys: {required_keys}")
                # Add missing keys with empty values
                for item in source_data:
                    for key in required_keys:
                        if key not in item:
                            item[key] = ""
                logger.info(f"Added missing keys to source data: {required_keys}")

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

            # CRITICAL FIX: Ensure the curated sources have the necessary keys
            # The 'raw_content' key is required by SearchAPIRetriever
            for source in curated_sources:
                if "raw_content" not in source:
                    # If raw_content is missing, try to extract it from other fields
                    # or set it to the most appropriate available content field
                    for key in ["content", "text", "body", "description"]:
                        if key in source and source[key]:
                            source["raw_content"] = source[key]
                            break
                    # If still not found, add an empty string to prevent errors
                    if "raw_content" not in source:
                        source["raw_content"] = ""
                        logger.warning(f"Added empty raw_content to source: {source}")

            # Filter out sources with empty raw_content to prevent downstream errors
            non_empty_sources: list[dict[str, Any]] = [s for s in curated_sources if s.get("raw_content", "").strip()]
            if len(non_empty_sources) < len(curated_sources):
                logger.warning(f"Filtered out {len(curated_sources) - len(non_empty_sources)} sources with empty content")

            # If all sources were filtered out (all had empty content), return original source_data
            if not non_empty_sources and source_data:
                logger.warning("All curated sources had empty content, returning original source data")
                return source_data

            curated_sources = non_empty_sources or []

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
