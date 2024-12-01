from datetime import datetime
from typing import Dict, Any
import asyncio

from .utils.views import print_agent_output
from .utils.llms import call_model

class ParserAgent:
    """Agent responsible for parsing and analyzing math problems."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def parse_problem(self, problem_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the math problem to determine its type, difficulty, and key elements.

        :param problem_state: Dictionary containing the problem statement
        :return: Dictionary with parsed problem details
        """
        task = problem_state.get("task")
        problem = task.get("problem")
        model = task.get("model", "gpt-4")

        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "parsing_problem",
                f"Parsing the problem: {problem}",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Parsing the problem: {problem}",
                agent="PARSER",
            )

        prompt = self._create_parsing_prompt(problem)

        parsed_result = await call_model(
            prompt=prompt,
            model=model,
            response_format="json",
        )

        return {
            "parsed_problem": parsed_result
        }

    def _create_parsing_prompt(self, problem: str) -> list:
        """Create the prompt for parsing the math problem."""
        return [
            {
                "role": "system",
                "content": "あなたは熟練した数学の問題解析エージェントです。与えられた数学の問題を解析し、その問題の種類、難易度、主要な要素を特定してください。"
            },
            {
                "role": "user",
                "content": f"次の数学の問題を解析してください:\n'{problem}'\n\nあなたのタスクは、問題の種類（例：方程式、幾何、微積分など）、難易度（初級、中級、上級）、主要な要素（変数、定数、図形など）を特定し、以下のJSON形式で返答することです。\n\n{{\n  \"type\": \"問題の種類\",\n  \"difficulty\": \"難易度\",\n  \"elements\": [\"主要な要素のリスト\"]\n}}\n\nJSON以外の出力はしないでください。"
            },
        ]

