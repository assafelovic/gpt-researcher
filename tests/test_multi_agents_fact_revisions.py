import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / "multi_agents" / "agents" / "fact_review.py"
spec = importlib.util.spec_from_file_location("fact_review", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_accept_none_notes():
    assert mod.route_fact_check({"fact_check_notes": None}) == "accept"


def test_revise_until_limit():
    assert mod.route_fact_check(
        {"fact_check_notes": "fix X", "fact_check_revision_count": 2},
        max_fact_check_revisions=2,
    ) == "revise"


def test_raises_past_limit():
    with pytest.raises(mod.MaxFactCheckRevisionsExceededError):
        mod.route_fact_check(
            {"fact_check_notes": "still bad", "fact_check_revision_count": 3},
            max_fact_check_revisions=2,
        )
