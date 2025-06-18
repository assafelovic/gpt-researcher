from __future__ import annotations

import json

from typing import Any, Awaitable, Callable

from fastapi import WebSocket


class HumanAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.headers: dict[str, str] = headers or {}

    async def review_plan(self, research_state: dict[str, Any]) -> dict[str, Any]:
        print(f"HumanAgent websocket: {self.websocket}")
        print(f"HumanAgent stream_output: {self.stream_output}")
        task: dict[str, Any] = research_state.get("task")
        layout: list[str] = research_state.get("sections")

        user_feedback = None

        if task.get("include_human_feedback") is True:
            # Stream response to the user if a websocket is provided (such as from web app)
            if self.websocket is not None and self.stream_output is not None:
                try:
                    await self.stream_output(
                        "human_feedback",
                        "request",
                        f"Any feedback on this plan of topics to research? {layout}? If not, please reply with 'no'.",
                        self.websocket,
                    )
                    response: str = await self.websocket.receive_text()
                    print(f"Received response: {response}", flush=True)
                    response_data: dict[str, Any] = json.loads(response)
                    if response_data.get("type") == "human_feedback":
                        user_feedback: str | None = response_data.get("content")
                    else:
                        print(
                            f"Unexpected response type: {response_data.get('type')}",
                            flush=True,
                        )
                except Exception as e:
                    print(f"Error receiving human feedback: {e}", flush=True)
            # Otherwise, prompt the user for feedback in the console
            else:
                user_feedback: str | None = input(f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> ")

        if user_feedback and "no" in user_feedback.strip().lower():
            user_feedback = None

        print(f"User feedback before return: `{user_feedback}`")

        return {"human_feedback": user_feedback}
