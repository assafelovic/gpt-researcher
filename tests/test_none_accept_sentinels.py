"""Strict None/no acceptance sentinels for multi_agents loops.

Regression for #1881 (reviewer/fact-checker false-accept on substring "None")
and shared helpers for the human plan-approval gate (#1882).
"""

import importlib.util
from pathlib import Path

import pytest

SENTINEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "multi_agents"
    / "agents"
    / "utils"
    / "none_sentinels.py"
)
spec = importlib.util.spec_from_file_location("none_sentinels", SENTINEL_PATH)
none_sentinels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(none_sentinels)

is_none_accept_response = none_sentinels.is_none_accept_response
is_human_plan_approval = none_sentinels.is_human_plan_approval


def test_none_accept_exact_token():
    assert is_none_accept_response("None") is True
    assert is_none_accept_response("none") is True
    assert is_none_accept_response("  NONE  ") is True


def test_none_accept_optional_quotes():
    assert is_none_accept_response('"None"') is True
    assert is_none_accept_response("'none'") is True


def test_none_accept_rejects_critical_feedback_containing_none():
    critical = "None of the guideline criteria are met — cite sources."
    assert is_none_accept_response(critical) is False
    assert is_none_accept_response("Return None of these claims.") is False
    assert is_none_accept_response("The draft is None of the requirements") is False


def test_none_accept_rejects_empty_and_unrelated():
    assert is_none_accept_response("") is False
    assert is_none_accept_response(None) is False
    assert is_none_accept_response("looks good") is False


def test_human_plan_approval_exact_no_only():
    assert is_human_plan_approval("no") is True
    assert is_human_plan_approval("  NO  ") is True
    assert is_human_plan_approval("No") is True


def test_human_plan_approval_rejects_feedback_containing_no():
    assert is_human_plan_approval("not enough on evaluation methods") is False
    assert is_human_plan_approval("add a section on novel applications") is False
    assert is_human_plan_approval("nope, rewrite it") is False
    assert is_human_plan_approval(None) is False
    assert is_human_plan_approval("") is False
