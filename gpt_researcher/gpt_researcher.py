from typing import Optional
import os

import openai

from gpt_researcher.context.research_context import ResearchContext
from gpt_researcher.utils.setup_check import check_agent_setup, check_openai_api_key


class GPTResearcher:
    def __init__(
            self,
            openai_api_key: Optional[str] = None,
            debug_mode: bool = False,
            allow_downloads: bool = False,
            selenium_web_browser: str = "chrome",
            search_api: str = "tavily",
            llm_provider: str = "ChatOpenAI",
            fast_llm_model: str = "gpt-3.5-turbo-16k",
            smart_llm_model: str = "gpt-4",
            fast_token_limit: int = 2000,
            smart_token_limit: int = 4000,
            browse_chunk_max_length: int = 8192,
            summary_token_limit: int = 700,
            temperature: float = 1.0,
            user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            memory_backend: str = "local"
    ):
        self.debug_mode = debug_mode
        self.allow_downloads = allow_downloads
        self.selenium_web_browser = selenium_web_browser
        self.search_api = search_api
        self.llm_provider = llm_provider
        self.fast_llm_model = fast_llm_model
        self.smart_llm_model = smart_llm_model
        self.fast_token_limit = fast_token_limit
        self.smart_token_limit = smart_token_limit
        self.browse_chunk_max_length = browse_chunk_max_length
        self.summary_token_limit = summary_token_limit
        self.temperature = temperature
        self.user_agent = user_agent
        self.memory_backend = memory_backend

        self.openai_api_key = openai_api_key if openai_api_key else os.getenv("OPENAI_API_KEY")

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
        research_context = ResearchContext(
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
