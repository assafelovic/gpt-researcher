from typing import Dict, Any
from .utils.views import print_agent_output
from .utils.llms import call_model
import asyncio

class PlannerAgent:
    """Agent responsible for planning the solution to the math problem."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def plan_solution(self, problem_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan the solution steps based on the parsed problem details.

        :param problem_state: Dictionary containing the parsed problem details
        :return: Dictionary with the solution plan
        """
        task = problem_state.get("task")
        parsed_problem = problem_state.get("parsed_problem")
        model = task.get("model", "gpt-4")

        problem_type = parsed_problem.get("type")
        difficulty = parsed_problem.get("difficulty")
        elements = parsed_problem.get("elements")

        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "planning_solution",
                f"Planning solution for the problem of type '{problem_type}' with difficulty '{difficulty}'.",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Planning solution for the problem of type '{problem_type}' with difficulty '{difficulty}'.",
                agent="PLANNER",
            )

        prompt = self._create_planning_prompt(parsed_problem)

        plan_result = await call_model(
            prompt=prompt,
            model=model,
            response_format="json",
        )

        return {
            "solution_plan": plan_result
        }

    def _create_planning_prompt(self, parsed_problem: Dict[str, Any]) -> list:
        """Create the prompt for planning the solution to the math problem."""
        problem_type = parsed_problem.get("type")
        difficulty = parsed_problem.get("difficulty")
        elements = parsed_problem.get("elements")

        return [
            {
                "role": "system",
                "content": "あなたは熟練した数学の教育者であり、学生が数学の問題を解くためのステップバイステップの解法を計画します。"
            },
            {
                "role": "user",
                "content": f"""以下の数学の問題に対する解法を計画してください。

問題の種類: {problem_type}
難易度: {difficulty}
主要な要素: {elements}

タスクは、問題を解くための詳細なステップをリストアップし、必要に応じて複数の解法アプローチを提示することです。各ステップには具体的な操作や適用する公式を含めてください。結果は以下のJSON形式で返答してください。

{{
  "steps": [
    "ステップ1の説明",
    "ステップ2の説明",
    "...（必要なだけ追加）"
  ],
  "approaches": [
    "アプローチ1の概要（任意）",
    "アプローチ2の概要（任意）"
  ]
}}

JSON以外の出力はしないでください。"""
            },
        ]
