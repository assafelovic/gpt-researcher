import asyncio
from dotenv import load_dotenv
import os
import sys
import uuid
import json

from multi_agents_ag2.agents import ChiefEditorAgent
from gpt_researcher.utils.enum import Tone


load_dotenv()


def open_task() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    task_json_path = os.path.join(current_dir, "task.json")

    with open(task_json_path, "r") as f:
        task = json.load(f)

    if not task:
        raise Exception(
            "No task found. Please ensure a valid task.json file is present in the multi_agents_ag2 directory."
        )

    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if strategic_llm and ":" in strategic_llm:
        model_name = strategic_llm.split(":", 1)[1]
        task["model"] = model_name
    elif strategic_llm:
        task["model"] = strategic_llm

    return task


async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report


async def main():
    task = open_task()

    chief_editor = ChiefEditorAgent(task)
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report


if __name__ == "__main__":
    asyncio.run(main())
