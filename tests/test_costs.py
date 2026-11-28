import sys
import unittest
from unittest import mock

import litellm

from gpt_researcher.utils.costs import (
    EMBEDDING_COST,
    INPUT_COST_PER_TOKEN,
    OUTPUT_COST_PER_TOKEN,
    calculate_llm_cost,
    estimate_embedding_cost,
    estimate_llm_cost,
)


class TestCosts(unittest.TestCase):
    def test_calculate_llm_cost_uses_anthropic_api_usage(self):
        cost = calculate_llm_cost(
            llm_provider="anthropic",
            model="claude-sonnet-4-6",
            input_content="ignored",
            output_content="ignored",
            response_metadata={
                "model": "claude-sonnet-4-6",
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                },
            },
        )

        self.assertAlmostEqual(cost, 0.0105)

    def test_calculate_llm_cost_supports_dated_anthropic_model_names(self):
        cost = calculate_llm_cost(
            llm_provider="anthropic",
            model="claude-haiku-4-5-20251001",
            input_content="ignored",
            output_content="ignored",
            response_metadata={
                "usage": {
                    "input_tokens": 2000,
                    "output_tokens": 1000,
                },
            },
        )

        self.assertAlmostEqual(cost, 0.007)

    def test_calculate_llm_cost_prefers_native_anthropic_usage(self):
        cost = calculate_llm_cost(
            llm_provider="anthropic",
            model="claude-opus-4-7",
            input_content="ignored",
            output_content="ignored",
            response_metadata={
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                },
            },
            usage_metadata={
                "input_tokens": 999999,
                "output_tokens": 999999,
            },
        )

        self.assertAlmostEqual(cost, 0.00175)

    def test_calculate_llm_cost_falls_back_without_usage(self):
        fallback_cost = calculate_llm_cost(
            llm_provider="anthropic",
            model="claude-sonnet-4-6",
            input_content="hello",
            output_content="world",
        )

        self.assertEqual(fallback_cost, estimate_llm_cost("hello", "world"))


class TestEmbeddingCost(unittest.TestCase):
    def test_estimate_embedding_cost_openai_model(self):
        cost = estimate_embedding_cost(
            model="text-embedding-3-small",
            docs=["hello world", "another document"],
        )
        self.assertGreater(cost, 0.0)

    def test_estimate_embedding_cost_non_openai_model_does_not_raise(self):
        # Non-OpenAI embedding models (Ollama, Cohere, Nomic, HuggingFace, ...)
        # are not known to tiktoken and used to raise KeyError, aborting cost
        # tracking mid-research. The estimator must degrade gracefully instead.
        cost = estimate_embedding_cost(
            model="nomic-embed-text",
            docs=["hello world", "another document"],
        )
        self.assertGreater(cost, 0.0)

    def test_estimate_embedding_cost_empty_docs(self):
        self.assertEqual(
            estimate_embedding_cost(model="nomic-embed-text", docs=[]),
            0.0,
        )


class TestOpenAICachedInputPricing(unittest.TestCase):
    """Covers #2065: cached OpenAI input tokens were billed at full price
    because calculate_llm_cost never read input_token_details.cache_read
    from LangChain's standardized usage_metadata."""

    def test_no_cache_details_unaffected(self):
        cost = calculate_llm_cost(
            llm_provider="openai",
            model="gpt-4o",
            input_content="",
            output_content="",
            usage_metadata={"input_tokens": 5000, "output_tokens": 200},
        )
        self.assertAlmostEqual(cost, 0.0145)

    def test_partial_cache_hit_is_discounted(self):
        # Exact repro from issue #2065: 4500 of 5000 input tokens hit the
        # cache and must be billed at the discounted rate, not full price.
        cost = calculate_llm_cost(
            llm_provider="openai",
            model="gpt-4o",
            input_content="",
            output_content="",
            usage_metadata={
                "input_tokens": 5000,
                "output_tokens": 200,
                "input_token_details": {"cache_read": 4500},
            },
        )
        self.assertLess(cost, 0.0145)
        self.assertAlmostEqual(cost, 0.008875)

    def test_explicit_zero_cache_read_matches_baseline(self):
        cost = calculate_llm_cost(
            llm_provider="openai",
            model="gpt-4o",
            input_content="",
            output_content="",
            usage_metadata={
                "input_tokens": 5000,
                "output_tokens": 200,
                "input_token_details": {"cache_read": 0},
            },
        )
        self.assertAlmostEqual(cost, 0.0145)

    def test_fully_cached_input(self):
        cost = calculate_llm_cost(
            llm_provider="openai",
            model="gpt-4o",
            input_content="",
            output_content="",
            usage_metadata={
                "input_tokens": 5000,
                "output_tokens": 200,
                "input_token_details": {"cache_read": 5000},
            },
        )
        expected = (5000 * 2.5 * 0.5 + 200 * 10.0) / 1_000_000
        self.assertAlmostEqual(cost, expected)

    def test_unknown_model_fallback_still_applies_cache_discount(self):
        cost = calculate_llm_cost(
            llm_provider="openai",
            model="some-future-model",
            input_content="",
            output_content="",
            usage_metadata={
                "input_tokens": 1000,
                "output_tokens": 100,
                "input_token_details": {"cache_read": 500},
            },
        )
        expected = (
            500 * INPUT_COST_PER_TOKEN * 0.5
            + 500 * INPUT_COST_PER_TOKEN
            + 100 * OUTPUT_COST_PER_TOKEN
        )
        self.assertAlmostEqual(cost, expected, places=12)


