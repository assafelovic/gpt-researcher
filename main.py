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

async def obsidian_command(command: str, url: str, token: str, filename: str, content: str = "") -> dict:
    """
    Executes a command in Obsidian.

    Args:
        command (str): The command to execute (e.g., "create", "open").
        url (str): The base URL of the Obsidian vault.
        token (str): The authorization token for accessing the Obsidian vault.
        filename (str): The name of the file to be created or opened, including the relative path within the vault.
        content (str): The content of the file to be created (only used for "create" command).

    Returns:
        dict: A dictionary with a message indicating the result of the command.

    Raises:
        HTTPException: If there was an error executing the command in Obsidian.
    """
    if command == "create":
        endpoint = f"vault/{quote(filename)}.md"
        method = "POST"
        data = content.encode('utf-8')
    elif command == "open":
        endpoint = f"open/{quote(filename)}.md?newLeaf=false"
        method = "GET"
        data = None
    else:
        raise ValueError("Invalid command")
    
    endpoint = re.sub(r"//+", "/", endpoint)
    
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/markdown'
    }
    response = requests.request(method, f"{url}{endpoint}", headers=headers, data=data)

    if response.status_code < 200 or response.status_code >= 300:
        raise HTTPException(status_code=response.status_code, detail=f"Error executing {command} command in Obsidian")

    return {"message": f"{command.capitalize()} command executed successfully"}

@app.post("/obsidian")
async def post_to_obsidian(content: str = Body(...)):
    first_heading_match = re.search(r"^#\s(.+)$", content, re.MULTILINE)
    filename = first_heading_match.group(1) if first_heading_match else 'default_filename'
    filename = re.sub(r"[:]", " -", filename)
    filename = re.sub(r"[#:/\\[\]|^]", "", filename)
    filename = f"{os.getenv('OBSIDIAN_FOLDER')}/{filename}"

    base_url = os.getenv("OBSIDIAN_URL")
    if not base_url.endswith('/'):
        base_url += '/'
    token = os.getenv("OBSIDIAN_TOKEN")
    
    await obsidian_command(command="create", url=base_url, token=token, filename=filename, content=content)
    await obsidian_command(command="open", url=base_url, filename=filename, token=token)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
