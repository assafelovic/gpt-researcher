from typing import Optional
import os
import configparser

import openai

from gpt_researcher.retriever.retriever_agent import RetrieverAgent
from gpt_researcher.utils.setup_check import check_agent_setup, check_openai_api_key


class GPTResearcher:
    def __init__(self, **kwargs):
        default_kwargs = {
            'openai_api_key': None,
            'debug_mode': False,
            'allow_downloads': False,
            'selenium_web_browser': 'chrome',
            'search_api': 'tavily',
            'llm_provider': 'ChatOpenAI',
            'fast_llm_model': 'gpt-3.5-turbo-16k',
            'smart_llm_model': 'gpt-4',
            'fast_token_limit': 2000,
            'smart_token_limit': 4000,
            'browse_chunk_max_length': 8192,
            'summary_token_limit': 700,
            'temperature': 1.0,
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'memory_backend': 'local'
        }

        default_kwargs.update(kwargs)

        for key, value in default_kwargs.items():
            setattr(self, key, value)

        self.openai_api_key = self.openai_api_key if self.openai_api_key else os.getenv("OPENAI_API_KEY")

        # Initialize the OpenAI API client
        openai.api_key = self.openai_api_key

        check_agent_setup(self)
        check_openai_api_key(self)

    def set_fast_llm_model(self, value: str) -> None:
        """Set the fast LLM model value."""
        self.fast_llm_model = value

    def set_smart_llm_model(self, value: str) -> None:
        """Set the smart LLM model value."""
        self.smart_llm_model = value

    def set_fast_token_limit(self, value: int) -> None:
        """Set the fast token limit value."""
        self.fast_token_limit = value

    def set_smart_token_limit(self, value: int) -> None:
        """Set the smart token limit value."""
        self.smart_token_limit = value

    def set_browse_chunk_max_length(self, value: int) -> None:
        """Set the browse_website command chunk max length value."""
        self.browse_chunk_max_length = value

    def set_openai_api_key(self, value: str) -> None:
        """Set the OpenAI API key value."""
        self.openai_api_key = value

    def set_debug_mode(self, value: bool) -> None:
        """Set the debug mode value."""
        self.debug_mode = value

    async def conduct_research(self, question, report_type, websocket=None):
        research_context = RetrieverAgent(
            question,
            self,
            websocket=websocket,
        )
        await research_context.prepare_directories()
        search_queries = await research_context.create_search_queries()
        for query in search_queries:
            research_result = await research_context.run_search_summary(query)
            research_context.research_summary += f"{research_result}\n\n"

        report, path = await research_context.write_report(report_type, websocket)

        return report, path


import asyncio


async def main():
    researcher = GPTResearcher()

    report, path = await researcher.conduct_research("rank the strongest characters in jujutsu kaisen", "research_report")

    print(report)


if __name__ == "__main__":
    asyncio.run(main())
