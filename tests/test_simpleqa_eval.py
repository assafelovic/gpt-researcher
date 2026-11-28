"""Offline tests for the SimpleQA grader parsing and question sampling."""

import pytest

from evals.simple_evals.simpleqa_eval import SimpleQAEval, parse_grade


class _Resp:
    def __init__(self, content):
        self.content = content


class _Grader:
    def __init__(self, reply):
        self.reply = reply

    def invoke(self, messages):
        return _Resp(self.reply)


@pytest.mark.parametrize("reply, grade", [
    ("A", "CORRECT"),
    ("B", "INCORRECT"),
    ("C", "NOT_ATTEMPTED"),
    ("A.", "CORRECT"),
    (" b \n", "INCORRECT"),
    ("(C)", "NOT_ATTEMPTED"),
    ("CORRECT", "CORRECT"),
    # Contains "CORRECT" as a substring; must not be read as CORRECT.
    ("INCORRECT", "INCORRECT"),
    ("The answer is INCORRECT.", "INCORRECT"),
    ("NOT ATTEMPTED", "NOT_ATTEMPTED"),
    ("NOT_ATTEMPTED", "NOT_ATTEMPTED"),
])
def test_parse_grade(reply, grade):
    assert parse_grade(reply) == grade


@pytest.mark.parametrize("reply", ["", "D", "maybe", "CORRECT or INCORRECT"])
def test_parse_grade_unreadable_returns_none(reply):
    assert parse_grade(reply) is None


def test_grade_response_incorrect_is_not_counted_correct():
    ev = SimpleQAEval.__new__(SimpleQAEval)
    ev.grader_model = _Grader("INCORRECT")
    assert ev.grade_response("q", "gold", "predicted") == "INCORRECT"


def test_sampling_reads_local_file_and_is_reproducible():
    a = SimpleQAEval(grader_model=None, num_examples=5, seed=7)
    b = SimpleQAEval(grader_model=None, num_examples=5, seed=7)
    assert [e["index"] for e in a.examples] == [e["index"] for e in b.examples]
    assert all({"problem", "answer"} <= e.keys() for e in a.examples)
