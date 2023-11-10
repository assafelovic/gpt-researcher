import json
from typing import Optional
import os
import asyncio
import openai

from gpt_researcher_old.retriever.retriever_agent import RetrieverAgent
from gpt_researcher_old.utils.setup_check import check_agent_setup, check_openai_api_key


class GPTResearcher:
    def __init__(self, **kwargs):
        self.openai_api_key = kwargs.get('openai_api_key', None)
        self.debug_mode = kwargs.get('debug_mode', False)
        self.allow_downloads = kwargs.get('allow_downloads', False)
        self.selenium_web_browser = kwargs.get('selenium_web_browser', 'chrome')
        self.search_api = kwargs.get('search_api', 'tavily')
        self.llm_provider = kwargs.get('llm_provider', 'ChatOpenAI')
        self.fast_llm_model = kwargs.get('fast_llm_model', 'gpt-3.5-turbo-16k')
        self.smart_llm_model = kwargs.get('smart_llm_model', 'gpt-4')
        self.fast_token_limit = kwargs.get('fast_token_limit', 2000)
        self.smart_token_limit = kwargs.get('fast_token_limit', 4000)
        self.browse_chunk_max_length = kwargs.get('browse_chunk_max_length', 8192)
        self.summary_token_limit = kwargs.get('summary_token_limit', 700)
        self.temperature = kwargs.get('temperature', 1.0)
        self.user_agent = kwargs.get('user_agent',
                                     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36')
        self.memory_backend = kwargs.get('memory_backend', 'local')

        self.openai_api_key = self.openai_api_key if self.openai_api_key else os.getenv("OPENAI_API_KEY")

        openai.api_key = self.openai_api_key

        check_agent_setup(self)
        check_openai_api_key(self)

    @classmethod
    def from_json(cls, file_path: str):
        with open(file_path) as f:
            config = json.load(f)
        return cls(**config)

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


# Example
async def main():
    researcher = GPTResearcher.from_json("config.json")

    report, path = await researcher.conduct_research("rank the strongest characters in jujutsu kaisen",
                                                     "research_report")

    print(report)


if __name__ == "__main__":
    asyncio.run(main())
