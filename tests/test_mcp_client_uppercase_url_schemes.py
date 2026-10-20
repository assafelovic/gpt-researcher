import pytest

from gpt_researcher.mcp.client import MCPClientManager


@pytest.mark.parametrize(
    ("url", "transport"),
    [
        ("HTTPS://mcp.example.com/service", "streamable_http"),
        ("HTTP://mcp.example.com/service", "streamable_http"),
        ("WSS://mcp.example.com/service", "websocket"),
        ("WS://mcp.example.com/service", "websocket"),
        ("HtTpS://mcp.example.com/service", "streamable_http"),
        ("WsS://mcp.example.com/service", "websocket"),
    ],
)
def test_uppercase_url_scheme_selects_remote_transport(url, transport):
    headers = {"Authorization": "Bearer test-token"}

    result = MCPClientManager(
        [
            {
                "name": "remote",
                "connection_url": url,
                "connection_headers": headers,
            }
        ]
    ).convert_configs_to_langchain_format()

    assert result["remote"] == {
        "transport": transport,
        "url": url,
        "headers": headers,
    }
