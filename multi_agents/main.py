from dotenv import load_dotenv
import sys
import os
import uuid
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
from multi_agents.deep_research import DeepResearchOrchestrator
import asyncio
import json
from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

def open_task():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to task.json
    task_json_path = os.path.join(current_dir, 'task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    return task

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

async def run_deep_research_task(query, breadth=4, depth=2, concurrency=2, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    """Run deep research on a given query"""
    task = open_task()
    task["query"] = query
    task["deep_research_breadth"] = breadth
    task["deep_research_depth"] = depth
    task["deep_research_concurrency"] = concurrency

    # Import here to avoid circular imports
    from multi_agents.deep_research.main import run_deep_research
    
    research_results = await run_deep_research(
        query=query,
        breadth=breadth,
        depth=depth,
        concurrency=concurrency,
        websocket=websocket,
        stream_output=stream_output,
        tone=tone,
        headers=headers,
        source=task.get("source", "web"),
        verbose=task.get("verbose", True),
        publish_formats=task.get("publish_formats", {"markdown": True})
    )

    if websocket and stream_output:
        await stream_output("logs", "deep_research_report", research_results, websocket)

    return research_results

async def main():
    parser = argparse.ArgumentParser(description="Run research tasks")
    parser.add_argument("--mode", type=str, choices=["standard", "deep"], default="standard", 
                        help="Research mode: standard or deep")
    parser.add_argument("--query", type=str, help="Research query (overrides task.json)")
    parser.add_argument("--breadth", type=int, default=4, help="Deep research breadth")
    parser.add_argument("--depth", type=int, default=2, help="Deep research depth")
    parser.add_argument("--concurrency", type=int, default=2, help="Deep research concurrency")
    
    args = parser.parse_args()
    
    task = open_task()
    query = args.query or task.get("query")
    
    if not query:
        raise ValueError("No query provided. Please specify a query in task.json or with --query")
    
    if args.mode == "deep":
        print(f"Running deep research on: {query}")
        research_report = await run_deep_research_task(
            query=query,
            breadth=args.breadth,
            depth=args.depth,
            concurrency=args.concurrency
        )
    else:
        print(f"Running standard research on: {query}")
        research_report = await run_research_task(query=query)

    return research_report

if __name__ == "__main__":
    asyncio.run(main())