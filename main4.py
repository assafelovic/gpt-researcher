#main.py

from backend.server import app
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Body, BackgroundTasks
from typing import List, Optional, Dict
# from pydantic import BaseModel, Field
from pydantic.v1 import BaseModel

from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport
from gpt_researcher.utils.validators import CompanyReport

from rq import Queue
from redis import Redis
from worker import conn
import asyncio

print(f"In main.py: BaseModel type: {type(BaseModel)}")

class ComplianceReportRequest(BaseModel):
    query: str
    subtopics: Optional[List[str]] = []
    directors: Optional[List[str]] = []
    include_domains: Optional[List[str]] = []
    exclude_domains: Optional[List[str]] = []
    parent_sub_queries: Optional[List[str]] = []
    child_sub_queries: Optional[List[str]] = []

app = FastAPI()
q = Queue(connection=conn)

async def generate_compliance_report(request: ComplianceReportRequest):
    from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport
    researcher = CustomDetailedReport(
        query=request.query,
        source_urls=None,
        config_path="",
        subtopics=request.subtopics,
        directors=request.directors,
        include_domains=request.include_domains,
        exclude_domains=request.exclude_domains,
        parent_sub_queries=request.parent_sub_queries,
        child_sub_queries=request.child_sub_queries
    )
    report = await researcher.run()
    return report

def sync_generate_compliance_report(request: ComplianceReportRequest):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(generate_compliance_report(request))
    return result

@app.post("/report/compliance_report", response_model=CompanyReport)
async def get_compliance_report(background_tasks: BackgroundTasks, request: ComplianceReportRequest = Body(...)):
    job = q.enqueue(sync_generate_compliance_report, request)
    return {"message": "Report generation started.", "job_id": job.get_id()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)