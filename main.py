#main.py

import os
from backend.server import app
from fastapi import Body
from rq import Queue
from redis import Redis
from worker import conn, process_report
from sf_researcher.utils.validators import ReportRequest
from dotenv import load_dotenv

load_dotenv()

LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

q = Queue(connection=conn)

@app.post("/report/compliance_report")
async def get_compliance_report(request: ReportRequest = Body(...)):
    job = q.enqueue(process_report, request.dict(), main_report_type="compliance_report", child_report_type="contact_report")
    return {"message": "Compliance report is being processed. You will receive the results via the Salesforce endpoint.", "job_id": job.id}

@app.post("/report/sales_report")
async def get_sales_report(request: ReportRequest = Body(...)):
    job = q.enqueue(process_report, request.dict(), main_report_type="sales_report", child_report_type="contact_report")
    return {"message": "Sales report is being processed. You will receive the results via the Salesforce endpoint.", "job_id": job.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)