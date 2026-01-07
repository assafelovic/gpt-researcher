import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure gpt_researcher can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.agent import GPTResearcher

@pytest.fixture
def mock_dependencies():
    """Mock external dependencies to isolate GPTResearcher initialization."""
    with patch('gpt_researcher.agent.Memory') as MockMemory, \
         patch('gpt_researcher.agent.VectorStoreWrapper') as MockVectorStore, \
         patch('gpt_researcher.agent.ResearchConductor'), \
         patch('gpt_researcher.agent.ReportGenerator'), \
         patch('gpt_researcher.agent.ContextManager'), \
         patch('gpt_researcher.agent.BrowserManager'), \
         patch('gpt_researcher.agent.SourceCurator'), \
         patch('gpt_researcher.agent.DeepResearchSkill'):
         
        yield

def test_config_initialization_defaults(mock_dependencies):
    """Test that config defaults are used when no headers are provided."""
    researcher = GPTResearcher(query="test query")
    # Verify default language (assuming english is default in Config variables)
    assert researcher.cfg.language == "english"

def test_config_override_from_headers(mock_dependencies):
    """Test that headers override config values."""
    headers = {
        "LANGUAGE": "zh-CN",
        "SMART_TOKEN_LIMIT": 10000,
        "REPORT_FORMAT": "pdf"
    }
    researcher = GPTResearcher(query="test query", headers=headers)
    
    assert researcher.cfg.language == "zh-CN"
    assert researcher.cfg.smart_token_limit == 10000
    assert researcher.cfg.report_format == "pdf"

def test_config_override_case_insensitivity(mock_dependencies):
    """Test that header keys are case-insensitive when matching config attributes."""
    # The current implementation lowercases header keys before checking cfg attributes
    headers = {
        "language": "fr-FR",
        "Smart_Token_Limit": 500
    }
    researcher = GPTResearcher(query="test query", headers=headers)
    
    assert researcher.cfg.language == "fr-FR"
    assert researcher.cfg.smart_token_limit == 500

def test_unknown_headers_ignored(mock_dependencies):
    """Test that headers not matching any config attribute are ignored."""
    headers = {
        "NON_EXISTENT_CONFIG_PARAM": "some_value"
    }
    researcher = GPTResearcher(query="test query", headers=headers)
    
    assert not hasattr(researcher.cfg, "non_existent_config_param")
