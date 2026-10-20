import importlib
import json

import httpx
import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import (
    GenericLLMProvider,
    _SUPPORTED_PROVIDERS as LLM_PROVIDERS,
)
from gpt_researcher.llm_provider.minimax import (
    MINIMAX_DEFAULT_MODEL,
    MINIMAX_ENDPOINTS,
    MINIMAX_MODEL_SPECS,
    get_minimax_base_url,
)
from gpt_researcher.memory.embeddings import Memory
from gpt_researcher.utils.llm import create_chat_completion


@pytest.fixture(autouse=True)
def minimax_environment(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("MINIMAX_REGION", "global_en")
    for name in ("MINIMAX_BASE_URL", "MINIMAX_ANTHROPIC_BASE_URL", "LLM_KWARGS"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(params=["minimax", "minimax_anthropic"])
def provider_name(request):
    if request.param == "minimax_anthropic":
        pytest.importorskip("langchain_anthropic")
    return request.param


@pytest.fixture
def requests(monkeypatch):
    captured = []

    async def send(client, request, **kwargs):
        http = importlib.import_module(type(request).__module__.split(".")[0])
        body = json.loads(request.content)
        captured.append((str(request.url), body))
        if request.url.path.endswith("/messages"):
            response = {
                "id": "msg_test", "type": "message", "role": "assistant",
                "content": [{"type": "text", "text": "ok"}],
                "model": body["model"], "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        else:
            response = {
                "id": "chatcmpl-test", "object": "chat.completion", "created": 0,
                "model": body["model"],
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        thinking = request.url.path.endswith("/messages") and body["model"] == MINIMAX_DEFAULT_MODEL
        if thinking:
            response["content"].insert(0, {"type": "thinking", "thinking": "reasoning", "signature": "test"})
        if body.get("stream"):
            if request.url.path.endswith("/messages"):
                events = [
                    {"type": "message_start", "message": {**response, "content": [], "stop_reason": None}},
                    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
                    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ok"}},
                    {"type": "content_block_stop", "index": 0},
                    {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 1}},
                    {"type": "message_stop"},
                ]
                if thinking:
                    for event in events:
                        if "index" in event:
                            event["index"] += 1
                    events[1:1] = [
                        {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": "", "signature": ""}},
                        {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "reasoning"}},
                        {"type": "content_block_stop", "index": 0},
                    ]
                content = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events)
            else:
                chunk = {**response, "object": "chat.completion.chunk", "choices": [
                    {"index": 0, "finish_reason": None, "delta": {"role": "assistant", "content": "ok"}},
                ]}
                content = f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n"
            return http.Response(200, content=content, headers={"content-type": "text/event-stream"}, request=request)
        return http.Response(200, json=response, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    # Recent Anthropic SDK versions use httpx2; older versions use httpx.
    if importlib.util.find_spec("httpx2") is not None:
        httpx2 = importlib.import_module("httpx2")
        monkeypatch.setattr(httpx2.AsyncClient, "send", send)
    return captured


def test_recommended_models():
    assert {"minimax", "minimax_anthropic"} <= LLM_PROVIDERS
    assert tuple(MINIMAX_MODEL_SPECS) == ("MiniMax-M3.1-Flash", "MiniMax-M3")
    flash = MINIMAX_MODEL_SPECS[MINIMAX_DEFAULT_MODEL]
    assert flash["context_window"] == 1_000_000
    assert flash["max_output_tokens"] == 524_288
    assert flash["thinking"] == ("adaptive",)
    assert flash["pricing_usd_per_million_tokens"] == {
        "input": 0.15, "output": 0.60, "cache_read": 0.015, "cache_write": None,
    }
    m3 = MINIMAX_MODEL_SPECS["MiniMax-M3"]
    assert m3["pricing_usd_per_million_tokens"] == {
        "input": 0.3, "output": 1.2, "cache_read": 0.06, "cache_write": None,
    }
    assert m3["pricing_above_512k_usd_per_million_tokens"] == {
        "input": 0.6, "output": 2.4, "cache_read": 0.12, "cache_write": None,
    }


@pytest.mark.parametrize("region", MINIMAX_ENDPOINTS)
@pytest.mark.parametrize("stream", [False, True])
async def test_default_provider_request(provider_name, region, stream, monkeypatch, requests):
    monkeypatch.setenv("MINIMAX_REGION", region)
    provider = GenericLLMProvider.from_provider(provider_name, verbose=False)
    assert await provider.get_chat_response([{"role": "user", "content": "hello"}], stream) == "ok"
    url, body = requests[0]
    protocol = "anthropic" if provider_name.endswith("anthropic") else "openai"
    suffix = "/v1/messages" if protocol == "anthropic" else "/chat/completions"
    assert url == MINIMAX_ENDPOINTS[region][protocol] + suffix
    assert body["model"] == MINIMAX_DEFAULT_MODEL
    assert "service_tier" not in body
    assert "reasoning_split" not in body
    assert "thinking" not in body  # Let the API apply its adaptive default.
    assert "reasoning_effort" not in body
    assert "output_config" not in body


async def test_custom_model_name_alias(provider_name, requests):
    provider = GenericLLMProvider.from_provider(provider_name, model_name="custom-alias", verbose=False)
    assert await provider.get_chat_response([{"role": "user", "content": "hello"}], False) == "ok"
    assert requests[0][1]["model"] == "custom-alias"


@pytest.mark.parametrize("model", ["MiniMax-M3.1-Flash", "MiniMax-M3", "MiniMax-M2.7", "custom-model"])
async def test_saved_config_reaches_completion_unchanged(provider_name, model, tmp_path, monkeypatch, requests):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({name: f"{provider_name}:{model}"
                               for name in ("FAST_LLM", "SMART_LLM", "STRATEGIC_LLM")}))
    for name in ("FAST_LLM", "SMART_LLM", "STRATEGIC_LLM", "LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    config = Config(str(path))
    assert config.fast_llm_model == config.smart_llm_model == config.strategic_llm_model == model
    assert await create_chat_completion(
        [{"role": "user", "content": "hello"}],
        model=config.fast_llm_model, llm_provider=config.fast_llm_provider,
    ) == "ok"
    assert requests[0][1]["model"] == model


@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
async def test_flash_effort_and_custom_endpoint(provider_name, effort, monkeypatch, requests):
    anthropic = provider_name.endswith("anthropic")
    env_name = "MINIMAX_ANTHROPIC_BASE_URL" if anthropic else "MINIMAX_BASE_URL"
    base = "https://custom.example/anthropic" if anthropic else "https://custom.example/v1"
    monkeypatch.setenv(env_name, base)
    options = {"thinking": {"type": "adaptive"}, "output_config": {"effort": effort}} if anthropic else {
        "extra_body": {"thinking": {"type": "adaptive"}}, "reasoning_effort": effort,
    }
    monkeypatch.setenv("LLM_KWARGS", json.dumps(options))
    assert await create_chat_completion(
        [{"role": "user", "content": "hello"}], model=MINIMAX_DEFAULT_MODEL,
        llm_provider=provider_name,
    ) == "ok"
    url, body = requests[0]
    assert url == base + ("/v1/messages" if anthropic else "/chat/completions")
    assert body["thinking"] == {"type": "adaptive"}
    assert (body["output_config"]["effort"] if anthropic else body["reasoning_effort"]) == effort


async def test_m3_multimodal_and_disabled_thinking(provider_name, requests):
    anthropic = provider_name.endswith("anthropic")
    image = {"type": "image", "source": {"type": "url", "url": "https://example.com/image.png"}} if anthropic else {
        "type": "image_url", "image_url": {"url": "https://example.com/image.png"},
    }
    content = [{"type": "text", "text": "describe"}, image]
    options = {"thinking": {"type": "disabled"}} if anthropic else {
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    assert await create_chat_completion(
        [{"role": "user", "content": content}], model="MiniMax-M3",
        llm_provider=provider_name, llm_kwargs=options,
    ) == "ok"
    body = requests[0][1]
    assert body["model"] == "MiniMax-M3"
    assert body["thinking"] == {"type": "disabled"}
    assert body["messages"][0]["content"] == content


@pytest.mark.parametrize("region", MINIMAX_ENDPOINTS)
def test_embedding_region_and_model_preserved(region, monkeypatch):
    monkeypatch.setenv("MINIMAX_REGION", region)
    embeddings = Memory("minimax", "embo-01").get_embeddings()
    assert str(embeddings.openai_api_base) == MINIMAX_ENDPOINTS[region]["openai"]
    assert embeddings.model == "embo-01"


def test_invalid_region_and_endpoint(monkeypatch):
    monkeypatch.setenv("MINIMAX_REGION", "invalid")
    with pytest.raises(ValueError, match="Unsupported MINIMAX_REGION"):
        get_minimax_base_url("openai")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://custom.example/wrong")
    with pytest.raises(ValueError, match="must end with /v1"):
        get_minimax_base_url("openai")
