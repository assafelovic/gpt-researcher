import asyncio
from dotenv import load_dotenv
import os
from .agents.flow import DevTeamFlow

load_dotenv()

async def main():
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = 'assafelovic/gpt-researcher'
    query = "Analyze the project structure"

    flow = DevTeamFlow(github_token, repo_name)
    result = await flow.run_flow(query)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())