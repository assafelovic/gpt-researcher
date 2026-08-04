import builtins
import importlib
import sys
import types
import typing
import unittest
from types import SimpleNamespace
from unittest.mock import patch


def _load_server_utils():
    utils_module = types.ModuleType("utils")
    utils_module.write_md_to_pdf = lambda *args, **kwargs: None
    utils_module.write_md_to_word = lambda *args, **kwargs: None
    utils_module.write_text_to_md = lambda *args, **kwargs: None

    with (
        patch.object(builtins, "Any", typing.Any, create=True),
        patch.object(builtins, "List", typing.List, create=True),
        patch.dict(sys.modules, {"utils": utils_module}),
    ):
        return importlib.import_module("backend.server.server_utils")


server_utils = _load_server_utils()


class MultiAgentStreamOutputTests(unittest.IsolatedAsyncioTestCase):
    async def test_execute_multi_agents_passes_stream_output_callback(self):
        websocket = object()
        manager = SimpleNamespace(active_connections=[websocket])
        received = {}

        async def run_multi_agent_task(query, active_websocket, output_callback):
            received.update(
                query=query,
                websocket=active_websocket,
                output_callback=output_callback,
            )
            return "research report"

        with patch.object(
            server_utils,
            "run_multi_agent_task",
            run_multi_agent_task,
        ):
            result = await server_utils.execute_multi_agents(manager)

        self.assertEqual(result, {"report": "research report"})
        self.assertEqual(received["query"], "Is AI in a hype cycle?")
        self.assertIs(received["websocket"], websocket)
        self.assertTrue(callable(received["output_callback"]))


if __name__ == "__main__":
    unittest.main()
