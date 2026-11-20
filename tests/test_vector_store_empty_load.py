"""Empty scrape batches must not be sent to a vector-store backend."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "gpt_researcher/vector_store/vector_store.py"

# Existing tests replace LangChain modules in sys.modules. A fresh interpreter
# exercises the real Document and splitter without depending on collection order.
RUN_LOAD = r'''
import importlib.util
import json
import socket
import sys
def block_network(self, address):
    raise RuntimeError("Network disabled for vector-store test")
socket.socket.connect = block_network

from langchain_core.documents import Document

spec = importlib.util.spec_from_file_location("vector_store_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RecordingStore:
    def __init__(self):
        self.batches = []
    def add_documents(self, documents):
        if not documents:
            raise ValueError("backend does not accept an empty embedding batch")
        self.batches.append(documents)

store = RecordingStore()
result = module.VectorStoreWrapper(store).load(json.loads(sys.argv[2]))
assert result is None
if sys.argv[3] == "empty":
    assert store.batches == []
else:
    assert len(store.batches) == 1
    documents = store.batches[0]
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].page_content == "research evidence"
    assert documents[0].metadata["source"] == "https://example.com/source"
'''


def run_load(data, expected):
    result = subprocess.run(
        [sys.executable, "-c", RUN_LOAD, str(MODULE_PATH), json.dumps(data), expected],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("data", [
    [],
    [None, {"raw_content": None}],
    [{"raw_content": "", "url": "https://example.com"}],
    [{"raw_content": " \n\t", "url": "https://example.com"}],
])
def test_empty_load_does_not_write_to_backend(data):
    run_load(data, "empty")


@pytest.mark.parametrize("include_skipped_rows", [False, True])
def test_nonempty_load_preserves_content_and_source(include_skipped_rows):
    data = [{"raw_content": "research evidence", "url": "https://example.com/source"}]
    if include_skipped_rows:
        data = [None, {"raw_content": None}] + data
    run_load(data, "valid")
