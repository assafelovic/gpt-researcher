from dotenv import load_dotenv
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
import asyncio
import argparse
import json
from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--task-file', dest='task_file', default=None, help='Path to task JSON file')
    return parser.parse_args()

def open_task(path_override=None):
    if path_override:
        task_json_path = path_override
    else:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the absolute path to task.json
        task_json_path = os.path.join(current_dir, 'task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    # Override model with STRATEGIC_LLM if defined in environment
    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if strategic_llm and ":" in strategic_llm:
        # Extract the model name (part after the first colon)
        model_name = strategic_llm.split(":", 1)[1]
        task["model"] = model_name
    elif strategic_llm:
        task["model"] = model_name

    return task

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

async def main(task_file=None):
    task = open_task(path_override=task_file)

    chief_editor = ChiefEditorAgent(task)
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(task_file=args.task_file))
