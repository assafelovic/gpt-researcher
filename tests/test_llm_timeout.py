"""Offline regressions for providers that stop responding (issue #1764).

The watchdog only prevents a broken implementation from hanging pytest; a
provider timeout must finish first and carry the actionable LLM error message.
"""

import asyncio
from contextlib import suppress
import sys
from types import ModuleType, SimpleNamespace

import pytest

from gpt_researcher.llm_provider.generic import base
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider


MESSAGES = [{"role": "user", "content": "Write a report"}]


def _chunk(content, **metadata):
    return SimpleNamespace(content=content, **metadata)


async def _with_watchdog(awaitable):
    task = asyncio.create_task(awaitable)
    try:
        done, _ = await asyncio.wait({task}, timeout=2)
        assert task in done, "LLM call hung until the test watchdog expired"
        return task.result()
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


class _StallingLLM:
    def __init__(self, first_chunk=False):
        self.first_chunk = first_chunk
        self.started = asyncio.Event()
        self.cleaned_up = False

    async def ainvoke(self, messages, **kwargs):
        try:
            self.started.set()
            await asyncio.Event().wait()
        finally:
            self.cleaned_up = True

    async def astream(self, messages, **kwargs):
        try:
            if self.first_chunk:
                yield _chunk("Partial report\n")
            self.started.set()
            await asyncio.Event().wait()
        finally:
            self.cleaned_up = True


@pytest.mark.asyncio
async def test_stalled_invoke_times_out_and_cancels_provider(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "0.05")
    llm = _StallingLLM()
    provider = GenericLLMProvider(llm, verbose=False)

    with pytest.raises(TimeoutError, match="LLM timed out.*a response"):
        await _with_watchdog(provider.get_chat_response(MESSAGES, stream=False))

    assert llm.started.is_set()
    assert llm.cleaned_up


@pytest.mark.asyncio
@pytest.mark.parametrize("first_chunk", [False, True], ids=["first-chunk", "midstream"])
async def test_stalled_stream_times_out_and_closes_generator(monkeypatch, first_chunk):
    monkeypatch.setenv("LLM_TIMEOUT", "0.05")
    llm = _StallingLLM(first_chunk=first_chunk)
    provider = GenericLLMProvider(llm, verbose=False)

    with pytest.raises(TimeoutError, match="LLM timed out.*next stream chunk"):
        await _with_watchdog(provider.get_chat_response(MESSAGES, stream=True))

    assert llm.started.is_set()
    assert llm.cleaned_up


@pytest.mark.asyncio
async def test_successful_invoke_preserves_content_metadata_and_kwargs(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "1")

    class LLM:
        async def ainvoke(self, messages, **kwargs):
            assert messages == MESSAGES
            assert kwargs == {"stop": ["END"]}
            return _chunk(
                "Complete report",
                usage_metadata={"input_tokens": 7, "output_tokens": 4},
                response_metadata={"model_name": "offline-model"},
            )

    provider = GenericLLMProvider(LLM(), verbose=False)
    assert await provider.get_chat_response(MESSAGES, stream=False, stop=["END"]) == "Complete report"
    assert provider.last_usage_metadata == {"input_tokens": 7, "output_tokens": 4}
    assert provider.last_response_metadata == {"model_name": "offline-model"}


@pytest.mark.asyncio
async def test_healthy_stream_can_exceed_timeout_and_empty_chunks_reset_it(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "0.15")

    class LLM:
        closed = False

        async def astream(self, messages, **kwargs):
            try:
                yield _chunk("Start ")
                # Metadata-only heartbeats also prove the provider is alive.
                # Total duration exceeds the deadline, each wait is well below it.
                for _ in range(8):
                    await asyncio.sleep(0.04)
                    yield _chunk("", response_metadata={"model_name": "offline-model"})
                yield _chunk("end", usage_metadata={"input_tokens": 7, "output_tokens": 4})
            finally:
                self.closed = True

    llm = LLM()
    provider = GenericLLMProvider(llm, verbose=False)
    assert await _with_watchdog(provider.get_chat_response(MESSAGES, stream=True)) == "Start end"
    assert provider.last_usage_metadata == {"input_tokens": 7, "output_tokens": 4}
    assert provider.last_response_metadata == {"model_name": "offline-model"}
    assert llm.closed


@pytest.mark.asyncio
async def test_timeout_does_not_include_websocket_delivery(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "0.03")

    class LLM:
        async def astream(self, messages, **kwargs):
            yield _chunk("First paragraph\n")
            yield _chunk("Second paragraph")

    class WebSocket:
        def __init__(self):
            self.outputs = []

        async def send_json(self, data):
            await asyncio.sleep(0.08)
            self.outputs.append(data["output"])

    websocket = WebSocket()
    provider = GenericLLMProvider(LLM(), verbose=False)
    response = await _with_watchdog(provider.get_chat_response(MESSAGES, stream=True, websocket=websocket))
    assert response == "First paragraph\nSecond paragraph"
    assert websocket.outputs == ["First paragraph\n", "Second paragraph"]


