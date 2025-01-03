import pytest
from gpt_researcher.config.config import Config
import json
import os

@pytest.fixture
def model_config_file(tmp_path):
    """Create config files for different LLM models"""
    config_path = tmp_path / "model_config.json"
    config = {
        "FAST_LLM": "openai:gpt-3.5-turbo",
        "SMART_LLM": "google_genai:gemini-pro",
        "STRATEGIC_LLM": "anthropic:claude-2",
        "FAST_LLM_TEMPERATURE": 0.3,
        "SMART_LLM_TEMPERATURE": 0.7,
        "STRATEGIC_LLM_TEMPERATURE": 0.9,
        "EMBEDDING": "google_genai:embedding-001",
        "RETRIEVER": "tavily"
    }
    config_path.write_text(json.dumps(config))
    return str(config_path)

@pytest.mark.asyncio
async def test_model_specific_temperatures(model_config_file):
    """Test that different models use their specific temperatures"""
    cfg = Config(config_path=model_config_file)
    
    assert cfg.fast_llm_model == "gpt-3.5-turbo"
    assert cfg.fast_llm_provider == "openai"
    assert cfg.fast_llm_temperature == 0.3
    
    assert cfg.smart_llm_model == "gemini-pro"
    assert cfg.smart_llm_provider == "google_genai"
    assert cfg.smart_llm_temperature == 0.7
    
    assert cfg.strategic_llm_model == "claude-2"
    assert cfg.strategic_llm_provider == "anthropic"
    assert cfg.strategic_llm_temperature == 0.9

@pytest.mark.asyncio
async def test_env_override_with_models():
    """Test environment variable overrides with different models"""
    os.environ["FAST_LLM"] = "anthropic:claude-instant"
    os.environ["FAST_LLM_TEMPERATURE"] = "0.4"
    
    cfg = Config()  # Should use default config + env overrides
    
    assert cfg.fast_llm_model == "claude-instant"
    assert cfg.fast_llm_provider == "anthropic"
    assert cfg.fast_llm_temperature == 0.4

@pytest.mark.asyncio
async def test_model_temperature_limits():
    """Test temperature limits for specific models"""
    os.environ["FAST_LLM"] = "google_genai:gemini-pro"
    
    # Test upper limit
    os.environ["FAST_LLM_TEMPERATURE"] = "1.0"
    cfg = Config()
    assert cfg.fast_llm_temperature == 1.0
    
    # Test lower limit
    os.environ["FAST_LLM_TEMPERATURE"] = "0.0"
    cfg = Config()
    assert cfg.fast_llm_temperature == 0.0 