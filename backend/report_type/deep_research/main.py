from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
from backend.utils import write_md_to_pdf
import asyncio


async def main():
    # Progress callback
    def on_progress(progress):
        print(f"Depth: {progress.current_depth}/{progress.total_depth}")
        print(f"Breadth: {progress.current_breadth}/{progress.total_breadth}")
        print(f"Queries: {progress.completed_queries}/{progress.total_queries}")
        if progress.current_query:
            print(f"Current query: {progress.current_query}")
    
    # Initialize researcher with deep research type
    researcher = GPTResearcher(
        query="Who is assaf elovic?",
        report_type="deep",  # This will trigger deep research
        tone=Tone.Objective,
    )
    
    # Run research with progress tracking
    print("Starting deep research...")
    context = await researcher.conduct_research(on_progress=on_progress)
    print("\nResearch completed. Generating report...")
    
    # Generate the final report
    report = await researcher.write_report()
    await write_md_to_pdf(report, "deep_research_report")
    print(f"\nFinal Report: {report}")

if __name__ == "__main__":
    asyncio.run(main())