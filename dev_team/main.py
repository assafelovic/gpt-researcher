import asyncio
from dotenv import load_dotenv
from . import run_dev_team_flow

load_dotenv()

async def main():
    result = await run_dev_team_flow(repo_url="https://github.com/elishakay/gpt-researcher", 
                                     query="I'd like to trigger the dev_team flow via websocket. It should be implemented via backend/server.py and backend/websocket_manager.py.",
                                     branch_name="devs")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())