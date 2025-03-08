from enum import Flag, auto
from typing import (
    Any,
    AsyncIterator,
    Generator,
    Literal,
    Protocol,
    Sequence,
)
import asyncio


class EventPosition(Flag):
    NONE = 0
    First = auto()
    Last = auto()


MessageType = Literal["logs", "report", "chat"]


class SseFormatter(Protocol):
    def add_message(
        self, message: str, position: EventPosition, message_type: MessageType
    ): ...
    def generate_response(self) -> str | Sequence[str]: ...


class SseWebSocketAdapter:
    def __init__(self, formatter: SseFormatter):
        self.queue: asyncio.Queue[tuple[str, EventPosition, MessageType]] = (
            asyncio.Queue()
        )
        self.completed = False
        self.formatter = formatter
        self.is_first = True

    async def send_text(self, message: str):
        if len(message) == 0:
            return
        return await self._send_text(message, "chat")

    async def _send_text(self, message: str, message_type: MessageType):
        if self.completed:
            raise RuntimeError("connection is closed.")
        position: EventPosition = EventPosition.NONE
        if self.is_first:
            position |= EventPosition.First
            self.is_first = False
        await self.queue.put((message, position, message_type))

    async def send_json(self, data: dict):
        message_type = data.get("type", "chat")
        if message_type not in ("report", "chat"):
            message_type = "logs"

        message = ""
        content = str(data.get("content", ""))
        if content:
            message += content + "\n"

        output = str(data.get("output", ""))
        if output:
            message += output + "\n"
        await self._send_text(message, message_type)

    async def complete(self, message: str):
        if self.completed:
            return
        await self.queue.put((message, EventPosition.Last, "chat"))
        self.completed = True

    async def close(self):
        if self.is_first:
            await self.send_text("Error: Connection closed before any data was sent.")
        await self.complete("")

    async def get_full_response(self) -> str:
        while not self.completed and self.queue.empty():
            message, position, message_type = await self.queue.get()
            self.formatter.add_message(
                message,
                position,
                message_type,
            )
        response = self.formatter.generate_response()
        if not isinstance(response, str):
            raise RuntimeError("Response is not a string")
        return response

    def __await__(self) -> Generator[Any, None, str]:
        return self.get_full_response().__await__()

    async def stream(self) -> AsyncIterator[str]:
        while True:
            try:
                if self.completed and self.queue.empty():
                    return
                message, position, message_type = await self.queue.get()
                self.formatter.add_message(message, position, message_type)
                response = self.formatter.generate_response()
                if isinstance(response, str):
                    yield f"data: {response}\n\n"
                else:
                    for item in response:
                        yield f"data: {item}\n\n"
            except asyncio.CancelledError:
                await self.close()
                raise

    def __aiter__(self) -> AsyncIterator[str]:
        return self.stream()
