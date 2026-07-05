#!/usr/bin/env python3
"""
Unit tests for MCPClientManager.convert_configs_to_langchain_format.

Regression coverage for the dead-branch bug where connection_headers were
silently dropped for HTTP/websocket transports because the guard checked
server_config["connection_type"] (never set) instead of the transport.
"""

import unittest

from gpt_researcher.mcp.client import MCPClientManager


class TestConvertConfigsHeaders(unittest.TestCase):
    def test_headers_forwarded_for_streamable_http(self):
        configs = [{
            "name": "my_server",
            "connection_url": "https://mcp.example.com",
            "connection_type": "streamable_http",
            "connection_headers": {"Authorization": "Bearer TOKEN"},
        }]
        result = MCPClientManager(configs).convert_configs_to_langchain_format()
        server = result["my_server"]
        self.assertEqual(server["transport"], "streamable_http")
        self.assertEqual(server["headers"], {"Authorization": "Bearer TOKEN"})

    def test_headers_forwarded_for_websocket(self):
        configs = [{
            "name": "ws_server",
            "connection_url": "wss://mcp.example.com",
            "connection_headers": {"Authorization": "Bearer WS"},
        }]
        result = MCPClientManager(configs).convert_configs_to_langchain_format()
        server = result["ws_server"]
        self.assertEqual(server["transport"], "websocket")
        self.assertEqual(server["headers"], {"Authorization": "Bearer WS"})

    def test_no_headers_when_not_provided(self):
        configs = [{
            "name": "plain",
            "connection_url": "https://mcp.example.com",
        }]
        result = MCPClientManager(configs).convert_configs_to_langchain_format()
        self.assertNotIn("headers", result["plain"])


if __name__ == "__main__":
    unittest.main()
