import asyncio
import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "report_store_async_io_testmod",
    ROOT / "backend/server/report_store.py",
)
REPORT_STORE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT_STORE_MODULE)
ReportStore = REPORT_STORE_MODULE.ReportStore


async def _heartbeat_completes_while(operation):
    heartbeat_ran = False

    async def heartbeat():
        nonlocal heartbeat_ran
        await asyncio.sleep(0.01)
        heartbeat_ran = True

    heartbeat_task = asyncio.create_task(heartbeat())
    await operation()
    completed_during_operation = heartbeat_ran
    await heartbeat_task
    return completed_during_operation


class ReportStoreAsyncIOTests(unittest.IsolatedAsyncioTestCase):
    async def test_read_does_not_block_event_loop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reports.json"
            path.write_text(
                json.dumps({"r1": {"id": "r1"}}),
                encoding="utf-8",
            )
            store = ReportStore(path)
            original_read_text = Path.read_text

            def slow_read_text(file_path, *args, **kwargs):
                time.sleep(0.05)
                return original_read_text(file_path, *args, **kwargs)

            with patch.object(Path, "read_text", slow_read_text):
                responsive = await _heartbeat_completes_while(
                    lambda: store.get_report("r1")
                )

        self.assertTrue(responsive)

    async def test_write_does_not_block_event_loop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reports.json"
            store = ReportStore(path)
            original_write_text = Path.write_text

            def slow_write_text(file_path, *args, **kwargs):
                time.sleep(0.05)
                return original_write_text(file_path, *args, **kwargs)

            with patch.object(Path, "write_text", slow_write_text):
                responsive = await _heartbeat_completes_while(
                    lambda: store.upsert_report("r1", {"id": "r1"})
                )

            stored = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(responsive)
        self.assertEqual(stored, {"r1": {"id": "r1"}})


if __name__ == "__main__":
    unittest.main()
