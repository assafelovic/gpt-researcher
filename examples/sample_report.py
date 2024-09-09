from gpt_researcher import GPTResearcher
import asyncio


async def main():
    """
    This is a sample script that shows how to run a research report.
    """
    # Query
    query = "What happened in the latest burning man floods?"
    # Initialize the researcher
    researcher = GPTResearcher(query=query)

    # Conduct research on the given query. Returns context for the report
    research_context = await researcher.conduct_research()

    # Write the report
    # FYI: You can pass ext_context (str) = "..." to write_report
    # to use it without conducting a research first, using your own context
    # In this case we're simply passing the already conducted research context
    report = await researcher.write_report(ext_context=researcher.context)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
