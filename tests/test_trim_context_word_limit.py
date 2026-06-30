"""Regression tests for trim_context_to_word_limit.

The function keeps the most recent context items within a word budget. The old
implementation ``break``ed on the first item that didn't fit. When the most
recent item alone exceeded the budget, that ``break`` fired on the first
iteration and discarded the ENTIRE context list -- including smaller, older
items that would have fit comfortably. The fix skips an oversized item and
keeps scanning, stopping only once the budget is actually exhausted.
"""

from gpt_researcher.skills.deep_research import trim_context_to_word_limit


def test_oversized_recent_item_does_not_drop_smaller_older_items():
    items = ["small one", "small two", "x " * 5000]  # newest is huge
    out = trim_context_to_word_limit(items, max_words=100)
    # The two small items must survive even though the newest is oversized.
    assert "small one" in out
    assert "small two" in out
    assert ("x " * 5000) not in out


def test_items_within_budget_all_kept_in_order():
    items = ["a b", "c d", "e f"]
    out = trim_context_to_word_limit(items, max_words=100)
    assert out == ["a b", "c d", "e f"]


def test_budget_stops_once_exhausted():
    # Each item is 50 words; budget 100 -> only the two most recent fit.
    items = ["w " * 50, "x " * 50, "y " * 50, "z " * 50]
    out = trim_context_to_word_limit(items, max_words=100)
    assert out == ["y " * 50, "z " * 50]
