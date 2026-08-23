"""OpenAlex location fields must tolerate non-dict API shapes."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "gpt_researcher" / "retrievers" / "openalex" / "openalex.py"


def _load():
    name = "gptr_openalex_under_test"
    spec = importlib.util.spec_from_file_location(name, MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_pick_href_non_dict_locations_fall_back_to_id():
    mod = _load()
    href = mod.OpenAlexSearch._pick_href(
        {
            "best_oa_location": "unexpected",
            "primary_location": [],
            "id": "https://openalex.org/W1",
        }
    )
    assert href == "https://openalex.org/W1"


def test_pick_href_prefers_pdf_when_dict():
    mod = _load()
    href = mod.OpenAlexSearch._pick_href(
        {
            "best_oa_location": {"pdf_url": "https://example.com/a.pdf"},
            "id": "https://openalex.org/W1",
        }
    )
    assert href == "https://example.com/a.pdf"
