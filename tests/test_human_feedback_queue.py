import asyncio
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


class FakeSocket:
    """Stands in for a FastAPI WebSocket: scripted incoming messages, recorded outgoing ones."""

    def __init__(self, incoming):
        self.incoming = asyncio.Queue()
        for message in incoming:
            self.incoming.put_nowait(message)
        self.sent = []
        self.state = types.SimpleNamespace()

    async def receive_text(self):
        message = await self.incoming.get()
        if message is None:
            from fastapi import WebSocketDisconnect

            raise WebSocketDisconnect(code=1000)
        return message

    async def send_json(self, data):
        self.sent.append(data)

    async def send_text(self, data):
        self.sent.append(data)


def test_is_human_feedback_message():
    from server.server_utils import is_human_feedback_message

    assert is_human_feedback_message(json.dumps({"type": "human_feedback", "content": "no"}))
    assert not is_human_feedback_message('start {"task": "x"}')
    assert not is_human_feedback_message('"just a string"')
    assert not is_human_feedback_message("ping")


@pytest.mark.asyncio
async def test_feedback_reaches_the_running_task_instead_of_being_dropped(monkeypatch):
    from server import server_utils

    received = asyncio.get_running_loop().create_future()

    async def fake_start(websocket, data, manager):
        received.set_result(json.loads(await websocket.state.human_feedback.get())["content"])

    monkeypatch.setattr(server_utils, "handle_start_command", fake_start)
    feedback = json.dumps({"type": "human_feedback", "content": "Add a section on costs"})
    socket = FakeSocket(['start {"task": "x"}', feedback])

    loop = asyncio.create_task(server_utils.handle_websocket_communication(socket, manager=None))
    assert await asyncio.wait_for(received, 2) == "Add a section on costs"
    assert not any(isinstance(m, dict) and m.get("content") == "warning" for m in socket.sent)
    socket.incoming.put_nowait(None)
    with pytest.raises(Exception):
        await asyncio.wait_for(loop, 2)


@pytest.mark.asyncio
async def test_human_agent_reads_feedback_from_the_queue():
    from multi_agents.agents.human import HumanAgent

    socket = FakeSocket([])
    socket.state.human_feedback = asyncio.Queue()
    socket.state.human_feedback.put_nowait(json.dumps({"type": "human_feedback", "content": "Drop section 3"}))
    handler = types.SimpleNamespace(websocket=socket)
    streamed = []

    async def stream_output(kind, content, output, websocket):
        streamed.append((kind, content))

    agent = HumanAgent(handler, stream_output)
    result = await agent.review_plan({"task": {"include_human_feedback": True}, "sections": ["A", "B", "C"]})
    assert streamed == [("human_feedback", "request")]
    assert result["human_feedback"] == "Drop section 3"
    assert result["plan_revision_count"] == 1
