import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from multi_agents.agents.fact_checker import FactCheckerAgent
from multi_agents.agents.visualizer import VisualizerAgent
import multi_agents.agents.fact_checker
import multi_agents.agents.visualizer

# Mock call_model
async def mock_call_model(prompt, model=None, response_format=None):
    prompt_text = str(prompt)
    if "Fact Checker" in prompt_text:
        return "- Inaccuracy: You claim it will replace all jobs by 2025, but the research data says it will create new jobs."
    elif "Data Visualizer" in prompt_text:
        return "```mermaid\npie title AI Jobs Impact\n    \"New Jobs Created\": 80\n    \"Jobs Replaced\": 20\n```"
    return "None"

multi_agents.agents.fact_checker.call_model = mock_call_model
multi_agents.agents.visualizer.call_model = mock_call_model

load_dotenv()

async def test_agents():
    # Mock research state
    state = {
        "task": {
            "model": "gpt-4o"
        },
        "introduction": "AI is definitely in a hype cycle and many claim it will replace all jobs by 2025.",
        "conclusion": "In conclusion, AI is completely overhyped and has no real utility.",
        "research_data": [
            {"title": "AI Trends 2024", "content": "AI adoption has increased by 50% year-over-year. 80% of companies report using AI for specific utility tasks like data processing. Predictions indicate it will create new jobs, not replace all of them by 2025."}
        ]
    }
    
    print("--- Testing FactCheckerAgent ---")
    fact_checker = FactCheckerAgent()
    try:
        fc_result = await fact_checker.run(state)
        print("FactChecker Result:")
        print(fc_result)
    except Exception as e:
        print(f"FactChecker Failed: {e}")
    
    print("\n--- Testing VisualizerAgent ---")
    visualizer = VisualizerAgent()
    try:
        vis_result = await visualizer.run(state)
        print("Visualizer Result:")
        print(vis_result)
    except Exception as e:
        print(f"Visualizer Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agents())
