import asyncio
import json
import json_repair
import pytest
import re
from gpt_researcher.actions import (
    agent_creator,
)
from gpt_researcher.prompts import (
    auto_agent_instructions,
)
from gpt_researcher.utils.llm import (
    create_chat_completion,
)
from types import (
    SimpleNamespace,
)


@pytest.mark.asyncio
async def test_handle_json_error_with_regex(monkeypatch):
    """
    Test that handle_json_error falls back correctly to JSON regex extraction when
    json_repair.loads fails, and correctly returns the 'server' and 'agent_role_prompt'
    from the embedded JSON substring.
    """
    fake_response = 'Random text before JSON {"server": "AgentFromRegex", "agent_role_prompt": "PromptFromRegex"} random text after JSON'

    def fake_json_repair_failure(_):
        raise Exception("Forced failure in json_repair.loads")

    monkeypatch.setattr(json_repair, "loads", fake_json_repair_failure)
    server, prompt = await agent_creator.handle_json_error(fake_response)
    assert server == "AgentFromRegex"
    assert prompt == "PromptFromRegex"


@pytest.mark.asyncio
async def test_handle_json_error_with_valid_json():
    """
    Test that handle_json_error returns the correct 'server' and 'agent_role_prompt'
    when the LLM response is a valid JSON string that can be directly parsed by json_repair.loads.
    """
    valid_response = '{"server": "ValidAgent", "agent_role_prompt": "ValidPrompt"}'
    server, prompt = await agent_creator.handle_json_error(valid_response)
    assert server == "ValidAgent"
    assert prompt == "ValidPrompt"


@pytest.mark.asyncio
async def test_choose_agent_success(monkeypatch):
    """
    Test that choose_agent returns the correct 'server' and 'agent_role_prompt'
    when create_chat_completion returns a valid JSON string. This test also verifies
    that the parent_query is concatenated with the query correctly.
    """
    dummy_cfg = SimpleNamespace(
        smart_llm_model="dummy-model",
        smart_llm_provider="dummy-provider",
        llm_kwargs={},
    )
    query = "Sub Query"
    parent_query = "Main Query"

    async def fake_create_chat_completion(
        *, model, messages, temperature, llm_provider, llm_kwargs, cost_callback
    ):
        expected_user_message = f"task: {parent_query} - {query}"
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == expected_user_message
        return json.dumps({"server": "TestAgent", "agent_role_prompt": "TestPrompt"})

    monkeypatch.setattr(
        agent_creator, "create_chat_completion", fake_create_chat_completion
    )
    server, prompt = await agent_creator.choose_agent(
        query, dummy_cfg, parent_query=parent_query
    )
    assert server == "TestAgent"
    assert prompt == "TestPrompt"


@pytest.mark.asyncio
async def test_handle_json_error_fallback(monkeypatch):
    """
    Test that handle_json_error returns the default agent and prompt
    when the LLM response does not contain any JSON, ensuring that the fallback behavior is triggered.
    """
    invalid_response = "This string does not contain any valid JSON."

    def fake_json_repair_failure(_):
        raise Exception("Forced failure in json_repair.loads")

    monkeypatch.setattr(json_repair, "loads", fake_json_repair_failure)
    expected_server = "Default Agent"
    expected_prompt = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    server, prompt = await agent_creator.handle_json_error(invalid_response)
    assert server == expected_server
    assert prompt == expected_prompt


@pytest.mark.asyncio
async def test_choose_agent_fallback_integration(monkeypatch):
    """
    Test that choose_agent properly falls back to the default agent and prompt
    when create_chat_completion returns a response that cannot be parsed as valid JSON.
    The test simulates an invalid JSON response triggering the exception branch.
    """
    dummy_cfg = SimpleNamespace(
        smart_llm_model="dummy-model",
        smart_llm_provider="dummy-provider",
        llm_kwargs={},
    )
    query = "Test Query"
    parent_query = "Parent Query"

    async def fake_create_chat_completion(
        *, model, messages, temperature, llm_provider, llm_kwargs, cost_callback
    ):
        return "This is not a valid JSON response at all!"

    monkeypatch.setattr(
        agent_creator, "create_chat_completion", fake_create_chat_completion
    )

    def fake_json_repair_failure(_):
        raise Exception("Forced failure in json_repair.loads")

    monkeypatch.setattr(json_repair, "loads", fake_json_repair_failure)
    expected_server = "Default Agent"
    expected_prompt = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    server, prompt = await agent_creator.choose_agent(
        query, dummy_cfg, parent_query=parent_query
    )
    assert server == expected_server
    assert prompt == expected_prompt


