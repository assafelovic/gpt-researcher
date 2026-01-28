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

if __name__ == '__main__':
    unittest.main()
