"""Unit tests for the Nebius Token Factory provider (LLM + embeddings).

These tests construct the provider objects with a dummy key and assert they
point at the Token Factory endpoint; no network calls are made.
"""
import os
import unittest

from gpt_researcher.llm_provider.generic.base import (
    GenericLLMProvider,
    _SUPPORTED_PROVIDERS as LLM_PROVIDERS,
)
from gpt_researcher.memory.embeddings import (
    Memory,
    _SUPPORTED_PROVIDERS as EMBEDDING_PROVIDERS,
)

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"


class TestNebiusProvider(unittest.TestCase):
    def setUp(self):
        self._orig = {k: os.environ.get(k) for k in ("NEBIUS_API_KEY", "NEBIUS_BASE_URL")}
        os.environ["NEBIUS_API_KEY"] = "test-key"
        os.environ.pop("NEBIUS_BASE_URL", None)

    def tearDown(self):
        for k, v in self._orig.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_nebius_registered_for_llm_and_embeddings(self):
        self.assertIn("nebius", LLM_PROVIDERS)
        self.assertIn("nebius", EMBEDDING_PROVIDERS)

    def test_llm_construction_uses_token_factory_base_url(self):
        provider = GenericLLMProvider.from_provider(
            "nebius", model="Qwen/Qwen3-235B-A22B-Instruct-2507", verbose=False
        )
        self.assertEqual(str(provider.llm.openai_api_base), NEBIUS_BASE_URL)

    def test_embeddings_construction_uses_token_factory_base_url(self):
        embeddings = Memory("nebius", "Qwen/Qwen3-Embedding-8B").get_embeddings()
        self.assertEqual(str(embeddings.openai_api_base), NEBIUS_BASE_URL)

    def test_base_url_can_be_overridden(self):
        os.environ["NEBIUS_BASE_URL"] = "https://self-hosted.example.com/v1"
        provider = GenericLLMProvider.from_provider(
            "nebius", model="Qwen/Qwen3-32B", verbose=False
        )
        self.assertEqual(
            str(provider.llm.openai_api_base), "https://self-hosted.example.com/v1"
        )

    def test_llm_requires_api_key(self):
        os.environ.pop("NEBIUS_API_KEY", None)
        with self.assertRaises(KeyError):
            GenericLLMProvider.from_provider(
                "nebius", model="Qwen/Qwen3-32B", verbose=False
            )


if __name__ == "__main__":
    unittest.main()
