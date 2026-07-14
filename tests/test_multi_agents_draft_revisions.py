import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "multi_agents" / "agents" / "draft_review.py"
spec = importlib.util.spec_from_file_location("draft_review", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_accept_when_no_review():
    assert mod.route_draft_review({"review": None}) == "accept"


def test_revise_until_limit():
    assert mod.route_draft_review(
        {"review": "fix sources", "draft_revision_count": 2},
        max_draft_revisions=2,
    ) == "revise"


def test_raises_after_limit():
    with pytest.raises(mod.MaxDraftRevisionsExceededError):
        mod.route_draft_review(
            {"review": "still bad", "draft_revision_count": 3},
            max_draft_revisions=2,
        )


def test_disable_limit():
    assert mod.route_draft_review(
        {"review": "again", "draft_revision_count": 99},
        max_draft_revisions=None,
    ) == "revise"
