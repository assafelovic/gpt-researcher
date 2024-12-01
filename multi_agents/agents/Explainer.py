from datetime import datetime
from typing import Dict, Any, List
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
        Explain the solution based on the SolverAgent's or FormatterAgent's output.

        :param solution_state: Dictionary containing the solutions and approaches
        :return: Dictionary with the user-friendly explanation for each approach
        """
        task = solution_state.get("task")
        solutions = solution_state.get("solutions")
        model = task.get("model", "gpt-4")

        if not solutions or not isinstance(solutions, list):
            print_agent_output("Error: solutions is None or not a list", agent="EXPLAINER")
            return {"explanations": []}

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
            # 各 solution が辞書であることを確認
            if not isinstance(solution, dict):
                print_agent_output("Error: Each solution should be a dict.", agent="EXPLAINER")
                continue

            # 解答データを取得
            steps = solution.get("solution_steps")  # None の場合も許容
            final_solution = solution.get("answer", solution.get("final_solution", "最終解答なし"))
            explanation_from_formatter = solution.get("explanation")  # FormatterAgentの説明

            if not steps:
                # `solution_steps` がない場合、FormatterAgentの説明を利用
                steps = explanation_from_formatter.split("\n") if explanation_from_formatter else []

            # Generate explanation for the solution
            prompt = self._create_explanation_prompt(steps, final_solution)

            try:
                explanation = await call_model(
                    prompt=prompt,
                    model=model,
                    response_format="text",
                )
            except Exception as e:
                print_agent_output(f"Error in explaining solution: {e}", agent="EXPLAINER")
                explanation = "エラーが発生しました。"

            explanations.append({
                "final_solution": final_solution,
                "explanation": explanation,
            })

        return {"explanations": explanations}

    def _create_explanation_prompt(self, steps: List[str], final_solution: str) -> list:
        """Create the prompt for explaining the solution."""
        steps_formatted = "\n".join(f"- {step}" for step in steps) if steps else "ステップが提供されていません。"

        return [
            {
                "role": "system",
                "content": "あなたは親切な数学教師です。解答そのものには手を加えず、解法の各ステップと背景を詳細に説明します。また、解説では LaTeX を用いて数式を正確に表現します。"
            },
            {
                "role": "user",
                "content": f"""以下の数学の問題に対する解法を説明してください。

ステップ:
{steps_formatted}

最終解答: {final_solution}

タスク:
1. 解法アプローチの概要を説明。
2. 各ステップの背景や意図を詳細に説明。
3. 最終解答の意味を解説。

解説は LaTeX を使用して以下の形式で返答してください:
- 解法アプローチの説明: `\\text{{...}}`
- 各ステップ: `\\begin{{align*}} ... \\end{{align*}}`
- 最終解答の意味: `\\boxed{{...}}`

LaTeX の文法以外の形式は含めないでください。"""
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
            explanations_str = json.dumps(explanations, indent=2, ensure_ascii=False)
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "explanations", explanations_str, self.websocket)
            else:
                print_agent_output(explanations_str, agent="EXPLAINER")

        return explanations
