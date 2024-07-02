from langgraph_sdk import get_client
import asyncio

task = {
  "query": "What is GPT Researcher?",
  "max_sections": 3,
  "publish_formats": {
    "markdown": True,
    "pdf": True,
    "docx": True
  },
  "follow_guidelines": False,
  "model": "gpt-4o",
  "guidelines": [],
  "verbose": True
}

async def main():
    client = get_client()

    # List all assistants
    assistants = await client.assistants.search()

    # We auto-create an assistant for each graph you register in config.
    agent = assistants[0]

    # Start a new thread
    thread = await client.threads.create()

    # Start a streaming run
    input = {"task": task}
    async for chunk in client.runs.stream(thread['thread_id'], agent['assistant_id'], input=input):
        print(chunk)

if __name__ == "__main__":
    asyncio.run(main())
