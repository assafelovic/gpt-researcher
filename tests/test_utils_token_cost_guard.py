"""Regression: calculate_cost / format_token_count tolerate None token counts."""

from gpt_researcher.actions.utils import calculate_cost, format_token_count


def test_format_token_count_none_and_string():
    assert format_token_count(None) == "0"
    assert format_token_count("1200") == "1,200"
    assert format_token_count(1200) == "1,200"


def test_calculate_cost_none_tokens():
    assert calculate_cost(None, 0, "gpt-4") == 0.0
    assert calculate_cost(0, None, "gpt-4") == 0.0
    # 1000 + 0 tokens at gpt-4 0.03 / 1k
    assert calculate_cost(1000, 0, "gpt-4") == 0.03


def test_calculate_cost_unknown_model_default():
    assert calculate_cost(10, 10, "unknown-model-xyz") == 0.0001
