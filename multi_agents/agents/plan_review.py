DEFAULT_MAX_PLAN_REVISIONS = 3


class MaxPlanRevisionsExceededError(RuntimeError):
    """Raised when human feedback requests exceed the configured planning limit."""


def route_human_feedback(review, max_plan_revisions=DEFAULT_MAX_PLAN_REVISIONS):
    if review.get("human_feedback") is None:
        return "accept"

    if max_plan_revisions is None:
        return "revise"

    plan_revision_count = review.get("plan_revision_count", 0)
    if plan_revision_count > max_plan_revisions:
        raise MaxPlanRevisionsExceededError(
            "Plan revision limit exceeded. "
            f"Received {plan_revision_count} revision requests; "
            f"max_plan_revisions is {max_plan_revisions}."
        )

    return "revise"
