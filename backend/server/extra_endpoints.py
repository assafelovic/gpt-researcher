from __future__ import annotations

import logging
import os
import time

from typing import TYPE_CHECKING, Any

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.server.server_utils import sanitize_filename
from backend.utils import write_md_to_pdf, write_md_to_word

if TYPE_CHECKING:
    from gpt_researcher.utils.enum import Tone

    from backend.server.server import ResearchRequest
    from backend.server.websocket_manager import run_agent


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


@app.get("/report/{research_id}")
async def read_report(request: Request, research_id: str) -> dict[str, str] | FileResponse:
    docx_path: str = os.path.join("outputs", f"{research_id}.docx")
    if not os.path.exists(docx_path):
        return {"message": "Report not found."}
    return FileResponse(docx_path)


async def write_report(
    research_request: ResearchRequest,
    research_id: str = None,
) -> dict[str, Any]:
    report_information: tuple[str, Any] = await run_agent(
        task=research_request.task,
        report_type=research_request.report_type,
        report_source=research_request.report_source,
        source_urls=[],
        document_urls=[],
        tone=Tone[research_request.tone],
        websocket=None,
        stream_output=None,
        headers=research_request.headers,
        query_domains=[],
        config_path="",
        return_researcher=True,
    )

    docx_path: str = await write_md_to_word(report_information[0], research_id)
    pdf_path: str = await write_md_to_pdf(report_information[0], research_id)
    if research_request.report_type != "multi_agents":
        report, researcher = report_information
        response = {
            "research_id": research_id,
            "research_information": {
                "source_urls": researcher.get_source_urls(),
                "research_costs": researcher.get_costs(),
                "visited_urls": list(researcher.visited_urls),
                "research_images": researcher.get_research_images(),
                # "research_sources": researcher.get_research_sources(),  # Raw content of sources may be very large
            },
            "report": report,
            "docx_path": docx_path,
            "pdf_path": pdf_path,
        }
    else:
        response: dict[str, str] = {"research_id": research_id, "report": "", "docx_path": docx_path, "pdf_path": pdf_path}

    return response


@app.post("/report/")
async def generate_report(research_request: ResearchRequest, background_tasks: BackgroundTasks) -> dict[str, str] | dict[str, Any]:
    research_id: str = sanitize_filename(f"task_{int(time.time())}_{research_request.task}")

    if research_request.generate_in_background:
        background_tasks.add_task(write_report, research_request=research_request, research_id=research_id)
        return {"message": "Your report is being generated in the background. Please check back later.", "research_id": research_id}
    else:
        response: dict[str, str] | dict[str, Any] = await write_report(research_request, research_id)
        return response
