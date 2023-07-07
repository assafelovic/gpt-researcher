from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from agent.run import run_agent
from markdown import markdown


class ResearchRequest(BaseModel):
    task: str
    report_type: str

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "report": None})

@app.post("/")
async def create_report(request: Request, task: str = Form(...), report_type: str = Form(...)):
    report, path = await run_agent(task, report_type)
    html_report = markdown(report)
    return templates.TemplateResponse('index.html', {"request": request, "report": html_report, "path": path})
