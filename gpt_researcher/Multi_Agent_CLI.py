import asyncio
import argparse
import json
import os
import sys
import uuid
from copy import deepcopy

# Adjust path for importing multi_agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
from gpt_researcher.utils.enum import Tone # Assuming Tone is needed
from dotenv import load_dotenv

# Load default task configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TASK_PATH = os.path.join(CURRENT_DIR, 'multi_agents', 'task.json') # Corrected path
try:
    with open(DEFAULT_TASK_PATH, 'r') as _f:
        DEFAULT_TASK = json.load(_f)
except FileNotFoundError:
    print(f"Error: Default task file not found at {DEFAULT_TASK_PATH}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {DEFAULT_TASK_PATH}")
    sys.exit(1)

# Recognize keys from the default task for argument parsing
# RECOGNIZED_KEYS is no longer needed as arguments are hardcoded
# RECOGNIZED_KEYS = set(DEFAULT_TASK.keys())

def deep_merge(dict1, dict2):
    """
    Deep merge two dictionaries. dict2 values override dict1 values.
    Handles nested dictionaries.
    """
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value

def load_task_config(args):
    """
    Load and assemble configuration based on the specified hierarchy:
    Default task.json -> Specified task file -> Query file -> Guidelines file -> Command-line arguments.
    """
    # 1. Start with default configuration
    config = deepcopy(DEFAULT_TASK)

    # 2. Load from a specified task config file if provided
    if args.task_config:
        if not os.path.exists(args.task_config):
            print(f"Error: Task config file '{args.task_config}' not found.")
            sys.exit(1)
        try:
            with open(args.task_config, 'r') as f:
                task_from_file = json.load(f)
            deep_merge(config, task_from_file)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{args.task_config}'")
            sys.exit(1)

    # 3. Override with command-line arguments
    # Directly use parsed arguments, which argparse has already handled based on defined types
    args_dict = vars(args)
    for key in DEFAULT_TASK.keys(): # Iterate through default keys to apply overrides
        # Check if the argument was provided and is not the default value set by argparse
        # This requires comparing to the default value set in add_argument
        # A simpler approach is to check if the argument is present in the parsed args
        # and not None, assuming argparse handles defaults appropriately.
        # For boolean flags, argparse sets the value based on presence, so check if the key exists
        if key in args_dict and args_dict[key] is not None:
             # Special handling for boolean flags where the argument name might be different (--no-key)
            if isinstance(DEFAULT_TASK.get(key), bool):
                 # Check if the flag was explicitly set (either --key or --no-key)
                 # This is tricky with argparse's default handling.
                 # A more robust way is to check if the argument's source is not the default.
                 # For now, assume if the key is in args_dict and not None, it was set.
                 config[key] = args_dict[key]
            elif not isinstance(DEFAULT_TASK.get(key), bool): # Handle non-boolean overrides
                 config[key] = args_dict[key]

    # Handle query file argument - overrides default and task config query
    if args.query_file:
        if not os.path.exists(args.query_file):
            print(f"Error: Query file '{args.query_file}' not found.")
            sys.exit(1)
        try:
            with open(args.query_file, 'r') as f:
                config['query'] = f.read().strip()
        except IOError:
            print(f"Error: Could not read query file '{args.query_file}'")
            sys.exit(1)

    # Handle guidelines file argument - overrides default, task config, and query file
    if args.guidelines_file:
        if not os.path.exists(args.guidelines_file):
            print(f"Error: Guidelines file '{args.guidelines_file}' not found.")
            sys.exit(1)
        try:
            with open(args.guidelines_file, 'r') as f:
                # Assuming guidelines file contains a string or a JSON list
                # Adjust reading logic based on expected file format
                guidelines_content = f.read().strip()
                # If guidelines are expected to be a list, you might need to parse JSON
                # try:
                #     config['guidelines'] = json.loads(guidelines_content)
                # except json.JSONDecodeError:
                #     print(f"Warning: Could not decode JSON from guidelines file '{args.guidelines_file}'. Using raw content as string.")
                config['guidelines'] = guidelines_content.splitlines() # Assuming each line is a guideline
        except IOError:
            print(f"Error: Could not read guidelines file '{args.guidelines_file}'")
            sys.exit(1)

    # Handle the query argument separately as it's positional - overrides query file
    if args.query:
        config['query'] = args.query

    # Handle output folder argument - overrides default, task config, query file, and guidelines file
    if args.output_folder:
        config['output_folder'] = args.output_folder

    # Handle output filename argument - overrides default, task config, query file, guidelines file, and output folder
    if args.output_filename:
        config['output_file'] = args.output_filename

    # Handle nested publish_formats separately
    if args.publish_markdown is not None:
        config['publish_formats']['markdown'] = args.publish_markdown
    if args.publish_pdf is not None:
        config['publish_formats']['pdf'] = args.publish_pdf
    if args.publish_docx is not None:
        config['publish_formats']['docx'] = args.publish_docx


    return config

