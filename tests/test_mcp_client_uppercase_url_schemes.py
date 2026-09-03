import pytest
from gpt_researcher.mcp.client import MCPClientManager

HEADERS = {"Authorization": "Bearer test-token"}

@pytest.mark.parametrize("url,expected_transport", [
    # Lowercase — must keep working
    ("http://mcp.example.com/service",  "streamable_http"),
    ("https://mcp.example.com/service", "streamable_http"),
    ("ws://mcp.example.com/ws",         "websocket"),
    ("wss://mcp.example.com/ws",        "websocket"),
    # Uppercase — the bug
    ("HTTP://mcp.example.com/service",  "streamable_http"),
    ("HTTPS://mcp.example.com/service", "streamable_http"),
    ("WS://mcp.example.com/ws",         "websocket"),
    ("WSS://mcp.example.com/ws",        "websocket"),
    # Mixed case
    ("Https://mcp.example.com/service", "streamable_http"),
    ("Wss://mcp.example.com/ws",        "websocket"),
])
def test_transport_autodetect_case_insensitive(url, expected_transport):
    """URI scheme names are case-insensitive per RFC 3986 §3.1."""
    result = MCPClientManager([{
        "name": "remote",
        "connection_url": url,
        "connection_headers": HEADERS,
    }]).convert_configs_to_langchain_format()

    assert result["remote"]["transport"] == expected_transport
    assert result["remote"]["url"] == url          # original URL preserved
    assert result["remote"]["headers"] == HEADERS  # headers forwarded

def test_uppercase_url_unknown_scheme_falls_through():
    """Unknown schemes should not crash, fall through to stdio or connection_type."""
    result = MCPClientManager([{
        "name": "custom",
        "connection_url": "ftp://files.example.com",
        "connection_type": "stdio",
    }]).convert_configs_to_langchain_format()
    assert result["custom"]["transport"] == "stdio"

def test_no_url_stdio_unchanged():
    """Local stdio configs without connection_url remain untouched."""
    result = MCPClientManager([{
        "name": "local",
        "command": "uvx",
        "args": ["my-mcp-server"],
    }]).convert_configs_to_langchain_format()
    assert result["local"]["transport"] == "stdio"
    assert "url" not in result["local"]
