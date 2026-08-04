import builtins
import importlib
import io
import sys
import tempfile
import types
import typing
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def _load_server_utils():
    utils_module = types.ModuleType("utils")
    utils_module.write_md_to_pdf = lambda *args, **kwargs: None
    utils_module.write_md_to_word = lambda *args, **kwargs: None
    utils_module.write_text_to_md = lambda *args, **kwargs: None

    original_any = getattr(builtins, "Any", None)
    original_list = getattr(builtins, "List", None)
    builtins.Any = typing.Any
    builtins.List = typing.List
    try:
        with patch.dict(sys.modules, {"utils": utils_module}):
            return importlib.import_module("backend.server.server_utils")
    finally:
        if original_any is None:
            del builtins.Any
        else:
            builtins.Any = original_any
        if original_list is None:
            del builtins.List
        else:
            builtins.List = original_list


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
