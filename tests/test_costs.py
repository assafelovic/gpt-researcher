import unittest

from gpt_researcher.utils.costs import calculate_llm_cost, estimate_llm_cost


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


if __name__ == "__main__":
    unittest.main()