async def main():
    parser = argparse.ArgumentParser(description="Multi-agent research CLI")

    # Positional argument for the query
    parser.add_argument("query", type=str, nargs='?', help="The research query (optional if provided in task config or query file).")

    # Optional argument for a task configuration file
    parser.add_argument("--task-config", type=str, help="Path to a task configuration JSON file.")

    # Optional argument for a query file
    parser.add_argument("--query-file", type=str, help="Path to a file containing the research query.")

    # Optional argument for guidelines file
    parser.add_argument("--guidelines-file", type=str, help="Path to a file containing the research guidelines.")

    # Optional argument for output folder
    parser.add_argument("--output-folder", type=str, help=f"Set the output folder (default: {DEFAULT_TASK.get('output_folder', 'outputs')})")

    # Optional argument for output filename
    parser.add_argument("--output-filename", type=str, help=f"Set the output filename (default: {DEFAULT_TASK.get('output_file', 'multi_agent_report_<uuid>.md')})")

    # Hardcoded arguments based on task.json
    parser.add_argument("--max-sections", type=int, help=f"Set max_sections (default: {DEFAULT_TASK.get('max_sections')})")

    # Arguments for publish_formats (nested dictionary)
    parser.add_argument("--publish-markdown", action=argparse.BooleanOptionalAction, help=f"Enable/disable markdown output (default: {DEFAULT_TASK.get('publish_formats', {}).get('markdown')})")
    parser.add_argument("--publish-pdf", action=argparse.BooleanOptionalAction, help=f"Enable/disable PDF output (default: {DEFAULT_TASK.get('publish_formats', {}).get('pdf')})")
    parser.add_argument("--publish-docx", action=argparse.BooleanOptionalAction, help=f"Enable/disable DOCX output (default: {DEFAULT_TASK.get('publish_formats', {}).get('docx')})")

    parser.add_argument("--include-human-feedback", action=argparse.BooleanOptionalAction, help=f"Enable/disable human feedback (default: {DEFAULT_TASK.get('include_human_feedback')})")
    parser.add_argument("--follow-guidelines", action=argparse.BooleanOptionalAction, help=f"Enable/disable following guidelines (default: {DEFAULT_TASK.get('follow_guidelines')})")
    parser.add_argument("--model", type=str, help=f"Set the model (default: {DEFAULT_TASK.get('model')})")
    parser.add_argument("--guidelines", nargs="+", type=str, help=f"Set guidelines (default: {DEFAULT_TASK.get('guidelines')})")
    parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, help=f"Enable/disable verbose output (default: {DEFAULT_TASK.get('verbose')})")


    args = parser.parse_args()

    # Load and assemble the task configuration based on the hierarchy
    task_config = load_task_config(args)

    # Ensure query is present after loading config
    if not task_config.get('query'):
        print("Error: No research query provided. Please specify a query via argument or in the task config.")
        sys.exit(1)

    # Instantiate and run the ChiefEditorAgent
    chief_editor = ChiefEditorAgent(task_config)
    print(f"Starting research for query: {task_config['query']}")
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    # Handle output (e.g., write to file)
    output_folder = task_config.get('output_folder', 'outputs')
    os.makedirs(output_folder, exist_ok=True)
    output_filename = task_config.get('output_file', f"multi_agent_report_{uuid.uuid4()}.md")
    output_path = os.path.join(output_folder, output_filename)

    # Determine publish formats - default to markdown if not specified
    publish_formats = task_config.get('publish_formats', {'markdown': True})

    # Basic handling for writing the report based on formats
    if publish_formats.get('markdown'):
        md_output_path = os.path.splitext(output_path)[0] + ".md"
        with open(md_output_path, "w", encoding='utf-8') as f:
            f.write(research_report['report'])
        print(f"Multi-agent report (Markdown) written to {md_output_path}")

    # Add logic here for PDF and DOCX if the ChiefEditorAgent returns them or if there's a separate publishing step

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
