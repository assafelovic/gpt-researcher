from dotenv import load_dotenv
from backend.multi_agents.agents import ChiefEditorAgent
import asyncio
import os

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

# backend/multi_agents/main.py

async def run_research_task(query, websocket=None):
    task = {
        "query": query,
        "max_sections": 3,
        "publish_formats": {
            "markdown": True,
            "pdf": True,
            "docx": True
        },
        "follow_guidelines": False,
        "model": "gpt-4o",
        "guidelines": [
            "The report MUST be written in APA format",
            "Each sub section MUST include supporting sources using hyperlinks. If none exist, erase the sub section or rewrite it to be a part of the previous section",
            "The report MUST be written in spanish"
        ],
        "verbose": True
    }

    chief_editor = ChiefEditorAgent(task, websocket)
    research_report = await chief_editor.run_research_task(websocket)

    return research_report

async def main(query, websocket=None):
    research_report = await run_research_task(query, websocket)
    return research_report

if __name__ == "__main__":
    query = "Is AI in a hype cycle?"  # Example query, you can change this as needed
    asyncio.run(main(query))