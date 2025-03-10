import os
import json
import asyncio
import argparse
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging - only show warnings and errors by default
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import required modules with fallbacks
try:
    from gpt_researcher.utils.enum import Tone
except ImportError:
    # Create a simple Tone enum if not available
    from enum import Enum
    class Tone(Enum):
        Objective = "objective"
        Balanced = "balanced"
        Critical = "critical"
        Optimistic = "optimistic"

try:
    from .orchestrator import DeepResearchOrchestrator
    from ..agents.writer import WriterAgent as MainWriterAgent
    from ..agents.publisher import PublisherAgent
    from .agents import WriterAgent, ReporterAgent
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
    logger.error("Please make sure all dependencies are installed correctly.")
    raise

async def run_deep_research(
    query: str,
    breadth: int = 4,
    depth: int = 2,
    concurrency: int = 2,
    websocket=None,
    stream_output=None,
    tone=None,  # Make tone optional with default set below
    headers=None,
    source="web",
    verbose=True,
    publish_formats=None,
    human_review=False
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
        human_review: Whether to enable human review during research
        
    Returns:
        Dictionary with research results
    """
    # Set default tone if not provided
    if tone is None:
        try:
            tone = Tone.Objective
        except:
            # If Tone enum is not available, use a string
            tone = "objective"
    
    # Set logging level based on verbose flag
    if verbose:
        logging.getLogger('multi_agents.deep_research').setLevel(logging.INFO)
    else:
        logging.getLogger('multi_agents.deep_research').setLevel(logging.WARNING)
            
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
    
    try:
        # Run deep research
        orchestrator = DeepResearchOrchestrator(
            task=task,
            websocket=websocket,
            stream_output=stream_output,
            tone=tone,
            headers=headers,
            human_review_enabled=human_review
        )
        
        # Run the research
        research_results = await orchestrator.run()
    except Exception as e:
        logger.error(f"Error during research: {str(e)}", exc_info=True)
        return {
            "query": query,
            "context": f"Error during research: {str(e)}",
            "sources": [],
            "citations": {},
            "error": str(e)
        }
    
    try:
        # Create the section writer agent
        writer = WriterAgent(websocket, stream_output, headers)
        
        # Get current date
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Format sources for references if they're in dictionary format
        sources = research_results.get("sources", [])
        formatted_sources = []
        
        for source in sources:
            if isinstance(source, dict) and "url" in source:
                # Format source as a reference
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                formatted_sources.append(f"- {title} [{url}]({url})")
            elif isinstance(source, str):
                # Source is already a string
                formatted_sources.append(source)
        
        # The context already contains the research results with sources
        # We don't need to check for empty sources as the context itself is the source
        # Just ensure the context is not empty
        context = research_results.get("context", "")
        if not context:
            error_msg = "No research context found in results. Cannot generate report without research data."
            if websocket and stream_output:
                await stream_output(
                    "logs",
                    "error",
                    error_msg,
                    websocket,
                )
            else:
                logger.error(error_msg)
            
            # Create a fallback context
            context = f"Research on: {query}\n\nNo specific research data was collected. This could be due to API limitations, network issues, or lack of relevant information."
            logger.info(f"Created fallback context: {len(context)} chars")
        
        # If we have sources but no formatted sources, create them
        if sources and not formatted_sources:
            logger.info("Creating formatted sources from sources")
            for i, source in enumerate(sources):
                if isinstance(source, dict):
                    title = source.get("title", f"Source {i+1}")
                    url = source.get("url", "")
                    formatted_sources.append(f"- {title} [{url}]({url})")
        
        # Prepare research state for writer
        research_state = {
            "task": task,
            "query": query,
            "title": f"Deep Research: {query}",
            "date": current_date,
            "context": context,  # Pass context as is, no need to convert
            "research_data": [{"topic": query, "content": context}],  # Pass context as is
            "sources": sources,  # Pass the original sources with full content
            "formatted_sources": formatted_sources,  # Also pass formatted sources for display
            "citations": research_results.get("citations", {})
        }
        
        # If context is empty but we have sources, create context from sources
        if not context and sources:
            logger.warning("Context is empty but sources exist. Creating context from sources.")
            context_parts = []
            for source in sources:
                if isinstance(source, dict) and "content" in source:
                    title = source.get("title", "Unknown Title")
                    url = source.get("url", "")
                    content = source.get("content", "")
                    if content:
                        context_parts.append(f"From {title} [{url}]:\n{content}")
            
            if context_parts:
                context = "\n\n".join(context_parts)
                research_state["context"] = context
                research_state["research_data"] = [{"topic": query, "content": context}]
                logger.info(f"Created context from sources: {len(context)} chars")
        
        # Generate sections and transform research data
        transformed_research_state = await writer.run(research_state)
        
        # Generate report using the Writer agent
        main_writer = MainWriterAgent(websocket, stream_output, headers)
        report_state = await main_writer.run(transformed_research_state)
        
        # Create the report formatter agent
        reporter = ReporterAgent(websocket, stream_output, headers)
        
        # Format the report for the publisher
        publisher_state = await reporter.run(report_state, transformed_research_state)
        
        # Publish the report if formats are specified
        if publish_formats:
            # Create the publisher agent
            publisher = PublisherAgent(orchestrator.output_dir, websocket, stream_output, headers)
            
            # Ensure all necessary components are in the publisher state
            complete_publisher_state = {
                "task": task,
                "headers": publisher_state.get("headers", {}),
                "research_data": publisher_state.get("research_data", []),
                "sources": publisher_state.get("sources", []),
                "introduction": publisher_state.get("introduction", ""),
                "conclusion": publisher_state.get("conclusion", ""),
                "table_of_contents": publisher_state.get("table_of_contents", ""),
                "title": publisher_state.get("title", f"Deep Research: {query}"),
                "date": publisher_state.get("date", current_date),
                "sections": publisher_state.get("sections", [])
            }
            
            # Run the publisher agent
            publish_state = await publisher.run(complete_publisher_state)
            
            # Add published files to results
            research_results["published_files"] = publish_state.get("published_files", [])
        
        # Add report to results
        research_results["report"] = report_state.get("report", "")
        
        return research_results
    except Exception as e:
        logger.error(f"Error during report generation: {str(e)}")
        # Return the research results even if report generation failed
        research_results["error"] = f"Error during report generation: {str(e)}"
        return research_results

async def main():
    """Main entry point for deep research"""
    parser = argparse.ArgumentParser(description="Run deep research on a topic")
    parser.add_argument("--query", type=str, help="Research query")
    parser.add_argument("--breadth", type=int, default=4, help="Research breadth")
    parser.add_argument("--depth", type=int, default=2, help="Research depth")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrency limit")
    parser.add_argument("--source", type=str, default="web", help="Research source (web or local)")
    parser.add_argument("--verbose", action="store_true", default=False, help="Verbose output")
    parser.add_argument("--markdown", action="store_true", default=True, help="Generate markdown output")
    parser.add_argument("--pdf", action="store_true", default=False, help="Generate PDF output")
    parser.add_argument("--docx", action="store_true", default=False, help="Generate DOCX output")
    parser.add_argument("--human-review", action="store_true", default=False, help="Enable human review during research")
    parser.add_argument("--mode", type=str, default="deep", help="Research mode (deep or standard)")
    
    args = parser.parse_args()
    
    # Handle the mode argument
    if args.mode != "deep":
        logger.warning(f"Mode '{args.mode}' is not supported. Using 'deep' mode.")
    
    # Get the query from arguments or prompt the user
    query = args.query
    if not query:
        query = input("Enter your research query: ")
    
    # Use command line arguments
    breadth = args.breadth
    depth = args.depth
    concurrency = args.concurrency
    source = args.source
    verbose = args.verbose
    publish_formats = {
        "markdown": args.markdown,
        "pdf": args.pdf,
        "docx": args.docx
    }
    human_review = args.human_review
    
    try:
        # Run deep research
        results = await run_deep_research(
            query=query,
            breadth=breadth,
            depth=depth,
            concurrency=concurrency,
            source=source,
            verbose=verbose,
            publish_formats=publish_formats,
            human_review=human_review
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
        
        if results.get("error"):
            print(f"\nWarning: {results['error']}")
        
        return results
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        print(f"\nError: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main()) 