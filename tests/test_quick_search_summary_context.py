"""Regression test: quick_search aggregated summary must include real result data.

All GPT-Researcher search retrievers return records keyed by ``href`` (URL)
and ``body`` (content) — never ``title``/``content``/``url``. The aggregated
summary path in ``quick_search`` built its context with
``result.get('content')`` / ``result.get('url')``, so for real retriever
output every field was empty and the LLM was summarizing
``[1] :  ()`` with no source data. The existing test masked this by feeding
fake ``title``/``content``/``url`` records that no retriever produces.

This test feeds the REAL retriever contract and asserts the body/URL reach
the summarization prompt.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from gpt_researcher.agent import GPTResearcher


class QuickSearchSummaryContextTests(unittest.TestCase):
    @patch("gpt_researcher.agent.get_search_results", new_callable=AsyncMock)
    @patch("gpt_researcher.agent.create_chat_completion", new_callable=AsyncMock)
    @patch("langchain_openai.OpenAIEmbeddings")
    def test_summary_prompt_contains_real_retriever_fields(
        self, _mock_embeddings, mock_create_chat, mock_search
    ):
        # Real retriever output shape: href + body.
        mock_search.return_value = [
            {"href": "https://example.com/a", "body": "Alpha finding about rust."},
            {"href": "https://example.com/b", "body": "Beta finding about async."},
        ]
        mock_create_chat.return_value = "summary"

        researcher = GPTResearcher(query="rust async")
        captured = {}

        def fake_quick_prompt(query, context):
            captured["context"] = context
            return f"PROMPT for {query}\n{context}"

        researcher.prompt_family.generate_quick_summary_prompt = fake_quick_prompt

        result = asyncio.run(
            researcher.quick_search("rust async", aggregated_summary=True)
        )

        self.assertEqual(result, "summary")
        ctx = captured["context"]
        # The bug produced an empty context ("[1] :  ()"); these must appear now.
        self.assertIn("Alpha finding about rust.", ctx)
        self.assertIn("Beta finding about async.", ctx)
        self.assertIn("https://example.com/a", ctx)
        self.assertIn("https://example.com/b", ctx)


if __name__ == "__main__":
    unittest.main()
