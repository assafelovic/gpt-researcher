import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from gpt_researcher.agent import GPTResearcher
import os

class TestQuickSearch(unittest.TestCase):

    @patch('gpt_researcher.agent.get_search_results', new_callable=AsyncMock)
    @patch('gpt_researcher.agent.create_chat_completion', new_callable=AsyncMock)
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_quick_search_no_summary(self, mock_embeddings, mock_create_chat, mock_search):
        # Setup mocks
        mock_search.return_value = [{'title': 'Test Result', 'content': 'Content', 'url': 'http://test.com'}]

        # Initialize researcher with dummy config to avoid API key issues
        researcher = GPTResearcher(query="test query")

        # Run quick_search without summary
        results = asyncio.run(researcher.quick_search("test query", aggregated_summary=False))

        # Verify
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Result')
        mock_create_chat.assert_not_called()

    @patch('gpt_researcher.agent.get_search_results', new_callable=AsyncMock)
    @patch('gpt_researcher.agent.create_chat_completion', new_callable=AsyncMock)
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_quick_search_with_summary(self, mock_embeddings, mock_create_chat, mock_search):
        # Setup mocks
        mock_search.return_value = [{'title': 'Test Result', 'content': 'Content', 'url': 'http://test.com'}]
        mock_create_chat.return_value = "This is a summary."

        # Initialize researcher
        researcher = GPTResearcher(query="test query")

        # Run quick_search with summary
        summary = asyncio.run(researcher.quick_search("test query", aggregated_summary=True))

        # Verify
        self.assertEqual(summary, "This is a summary.")
        mock_create_chat.assert_called_once()

    @patch('gpt_researcher.agent.get_search_results', new_callable=AsyncMock)
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_quick_search_all_retrievers_merges_and_dedups(self, mock_embeddings, mock_search):
        # Two retrievers return overlapping results; the shared URL should appear once.
        mock_search.side_effect = [
            [
                {'title': 'A', 'body': 'a', 'href': 'http://dup.com'},
                {'title': 'B', 'body': 'b', 'href': 'http://b.com'},
            ],
            [
                {'title': 'A dup', 'body': 'a2', 'href': 'http://dup.com'},
                {'title': 'C', 'body': 'c', 'href': 'http://c.com'},
            ],
        ]

        researcher = GPTResearcher(query="test query")
        # Force two retrievers regardless of env configuration.
        researcher.retrievers = [MagicMock(__name__='R1'), MagicMock(__name__='R2')]

        results = asyncio.run(
            researcher.quick_search("test query", all_retrievers=True)
        )

        self.assertEqual(mock_search.await_count, 2)
        hrefs = [r.get('href') for r in results]
        self.assertEqual(hrefs.count('http://dup.com'), 1)
        self.assertEqual(len(results), 3)

    @patch('gpt_researcher.agent.get_search_results', new_callable=AsyncMock)
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_quick_search_all_retrievers_skips_failing_retriever(self, mock_embeddings, mock_search):
        # One retriever raises; results from the healthy one are still returned.
        mock_search.side_effect = [
            RuntimeError("provider down"),
            [{'title': 'B', 'body': 'b', 'href': 'http://b.com'}],
        ]

        researcher = GPTResearcher(query="test query")
        researcher.retrievers = [MagicMock(__name__='R1'), MagicMock(__name__='R2')]

        results = asyncio.run(
            researcher.quick_search("test query", all_retrievers=True)
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['href'], 'http://b.com')

    @patch('gpt_researcher.agent.get_search_results', new_callable=AsyncMock)
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_quick_search_single_retriever_ignores_all_flag(self, mock_embeddings, mock_search):
        # With only one retriever, all_retrievers=True falls back to the primary path.
        mock_search.return_value = [{'title': 'Test', 'body': 'x', 'href': 'http://test.com'}]

        researcher = GPTResearcher(query="test query")
        researcher.retrievers = [MagicMock(__name__='R1')]

        results = asyncio.run(
            researcher.quick_search("test query", all_retrievers=True)
        )

        self.assertEqual(mock_search.await_count, 1)
        self.assertEqual(len(results), 1)


if __name__ == '__main__':
    unittest.main()
