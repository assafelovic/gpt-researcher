from datetime import datetime
from typing import Dict, Any
import json5 as json
from .utils.views import print_agent_output
from .utils.llms import call_model

class ExplainerAgent:
    """Agent responsible for explaining the solution in a user-friendly way."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers

    async def explain_solution(self, solution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explain the solution based on the SolverAgent's output.

        :param solution_state: Dictionary containing the solutions and approaches
        :return: Dictionary with the user-friendly explanation for each approach
        """
        task = solution_state.get("task")
        solutions = solution_state.get("solutions")
        model = task.get("model", "gpt-4")

        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "explaining_solution",
                "Explaining the solution for the given problem...",
                self.websocket,
            )
        else:
            print_agent_output(
                "Explaining the solution for the given problem...",
                agent="EXPLAINER",
            )

        explanations = []
        for solution in solutions:
            approach = solution.get("approach")
            steps = solution.get("solution_steps")
            final_solution = solution.get("final_solution")

            # Generate explanation for each approach
            prompt = self._create_explanation_prompt(approach, steps, final_solution)

            explanation = await call_model(
                prompt=prompt,
                model=model,
                response_format="text",
            )

            explanations.append({
                "approach": approach,
                "explanation": explanation,
            })

        return {"explanations": explanations}

    def _create_explanation_prompt(self, approach: str, steps: list, final_solution: str) -> list:
        """Create the prompt for explaining the solution."""
        steps_formatted = "\n".join(f"- {step}" for step in steps)

        return [
            {
                "role": "system",
                "content": "あなたは親切な数学教師です。学生が理解しやすいように、解法の各ステップと最終解答について詳細な説明を行います。"
            },
            {
                "role": "user",
                "content": f"""以下の数学の問題に対する解法を説明してください。

解法アプローチ: {approach}

ステップ:
{steps_formatted}

最終解答: {final_solution}

タスクは、学生がわかりやすい言葉で解法の流れと最終解答の意味を説明することです。結果は以下のような文章形式で返答してください。

- 解法アプローチの概要。
- 各ステップの詳細な解説。
- 最終解答の意味を説明。

文章以外の形式では返答しないでください。"""
            },
        ]

    async def run(self, solution_state: Dict[str, Any]):
        """
        Main method to explain the solution.

        :param solution_state: Dictionary containing the solutions and related information
        :return: Explanations for the solutions
        """
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "starting_explanation",
                "Starting explanation process...",
                self.websocket,
            )
        else:
            print_agent_output("Starting explanation process...", agent="EXPLAINER")

        explanations = await self.explain_solution(solution_state)

        if solution_state.get("task").get("verbose"):
            if self.websocket and self.stream_output:
                explanations_str = json.dumps(explanations, indent=2)
                await self.stream_output(
                    "logs",
                    "explanations",
                    explanations_str,
                    self.websocket,
                )
            else:
                print_agent_output(explanations, agent="EXPLAINER")

        return explanations
