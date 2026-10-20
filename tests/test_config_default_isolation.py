"""Mutable defaults must not be shared between Config instances."""

import json
from copy import deepcopy

import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch):
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)


@pytest.fixture(autouse=True)
def restore_defaults():
    original = deepcopy(DEFAULT_CONFIG)
    yield
    DEFAULT_CONFIG.clear()
    DEFAULT_CONFIG.update(original)


@pytest.fixture(params=["default", "file"])
def make_config(request, tmp_path):
    if request.param == "default":
        return Config
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"TOTAL_WORDS": 500}))
    return lambda: Config(str(path))


def test_set_verbose_does_not_leak_into_other_instances(make_config):
    make_config().set_verbose(True)

    assert DEFAULT_CONFIG["LLM_KWARGS"] == {}
    assert make_config().llm_kwargs == {}


@pytest.mark.parametrize(
    ("key", "attribute", "value"),
    [
        ("LLM_KWARGS", "llm_kwargs", {"top_p": 0.5}),
        ("EMBEDDING_KWARGS", "embedding_kwargs", {"dimensions": 256}),
        ("MCP_SERVERS", "mcp_servers", [{"name": "local-search"}]),
        ("MCP_ALLOWED_ROOT_PATHS", "mcp_allowed_root_paths", ["/srv/research"]),
    ],
)
def test_mutable_defaults_are_per_instance(make_config, key, attribute, value):
    first, second = make_config(), make_config()

    current = getattr(first, attribute)
    if isinstance(current, dict):
        current.update(value)
    else:
        current.extend(value)

    assert getattr(second, attribute) == DEFAULT_CONFIG[key]
    assert DEFAULT_CONFIG[key] in ({}, [])
