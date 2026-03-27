from __future__ import annotations

import sys
import types

from gpt_researcher.llm_provider.generic import base as llm_base
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider


class DummyChatOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _install_dummy_chat_openai(monkeypatch):
    dummy_module = types.ModuleType("langchain_openai")
    dummy_module.ChatOpenAI = DummyChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", dummy_module)
    monkeypatch.setattr(llm_base, "_check_pkg", lambda _pkg: None)


def test_openai_provider_uses_openai_base_url(monkeypatch):
    _install_dummy_chat_openai(monkeypatch)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:1234/v1")

    provider = GenericLLMProvider.from_provider("openai", model="gpt-4o")

    assert provider.llm.kwargs["openai_api_base"] == "http://localhost:1234/v1"
    assert provider.llm.kwargs["model"] == "gpt-4o"


def test_avian_provider_prefers_avian_env_names(monkeypatch):
    _install_dummy_chat_openai(monkeypatch)
    monkeypatch.setenv("AVIAN_API_KEY", "avian-key")
    monkeypatch.setenv("AVIAN_BASE_URL", "https://api.avian.io/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "fallback-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://fallback.example/v1")

    provider = GenericLLMProvider.from_provider("avian", model="z-ai/glm-5")

    assert provider.llm.kwargs["openai_api_key"] == "avian-key"
    assert provider.llm.kwargs["openai_api_base"] == "https://api.avian.io/v1"
    assert provider.llm.kwargs["model"] == "z-ai/glm-5"


def test_avian_provider_falls_back_to_openai_env_names(monkeypatch):
    _install_dummy_chat_openai(monkeypatch)
    monkeypatch.delenv("AVIAN_API_KEY", raising=False)
    monkeypatch.delenv("AVIAN_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fallback-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://fallback.example/v1")

    provider = GenericLLMProvider.from_provider("avian", model="z-ai/glm-5")

    assert provider.llm.kwargs["openai_api_key"] == "fallback-key"
    assert provider.llm.kwargs["openai_api_base"] == "http://fallback.example/v1"
