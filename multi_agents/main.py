from dotenv import load_dotenv
from agents import MasterAgent
import asyncio
import json
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

with open('task.json', 'r') as f:
    task = json.load(f)


async def main():
    master_agent = MasterAgent(task)
    research_report = await master_agent.run()
    print(research_report)

if __name__ == "__main__":
    asyncio.run(main())
