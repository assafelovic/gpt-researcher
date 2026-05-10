import importlib.util
from pathlib import Path

import pytest


PLAN_REVIEW_PATH = (
    Path(__file__).resolve().parents[1] /
    "multi_agents" / "agents" / "plan_review.py"
)
spec = importlib.util.spec_from_file_location(
    "plan_review",
    PLAN_REVIEW_PATH,
)
plan_review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_review)


def test_human_feedback_route_accepts_when_no_feedback():
    assert plan_review.route_human_feedback({"human_feedback": None}) == "accept"


def test_human_feedback_route_revises_until_limit():
    assert plan_review.route_human_feedback({
        "human_feedback": "add a section",
        "plan_revision_count": 2,
    }, max_plan_revisions=2) == "revise"


def test_human_feedback_route_raises_after_limit():
    with pytest.raises(plan_review.MaxPlanRevisionsExceededError):
        plan_review.route_human_feedback({
            "human_feedback": "try again",
            "plan_revision_count": 3,
        }, max_plan_revisions=2)


def test_human_feedback_route_can_disable_limit():
    assert plan_review.route_human_feedback({
        "human_feedback": "keep revising",
        "plan_revision_count": 99,
    }, max_plan_revisions=None) == "revise"
