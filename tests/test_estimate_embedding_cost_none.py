"""estimate_embedding_cost must tolerate None/non-str arguments and empty/None docs."""

import importlib.util
import pathlib

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "utils"
    / "costs.py"
)
_spec = importlib.util.spec_from_file_location("_costs_ut", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_none_docs_return_zero():
    assert _mod.estimate_embedding_cost(None, None) == 0.0
    assert _mod.estimate_embedding_cost("text-embedding-3-small", None) == 0.0


def test_empty_docs_return_zero():
    assert _mod.estimate_embedding_cost("text-embedding-3-small", []) == 0.0
    assert _mod.estimate_embedding_cost(None, []) == 0.0


def test_none_or_non_str_model_uses_fallback():
    cost_none = _mod.estimate_embedding_cost(None, ["hello world"])
    assert isinstance(cost_none, float)
    assert cost_none > 0.0

    cost_int = _mod.estimate_embedding_cost(12345, ["hello world"])
    assert isinstance(cost_int, float)
    assert cost_int > 0.0


def test_string_doc_tolerated():
    cost = _mod.estimate_embedding_cost("text-embedding-3-small", "hello world")
    assert isinstance(cost, float)
    assert cost > 0.0


def test_non_openai_model_does_not_raise():
    cost = _mod.estimate_embedding_cost("nomic-embed-text", ["hello world"])
    assert isinstance(cost, float)
    assert cost > 0.0
