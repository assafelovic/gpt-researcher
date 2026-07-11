DEFAULT_MAX_DRAFT_REVISIONS = 3


class MaxDraftRevisionsExceededError(RuntimeError):
    """Raised when reviewer/reviser rounds exceed the configured draft limit."""


def route_draft_review(draft, max_draft_revisions=DEFAULT_MAX_DRAFT_REVISIONS):
    """Return accept | revise for the editor review loop.

    * ``review is None`` → accept (including after a hard ceiling force-accept
      where the caller clears review).
    * ``max_draft_revisions is None`` → never force-accept (operator opt-out).
    * ``draft_revision_count > max`` → raise so the edge can force-accept
      gracefully rather than hit LangGraph's recursion_limit.
    """
    if draft.get("review") is None:
        return "accept"

    if max_draft_revisions is None:
        return "revise"

    count = draft.get("draft_revision_count", 0)
    if count > max_draft_revisions:
        raise MaxDraftRevisionsExceededError(
            "Draft revision limit exceeded. "
            f"Received {count} revision rounds; "
            f"max_draft_revisions is {max_draft_revisions}."
        )

    return "revise"
