"""Unit tests for the API Route provider (LLM + embeddings).

These tests construct the provider objects with a dummy key and assert they
point at the API Route gateway endpoint; no network calls are made.
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

API_ROUTE_BASE_URL = "https://global.api-route.com/v1"


class TestApiRouteProvider(unittest.TestCase):
    def setUp(self):
        self._orig = {k: os.environ.get(k) for k in ("API_ROUTE_API_KEY", "API_ROUTE_BASE_URL")}
        os.environ["API_ROUTE_API_KEY"] = "test-key"
        os.environ.pop("API_ROUTE_BASE_URL", None)

    def tearDown(self):
        for k, v in self._orig.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_api_route_registered_for_llm_and_embeddings(self):
        self.assertIn("api-route", LLM_PROVIDERS)
        self.assertIn("api-route", EMBEDDING_PROVIDERS)

    def test_llm_construction_uses_api_route_base_url(self):
        provider = GenericLLMProvider.from_provider(
            "api-route", model="claude-sonnet-4-5", verbose=False
        )
        self.assertEqual(str(provider.llm.openai_api_base), API_ROUTE_BASE_URL)

    def test_embeddings_construction_uses_api_route_base_url(self):
        embeddings = Memory("api-route", "text-embedding-3-small").get_embeddings()
        self.assertEqual(str(embeddings.openai_api_base), API_ROUTE_BASE_URL)

    def test_base_url_can_be_overridden(self):
        os.environ["API_ROUTE_BASE_URL"] = "https://custom.api-route.com/v1"
        provider = GenericLLMProvider.from_provider(
            "api-route", model="gpt-4o", verbose=False
        )
        self.assertEqual(
            str(provider.llm.openai_api_base), "https://custom.api-route.com/v1"
        )

    def test_llm_requires_api_key(self):
        os.environ.pop("API_ROUTE_API_KEY", None)
        with self.assertRaises(KeyError):
            GenericLLMProvider.from_provider(
                "api-route", model="claude-sonnet-4-5", verbose=False
            )


if __name__ == "__main__":
    unittest.main()
