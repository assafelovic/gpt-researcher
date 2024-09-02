import asyncio
from dotenv import load_dotenv
from . import run_dev_team_flow

load_dotenv()

async def main():
    result = await run_dev_team_flow(repo_url="https://github.com/elishakay/gpt-researcher", query="Analyze the project structure")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())