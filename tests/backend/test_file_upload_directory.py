import importlib.util
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def _load_server_utils():
    gpt_researcher = types.ModuleType("gpt_researcher")
    gpt_researcher.__path__ = []
    gpt_researcher.GPTResearcher = object

    document_package = types.ModuleType("gpt_researcher.document")
    document_package.__path__ = []
    document_module = types.ModuleType("gpt_researcher.document.document")
    document_module.DocumentLoader = object

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
        "backend.server._server_utils_upload_test",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    dependencies = {
        "gpt_researcher": gpt_researcher,
        "gpt_researcher.document": document_package,
        "gpt_researcher.document.document": document_module,
        "utils": utils_module,
        "backend.server.multi_agent_runner": runner_module,
        "chat": chat_package,
        "chat.chat": chat_module,
    }
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(module)
    return module


server_utils = _load_server_utils()


class _DocumentLoader:
    def __init__(self, path):
        self.path = path

    async def load(self):
        return []


class FileUploadDirectoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_creates_document_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir) / "documents"
            upload = SimpleNamespace(
                filename="notes.txt",
                file=io.BytesIO(b"uploaded content"),
            )

            with patch.object(server_utils, "DocumentLoader", _DocumentLoader):
                result = await server_utils.handle_file_upload(
                    upload,
                    str(document_dir),
                )

            uploaded_file = document_dir / "notes.txt"
            self.assertTrue(document_dir.is_dir())
            self.assertEqual(uploaded_file.read_bytes(), b"uploaded content")
            self.assertEqual(result["path"], str(uploaded_file))


if __name__ == "__main__":
    unittest.main()