@pytest.mark.asyncio
async def test_websocket_failure_closes_suspended_provider_stream(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "1")
    send_error = RuntimeError("Client disconnected")

    class LLM:
        closed = False

        async def astream(self, messages, **kwargs):
            try:
                yield _chunk("First paragraph\n")
                yield _chunk("Second paragraph")
            finally:
                self.closed = True

    class WebSocket:
        async def send_json(self, data):
            raise send_error

    llm = LLM()
    provider = GenericLLMProvider(llm, verbose=False)
    with pytest.raises(RuntimeError) as exc:
        await provider.get_chat_response(MESSAGES, stream=True, websocket=WebSocket())
    assert exc.value is send_error
    assert llm.closed


@pytest.mark.asyncio
async def test_cancellation_during_websocket_send_closes_suspended_stream(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "1")
    sending = asyncio.Event()

    class LLM:
        closed = False

        async def astream(self, messages, **kwargs):
            try:
                yield _chunk("First paragraph\n")
                yield _chunk("Second paragraph")
            finally:
                self.closed = True

    class WebSocket:
        async def send_json(self, data):
            sending.set()
            await asyncio.Event().wait()

    llm = LLM()
    provider = GenericLLMProvider(llm, verbose=False)
    task = asyncio.create_task(provider.get_chat_response(MESSAGES, stream=True, websocket=WebSocket()))
    try:
        await asyncio.wait_for(sending.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert llm.closed
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_zero_disables_timeout(monkeypatch, stream):
    monkeypatch.setenv("LLM_TIMEOUT", "0")

    class LLM:
        async def ainvoke(self, messages, **kwargs):
            await asyncio.sleep(0.08)
            return _chunk("Delayed report")

        async def astream(self, messages, **kwargs):
            yield await self.ainvoke(messages, **kwargs)

    provider = GenericLLMProvider(LLM(), verbose=False)
    assert await _with_watchdog(provider.get_chat_response(MESSAGES, stream=stream)) == "Delayed report"


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_caller_cancellation_is_preserved_and_cleans_up(monkeypatch, stream):
    monkeypatch.setenv("LLM_TIMEOUT", "30")
    llm = _StallingLLM()
    provider = GenericLLMProvider(llm, verbose=False)
    task = asyncio.create_task(provider.get_chat_response(MESSAGES, stream=stream))
    try:
        await asyncio.wait_for(llm.started.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert llm.cleaned_up
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_provider_timeout_error_is_not_replaced(monkeypatch, stream):
    monkeypatch.setenv("LLM_TIMEOUT", "1")
    upstream_error = TimeoutError("SDK connection timeout")

    class LLM:
        async def ainvoke(self, messages, **kwargs):
            raise upstream_error

        async def astream(self, messages, **kwargs):
            yield await self.ainvoke(messages, **kwargs)

    provider = GenericLLMProvider(LLM(), verbose=False)
    with pytest.raises(TimeoutError) as exc:
        await provider.get_chat_response(MESSAGES, stream=stream)
    assert exc.value is upstream_error


def test_timeout_configuration_default_and_explicit_precedence(monkeypatch):
    monkeypatch.delenv("LLM_TIMEOUT", raising=False)
    assert GenericLLMProvider(object()).llm_timeout == 300
    monkeypatch.setenv("LLM_TIMEOUT", "12.5")
    assert GenericLLMProvider(object()).llm_timeout == 12.5
    assert GenericLLMProvider(object(), llm_timeout=2).llm_timeout == 2
    assert GenericLLMProvider(object(), llm_timeout=0).llm_timeout == 0


@pytest.mark.parametrize("value", ["", "slow", "-1", "nan", "inf", "-inf"])
def test_invalid_environment_timeout_fails_clearly(monkeypatch, value):
    monkeypatch.setenv("LLM_TIMEOUT", value)
    with pytest.raises(ValueError, match="LLM_TIMEOUT"):
        GenericLLMProvider(object())


@pytest.mark.parametrize("value", [True, False, -1, float("nan"), float("inf"), "slow"])
def test_invalid_explicit_timeout_fails_clearly(value):
    with pytest.raises(ValueError, match="llm_timeout"):
        GenericLLMProvider(object(), llm_timeout=value)


def test_factory_consumes_llm_timeout_and_preserves_sdk_timeout(monkeypatch):
    captured = {}
    module = ModuleType("langchain_openai")

    class ChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    module.ChatOpenAI = ChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", module)
    monkeypatch.setattr(base, "_check_pkg", lambda name: None)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_TIMEOUT", "300")

    provider = GenericLLMProvider.from_provider(
        "openai", model="offline-model", llm_timeout=0.5, timeout=42, verbose=False
    )
    assert provider.llm_timeout == 0.5
    assert "llm_timeout" not in captured
    assert captured["timeout"] == 42
    assert captured["model"] == "offline-model"
