"""Prompt-family selection must preserve the caller's configuration."""

import json

import pytest

import gpt_researcher.agent as agent_module
from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.prompts import PromptFamily, get_prompt_family, prompt_family_mapping
from gpt_researcher.utils.enum import PromptFamily as PromptFamilyEnum


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch):
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)


@pytest.mark.parametrize("name", ["unknown-family", ""])
def test_invalid_prompt_family_warns_and_returns_default_with_config(name):
    config = Config()

    with pytest.warns(UserWarning, match="Using default prompt family: default prompt"):
        family = get_prompt_family(name, config)

    assert type(family) is PromptFamily
    assert family.cfg is config


@pytest.mark.parametrize("name", list(PromptFamilyEnum))
@pytest.mark.parametrize("use_string", [False, True], ids=["enum", "string"])
def test_valid_prompt_family_preserves_config(name, use_string):
    config = Config()

    family = get_prompt_family(name.value if use_string else name, config)

    assert type(family) is prompt_family_mapping[name.value]
    assert family.cfg is config


@pytest.mark.parametrize("source", ["argument", "environment", "file"])
def test_researcher_initializes_with_invalid_prompt_family(monkeypatch, tmp_path, source):
    # Retriever setup is outside the prompt-family selection under test.
    monkeypatch.setattr(agent_module, "get_retrievers", lambda *_args: [])
    kwargs = {}
    if source == "argument":
        kwargs["prompt_family"] = "unknown-family"
    elif source == "environment":
        monkeypatch.setenv("PROMPT_FAMILY", "unknown-family")
    else:
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"PROMPT_FAMILY": "unknown-family"}))
        kwargs["config_path"] = str(config_path)

    with pytest.warns(UserWarning, match="Using default prompt family: default prompt"):
        researcher = agent_module.GPTResearcher(query="Test question", verbose=False, **kwargs)

    assert type(researcher.prompt_family) is PromptFamily
    assert researcher.prompt_family.cfg is researcher.cfg
