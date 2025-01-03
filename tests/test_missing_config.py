import pytest
import os
from gpt_researcher.config.config import Config
import json

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file with minimal settings"""
    config_path = tmp_path / "minimal_config.json"
    minimal_config = {
        "RETRIEVER": "tavily",
        "EMBEDDING": "google_genai:embedding-001"
        # Deliberately missing temperature settings
    }
    config_path.write_text(json.dumps(minimal_config))
    return str(config_path)

@pytest.mark.asyncio
async def test_missing_temperature_values(temp_config_file):
    """Test that missing temperature values fall back to defaults"""
    cfg = Config(config_path=temp_config_file)
    
    # Should fall back to default values
    assert cfg.llm_temperature == 0.55
    assert cfg.fast_llm_temperature == 0.55
    assert cfg.smart_llm_temperature == 0.55
    assert cfg.strategic_llm_temperature == 0.55

@pytest.mark.asyncio
async def test_partial_temperature_config(temp_config_file):
    """Test with only some temperature values set"""
    # Update config with partial temperature settings
    with open(temp_config_file, 'r+') as f:
        config = json.load(f)
        config["FAST_LLM_TEMPERATURE"] = 0.3  # Only set one temperature
        f.seek(0)
        json.dump(config, f)
        f.truncate()
    
    cfg = Config(config_path=temp_config_file)
    
    # Specific value set
    assert cfg.fast_llm_temperature == 0.3
    # Others should fall back to defaults
    assert cfg.smart_llm_temperature == 0.55
    assert cfg.strategic_llm_temperature == 0.55

@pytest.mark.asyncio
async def test_empty_config(tmp_path):
    """Test with completely empty config file"""
    empty_config = tmp_path / "empty_config.json"
    empty_config.write_text("{}")
    
    cfg = Config(config_path=str(empty_config))
    
    # Should use all default values
    assert cfg.llm_temperature == 0.55
    assert cfg.fast_llm_temperature == 0.55
    assert cfg.smart_llm_temperature == 0.55
    assert cfg.strategic_llm_temperature == 0.55 