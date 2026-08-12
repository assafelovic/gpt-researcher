import asyncio
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


document_module = _load_module(
    "document_loader_offload_testmod",
    "gpt_researcher/document/document.py",
)
online_module = _load_module(
    "online_document_loader_offload_testmod",
    "gpt_researcher/document/online_document.py",
)


class _Page:
    page_content = "content"
    metadata = {"source": "source.txt"}


class _SlowLoader:
    def __init__(self, *args, **kwargs):
        pass

    def load(self):
        time.sleep(0.05)
        return [_Page()]


LOADER_NAMES = (
    "PyMuPDFLoader",
    "TextLoader",
    "UnstructuredCSVLoader",
    "UnstructuredExcelLoader",
    "UnstructuredMarkdownLoader",
    "UnstructuredPowerPointLoader",
    "UnstructuredWordDocumentLoader",
)


async def _heartbeat_completes_while_loading(load):
    heartbeat_ran = False

    async def heartbeat():
        nonlocal heartbeat_ran
        await asyncio.sleep(0.01)
        heartbeat_ran = True

    heartbeat_task = asyncio.create_task(heartbeat())
    await load()
    completed_during_load = heartbeat_ran
    await heartbeat_task
    return completed_during_load


class DocumentLoaderOffloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_document_parsing_keeps_event_loop_responsive(self):
        replacements = {name: _SlowLoader for name in LOADER_NAMES}
        replacements["BSHTMLLoader"] = _SlowLoader
        loader = document_module.DocumentLoader.__new__(
            document_module.DocumentLoader
        )

        with patch.multiple(document_module, **replacements):
            responsive = await _heartbeat_completes_while_loading(
                lambda: loader._load_document("source.txt", "txt")
            )

        self.assertTrue(responsive)

    async def test_online_document_parsing_keeps_event_loop_responsive(self):
        replacements = {name: _SlowLoader for name in LOADER_NAMES}
        loader = online_module.OnlineDocumentLoader.__new__(
            online_module.OnlineDocumentLoader
        )

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as file:
            path = file.name

        with patch.multiple(online_module, **replacements):
            responsive = await _heartbeat_completes_while_loading(
                lambda: loader._load_document(path, "txt")
            )

        self.assertTrue(responsive)


if __name__ == "__main__":
    unittest.main()
