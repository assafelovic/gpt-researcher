import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.utils.costs import (
    calculate_llm_cost,
    estimate_llm_cost,
    estimate_token_usage,
    estimate_embedding_cost,
    _resolve_pricing,
    INPUT_COST_PER_TOKEN,
    OUTPUT_COST_PER_TOKEN
)

def test_resolve_pricing_with_env_config():
    """Test pricing resolution from environment variable."""
    env_data = '{"gpt-4o": {"input": 5.0, "output": 15.0}, "gpt-3.5": {"input": 0.5, "output": 1.5}}'
    with patch.dict(os.environ, {"MODEL_PRICING_PER_1M_JSON": env_data}):
        pricing = _resolve_pricing("gpt-4o")
        assert pricing is not None
        assert pricing["input"] == 5.0
        assert pricing["output"] == 15.0

        # Test fuzzy matching
        pricing_fuzzy = _resolve_pricing("openai/gpt-4o")
        assert pricing_fuzzy is not None
        assert pricing_fuzzy["input"] == 5.0

def test_calculate_llm_cost_with_config():
    """Test cost calculation with valid pricing config."""
    env_data = '{"gpt-4": {"input": 30.0, "output": 60.0}}'
    with patch.dict(os.environ, {"MODEL_PRICING_PER_1M_JSON": env_data}):
        cost = calculate_llm_cost(1_000_000, 1_000_000, "gpt-4")
        # 1M tokens * $30/1M + 1M tokens * $60/1M = $90
        assert cost == 90.0

def test_calculate_llm_cost_fallback():
    """Test fallback when no pricing config is present."""
    # Ensure environment is clean
    with patch.dict(os.environ, {}, clear=True):
        cost = calculate_llm_cost(1000, 1000, "unknown-model")
        # Fallback rates
        expected = 1000 * INPUT_COST_PER_TOKEN + 1000 * OUTPUT_COST_PER_TOKEN
        assert cost == expected

def test_estimate_token_usage():
    """Test token estimation (simple assertion, exact count depends on tokenizer)."""
    usage = estimate_token_usage("hello", "world", model="gpt-4")
    assert usage["prompt_tokens"] > 0
    assert usage["completion_tokens"] > 0
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

def test_estimate_llm_cost_integration():
    """Test full estimation logic."""
    env_data = '{"gpt-4": {"input": 10.0, "output": 10.0}}'
    with patch.dict(os.environ, {"MODEL_PRICING_PER_1M_JSON": env_data}):
        # Mocking estimate_token_usage to check math logic independent of tokenizer
        with patch("gpt_researcher.utils.costs.estimate_token_usage") as mock_est:
            mock_est.return_value = {"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000}
            
            cost = estimate_llm_cost("in", "out", model="gpt-4")
            
            # 1000/1M * 10 + 1000/1M * 10 = 0.01 + 0.01 = 0.02
            assert abs(cost - 0.02) < 1e-6

def test_estimate_embedding_cost():
    """Test embedding cost calculation."""
    docs = ["doc1", "doc2"]
    cost = estimate_embedding_cost("text-embedding-3-small", docs)
    assert cost > 0
