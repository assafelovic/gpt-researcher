import os
import json
import re
import requests
from urllib.parse import quote
from pydantic import BaseModel
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.llm_utils import choose_agent
from agent.run import WebSocketManager

app = FastAPI()
app.mount("/site", StaticFiles(directory="client"), name="site")
app.mount("/static", StaticFiles(directory="client/static"), name="static")

class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str

@app.on_event("startup")
def startup_event():
    if not os.path.isdir("outputs"):
        os.makedirs("outputs")
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

templates = Jinja2Templates(directory="client")
manager = WebSocketManager()

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "report": None})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("start"):
                json_data = json.loads(data[6:])
                task = json_data.get("task")
                report_type = json_data.get("report_type")
                agent = json_data.get("agent")
                if agent == "Auto Agent":
                    agent_dict = choose_agent(task)
                    agent = agent_dict.get("agent")
                    agent_role_prompt = agent_dict.get("agent_role_prompt")
                else:
                    agent_role_prompt = None

                await websocket.send_json({"type": "logs", "output": f"Initiated an Agent: {agent}"})
                if task and report_type and agent:
                    await manager.start_streaming(task, report_type, agent, agent_role_prompt, websocket)
                else:
                    print("Error: not enough parameters provided.")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.post("/obsidian")
async def post_to_obsidian(content: str = Body(...)):
    first_heading_match = re.search(r"^#\s(.+)$", content, re.MULTILINE)
    filename = first_heading_match.group(1) if first_heading_match else 'default_filename'
    filename = re.sub(r"[:]", " -", filename)
    filename = re.sub(r"[#:/\\[\]|^]", "", filename)
    
    base_url = os.getenv("OBSIDIAN_URL")
    if not base_url.endswith('/'):
        base_url += '/'
    token = os.getenv("OBSIDIAN_TOKEN")
    url = f"{base_url}{quote(filename)}.md"
    
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/markdown'
    }
    response = requests.post(url, headers=headers, data=content.encode('utf-8'))

    if response.status_code != 204:
        raise HTTPException(status_code=400, detail="Error posting to Obsidian")

    return {"message": "File created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
