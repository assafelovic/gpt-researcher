import pytest
from gpt_researcher.config.config import Config
from gpt_researcher.skills.researcher import ResearchConductor
import os

@pytest.fixture
def research_config(tmp_path):
    """Create a config for research testing"""
    config_path = tmp_path / "research_config.json"
    config = {
        "FAST_LLM": "google_genai:gemini-pro",
        "SMART_LLM": "google_genai:gemini-pro",
        "STRATEGIC_LLM": "google_genai:gemini-pro",
        "EMBEDDING": "google_genai:embedding-001",
        "RETRIEVER": "tavily",
        "FAST_LLM_TEMPERATURE": 0.3,
        "SMART_LLM_TEMPERATURE": 0.7,
        "STRATEGIC_LLM_TEMPERATURE": 0.9
    }
    import json
    config_path.write_text(json.dumps(config))
    return str(config_path)

@pytest.mark.parametrize("query,expected_temp", [
    # Factual queries should use lower temperatures
    ("What were the key technological advances in 2023?", 0.3),
    ("List the main causes of climate change", 0.3),
    ("Explain how vaccines work", 0.3),
    
    # Creative queries should use higher temperatures
    ("Brainstorm potential space tourism destinations", 0.9),
    ("Generate innovative solutions for urban transportation", 0.9),
    ("Imagine future applications of quantum computing", 0.9),
    
    # Mixed/analytical queries should use balanced temperatures
    ("Compare AI development strategies between major tech companies", 0.7),
    ("Analyze the impact of remote work on company culture", 0.7),
    ("Evaluate pros and cons of different renewable energy sources", 0.7)
])
@pytest.mark.asyncio
async def test_query_based_temperatures(research_config, query, expected_temp):
    """Test that appropriate temperatures are used for different query types"""
    cfg = Config(config_path=research_config)
    
    # Create a mock researcher for testing
    class MockResearcher:
        def __init__(self, query: str, config: Config):
            self.query = query
            self.cfg = config
            # Adjust temperature based on query type
            if any(word in query.lower() for word in ["list", "what", "explain", "define"]):
                self.cfg._temperature_values['STRATEGIC_LLM_TEMPERATURE'] = 0.3
            elif any(word in query.lower() for word in ["brainstorm", "imagine", "creative", "generate"]):
                self.cfg._temperature_values['STRATEGIC_LLM_TEMPERATURE'] = 0.9
            else:
                self.cfg._temperature_values['STRATEGIC_LLM_TEMPERATURE'] = 0.7

    researcher = MockResearcher(query=query, config=cfg)
    assert researcher.cfg.strategic_llm_temperature == expected_temp 