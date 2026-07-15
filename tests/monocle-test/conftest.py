"""Pytest scaffold for the gpt-researcher Monocle test suite.

Enables Monocle tracing, loads the repo `.env`, and exposes ``run_gptresearcher``
-- the single entry a live test uses to drive the multi-agent workflow under
instrumentation. gpt-researcher's ``ChiefEditorAgent`` is asyncio-based, so the
entry is an ``async def`` and is driven live via ``validator.test_workflow_async``.
"""
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from monocle_apptrace import setup_monocle_telemetry

HERE = Path(__file__).resolve().parent
TRACES = HERE / "traces"
REPO_ROOT = HERE.parent.parent  # tests/monocle-test -> tests -> repo root

setup_monocle_telemetry(workflow_name="gpt-researcher")
load_dotenv(REPO_ROOT / ".env")

# gpt-researcher's web retriever defaults to Tavily; fall back to Serper when no
# Tavily key is configured, so the live test has a working retriever without the
# caller having to remember to set RETRIEVER.
if not os.environ.get("TAVILY_API_KEY"):
    os.environ.setdefault("RETRIEVER", "serper")

# multi_agents (the live entry point) lives at the repo root, so make it importable.
sys.path.insert(0, str(REPO_ROOT))


async def run_gptresearcher(message: str) -> str:
    """Run the gpt-researcher multi-agent workflow once and return its report text.

    Uses the same ``ChiefEditorAgent`` path as ``multi_agents/main.py``. Kept
    single-section / markdown-only so a live run stays fast and cheap.
    """
    from multi_agents.agents import ChiefEditorAgent

    task = {
        "query": message,
        "max_sections": 1,
        "max_plan_revisions": 1,
        "publish_formats": {"markdown": True, "pdf": False, "docx": False},
        "include_human_feedback": False,
        "follow_guidelines": False,
        "source": "web",
        "model": "gpt-4o-mini",
        "guidelines": [],
        "verbose": False,
    }
    chief_editor = ChiefEditorAgent(task)
    report = await chief_editor.run_research_task(task_id=uuid.uuid4())
    return str(report)
