import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "openalex" / "openalex.py"


def _load():
    requests_mod = types.ModuleType("requests")
    class RequestException(Exception):
        pass
    requests_mod.RequestException = RequestException
    requests_mod.get = MagicMock()
    sys.modules["requests"] = requests_mod
    for key in list(sys.modules):
        if "openalex.openalex" in key:
            sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.openalex.openalex_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, requests_mod


class OpenAlexMalformedTests(unittest.TestCase):
    def test_skips_non_dict_and_guards_abstract(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "results": [
                {
                    "title": "Paper",
                    "id": "https://openalex.org/W1",
                    "abstract_inverted_index": {"hello": [0], "world": [1]},
                    "best_oa_location": {},
                    "primary_location": {},
                },
                "bad",
                {
                    "title": "Broken abstract",
                    "id": "https://openalex.org/W2",
                    "abstract_inverted_index": "not-a-dict",
                        "best_oa_location": {},
                    "primary_location": {},
                },
            ]
        }
        requests_mod.get.return_value = resp
        out = mod.OpenAlexSearch("q").search()
        self.assertEqual(out[0]["href"], "https://openalex.org/W1")
        self.assertEqual(out[0]["body"], "hello world")
        self.assertEqual(out[1]["href"], "https://openalex.org/W2")
        self.assertEqual(out[1]["body"], "Abstract not available")

    def test_non_dict_payload(self):
        mod, requests_mod = _load()
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = ["nope"]
        requests_mod.get.return_value = resp
        self.assertEqual(mod.OpenAlexSearch("q").search(), [])


if __name__ == "__main__":
    unittest.main()
