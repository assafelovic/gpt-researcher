from datetime import datetime
from typing import Dict, Any
import asyncio
import base64
import os

from .utils.views import print_agent_output
from .utils.llms import call_model

class ParserAgent:
    """Agent responsible for parsing and analyzing math problems, now with image processing capabilities."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encode an image file to a Base64 string."""
        if not os.path.exists(image_path):
            return None  # Return None if the file does not exist
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def parse_problem(self, problem_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the math problem, including image-based problems, to determine its type, difficulty, and key elements.

        :param problem_state: Dictionary containing the problem statement
        :return: Dictionary with parsed problem details
        """
        task = problem_state.get("task")
        problem = task.get("problem")
        model = task.get("model", "gpt-4")
        image_path = task.get("image_path")

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

        # If an image is provided and exists, include it in the prompt
        if image_path and (base64_image := self.encode_image(image_path)):
            prompt = self._create_image_parsing_prompt(problem, base64_image)
        else:  # Fall back to text-based prompt
            prompt = self._create_text_parsing_prompt(problem)

        parsed_result = await call_model(
            prompt=prompt,
            model=model,
            response_format="json",
        )

        return {
            "parsed_problem": parsed_result
        }

    def _create_text_parsing_prompt(self, problem: str) -> list:
        """Create the prompt for parsing text-based math problems."""
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

    def _create_image_parsing_prompt(self, problem: str, base64_image: str) -> list:
        """Create the prompt for parsing image-based math problems."""
        return [
            {
                "role": "system",
                "content": "あなたは熟練した数学の問題解析エージェントです。与えられた画像と説明を解析し、その問題の種類、難易度、主要な要素を特定してください。"
            },
            {
                "role": "user",
                "content": f"次の数学の問題を解析してください:\n'{problem}'\n\n添付された画像を考慮してください。以下は画像のデータです。\n\n画像(Base64):\n{base64_image}\n\nあなたのタスクは、問題の種類（例：方程式、幾何、微積分など）、難易度（初級、中級、上級）、主要な要素（変数、定数、図形など）を特定し、以下のJSON形式で返答することです。\n\n{{\n  \"type\": \"問題の種類\",\n  \"difficulty\": \"難易度\",\n  \"elements\": [\"主要な要素のリスト\"]\n}}\n\nJSON以外の出力はしないでください。"
            },
        ]
