from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Any
import json
import os
from gpt_researcher.utils.websocket_manager import WebSocketManager
from .utils import write_md_to_pdf
from pydantic import BaseModel
from gpt_researcher.config.config import Config 

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


app = FastAPI()

app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")

templates = Jinja2Templates(directory="./frontend")

manager = WebSocketManager()


# Dynamic directory for outputs once first research is run
@app.on_event("startup")
def startup_event():
    if not os.path.isdir("outputs"):
        os.makedirs("outputs")
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

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
                if task and report_type:
                    report = await manager.start_streaming(task, report_type, websocket)
                    path = await write_md_to_pdf(report)
                    await websocket.send_json({"type": "path", "output": path})
                else:
                    print("Error: not enough parameters provided.")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@app.post("/update-config")
async def update_config(config_update: ConfigUpdateRequest):
    try:
        # Read existing config
        config_data = Config.read_config_from_file()

        # Update config
        config_data[config_update.key] = config_update.value

        # Write updated config to file
        Config.write_config_to_file(config_data)

        return {"message": "Configuration updated successfully"}
    except Exception as e:
        # Log the actual error for debugging
        print(f"Error updating configuration: {str(e)}")

        # Return a generic error message to the client
        raise HTTPException(status_code=500, detail="Error updating configuration")


@app.get("/get-config")
async def get_config():
    try:
        config_data = Config.read_config_from_file()
        config_descriptions = Config.config_description
        return {"config": config_data, "descriptions": config_descriptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
