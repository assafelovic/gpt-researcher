"""Verify generation options on real tool-bound HTTP requests, without a provider."""

import json

import httpx
import pytest
from langchain_core.tools import tool

from gpt_researcher.utils.tools import create_chat_completion_with_tools


@tool
def lookup(topic: str) -> str:
    """Look up a research topic."""
    return f"Notes about {topic}"


@pytest.mark.asyncio
@pytest.mark.parametrize("calls_tool", [False, True])
@pytest.mark.parametrize(
    "options, overrides, model, expected_temperature, expected_limit",
    [
        ({"temperature": 0.2, "max_tokens": 123}, {}, "gpt-4o-mini", 0.2, 123),
        ({}, {}, "gpt-4o-mini", 0.4, 4000),
        (
            {"temperature": 0.2, "max_tokens": 123},
            {"temperature": 0.8, "max_tokens": 456},
            "gpt-4o-mini", 0.8, 456,
        ),
        ({"temperature": 0.2, "max_tokens": 123}, {}, "o3", None, 123),
        ({"temperature": None, "max_tokens": None}, {}, "gpt-4o-mini", None, None),
    ],
)
async def test_tool_requests_keep_generation_options(
    monkeypatch, calls_tool, options, overrides, model, expected_temperature, expected_limit
):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    requests = []

    async def respond(request):
        requests.append(json.loads(request.content))
        if calls_tool and len(requests) == 1:
            message = {
                "role": "assistant", "content": None,
                "tool_calls": [{
                    "id": "call_lookup", "type": "function",
                    "function": {"name": "lookup", "arguments": '{"topic":"agents"}'},
                }],
            }
            finish_reason = "tool_calls"
        else:
            message = {"role": "assistant", "content": "Research complete."}
            finish_reason = "stop"
        return httpx.Response(200, json={
            "id": "chatcmpl-offline", "object": "chat.completion", "created": 1,
            "model": model,
            "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http_client:
        answer, calls = await create_chat_completion_with_tools(
            messages=[{"role": "user", "content": "Research agents"}],
            tools=[lookup], model=model, llm_provider="openai",
            llm_kwargs={
                "api_key": "offline-test-key", "base_url": "https://offline.invalid/v1",
                "http_async_client": http_client, "use_responses_api": False, **overrides,
            },
            **options,
        )

    assert answer == "Research complete."
    assert len(requests) == (2 if calls_tool else 1)
    assert len(calls) == int(calls_tool)
    if calls_tool:
        assert requests[1]["messages"][-1]["content"] == "Notes about agents"
    for request in requests:
        assert request.get("temperature") == expected_temperature
        assert request.get("max_completion_tokens") == expected_limit
        assert request["tools"][0]["function"]["name"] == "lookup"
