"""estimate_llm_cost must tolerate None/non-str arguments."""
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


def test_none_inputs_return_zeroish():
    assert _mod.estimate_llm_cost(None, None) == 0.0


def test_mixed_none_does_not_raise():
    cost = _mod.estimate_llm_cost("hello world", None)
    assert isinstance(cost, float)
    assert cost > 0


def test_non_str_coerced():
    cost = _mod.estimate_llm_cost(12345, ["a", "b"])
    assert isinstance(cost, float)
    assert cost > 0
