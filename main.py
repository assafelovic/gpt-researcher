from backend.server import app
from dotenv import load_dotenv
load_dotenv()

from fastapi import Body
from typing import List, Optional, Dict
from pydantic import BaseModel

from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport
from gpt_researcher.utils.validators import CompanyReport
from rq import Queue
from worker import conn, process_compliance_report

q = Queue(connection=conn)

class ComplianceReportRequest(BaseModel):
    query: str
    salesforce_id: str
    directors: Optional[List[str]] = []
    directors: Optional[List[str]] = []
    include_domains: Optional[List[str]] = []
    exclude_domains: Optional[List[str]] = []
    parent_sub_queries: Optional[List[str]] = []
    child_sub_queries: Optional[List[str]] = []

@app.post("/report/compliance_report")
async def get_compliance_report(request: ComplianceReportRequest = Body(...)):
    job = q.enqueue(process_compliance_report, request.dict())
    return {"message": "Compliance report is being processed. You will receive the results via the Salesforce endpoint.", "job_id": job.id}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)