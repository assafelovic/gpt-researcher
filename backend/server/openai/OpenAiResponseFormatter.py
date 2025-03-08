import logging
from backend.server.openai.sse_websocket_adapter import (
    EventPosition,
    MessageType,
    SseFormatter,
)

import json
from typing import Iterable, Sequence

logger = logging.getLogger(__name__)


class OpenAiResponseFormatter(SseFormatter):
    think_tag_start = "\n<think>\n"
    think_tag_end = "\n</think>\n"

    def __init__(self, response_id: str, created_time: int, stream: bool):
        self.response_id = response_id
        self.created_time = created_time
        self.stream = stream
        self.thinking_done = False
        self.was_thinking = False
        self.messages: list[str] = []
        self.position = EventPosition.NONE

    def add_message(
        self, message: str, position: EventPosition, message_type: MessageType
    ):
        if self.stream:
            is_thinking = False
            if message_type == "logs":
                is_thinking = True

            ignore_message = False
            if self.thinking_done:
                if is_thinking:
                    # thinking is done, ignore the message
                    logger.debug(
                        f"Ignoring log messages after thinking is done: {message}"
                    )
                    ignore_message = True
            else:
                if is_thinking and not self.was_thinking:
                    self.messages.append(self.think_tag_start)

                if not is_thinking and self.was_thinking:
                    self.messages.append(self.think_tag_end)
                    self.thinking_done = True
            if not ignore_message:
                self.messages.append(message)
            self.was_thinking = is_thinking
        else:
            if message_type == "logs":
                message = ""
            self.messages.append(message)

        self.position |= position

    def stream_response(self) -> Iterable[str]:
        def build_chunk(message: str) -> str:
            delta = {"content": message} if message else {}
            if EventPosition.First in self.position:
                delta["role"] = "assistant"
                self.position &= ~EventPosition.First

            if EventPosition.Last in self.position:
                finish_reason = "stop"
                self.position &= ~EventPosition.Last
            else:
                finish_reason = None
            chunk = {
                "id": self.response_id,
                "object": "chat.completion.chunk",
                "created": self.created_time,
                "model": "gpt-researcher",
                "choices": [
                    {"index": 0, "delta": delta, "finish_reason": finish_reason}
                ],
            }
            return json.dumps(chunk)

        message_buffer = []
        i = 0
        while True:
            if i >= len(self.messages):
                break
            try:
                message = self.messages[i]
                message_buffer.append(message)
                # need to separate reasoning tokens and chat messages, to avoid confusing the client
                if i == len(self.messages) - 1 or message == self.think_tag_end:
                    yield build_chunk("".join(message_buffer))
                    message_buffer.clear()
            finally:
                i += 1

    def message_response(self) -> str:
        message = "".join(self.messages)
        return json.dumps(
            {
                "id": self.response_id,
                "object": "chat.completion",
                "created": self.created_time,
                "model": "gpt-researcher",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": message,
                        },
                        "finish_reason": "stop",
                        "index": 0,
                    }
                ],
            }
        )

    def on_response_generated(self):
        self.messages.clear()
        self.position = EventPosition.NONE

    def generate_response(self) -> str | Sequence[str]:
        if self.stream:
            response = tuple(self.stream_response())
        else:
            response = self.message_response()
        self.on_response_generated()
        return response
