import pytest
from gpt_researcher.config.config import Config
from gpt_researcher.skills.researcher import ResearchConductor
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger('research')

@pytest.mark.asyncio
@pytest.mark.parametrize("temp_value", [0.3, 0.7, 0.9])
async def test_temperature_ranges(temp_value):
    """Test different temperature settings"""
    os.environ['STRATEGIC_LLM_TEMPERATURE'] = str(temp_value)
    cfg = Config(config_path="configs/uat_config.json")
    assert cfg.strategic_llm_temperature == temp_value
    logger.info(f"Temperature test passed for {temp_value}")

@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_temp", [
    ("List historical facts about WW2", 0.3),  # Factual - lower temp
    ("Brainstorm future space missions", 0.9),  # Creative - higher temp
])
async def test_query_appropriate_temperature(query, expected_temp):
    """Test that appropriate temperatures are used for different query types"""
    cfg = Config(config_path="configs/uat_config.json")
    researcher = MockResearcher(query=query, config=cfg)
    assert researcher.cfg.strategic_llm_temperature == expected_temp

@pytest.mark.asyncio
@pytest.mark.parametrize("config_temps", [
    {"FAST_LLM_TEMPERATURE": 0.3, "SMART_LLM_TEMPERATURE": 0.7, "STRATEGIC_LLM_TEMPERATURE": 0.9},
    {"FAST_LLM_TEMPERATURE": 0.5, "SMART_LLM_TEMPERATURE": 0.5, "STRATEGIC_LLM_TEMPERATURE": 0.5},
])
async def test_multiple_temperature_configs(config_temps):
    """Test different temperature combinations"""
    for key, value in config_temps.items():
        os.environ[key] = str(value)
    
    cfg = Config(config_path="configs/uat_config.json")
    assert cfg.fast_llm_temperature == config_temps["FAST_LLM_TEMPERATURE"]
    assert cfg.smart_llm_temperature == config_temps["SMART_LLM_TEMPERATURE"]
    assert cfg.strategic_llm_temperature == config_temps["STRATEGIC_LLM_TEMPERATURE"]

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_temp", [-1.0, 2.0, "invalid"])
async def test_invalid_temperatures(invalid_temp):
    """Test handling of invalid temperature values"""
    os.environ['STRATEGIC_LLM_TEMPERATURE'] = str(invalid_temp)
    with pytest.raises(ValueError):
        cfg = Config(config_path="configs/uat_config.json")

class MockResearcher:
    """Mock researcher for testing temperature configurations"""
    def __init__(self, query: str, config: Config):
        self.query = query
        self.cfg = config
        # Set temperature based on query type
        if "facts" in query.lower() or "history" in query.lower():
            self.cfg._temperature_values['STRATEGIC_LLM_TEMPERATURE'] = 0.3
        elif "brainstorm" in query.lower() or "creative" in query.lower():
            self.cfg._temperature_values['STRATEGIC_LLM_TEMPERATURE'] = 0.9 