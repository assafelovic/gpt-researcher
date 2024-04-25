from dotenv import load_dotenv
from agents import MasterAgent
import asyncio

load_dotenv()

task = {
    "query": "What is Langgraph?",
    "max_sub_headers": 3,
}


async def main():
    master_agent = MasterAgent(task)
    await master_agent.run()

if __name__ == "__main__":
    asyncio.run(main())
