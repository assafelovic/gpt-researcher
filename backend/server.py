from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from backend.websocket_manager import WebSocketManager
from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md
import time
import json
import os


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
                filename = f"task_{int(time.time())}_{task}"
                if task and report_type:
                    report = await manager.start_streaming(task, report_type, websocket)
                    # Saving report as pdf
                    pdf_path = await write_md_to_pdf(report, filename)
                    # Saving report as docx
                    docx_path = await write_md_to_word(report, filename)
                    # Returning the path of saved report files
                    md_path = await write_text_to_md(report, filename)
                    await websocket.send_json({"type": "path", "output": {"pdf": pdf_path, "docx": docx_path, "md": md_path}})
                else:
                    print("Error: not enough parameters provided.")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)