if __name__ == "__main__":
    unittest.main()


class TestProviderPricing(unittest.TestCase):
    """Models outside the OpenAI table and Anthropic rules used to be billed at
    the flat $5/$15 per 1M fallback. Mapped providers are now priced from
    litellm's model price table."""

    def _flat(self, input_tokens, output_tokens):
        return input_tokens * INPUT_COST_PER_TOKEN + output_tokens * OUTPUT_COST_PER_TOKEN

    def _cost(self, provider, model, input_tokens, output_tokens, cache_read=0):
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        if cache_read:
            usage["input_token_details"] = {"cache_read": cache_read}
        return calculate_llm_cost(
            llm_provider=provider,
            model=model,
            input_content="",
            output_content="",
            usage_metadata=usage,
        )

    def test_provider_models_use_litellm_prices(self):
        cases = (
            ("google_genai", "gemini", "gemini-2.5-flash"),
            ("deepseek", "deepseek", "deepseek-chat"),
            ("mistralai", "mistral", "mistral-large-latest"),
        )
        for provider, litellm_provider, model in cases:
            with self.subTest(provider=provider, model=model):
                info = litellm.get_model_info(model, custom_llm_provider=litellm_provider)
                expected = (
                    10_000 * info["input_cost_per_token"]
                    + 2_000 * info["output_cost_per_token"]
                )
                cost = self._cost(provider, model, 10_000, 2_000)
                self.assertAlmostEqual(cost, expected, places=12)
                self.assertNotAlmostEqual(cost, self._flat(10_000, 2_000), places=12)

    def test_cached_input_uses_the_cache_read_price(self):
        info = litellm.get_model_info("gemini-2.5-flash", custom_llm_provider="gemini")
        expected = (
            500 * info["input_cost_per_token"]
            + 4_500 * info["cache_read_input_token_cost"]
            + 200 * info["output_cost_per_token"]
        )
        cost = self._cost("google_genai", "gemini-2.5-flash", 5_000, 200, cache_read=4_500)
        self.assertAlmostEqual(cost, expected, places=12)

    def test_anthropic_rules_still_win(self):
        # calculate_anthropic_cost (cache writes at 1.25x) is used before litellm.
        cost = calculate_llm_cost(
            llm_provider="anthropic",
            model="claude-sonnet-4-6",
            input_content="",
            output_content="",
            response_metadata={
                "model": "claude-sonnet-4-6",
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "cache_creation_input_tokens": 1000,
                },
            },
        )
        self.assertAlmostEqual(cost, (1000 * 3 + 1000 * 3 * 1.25 + 500 * 15) / 1_000_000)

    def test_unmapped_provider_keeps_flat_fallback(self):
        self.assertAlmostEqual(self._cost("ollama", "llama3", 1000, 100), self._flat(1000, 100), places=12)

    def test_model_litellm_does_not_know_keeps_flat_fallback(self):
        cost = self._cost("google_genai", "not-a-real-model-xyz", 1000, 100)
        self.assertAlmostEqual(cost, self._flat(1000, 100), places=12)

    def test_litellm_unavailable_keeps_flat_fallback(self):
        with mock.patch.dict(sys.modules, {"litellm": None}):
            cost = self._cost("google_genai", "gemini-2.5-flash", 1000, 100)
        self.assertAlmostEqual(cost, self._flat(1000, 100), places=12)

    def test_openai_provider_keeps_openai_table(self):
        self.assertAlmostEqual(self._cost("openai", "gpt-4o", 5000, 200), 0.0145)
