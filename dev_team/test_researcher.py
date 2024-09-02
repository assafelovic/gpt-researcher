from dotenv import load_dotenv

import asyncio
from gpt_researcher.master.agent import GPTResearcher

load_dotenv()

async def main():
    researcher = GPTResearcher(query="Your test query", report_type="research_report")
    await researcher.conduct_research()
    report = await researcher.write_report()
    print(report)

if __name__ == "__main__":
    asyncio.run(main())