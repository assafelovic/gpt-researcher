import json
import os
import re
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md
from backend.websocket_manager import WebSocketManager

import shutil
from multi_agents.main import run_research_task
from gpt_researcher.document.document import DocumentLoader
from gpt_researcher.master.actions import stream_output


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str

class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''

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
    return templates.TemplateResponse(
        "index.html", {"request": request, "report": None}
    )


# Add the sanitize_filename function here
def sanitize_filename(filename):
    return re.sub(r"[^\w\s-]", "", filename).strip()

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
                tone = json_data.get("tone")
                headers = json_data.get("headers", {})
                filename = f"task_{int(time.time())}_{task}"
                sanitized_filename = sanitize_filename(
                    filename
                )  # Sanitize the filename
                report_source = json_data.get("report_source")
                if task and report_type:
                    report = await manager.start_streaming(
                        task, report_type, report_source, tone, websocket, headers
                    )
                    # Ensure report is a string
                    if not isinstance(report, str):
                        report = str(report)

                    # Saving report as pdf
                    pdf_path = await write_md_to_pdf(report, sanitized_filename)
                    # Saving report as docx
                    docx_path = await write_md_to_word(report, sanitized_filename)
                    # Returning the path of saved report files
                    md_path = await write_text_to_md(report, sanitized_filename)
                    await websocket.send_json(
                        {
                            "type": "path",
                            "output": {
                                "pdf": pdf_path,
                                "docx": docx_path,
                                "md": md_path,
                            },
                        }
                    )
                else:
                    print("Error: not enough parameters provided.")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.post("/api/multi_agents")
async def run_multi_agents():
    websocket = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        report = await run_research_task("Is AI in a hype cycle?", websocket, stream_output)
        return {"report": report}
    else:
        return JSONResponse(status_code=400, content={"message": "No active WebSocket connection"})

@app.get("/getConfig")
async def get_config(
    langchain_api_key: str = Header(None),
    openai_api_key: str = Header(None),
    tavily_api_key: str = Header(None),
    google_api_key: str = Header(None),
    google_cx_key: str = Header(None),
    bing_api_key: str = Header(None),
    serpapi_api_key: str = Header(None),
    serper_api_key: str = Header(None),
    searx_url: str = Header(None)
):
    config = {
        "LANGCHAIN_API_KEY": langchain_api_key if langchain_api_key else os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key if openai_api_key else os.getenv("OPENAI_API_KEY", ""),
        "TAVILY_API_KEY": tavily_api_key if tavily_api_key else os.getenv("TAVILY_API_KEY", ""),
        "GOOGLE_API_KEY": google_api_key if google_api_key else os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key if google_cx_key else os.getenv("GOOGLE_CX_KEY", ""),
        "BING_API_KEY": bing_api_key if bing_api_key else os.getenv("BING_API_KEY", ""),
        "SERPAPI_API_KEY": serpapi_api_key if serpapi_api_key else os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key if serper_api_key else os.getenv("SERPER_API_KEY", ""),
        "SEARX_URL": searx_url if searx_url else os.getenv("SEARX_URL", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "DOC_PATH": os.getenv("DOC_PATH", ""),
        "RETRIEVER": os.getenv("RETRIEVER", "")
    }
    return config

@app.post("/setConfig")
async def set_config(config: ConfigRequest):
    os.environ["ANTHROPIC_API_KEY"] = config.ANTHROPIC_API_KEY
    os.environ["TAVILY_API_KEY"] = config.TAVILY_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = config.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_API_KEY"] = config.LANGCHAIN_API_KEY
    os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
    os.environ["DOC_PATH"] = config.DOC_PATH
    os.environ["RETRIEVER"] = config.RETRIEVER
    os.environ["GOOGLE_API_KEY"] = config.GOOGLE_API_KEY
    os.environ["GOOGLE_CX_KEY"] = config.GOOGLE_CX_KEY
    os.environ["BING_API_KEY"] = config.BING_API_KEY
    os.environ["SERPAPI_API_KEY"] = config.SERPAPI_API_KEY
    os.environ["SERPER_API_KEY"] = config.SERPER_API_KEY
    os.environ["SEARX_URL"] = config.SEARX_URL
    return {"message": "Config updated successfully"}

# Enable CORS for your frontend domain (adjust accordingly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define DOC_PATH
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")
if not os.path.exists(DOC_PATH):
    os.makedirs(DOC_PATH)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(DOC_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"File uploaded to {file_path}")

    # Load documents after upload
    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": file.filename, "path": file_path}


@app.get("/files/")
async def list_files():
    files = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    file_path = os.path.join(DOC_PATH, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")
        return {"message": "File deleted successfully"}
    else:
        print(f"File not found: {file_path}")
        return JSONResponse(status_code=404, content={"message": "File not found"})