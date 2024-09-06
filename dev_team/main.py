import asyncio
from dotenv import load_dotenv
from . import run_dev_team_flow

load_dotenv()

async def main():
    result = await run_dev_team_flow(repo_url="https://github.com/elishakay/gpt-researcher", 
                                     query="I'd like to trigger the dev_team flow via websocket. It should be implemented via backend/server.py and backend/websocket_manager.py.",
                                     branch_name="devs")
    print(result)

async def trigger_dev_team_flow(repo_url, query, branch_name, websocket=None, stream_output=None):
    # Your existing code here
    if websocket and stream_output:
        await stream_output("logs", "dev_team_progress", "Starting dev team flow...", websocket)

    result = await run_dev_team_flow(repo_url=repo_url, 
                                     query=query,
                                     branch_name=branch_name,
                                     websocket=websocket,
                                     stream_output=stream_output)
    
    if websocket and stream_output:
        await stream_output("logs", "dev_team_result", result, websocket)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())