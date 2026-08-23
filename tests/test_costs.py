import unittest

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