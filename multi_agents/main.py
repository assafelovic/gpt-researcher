from __future__ import annotations

import os
import sys
import uuid

from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json

from gpt_researcher.utils.enum import Tone

from multi_agents.agents import ChiefEditorAgent

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()


def open_task():
    # Get the directory of the current script
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to task.json
    task_json_path: str = os.path.join(current_dir, "task.json")

    with open(task_json_path, "r") as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    # Override model with STRATEGIC_LLM if defined in environment
    strategic_llm: str | None = os.environ.get("STRATEGIC_LLM")
    if strategic_llm and ":" in strategic_llm:
        # Extract the model name (part after the first colon)
        model_name: str = strategic_llm.split(":", 1)[1]
        task["model"] = model_name
    elif strategic_llm:
        task["model"] = strategic_llm

    return task


async def run_research_task(
    query: str,
    websocket: Any | None = None,
    stream_output: Any | None = None,
    tone: Tone = Tone.Objective,
    headers: Any | None = None,
) -> str:
    task: dict[str, Any] = open_task()
    task["query"] = query

    chief_editor: ChiefEditorAgent = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report: str = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report


async def main() -> str:
    task: dict[str, Any] = open_task()

    chief_editor: ChiefEditorAgent = ChiefEditorAgent(task)
    research_report: str = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report


if __name__ == "__main__":
    asyncio.run(main())
