from __future__ import annotations

import json

from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable, Coroutine

if TYPE_CHECKING:
    from logging import Logger

    from fastapi import WebSocket

logger: Logger = getLogger(__name__)


class HumanAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Coroutine[Any, Any, None]] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Coroutine[Any, Any, None]] | None = stream_output
        self.headers: dict[str, Any] | None = headers

    async def review_plan(
        self,
        research_state: dict,
    ) -> dict[str, Any]:
        logger.info(f"HumanAgent websocket: {self.websocket}")
        logger.info(f"HumanAgent stream_output: {self.stream_output}")
        task: dict[str, Any] = research_state.get("task", {})
        layout: str = research_state.get("sections", "")

        user_feedback: str | None = None

        if task.get("include_human_feedback"):
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
                    logger.info(f"Received response: {response}")
                    response_data: dict[str, Any] = json.loads(response)
                    if response_data.get("type") == "human_feedback":
                        user_feedback = response_data.get("content")
                    else:
                        logger.error(
                            f"Unexpected response type: {response_data.get('type')}",
                        )
                except Exception as e:
                    logger.error(f"Error receiving human feedback: {e}")
            # Otherwise, prompt the user for feedback in the console
            else:
                user_feedback = input(f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> ")

        if user_feedback and "no" in user_feedback.strip().casefold():
            user_feedback: str | None = None

        logger.info(f"User feedback before return: {user_feedback}")

        return {"human_feedback": user_feedback}
