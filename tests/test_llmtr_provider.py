"""Unit tests for the LLMTR OpenAI-compatible provider.

These tests construct the provider with a dummy key and assert it points at
https://llmtr.com/v1; no network calls are made.
"""
import os
import unittest

from gpt_researcher.llm_provider.generic.base import (
    GenericLLMProvider,
    _SUPPORTED_PROVIDERS as LLM_PROVIDERS,
)

LLMTR_BASE_URL = "https://llmtr.com/v1"


class TestLlmtrProvider(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.get("LLMTR_API_KEY")
        os.environ["LLMTR_API_KEY"] = "test-key"

    def tearDown(self):
        if self._orig is None:
            os.environ.pop("LLMTR_API_KEY", None)
        else:
            os.environ["LLMTR_API_KEY"] = self._orig

    def test_llmtr_is_registered(self):
        self.assertIn("llmtr", LLM_PROVIDERS)

    def test_llm_construction_uses_llmtr_base_url(self):
        provider = GenericLLMProvider.from_provider(
            "llmtr", model="minimax/minimax-m3.1-flash", verbose=False
        )
        self.assertEqual(str(provider.llm.openai_api_base), LLMTR_BASE_URL)

    def test_llm_requires_api_key(self):
        os.environ.pop("LLMTR_API_KEY", None)
        with self.assertRaises(KeyError):
            GenericLLMProvider.from_provider(
                "llmtr", model="minimax/minimax-m3.1-flash", verbose=False
            )


if __name__ == "__main__":
    unittest.main()
