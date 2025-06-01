"""
Hi! The following test cases are for the new parameter `complement_source_urls` and fix on the functional error with `source_urls` in GPTResearcher class.

The source_urls parameter was resetting each time in conduct_research function causing gptr to forget the given links. Now, that has been fixed and a new parameter is introduced.
This parameter named will `complement_source_urls` allow GPTR to research on sources other than the provided sources via source_urls if set to True. 
Default is False, i.e., no additional research will be conducted on newer sources.
"""

## Notes:
## Please uncomment the test case to run and comment the rest.
## Thanks!



#### Test case 1 (original test case as control from https://docs.gptr.dev/docs/gpt-researcher/tailored-research)

from gpt_researcher.agent import GPTResearcher  # Ensure this path is correct
import asyncio
import logging
from typing import List, Dict, Any
from backend.server.server_utils import CustomLogsHandler  # Update import

async def get_report(query: str, report_type: str, sources: list) -> str:
    custom_logs_handler = CustomLogsHandler(None, query)  # Pass query parameter
    researcher = GPTResearcher(query=query, 
                               report_type=report_type, 
                               complement_source_urls=False,
                               websocket=custom_logs_handler)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report, researcher

if __name__ == "__main__":
    query = "Write an analysis on paul graham"
    report_type = "research_report"
    sources = ["https://www.paulgraham.com/when.html", "https://www.paulgraham.com/noob.html"]  # query is related

    report, researcher = asyncio.run(get_report(query, report_type, sources))
    print(report)

    print(f"\nLength of the context = {len(researcher.get_research_context())}") # Must say Non-zero value because the query is related to the contents of the page, so there will be relevant context present



#### Test case 2 (Illustrating the problem, i.e., source_urls are not scoured. Hence, no relevant context)

# from gpt_researcher.agent import GPTResearcher  # Ensure this path is correct
# import asyncio

# async def get_report(query: str, report_type: str, sources: list) -> str:
#     researcher = GPTResearcher(query=query, report_type=report_type, source_urls=sources)
#     await researcher.conduct_research()
#     report = await researcher.write_report()
#     return report, researcher

# if __name__ == "__main__":
#     query = "What is Microsoft's business model?"
#     report_type = "research_report"
#     sources = ["https://www.apple.com", "https://en.wikipedia.org/wiki/Olympic_Games"]  # query is UNRELATED.

#     report, researcher = asyncio.run(get_report(query, report_type, sources))
#     print(report)

#     print(f"\nLength of the context = {len(researcher.get_research_context())}") # Must say 0 (zero) value because the query is UNRELATED to the contents of the pages, so there will be NO relevant context present



#### Test case 3 (Suggested solution - complement_source_urls parameter allows GPTR to scour more of the web and not restrict to source_urls)

# from gpt_researcher.agent import GPTResearcher  # Ensure this path is correct
# import asyncio

# async def get_report(query: str, report_type: str, sources: list) -> str:
#     researcher = GPTResearcher(query=query, report_type=report_type, source_urls=sources, complement_source_urls=True)
#     await researcher.conduct_research()
#     report = await researcher.write_report()
#     return report, researcher

# if __name__ == "__main__":
#     query = "What is Microsoft's business model?"
#     report_type = "research_report"
#     sources = ["https://www.apple.com", "https://en.wikipedia.org/wiki/Olympic_Games"]  # query is UNRELATED

#     report, researcher = asyncio.run(get_report(query, report_type, sources))
#     print(report)

#     print(f"\nLength of the context = {len(researcher.get_research_context())}") # Must say Non-zero value because the query is UNRELATED to the contents of the page, but the complement_source_urls is set which should make gptr do default web search to gather contexts
    


# #### Test case 4 (Furthermore, GPTR will create more context in addition to source_urls if the complement_source_urls parameter is set allowing for a larger research scope)

# from gpt_researcher.agent import GPTResearcher  # Ensure this path is correct
# import asyncio

# async def get_report(query: str, report_type: str, sources: list) -> str:
#     researcher = GPTResearcher(query=query, report_type=report_type, source_urls=sources, complement_source_urls=True)
#     await researcher.conduct_research()
#     report = await researcher.write_report()
#     return report, researcher

# if __name__ == "__main__":
#     query = "What are the latest advancements in AI?"
#     report_type = "research_report"
#     sources = ["https://en.wikipedia.org/wiki/Artificial_intelligence", "https://www.ibm.com/watson/ai"]  # query is related

#     report, researcher = asyncio.run(get_report(query, report_type, sources))
#     print(report)

#     print(f"\nLength of the context = {len(researcher.get_research_context())}") # Must say Non-zero value because the query is related to the contents of the page, and additionally the complement_source_urls is set which should make gptr do default web search to gather more contexts!
