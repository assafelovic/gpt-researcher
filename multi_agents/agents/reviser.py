from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import WebSocket

from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output


sample_revision_notes = """
{
  "draft": {
    draft title: The revised draft that you are submitting for review
  },
  "revision_notes": Your message to the reviewer about the changes you made to the draft based on their feedback
}
"""


class ReviserAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.headers: dict[str, str] = {} if headers is None else headers

    async def revise_draft(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Review a draft article.

        Args:
            draft_state (dict[str, Any]): The draft state.

        Returns:
            dict[str, Any]: The revision state.
        """
        review: str | None = draft_state.get("review")
        task: dict[str, Any] = draft_state.get("task")
        draft_report: str | None = draft_state.get("draft")
        if draft_report is None:
            raise ValueError("Draft is None")
        if review is None:
            raise ValueError("Review is None")
        prompt: list[dict[str, str]] = [
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
{sample_revision_notes}

Please return the JSON only, no other text or comments.
""",
            },
        ]

        response: dict[str, Any] = await call_model(
            prompt,
            model=task.get("model"),
            response_format="json",
        )
        return response

    async def run(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Run the reviser agent.

        Args:
            draft_state (dict[str, Any]): The draft state.

        Returns:
            dict[str, Any]: The revision state.
        """
        print_agent_output("Rewriting draft based on feedback...", agent="REVISOR")
        revision: dict[str, Any] = await self.revise_draft(draft_state)

        if draft_state.get("task", {}).get("verbose"):
            if self.websocket is not None and self.stream_output is not None:
                await self.stream_output(
                    "logs",
                    "revision_notes",
                    f"Revision notes: {revision.get('revision_notes')}",
                    self.websocket,
                )
            else:
                print_agent_output(f"Revision notes: {revision.get('revision_notes')}", agent="REVISOR")

        return {
            "draft": revision.get("draft"),
            "revision_notes": revision.get("revision_notes"),
        }
