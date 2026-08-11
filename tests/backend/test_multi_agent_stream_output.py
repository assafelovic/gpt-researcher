import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


async def expected_stream_output(*args, **kwargs):
    pass


def _load_server_utils():
    gpt_researcher = types.ModuleType("gpt_researcher")
    gpt_researcher.__path__ = []
    gpt_researcher.GPTResearcher = object

    document_package = types.ModuleType("gpt_researcher.document")
    document_package.__path__ = []
    document_module = types.ModuleType("gpt_researcher.document.document")
    document_module.DocumentLoader = object

    actions_module = types.ModuleType("gpt_researcher.actions")
    actions_module.stream_output = expected_stream_output

    utils_module = types.ModuleType("utils")
    utils_module.write_md_to_pdf = lambda *args, **kwargs: None
    utils_module.write_md_to_word = lambda *args, **kwargs: None
    utils_module.write_text_to_md = lambda *args, **kwargs: None

    runner_module = types.ModuleType("backend.server.multi_agent_runner")
    runner_module.run_multi_agent_task = None

    chat_package = types.ModuleType("chat")
    chat_package.__path__ = []
    chat_module = types.ModuleType("chat.chat")
    chat_module.ChatAgentWithMemory = object

    module_path = Path(__file__).resolve().parents[2] / "backend/server/server_utils.py"
    spec = importlib.util.spec_from_file_location(
        "backend.server._server_utils_stream_test",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    dependencies = {
        "gpt_researcher": gpt_researcher,
        "gpt_researcher.document": document_package,
        "gpt_researcher.document.document": document_module,
        "gpt_researcher.actions": actions_module,
        "utils": utils_module,
        "backend.server.multi_agent_runner": runner_module,
        "chat": chat_package,
        "chat.chat": chat_module,
    }
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(module)
    return module


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
        self.assertIs(server_utils.stream_output, expected_stream_output)
        self.assertIs(received["output_callback"], expected_stream_output)


if __name__ == "__main__":
    unittest.main()
