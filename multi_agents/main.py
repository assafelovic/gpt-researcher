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

<<<<<<< HEAD
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
=======
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
>>>>>>> e2b264d3a41f83dff6fb338c7a970c6eecc11503

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

    # Override publish_formats if output_file argument is provided
    if ARGS and ARGS.output_file:
        ext = os.path.splitext(ARGS.output_file)[1].lower()
        pub = {'markdown': False, 'pdf': False, 'docx': False}
        if ext == '.md':
            pub['markdown'] = True
        elif ext == '.pdf':
            pub['pdf'] = True
        elif ext == '.docx':
            pub['docx'] = True
        config['publish_formats'] = pub
        config['output_file'] = ARGS.output_file
    return config

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    # Pass output_file through task to publisher
    if 'output_file' in task:
        chief_editor.output_file = task['output_file']
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
<<<<<<< HEAD
    parser = argparse.ArgumentParser(description="Multi-agents CLI")
    parser.add_argument("-t", "--config-file", type=str, help="Path to a single JSON configuration file")
    parser.add_argument("--config-files", nargs="+", type=str, help="Paths to one or more JSON configuration files")
    parser.add_argument("--query-file", type=str, help="Path to a file containing query JSON or text")
    parser.add_argument("-o", "--output-file", type=str, help="Path to write the output file; extension determines publish format (md, pdf, docx)")
    args = parser.parse_args()
    # Assign parsed arguments for open_task
    ARGS = args
    # Execute main with assembled configuration
    asyncio.run(main())
=======
    args = parse_args()
    asyncio.run(main(task_file=args.task_file))
>>>>>>> e2b264d3a41f83dff6fb338c7a970c6eecc11503
