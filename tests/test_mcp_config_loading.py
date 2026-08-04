import json

from gpt_researcher import GPTResearcher
from gpt_researcher.config.config import Config


MCP_SERVERS = [
    {
        "name": "local-search",
        "command": "python",
        "args": ["search_server.py"],
    }
]


def test_config_preserves_mcp_servers_from_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"MCP_SERVERS": MCP_SERVERS}))

    config = Config(str(config_path))

    assert config.mcp_servers == MCP_SERVERS


def test_config_preserves_mcp_servers_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_SERVERS", json.dumps(MCP_SERVERS))

    config = Config()

    assert config.mcp_servers == MCP_SERVERS


def test_researcher_uses_configured_mcp_servers(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"MCP_SERVERS": MCP_SERVERS}))
    monkeypatch.setattr("gpt_researcher.agent.Memory", lambda *args, **kwargs: object())

    researcher = GPTResearcher(query="test query", config_path=str(config_path))

    assert researcher.mcp_configs == MCP_SERVERS
    assert "mcp" in researcher.cfg.retrievers


def test_explicit_empty_mcp_configs_override_file_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"MCP_SERVERS": MCP_SERVERS}))
    monkeypatch.setattr("gpt_researcher.agent.Memory", lambda *args, **kwargs: object())

    researcher = GPTResearcher(
        query="test query",
        config_path=str(config_path),
        mcp_configs=[],
    )

    assert researcher.mcp_configs == []
    assert researcher.cfg.retrievers == ["tavily"]
