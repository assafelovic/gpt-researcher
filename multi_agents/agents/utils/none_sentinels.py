"""Strict parsers for LLM / human "none" / "no" acceptance sentinels.

Substring checks (``"None" in response``, ``"no" in feedback``) false-accept
review notes like "None of the criteria are met" or human plan feedback like
"not enough cost data". Keep the sentinels exact (optional surrounding
quotes / whitespace) so real critical notes are never treated as approval.
"""

from __future__ import annotations


def is_none_accept_response(response: str | None) -> bool:
    """True only when *response* is exactly the accept sentinel ``None``.

    Accepts optional surrounding whitespace and a single pair of matching
    ``'`` / ``"`` quotes (models often quote the token). Empty / ``None``
    inputs are not treated as acceptance — callers that meant "no review"
    should pass that state explicitly rather than lean on empty strings.
    """
    if response is None:
        return False
    if not isinstance(response, str):
        response = str(response)
    text = response.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text.lower() == "none"


def is_human_plan_approval(feedback: str | None) -> bool:
    """True only when *feedback* is exactly the cancel/approve sentinel ``no``.

    The human-feedback prompt asks users to reply with ``no`` when the plan
    needs no changes. Matching the whole (normalized) string avoids dropping
    real revision requests that merely contain the letters ``no``
    (e.g. "not enough on evaluation", "novel methods").
    """
    if feedback is None:
        return False
    if not isinstance(feedback, str):
        feedback = str(feedback)
    return feedback.strip().lower() == "no"
