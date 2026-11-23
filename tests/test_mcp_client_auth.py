"""HTTP MCP token authentication through the real optional adapter. :-)"""

import asyncio
from copy import deepcopy
import json
import socket

import pytest

from gpt_researcher.mcp.client import MCPClientManager


@pytest.mark.parametrize("scheme", ["http", "https", "HTTPS"])
def test_connection_token_becomes_http_bearer_header(scheme):
    config = {
        "name": "research",
        "connection_url": f"{scheme}://mcp.example.com/mcp",
        "connection_token": "fixture-token",
        "connection_headers": {"X-Project": "research"},
    }
    before = deepcopy(config)

    connection = MCPClientManager([config]).convert_configs_to_langchain_format()["research"]

    assert connection["headers"] == {
        "X-Project": "research",
        "Authorization": "Bearer fixture-token",
    }
    assert "token" not in connection
    assert config == before


@pytest.mark.parametrize("header", ["Authorization", "authorization", "AUTHORIZATION"])
def test_explicit_authorization_takes_precedence_over_token(header):
    config = {
        "name": "research",
        "connection_url": "https://mcp.example.com/mcp",
        "connection_token": "unused-fallback",
        "connection_headers": {header: "Basic explicit", "X-Project": "research"},
    }
    before = deepcopy(config)

    connection = MCPClientManager([config]).convert_configs_to_langchain_format()["research"]

    assert connection["headers"] == config["connection_headers"]
    assert "token" not in connection
    assert config == before


@pytest.mark.parametrize(
    "connection",
    [{"command": "python", "args": ["server.py"]}, {"connection_url": "wss://example.com/mcp"}],
)
def test_connection_token_rejects_unsupported_transports(connection):
    config = {**connection, "connection_token": "fixture-token"}

    with pytest.raises(ValueError, match="requires an HTTP MCP connection"):
        MCPClientManager([config]).convert_configs_to_langchain_format()


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit_header", [None, "Authorization", "authorization"])
async def test_authenticated_http_tool_discovery_and_invocation(explicit_header):
    pytest.importorskip("langchain_mcp_adapters.client")
    import httpx
    import uvicorn
    from mcp.server.fastmcp import FastMCP
    from starlette.datastructures import Headers
    from starlette.responses import Response

    mcp = FastMCP("Private research sources", stateless_http=True, json_response=True)
    expected = "Basic explicit" if explicit_header else "Bearer fixture-token"
    methods = []
    calls = []

    @mcp.tool()
    def lookup_source(topic: str) -> str:
        calls.append(topic)
        return json.dumps({"title": topic, "url": "https://example.com/source", "body": "Evidence"})

    app = mcp.streamable_http_app()

    async def authenticated_app(scope, receive, send):
        if scope["type"] == "http":
            if Headers(scope=scope).get("authorization") != expected:
                await Response(status_code=401)(scope, receive, send)
                return
            methods.append(scope["method"])
        await app(scope, receive, send)

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen()
    sock.setblocking(False)
    url = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
    server = uvicorn.Server(uvicorn.Config(authenticated_app, log_level="error"))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    config = {"name": "research", "connection_url": url, "connection_token": "fixture-token"}
    if explicit_header:
        config["connection_headers"] = {explicit_header: expected}
    manager = MCPClientManager([config])
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    await task
                    pytest.fail("MCP server stopped before startup")
                await asyncio.sleep(0.01)
            async with httpx.AsyncClient() as client:
                assert (await client.post(url, json={})).status_code == 401
            tools = await manager.get_all_tools()
            assert [tool.name for tool in tools] == ["lookup_source"]
            result = await tools[0].ainvoke({"topic": "dependency upgrade"})
        assert "https://example.com/source" in str(result)
        assert calls == ["dependency upgrade"]
        assert methods.count("POST") >= 4
    finally:
        await manager.close_client()
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=5)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            sock.close()
    assert manager._client is None
    assert task.done()
