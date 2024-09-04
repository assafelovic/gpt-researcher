import asyncio
from dotenv import load_dotenv
from . import run_dev_team_flow

load_dotenv()

async def main():
    result = await run_dev_team_flow(repo_url="https://github.com/assafelovic/gpt-researcher", query="when I do pip install i dont get the latest and when i force pip to install the latest i get that error mentioned above in reply to this message that was normally addressed in github about the logurun/loguru")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())