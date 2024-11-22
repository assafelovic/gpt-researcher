from typing import Dict, Optional, List
import json
from ..config.config import Config
from ..utils.llm import create_chat_completion
from ..prompts import rank_sources as rank_sources_prompt
from ..actions import stream_output


class SourceRanker:
    """Ranks sources based on their relevance, credibility and reliability."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def rank_sources(
        self,
        query: str,
        source_data: List,
        agent_role_prompt: str = "",
        max_results: int = 5,
    ) -> str:
        """
        Rank sources based on research data and guidelines.
        
        Args:
            query: The research query/task
            source_data: List of source documents to rank
            agent_role_prompt: Optional role prompt for the agent
            max_results: Maximum number of top sources to return
            websocket: Optional websocket for streaming output
            cost_callback: Optional callback for tracking costs
            config: Configuration object
            
        Returns:
            str: Ranked list of source URLs with reasoning
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "ranking_sources", 
                f"⚖️ Evaluating source credibility and relevance for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        try:
            ranked_source_urls = await create_chat_completion(
                model=self.researcher.cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": f"{agent_role_prompt}"},
                    {"role": "user", "content": rank_sources_prompt(
                        query, source_data, max_results)},
                ],
                temperature=self.researcher.cfg.temperature,
                llm_provider=self.researcher.cfg.smart_llm_provider,
                stream=True,
                websocket=self.researcher.websocket,
                max_tokens=self.researcher.cfg.smart_token_limit,
                llm_kwargs=self.researcher.cfg.llm_kwargs,
                cost_callback=self.researcher.add_costs,
            )

            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "ranking_complete",
                    f"🏅 Verified and ranked top {max_results} most reliable sources",
                    self.researcher.websocket,
                )

            return ranked_source_urls

        except Exception as e:
            if self.researcher.verbose:
                await stream_output(
                    "logs", 
                    "ranking_error",
                    f"🚫 Source verification failed: {str(e)}",
                    self.researcher.websocket,
                )
            raise
