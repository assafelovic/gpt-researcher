from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

from gpt_researcher import GPTResearcher

from backend.utils import write_md_to_pdf

if TYPE_CHECKING:
    from backend.report_type.deep_research.example import ResearchProgress


async def main(task: str):
    # Progress callback
    def on_progress(progress: ResearchProgress):
        print(f"Depth: {progress.current_depth}/{progress.total_depth}")
        print(f"Breadth: {progress.current_breadth}/{progress.total_breadth}")
        print(f"Queries: {progress.completed_queries}/{progress.total_queries}")
        if progress.current_query and progress.current_query.strip():
            print(f"Current query: '''{progress.current_query}'''\n")

    # Initialize researcher with deep research type
    researcher = GPTResearcher(
        query=task,
        report_type="deep",  # This will trigger deep research
    )

    # Run research with progress tracking
    print("Starting deep research...")
    _ = await researcher.conduct_research(on_progress=on_progress)
    print("\nResearch completed. Generating report...")

    # Generate the final report
    report = await researcher.write_report()
    await write_md_to_pdf(report, "deep_research_report")
    print(f"\nFinal Report: {report}")


if __name__ == "__main__":
    query = "What are the most effective ways for beginners to start investing?"
    asyncio.run(main(query))
