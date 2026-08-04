import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _FakeBlobServiceClient:
    @classmethod
    def from_connection_string(cls, connection_string):
        return cls()

    def get_container_client(self, container_name):
        return None


azure_module = types.ModuleType("azure")
azure_storage_module = types.ModuleType("azure.storage")
azure_blob_module = types.ModuleType("azure.storage.blob")
azure_blob_module.BlobServiceClient = _FakeBlobServiceClient
sys.modules.setdefault("azure", azure_module)
sys.modules.setdefault("azure.storage", azure_storage_module)
sys.modules.setdefault("azure.storage.blob", azure_blob_module)

module_path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "document" / "azure_document_loader.py"
spec = importlib.util.spec_from_file_location("azure_document_loader", module_path)
azure_document_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(azure_document_loader)
AzureDocumentLoader = azure_document_loader.AzureDocumentLoader


class _Blob:
    def __init__(self, name):
        self.name = name


class _BlobDownload:
    def __init__(self, content):
        self._content = content

    def readall(self):
        return self._content


class _BlobClient:
    def __init__(self, content):
        self._content = content

    def download_blob(self):
        return _BlobDownload(self._content)


class _Container:
    def __init__(self, blobs):
        self._blobs = blobs

    def list_blobs(self):
        return [_Blob(name) for name in self._blobs]

    def get_blob_client(self, name):
        return _BlobClient(self._blobs[name])


class TestAzureDocumentLoader(unittest.IsolatedAsyncioTestCase):
    async def test_load_creates_parent_directories_for_virtual_blob_paths(self):
        loader = AzureDocumentLoader.__new__(AzureDocumentLoader)
        loader.container = _Container({"reports/2026/summary.txt": b"hello"})

        file_paths = await loader.load()

        self.assertEqual(len(file_paths), 1)
        downloaded_file = Path(file_paths[0])
        self.assertEqual(downloaded_file.name, "summary.txt")
        self.assertEqual(downloaded_file.read_bytes(), b"hello")
        self.assertIn("reports", downloaded_file.parts)
        self.assertIn("2026", downloaded_file.parts)

    async def test_load_rejects_blob_names_that_escape_temp_dir(self):
        loader = AzureDocumentLoader.__new__(AzureDocumentLoader)
        loader.container = _Container({"../escape.txt": b"nope"})

        with tempfile.TemporaryDirectory() as parent:
            temp_dir = Path(parent) / "azure-download"
            temp_dir.mkdir()

            with patch.object(
                azure_document_loader.tempfile,
                "mkdtemp",
                return_value=str(temp_dir),
            ):
                with self.assertRaises(ValueError):
                    await loader.load()

            self.assertFalse(temp_dir.exists())

    async def test_load_removes_unused_directory_for_empty_container(self):
        loader = AzureDocumentLoader.__new__(AzureDocumentLoader)
        loader.container = _Container({})

        with tempfile.TemporaryDirectory() as parent:
            temp_dir = Path(parent) / "azure-download"
            temp_dir.mkdir()

            with patch.object(
                azure_document_loader.tempfile,
                "mkdtemp",
                return_value=str(temp_dir),
            ):
                file_paths = await loader.load()

            self.assertEqual(file_paths, [])
            self.assertFalse(temp_dir.exists())


if __name__ == "__main__":
    unittest.main()
