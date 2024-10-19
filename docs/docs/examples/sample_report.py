import nest_asyncio  # required for notebooks

nest_asyncio.apply()

from gpt_researcher import GPTResearcher
import asyncio


async def get_report(query: str, report_type: str):
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()

    # Get additional information
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()

    return report, research_context, research_costs, research_images, research_sources


if __name__ == "__main__":
    query = "Should I invest in Nvidia?"
    report_type = "research_report"

    report, context, costs, images, sources = asyncio.run(get_report(query, report_type))

    print("Report:")
    print(report)
    print("\nResearch Costs:")
    print(costs)
    print("\nResearch Images:")
    print(images)
    print("\nResearch Sources:")
    print(sources)