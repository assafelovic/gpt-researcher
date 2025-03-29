import nest_asyncio  # required for notebooks

nest_asyncio.apply()

from gpt_researcher import GPTResearcher
import asyncio


async def get_report(query: str, report_type: str, custom_prompt: str = None):
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    
    # Generate report with optional custom prompt
    report = await researcher.write_report(custom_prompt=custom_prompt)

    # Get additional information
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()

    return report, research_context, research_costs, research_images, research_sources


if __name__ == "__main__":
    query = "Should I invest in Nvidia?"
    report_type = "research_report"

    # Standard report
    report, context, costs, images, sources = asyncio.run(get_report(query, report_type))

    print("Standard Report:")
    print(report)
    
    # Custom report with specific formatting requirements
    custom_prompt = "Answer in short, 2 paragraphs max without citations. Focus on the most important facts for investors."
    custom_report, _, _, _, _ = asyncio.run(get_report(query, report_type, custom_prompt))
    
    print("\nCustomized Short Report:")
    print(custom_report)
    
    print("\nResearch Costs:")
    print(costs)
    print("\nNumber of Research Images:")
    print(len(images))
    print("\nNumber of Research Sources:")
    print(len(sources))