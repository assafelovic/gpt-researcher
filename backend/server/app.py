from __future__ import annotations

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.chat.chat import ChatAgentWithMemory

logger: logging.Logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Welcome to GPT Researcher"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_agent = ChatAgentWithMemory(report="Sample report", config_path="path/to/config", headers={})
    try:
        while True:
            data = await websocket.receive_text()
            await chat_agent.chat(data, websocket)
    except WebSocketDisconnect:
        await websocket.close()
