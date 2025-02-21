from deep_research import DeepResearch
import asyncio

async def main():
    # Progress callback
    def on_progress(progress):
        print(f"Depth: {progress.current_depth}/{progress.total_depth}")
        print(f"Breadth: {progress.current_breadth}/{progress.total_breadth}")
        print(f"Queries: {progress.completed_queries}/{progress.total_queries}")
        if progress.current_query:
            print(f"Current query: {progress.current_query}")
    
    # Initialize researcher
    researcher = DeepResearch(
        query="What is new with LangGraph?",
        breadth=4,
        depth=2,
        concurrency_limit=2 
    )
    
    # Run research with progress tracking
    report = await researcher.run(on_progress=on_progress)
    print(report)

if __name__ == "__main__":
    asyncio.run(main())