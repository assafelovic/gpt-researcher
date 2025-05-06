from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine

from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket


SAMPLE_REVISION_NOTES = """
{
    "draft": {
        "draft title": The revised draft that you are submitting for review
    },
    "revision_notes": Your message to the reviewer about the changes you made to the draft based on their feedback
}
"""


class ReviserAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]] | None = stream_output
        self.headers: dict[str, Any] = {} if headers is None else headers

    async def revise_draft(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Review a draft article.

        Args:
            draft_state: The state of the draft

        Returns:
            The revised draft
        """
        review: str = draft_state.get("review", "") or ""
        task: dict[str, Any] = draft_state.get("task", {}) or {}
        model: str = task.get("model", "") or ""
        if not model or not model.strip():
            raise ValueError("Model is required but not found in task from draft_state")

        draft_report: str = draft_state.get("draft", "") or ""
        if not draft_report or not draft_report.strip():
            raise ValueError("Draft is required but not found in draft_state")

        prompt: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": "You are an expert writer. Your goal is to revise drafts based on reviewer notes.",
            },
            {
                "role": "user",
                "content": f"""Draft:\n{draft_report}\n\nReviewer's notes:\n{review}\n\n
You have been tasked by your reviewer with revising the following draft, which was written by a non-expert.
If you decide to follow the reviewer's notes, please write a new draft and make sure to address all of the points they raised.
Please keep all other aspects of the draft the same.
You MUST return nothing but a JSON in the following format:
{SAMPLE_REVISION_NOTES}
""",
            },
        ]

        response: dict[str, Any] = await call_model(
            prompt,
            model=model,
            response_format="json",
        )
        return response

    async def run(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        print_agent_output("Rewriting draft based on feedback...", agent="REVISOR")
        revision: dict[str, Any] | list[Any] | tuple[Any, list[dict[str, str]]] = await self.revise_draft(draft_state)
        if not isinstance(revision, dict):
            raise ValueError(f"Revision is not a dictionary, instead was {revision.__class__.__name__}: {revision!r}")

        task: dict[str, Any] = draft_state.get("task", {})
        if task and task.get("verbose"):
            revision_notes: str = revision.get("revision_notes", "")
            if not self.websocket or not self.stream_output:
                print_agent_output(f"Revision notes: {revision_notes}", agent="REVISOR")
                return revision
            await self.stream_output(
                "logs",
                "revision_notes",
                f"Revision notes: {revision_notes}",
                self.websocket,
            )

        return {
            "draft": revision.get("draft"),
            "revision_notes": revision.get("revision_notes"),
        }
