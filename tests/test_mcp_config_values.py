"""MCP settings must survive the same file/env loading as other settings."""

import json

import pytest

from gpt_researcher import GPTResearcher
from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


SERVERS = [
    {"name": "local-search", "command": "python", "args": ["search.py"]},
    {"name": "remote-search", "connection_url": "https://mcp.example.com"},
]
ROOTS = ["/srv/research", "/srv/shared documents"]


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch):
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)


def write_config(tmp_path, servers=SERVERS, roots=ROOTS):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "MCP_SERVERS": servers,
        "MCP_ALLOWED_ROOT_PATHS": roots,
    }))
    return str(path)


@pytest.mark.parametrize("source", ["file", "environment"])
def test_mcp_settings_survive_initialization(source, tmp_path, monkeypatch):
    if source == "file":
        config = Config(write_config(tmp_path))
    else:
        monkeypatch.setenv("MCP_SERVERS", json.dumps(SERVERS))
        monkeypatch.setenv("MCP_ALLOWED_ROOT_PATHS", json.dumps(ROOTS))
        config = Config()

    assert config.mcp_servers == SERVERS
    assert config.mcp_allowed_root_paths == ROOTS
    assert config.get_mcp_server_config("local-search") == SERVERS[0]
    assert config.get_mcp_server_config("remote-search") == SERVERS[1]


def test_mcp_environment_overrides_file(tmp_path, monkeypatch):
    environment_server = {"name": "environment-search", "command": "node"}
    monkeypatch.setenv("MCP_SERVERS", json.dumps([environment_server]))
    monkeypatch.setenv("MCP_ALLOWED_ROOT_PATHS", json.dumps(["/env/research"]))

    config = Config(write_config(tmp_path))

    assert config.mcp_servers == [environment_server]
    assert config.mcp_allowed_root_paths == ["/env/research"]
    assert config.get_mcp_server_config("environment-search") == environment_server
    assert config.get_mcp_server_config("local-search") == {}


def test_empty_mcp_environment_overrides_populated_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_SERVERS", "[]")
    monkeypatch.setenv("MCP_ALLOWED_ROOT_PATHS", "[]")

    config = Config(write_config(tmp_path))

    assert config.mcp_servers == []
    assert config.mcp_allowed_root_paths == []
    assert config.get_mcp_server_config("local-search") == {}


def test_mcp_file_settings_do_not_replace_defaults(tmp_path):
    Config(write_config(tmp_path))

    default_config = Config()

    assert default_config.mcp_servers == []
    assert default_config.mcp_allowed_root_paths == []
    assert DEFAULT_CONFIG["MCP_SERVERS"] == []
    assert DEFAULT_CONFIG["MCP_ALLOWED_ROOT_PATHS"] == []


@pytest.mark.parametrize(
    ("key", "attribute", "value"),
    [
        ("MCP_SERVERS", "mcp_servers", SERVERS[0]),
        ("MCP_ALLOWED_ROOT_PATHS", "mcp_allowed_root_paths", ROOTS[0]),
    ],
)
def test_default_mcp_lists_are_isolated(key, attribute, value):
    first = Config()
    second = Config()
    original_default = DEFAULT_CONFIG[key][:]
    try:
        getattr(first, attribute).append(value)

        assert getattr(second, attribute) == []
        assert getattr(Config(), attribute) == []
        assert DEFAULT_CONFIG[key] == []
    finally:
        DEFAULT_CONFIG[key][:] = original_default


def test_mcp_lookup_skips_malformed_rows(tmp_path):
    config = Config(write_config(tmp_path, servers=[None, "invalid", SERVERS[0]]))

    assert config.get_mcp_server_config("local-search") == SERVERS[0]
    assert config.get_mcp_server_config("unknown") == {}
    assert config.get_mcp_server_config(None) == {}


def test_researcher_preserves_mcp_config_values(tmp_path):
    researcher = GPTResearcher(
        query="local MCP configuration check",
        config_path=write_config(tmp_path),
        verbose=False,
    )
    try:
        assert researcher.cfg.mcp_servers == SERVERS
        assert researcher.cfg.mcp_allowed_root_paths == ROOTS
        assert researcher.cfg.get_mcp_server_config("local-search") == SERVERS[0]
    finally:
        researcher.scraper_manager.worker_pool.executor.shutdown()
