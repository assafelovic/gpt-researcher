import asyncio
from dotenv import load_dotenv
from multi_agents.dev_team import run_dev_team_flow

load_dotenv()

async def main():
    result = await run_dev_team_flow(repo_name="elishakay/gpt-researcher", 
                                     query="I'd like to trigger the dev_team flow via websocket. It should be implemented via backend/server.py and backend/websocket_manager.py.",
                                     branch_name="devs")
    print(result)

async def trigger_dev_team_flow(repo_name, query, branch_name, websocket=None, stream_output=None):
    print(
        f"Triggering dev team flow with repo_name as: {repo_name}",
        flush=True,
    )
    if websocket and stream_output:
        await stream_output("logs", "dev_team_progress", "Starting dev team flow...", websocket)

    try:
        result = await run_dev_team_flow(repo_name=repo_name, 
                                        query=query,
                                        branch_name=branch_name,
                                        websocket=websocket,
                                        stream_output=stream_output)
        
        print("result in trigger dev team flow", result)

        # Remove the FAISS object from the result dictionary
        if isinstance(result, dict):
            result = {k: v for k, v in result.items() if k != 'vector_store'}
        
        if websocket and stream_output:
            try:
                await stream_output("logs", "dev_team_result", result, websocket)
            except Exception as e:
                print(f"Error sending result over WebSocket: {e}")
                # You might want to send an error message to the client here
        
        return result
    except Exception as e:
        if websocket and stream_output:
            try:
                await stream_output("logs", "dev_team_result", result, websocket)
            except Exception as e:
                print(f"Error sending result over WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(main())