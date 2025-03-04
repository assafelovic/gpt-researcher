#!/usr/bin/env python3
"""
Example script demonstrating how to use the post-retrieval processing feature.
"""

import asyncio
from pathlib import Path

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType


async def main():
    """Run the example."""
    post_retrieval_processing_instructions = """
    In the provided text, please extract and format the most important information as follows:
    
    1. Identify the most important exact snippets related to quantum computing advancements
    2. Format each important snippet as a markdown quote block
    3. For each quote, include the source URL if available
    4. Highlight key statistics, findings, and breakthrough technologies
    5. If there are links to follow for more detailed information, include them with a brief explanation
    6. Organize the information by recency, with the most recent advancements first
    """

    # Set up the researcher
    researcher: GPTResearcher = GPTResearcher(
        query="What are the latest advancements in quantum computing?",
        report_type=ReportType.ResearchReport,
        report_title="Latest Advancements in Quantum Computing",
        post_retrieval_processing_instructions=post_retrieval_processing_instructions,
    )
    
    # Run the research
    report: list[str] = await researcher.conduct_research()
    
    # Save the report
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "quantum_computing_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"Report saved to {output_dir / 'quantum_computing_report.md'}")


if __name__ == "__main__":
    asyncio.run(main()) 