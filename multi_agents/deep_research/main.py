import os
import json
import asyncio
import argparse
from typing import Dict, Any, Optional
from gpt_researcher.utils.enum import Tone

from .orchestrator import DeepResearchOrchestrator
from ..agents.writer import WriterAgent
from ..agents.publisher import PublisherAgent

async def run_deep_research(
    query: str,
    breadth: int = 4,
    depth: int = 2,
    concurrency: int = 2,
    websocket=None,
    stream_output=None,
    tone=Tone.Objective,
    headers=None,
    source="web",
    verbose=True,
    publish_formats=None
) -> Dict[str, Any]:
    """
    Run deep research on a given query.
    
    Args:
        query: The research query
        breadth: Number of parallel search queries at each level
        depth: Maximum depth of recursive research
        concurrency: Maximum number of concurrent research tasks
        websocket: Optional websocket for streaming output
        stream_output: Optional stream output function
        tone: Research tone
        headers: Optional headers for API requests
        source: Research source ('web' or 'local')
        verbose: Whether to print verbose output
        publish_formats: Output formats to publish
        
    Returns:
        Dictionary with research results
    """
    # Create task configuration
    task = {
        "query": query,
        "deep_research_breadth": breadth,
        "deep_research_depth": depth,
        "deep_research_concurrency": concurrency,
        "source": source,
        "verbose": verbose,
        "publish_formats": publish_formats or {"markdown": True}
    }
    
    # Run deep research
    orchestrator = DeepResearchOrchestrator(
        task=task,
        websocket=websocket,
        stream_output=stream_output,
        tone=tone,
        headers=headers
    )
    
    # Run the research
    research_results = await orchestrator.run()
    
    # Generate report using the Writer agent
    writer = WriterAgent(websocket, stream_output, headers)
    
    # Prepare research state for writer
    research_state = {
        "task": task,
        "query": query,
        "title": f"Deep Research: {query}",
        "date": research_results.get("date", ""),
        "context": research_results.get("context", ""),
        "research_data": [{"topic": query, "content": research_results.get("context", "")}],
        "sources": research_results.get("sources", []),
        "citations": research_results.get("citations", {})
    }
    
    # Write the report
    report_state = await writer.run(research_state)
    
    # Publish the report if formats are specified
    if publish_formats:
        publisher = PublisherAgent(orchestrator.output_dir, websocket, stream_output, headers)
        publish_state = await publisher.run({
            "task": task,
            "report": report_state.get("report", ""),
            "title": research_state.get("title", "")
        })
        
        # Add published files to results
        research_results["published_files"] = publish_state.get("published_files", [])
    
    # Add report to results
    research_results["report"] = report_state.get("report", "")
    
    return research_results

def open_task_file() -> Dict[str, Any]:
    """Open and parse the task.json file"""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the multi_agents directory
    parent_dir = os.path.dirname(script_dir)
    # Construct the path to task.json
    task_path = os.path.join(parent_dir, "task.json")
    
    # Read and parse the task file
    with open(task_path, "r") as f:
        return json.load(f)

async def main():
    """Main entry point for deep research"""
    parser = argparse.ArgumentParser(description="Run deep research on a topic")
    parser.add_argument("--query", type=str, help="Research query")
    parser.add_argument("--breadth", type=int, default=4, help="Research breadth")
    parser.add_argument("--depth", type=int, default=2, help="Research depth")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrency limit")
    parser.add_argument("--source", type=str, default="web", help="Research source (web or local)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--task-file", action="store_true", help="Use task.json file")
    
    args = parser.parse_args()
    
    if args.task_file:
        # Use task.json file
        task = open_task_file()
        query = task.get("query")
        breadth = task.get("deep_research_breadth", 4)
        depth = task.get("deep_research_depth", 2)
        concurrency = task.get("deep_research_concurrency", 2)
        source = task.get("source", "web")
        verbose = task.get("verbose", True)
        publish_formats = task.get("publish_formats", {"markdown": True})
    else:
        # Use command line arguments
        query = args.query
        breadth = args.breadth
        depth = args.depth
        concurrency = args.concurrency
        source = args.source
        verbose = args.verbose
        publish_formats = {"markdown": True}
    
    if not query:
        print("Please provide a research query with --query or use --task-file")
        return
    
    # Run deep research
    results = await run_deep_research(
        query=query,
        breadth=breadth,
        depth=depth,
        concurrency=concurrency,
        source=source,
        verbose=verbose,
        publish_formats=publish_formats
    )
    
    # Print summary
    print(f"\nDeep Research completed for: {query}")
    print(f"Execution time: {results.get('execution_time', 'N/A')}")
    print(f"Learnings: {len(results.get('learnings', []))}")
    print(f"Sources: {len(results.get('sources', []))}")
    
    if results.get("published_files"):
        print("\nPublished files:")
        for file in results["published_files"]:
            print(f"- {file}")

if __name__ == "__main__":
    asyncio.run(main()) 