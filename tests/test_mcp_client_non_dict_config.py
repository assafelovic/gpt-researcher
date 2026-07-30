"""MCPClientManager must skip non-dict server configs."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load client.py directly to avoid gpt_researcher package __init__ side effects /
# unrelated import-time NameErrors on other modules.
ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "gpt_researcher" / "mcp" / "client.py"
spec = importlib.util.spec_from_file_location("gptr_mcp_client_under_test", CLIENT_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
MCPClientManager = mod.MCPClientManager


def test_skips_non_dict_entries():
    mgr = MCPClientManager(
        [
            {"name": "ok", "connection_url": "https://example.test/mcp"},
            "not-a-dict",
            None,
            12,
            {"name": "stdio_ok", "connection_type": "stdio", "command": "echo"},
        ]
    )
    out = mgr.convert_configs_to_langchain_format()
    assert "ok" in out
    assert out["ok"]["transport"] == "streamable_http"
    assert "stdio_ok" in out
    assert out["stdio_ok"]["transport"] == "stdio"
    assert len(out) == 2