@pytest.mark.asyncio
async def test_choose_agent_without_parent_query(monkeypatch):
    """
    Test that choose_agent returns the correct 'server' and 'agent_role_prompt'
    when no parent_query is provided. This verifies that the query is not modified
    (i.e. no concatenation with a parent query) in the LLM message.
    """
    dummy_cfg = SimpleNamespace(
        smart_llm_model="dummy-model",
        smart_llm_provider="dummy-provider",
        llm_kwargs={},
    )
    query = "Only Query"

    async def fake_create_chat_completion(
        *, model, messages, temperature, llm_provider, llm_kwargs, cost_callback
    ):
        expected_user_message = "task: Only Query"
        assert messages[1]["content"] == expected_user_message
        return json.dumps(
            {"server": "NoParentAgent", "agent_role_prompt": "NoParentPrompt"}
        )

    monkeypatch.setattr(
        agent_creator, "create_chat_completion", fake_create_chat_completion
    )
    server, prompt = await agent_creator.choose_agent(
        query, dummy_cfg, parent_query=None
    )
    assert server == "NoParentAgent"
    assert prompt == "NoParentPrompt"


@pytest.mark.asyncio
async def test_handle_json_error_invalid_json_in_regex(monkeypatch):
    """
    Test that handle_json_error returns the default agent and prompt when the regex extracts
    an invalid JSON snippet that cannot be decoded. This simulates a scenario where both json_repair.loads
    and json.loads (on the regex substring) fail, triggering the fallback behavior.
    """
    invalid_response = (
        "Some random text {invalid json without proper quotes} some more text."
    )

    def fake_json_repair_failure(_):
        raise Exception("Forced failure in json_repair.loads")

    monkeypatch.setattr(json_repair, "loads", fake_json_repair_failure)
    default_server = "Default Agent"
    default_prompt = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    server, prompt = await agent_creator.handle_json_error(invalid_response)
    assert server == default_server
    assert prompt == default_prompt


@pytest.mark.asyncio
async def test_handle_json_error_with_empty_response(monkeypatch):
    """
    Test that handle_json_error returns the default agent and prompt when the input LLM response
    is an empty or whitespace-only string. This simulates an edge case where no valid JSON is provided.
    """
    empty_response = "    "

    def fake_json_repair_failure(_):
        raise Exception("Forced failure in json_repair.loads")

    monkeypatch.setattr(json_repair, "loads", fake_json_repair_failure)
    expected_server = "Default Agent"
    expected_prompt = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    server, prompt = await agent_creator.handle_json_error(empty_response)
    assert server == expected_server
    assert prompt == expected_prompt


@pytest.mark.asyncio
async def test_extract_json_with_multiple_jsons():
    """
    Test that extract_json_with_regex returns only the first JSON substring when multiple JSONs
    are present in the response.
    """
    response = 'Some info text before the JSON block {"server": "FirstAgent", "agent_role_prompt": "FirstPrompt"} and then some extra info {"server": "SecondAgent", "agent_role_prompt": "SecondPrompt"} extra text.'
    extracted = agent_creator.extract_json_with_regex(response)
    expected = '{"server": "FirstAgent", "agent_role_prompt": "FirstPrompt"}'
    assert extracted == expected


@pytest.mark.asyncio
async def test_choose_agent_cost_callback(monkeypatch):
    """
    Test that choose_agent passes the cost_callback correctly to create_chat_completion,
    and that the cost_callback is invoked during the agent creation process.
    """
    dummy_cfg = SimpleNamespace(
        smart_llm_model="dummy-model",
        smart_llm_provider="dummy-provider",
        llm_kwargs={},
    )
    query = "Test Query with Callback"
    parent_query = "Parent Query Callback"
    callback_called = []

    async def fake_create_chat_completion(
        *, model, messages, temperature, llm_provider, llm_kwargs, cost_callback
    ):
        if callable(cost_callback):
            cost_callback(42)
        return json.dumps(
            {"server": "CallbackAgent", "agent_role_prompt": "CallbackPrompt"}
        )

    monkeypatch.setattr(
        agent_creator, "create_chat_completion", fake_create_chat_completion
    )

    def cost_callback(cost):
        callback_called.append(cost)

    server, prompt = await agent_creator.choose_agent(
        query, dummy_cfg, parent_query=parent_query, cost_callback=cost_callback
    )
    assert callback_called == [42]
    assert server == "CallbackAgent"
    assert prompt == "CallbackPrompt"
