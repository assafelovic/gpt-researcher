import builtins
import importlib
import os
import sys
import tempfile
import types
import typing
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


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


class LogFileUniquenessTests(unittest.TestCase):
    def test_same_task_in_same_second_uses_distinct_log_files(self):
        fake_uuid = SimpleNamespace(
            uuid4=Mock(
                side_effect=[
                    SimpleNamespace(hex="a" * 32),
                    SimpleNamespace(hex="b" * 32),
                ]
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                with (
                    patch.object(server_utils.time, "time", return_value=1000),
                    patch.object(server_utils, "uuid", fake_uuid, create=True),
                ):
                    first = server_utils.CustomLogsHandler(None, "same task")
                    second = server_utils.CustomLogsHandler(None, "same task")
            finally:
                os.chdir(previous_cwd)

        self.assertNotEqual(first.log_file, second.log_file)


if __name__ == "__main__":
    unittest.main()
