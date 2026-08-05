import asyncio
import builtins
import importlib
import typing
import unittest
from unittest.mock import patch


def _load_streamer_class():
    with (
        patch.object(builtins, "Any", typing.Any, create=True),
        patch.object(builtins, "List", typing.List, create=True),
    ):
        module = importlib.import_module("gpt_researcher.mcp.streaming")
    return module.MCPStreamer


MCPStreamer = _load_streamer_class()


class MCPStreamingTests(unittest.TestCase):
    def test_stream_log_forwards_websocket_payload(self):
        websocket = object()
        calls = []

        async def fake_stream_output(
            log_type,
            step,
            content,
            websocket=None,
            with_data=False,
            data=None,
        ):
            calls.append(
                {
                    "log_type": log_type,
                    "step": step,
                    "content": content,
                    "websocket": websocket,
                    "with_data": with_data,
                    "data": data,
                }
            )

        with patch(
            "gpt_researcher.actions.utils.stream_output",
            new=fake_stream_output,
        ):
            asyncio.run(
                MCPStreamer(websocket).stream_log(
                    "selected tools",
                    {"count": 2},
                )
            )

        self.assertEqual(
            calls,
            [
                {
                    "log_type": "logs",
                    "step": "mcp_retriever",
                    "content": "selected tools",
                    "websocket": websocket,
                    "with_data": True,
                    "data": {"count": 2},
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
