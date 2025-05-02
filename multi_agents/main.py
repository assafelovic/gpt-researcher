from dotenv import load_dotenv
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
import asyncio
import json
from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

# Load default configuration and recognized keys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TASK_PATH = os.path.join(CURRENT_DIR, 'task.json')
with open(DEFAULT_TASK_PATH, 'r') as _f:
    DEFAULT_TASK = json.load(_f)
RECOGNIZED_KEYS = set(DEFAULT_TASK.keys())

# Placeholder for CLI arguments
ARGS = None

# CLI imports for argument parsing and deep copy
import argparse
from copy import deepcopy

def open_task():
    """
    Load and assemble configuration based on CLI arguments or default task.json.
    """
    global ARGS
    # Merge multiple config files if provided
    if ARGS and ARGS.config_files:
        config = deepcopy(DEFAULT_TASK)
        for config_path in ARGS.config_files:
            with open(config_path, 'r') as cf:
                loaded = json.load(cf)
            for key in RECOGNIZED_KEYS:
                if key in loaded:
                    config[key] = loaded[key]
    # Single config file override
    elif ARGS and ARGS.config_file:
        with open(ARGS.config_file, 'r') as cf:
            loaded = json.load(cf)
        config = {key: loaded[key] for key in RECOGNIZED_KEYS if key in loaded}
    # Default task.json
    else:
        config = deepcopy(DEFAULT_TASK)

    # Override query if a query-file is provided
    if ARGS and ARGS.query_file:
        try:
            with open(ARGS.query_file, 'r') as qf:
                content = qf.read()
            parsed = json.loads(content)
            if isinstance(parsed, dict) and 'query' in parsed:
                config['query'] = parsed['query']
            else:
                config['query'] = content
        except (json.JSONDecodeError, UnicodeDecodeError):
            with open(ARGS.query_file, 'r') as qf:
                config['query'] = qf.read()

    return config

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
    parser = argparse.ArgumentParser(description="Multi-agents CLI")
    parser.add_argument("-t", "--config-file", type=str, help="Path to a single JSON configuration file")
    parser.add_argument("--config-files", nargs="+", type=str, help="Paths to one or more JSON configuration files")
    parser.add_argument("--query-file", type=str, help="Path to a file containing query JSON or text")
    args = parser.parse_args()
    # Assign parsed arguments for open_task
    ARGS = args
    # Execute main with assembled configuration
    asyncio.run(main())
