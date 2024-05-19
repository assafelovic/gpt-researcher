# tests/test_llm.py

import pytest
from unittest.mock import patch, AsyncMock

from gpt_researcher.llm import choose_agent

# Example test for choose_agent function
@patch('gpt_researcher.llm.create_chat_completion', new_callable=AsyncMock)
def test_choose_agent(mock_create_chat_completion):
    mock_create_chat_completion.return_value = '{"server": "Test Server", "agent_role_prompt": "Test Prompt"}'
    
    # Call the function
    result = choose_agent("gpt-3.5-turbo", "openai", "test task")

    # Assertions
    assert result['server'] == "Test Server"
    assert result['agent_role_prompt'] == "Test Prompt"
