import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gpt_researcher.config import Config


class TestConfigParsing:
    def test_parse_llm_valid(self):
        provider, model = Config.parse_llm("openai:gpt-4o-mini")
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_parse_llm_invalid_format(self):
        with pytest.raises(ValueError):
            Config.parse_llm("invalid-no-colon")

    def test_parse_llm_none(self):
        assert Config.parse_llm(None) == (None, None)

    def test_parse_embedding_valid(self):
        provider, model = Config.parse_embedding("openai:text-embedding-3-large")
        assert provider == "openai"
        assert model == "text-embedding-3-large"

    def test_parse_embedding_invalid_format(self):
        with pytest.raises(ValueError):
            Config.parse_embedding("invalid")

    def test_parse_embedding_none(self):
        assert Config.parse_embedding(None) == (None, None)

    def test_parse_reasoning_effort_default(self):
        assert Config.parse_reasoning_effort(None) == "medium"

    def test_parse_reasoning_effort_valid(self):
        assert Config.parse_reasoning_effort("high") == "high"

    def test_parse_reasoning_effort_invalid(self):
        with pytest.raises(ValueError):
            Config.parse_reasoning_effort("invalid")


class TestConvertEnvValue:
    def test_bool_true(self):
        assert Config.convert_env_value("TEST", "true", bool) is True
        assert Config.convert_env_value("TEST", "1", bool) is True
        assert Config.convert_env_value("TEST", "yes", bool) is True

    def test_bool_false(self):
        assert Config.convert_env_value("TEST", "false", bool) is False
        assert Config.convert_env_value("TEST", "0", bool) is False

    def test_int(self):
        assert Config.convert_env_value("TEST", "42", int) == 42

    def test_float(self):
        assert Config.convert_env_value("TEST", "3.14", float) == 3.14

    def test_str(self):
        assert Config.convert_env_value("TEST", "hello", str) == "hello"

    def test_any_type(self):
        assert Config.convert_env_value("TEST", "hello", str) == "hello"

    def test_union_none_first(self):
        from typing import Union
        result = Config.convert_env_value("TEST", "none", Union[None, str])
        assert result is None

    def test_union_valid(self):
        from typing import Union
        result = Config.convert_env_value("TEST", "hello", Union[None, str])
        assert result == "hello"

    def test_unsupported_type(self):
        with pytest.raises(ValueError):
            Config.convert_env_value("TEST", "val", bytes)

    def test_list_type(self):
        from typing import List
        result = Config.convert_env_value("TEST", '["a", "b"]', List[str])
        assert result == ["a", "b"]


class TestLoadConfig:
    def test_default_config(self):
        config = Config.load_config(None)
        assert isinstance(config, dict)
        assert "RETRIEVER" in config
        assert "FAST_LLM" in config

    def test_custom_path_not_found(self):
        config = Config.load_config("/nonexistent/path.json")
        assert isinstance(config, dict)
        assert "RETRIEVER" in config

    def test_list_available_configs(self):
        configs = Config.list_available_configs()
        assert "default" in configs


class TestDeprecatedEnvVars:
    def test_deprecated_embedding_provider_openai(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
        cfg = Config()
        assert cfg.embedding_provider == "openai"
        assert cfg.embedding_model == "text-embedding-3-large"

    def test_deprecated_embedding_provider_ollama(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
        monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "llama2")
        cfg = Config()
        assert cfg.embedding_provider == "ollama"
        assert cfg.embedding_model == "llama2"

    def test_deprecated_llm_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("FAST_LLM", "openai:gpt-4o-mini")
        monkeypatch.setenv("SMART_LLM", "openai:gpt-4o")
        cfg = Config()
        assert cfg.fast_llm_provider == "openai"
        assert cfg.smart_llm_provider == "openai"

    def test_deprecated_fast_llm_model(self, monkeypatch):
        monkeypatch.setenv("FAST_LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("FAST_LLM", "openai:gpt-4o-mini")
        monkeypatch.setenv("SMART_LLM", "openai:gpt-4o")
        cfg = Config()
        assert cfg.fast_llm_model == "gpt-4o-mini"

    def test_deprecated_smart_llm_model(self, monkeypatch):
        monkeypatch.setenv("SMART_LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("FAST_LLM", "openai:gpt-4o-mini")
        monkeypatch.setenv("SMART_LLM", "openai:gpt-4o")
        cfg = Config()
        assert cfg.smart_llm_model == "gpt-4o"