from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine

from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket

TEMPLATE = """You are an expert research article reviewer. \
Your goal is to review research drafts and provide feedback to the reviser only based on specific guidelines. \
"""


class ReviewerAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]] | None = stream_output
        self.headers: dict[str, str] = {} if headers is None else headers

    async def review_draft(
        self,
        draft_state: dict,
    ) -> dict[str, Any] | None:
        """Review a draft article.

        Args:
            draft_state (dict): The state of the draft article.

        Returns:
            str: The feedback for the reviser.
        """
        task: dict[str, Any] = draft_state.get("task", {})
        guidelines: str = "- ".join(guideline for guideline in task.get("guidelines", []))
        revision_notes: str = draft_state.get("revision_notes", "")

        revise_prompt = f"""The reviser has already revised the draft based on your previous review notes with the following feedback:
{revision_notes}\n
Please provide additional feedback ONLY if critical since the reviser has already made changes based on your previous feedback.
If you think the article is sufficient or that non critical revisions are required, please aim to return None.
"""

        review_prompt = f"""You have been tasked with reviewing the draft which was written by a non-expert based on specific guidelines.
Please accept the draft if it is good enough to publish, or send it for revision, along with your notes to guide the revision.
If not all of the guideline criteria are met, you should send appropriate revision notes.
If the draft meets all the guidelines, please return None.
{revise_prompt if revision_notes else ""}

Guidelines: {guidelines}\nDraft: {draft_state.get("draft")}\n
"""
        prompt: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": TEMPLATE,
            },
            {
                "role": "user",
                "content": review_prompt,
            },
        ]

        response: dict[str, Any] = await call_model(prompt, model=task.get("model", ""))

        if task.get("verbose"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "review_feedback",
                    f"Review feedback is: {response}...",
                    self.websocket,
                )
            else:
                print_agent_output(f"Review feedback is: {response}...", agent="REVIEWER")

        if "None" in response:
            return None
        return response

    async def run(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        task: dict[str, Any] = draft_state.get("task", {})
        guidelines: list[str] = task.get("guidelines", [])
        to_follow_guidelines: bool = task.get("follow_guidelines", False)
        review: dict[str, Any] | None = None
        if to_follow_guidelines:
            print_agent_output("Reviewing draft...", agent="REVIEWER")

            if task.get("verbose"):
                print_agent_output(
                    f"Following guidelines {guidelines}...",
                    agent="REVIEWER",
                )

            review = await self.review_draft(draft_state)
        else:
            print_agent_output("Ignoring guidelines...", agent="REVIEWER")
        return {"review": review}
