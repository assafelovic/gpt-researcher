from gpt_researcher import GPTResearcher
import asyncio


async def get_report(query: str, report_source: str, sources: list) -> str:
    researcher = GPTResearcher(query=query, report_source=report_source, source_urls=sources)
    research_context = await researcher.conduct_research()
    return await researcher.write_report()

if __name__ == "__main__":
    query = "What are the biggest trends in AI lately?"
    report_source = "static"
    sources = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://www.ibm.com/think/insights/artificial-intelligence-trends",
        "https://www.forbes.com/advisor/business/ai-statistics"
    ]

    report = asyncio.run(get_report(query=query, report_source=report_source, sources=sources))
    print(report)
