"""Reasoning effort must follow the normal file/environment precedence."""

import json

import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch):
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    for key in (
        "CONFIG_PATH",
        "EMBEDDING_PROVIDER",
        "LLM_PROVIDER",
        "FAST_LLM_MODEL",
        "SMART_LLM_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(params=["argument", "environment"])
def make_file_config(request, tmp_path, monkeypatch):
    path = tmp_path / "config.json"

    def make_config(effort):
        path.write_text(json.dumps({"REASONING_EFFORT": effort}), encoding="utf-8")
        if request.param == "environment":
            monkeypatch.setenv("CONFIG_PATH", str(path))
            return Config()
        return Config(str(path))

    return make_config


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_reasoning_effort_from_file(make_file_config, effort):
    assert make_file_config(effort).reasoning_effort == effort


@pytest.mark.parametrize(
    ("file_effort", "environment_effort"), [("high", "low"), ("low", "high")]
)
def test_reasoning_effort_environment_overrides_file(
    make_file_config, monkeypatch, file_effort, environment_effort
):
    monkeypatch.setenv("REASONING_EFFORT", environment_effort)
    assert make_file_config(file_effort).reasoning_effort == environment_effort


def test_reasoning_effort_default():
    assert Config().reasoning_effort == "medium"


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_reasoning_effort_from_environment(monkeypatch, effort):
    monkeypatch.setenv("REASONING_EFFORT", effort)
    assert Config().reasoning_effort == effort


def test_reasoning_effort_file_is_validated(make_file_config):
    with pytest.raises(ValueError, match="Invalid reasoning effort"):
        make_file_config("invalid")


def test_invalid_reasoning_effort_environment_does_not_fall_back(
    make_file_config, monkeypatch
):
    monkeypatch.setenv("REASONING_EFFORT", "invalid")
    with pytest.raises(ValueError, match="Invalid reasoning effort"):
        make_file_config("low")


def test_null_reasoning_effort_file_uses_parser_default(make_file_config):
    assert make_file_config(None).reasoning_effort == "medium"
