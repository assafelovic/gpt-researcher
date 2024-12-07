from typing import Dict, Any
from .utils.views import print_agent_output
from .utils.llms import call_model

class FormatterAgent:
    """Agent responsible for formatting and verifying the solution from SolverAgent."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def validate_solution(self, solution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and verify the solution provided by SolverAgent.

        :param solution_state: Dictionary containing the solution from SolverAgent
        :return: Dictionary with validation results
        """
        task = solution_state.get("task")
        solutions = solution_state.get("solutions")  # Expecting a list of solutions

        if not solutions or not isinstance(solutions, list):
            print_agent_output("Error: No solution provided or invalid format", agent="FORMATTER")
            return {"validation_passed": False, "solutions": None}

        solution_text = solutions[0]  # Take the first solution for validation

        # Validation logs
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "validating_solution",
                "Validating and formatting the solution...",
                self.websocket,
            )
        else:
            print_agent_output("Validating and formatting the solution...", agent="FORMATTER")

        # Create a validation prompt
        prompt = self._create_validation_prompt(solution_text)

        try:
            validation_result = await call_model(
                prompt=prompt,
                model=task.get("model", "gpt-4"),
                response_format="json",
            )
        except Exception as e:
            print_agent_output(f"Error in validating solution: {e}", agent="FORMATTER")
            return {"validation_passed": False, "solutions": None}

        if not validation_result or "answer" not in validation_result:
            print_agent_output("Validation failed: No valid answer in response", agent="FORMATTER")
            return {"validation_passed": False, "solutions": None}

        # Return the validated solution with formatting
        formatted_solution = {
            "validation_passed": True,
            "solutions": [validation_result],  # Ensure it stays as a list
            "formatted_answer": validation_result.get("answer"),
            "formatted_explanation": validation_result.get("explanation"),
        }

        return formatted_solution

    def _create_validation_prompt(self, solution_text: str) -> list:
        """Create the prompt for validating and formatting the solution."""
        guidelines = """
あなたは数学の専門家です。以下の解答を数学的な慣習に従ってチェックし、必要に応じて修正してください。

**要件**:
- 解答が数学的な慣習に従っているか確認し、必要に応じて修正する。
- 数学記号や用語を統一する。
- 不足している論理ステップや理由があれば補完する。
- 解答と解説を分離し、以下の形式に整形する。

**合同条件**:
1. 三辺が等しい場合。
2. 二辺とその間の角が等しい場合。
3. 一辺とその両端の角が等しい場合。
4. 直角三角形における斜辺と他の一辺が等しい場合。

**相似条件**:
1. 三角形のすべての角が等しい場合。
2. 二辺の比とその間の角が等しい場合。
3. 三辺の比が等しい場合。

**書式**:
1. 仮定よりわかることに関しては"仮定より"の後に続くように明解なことを書け。

**出力形式**:
{ "answer": "【解答】\n（ここに修正済みの解答を記述）", "explanation": "【解説】\n（ここに修正済みの解説を記述）" }

**注意**:
- 解答が正しい手順で進められているか、論理の飛躍や誤りがないか確認する。
- 図形の証明問題の場合、合同条件や相似条件を明示する。
- 問題がある場合、"feedback" フィールドに具体的なフィードバックを記述する。
- フィードバックがない場合、"feedback" フィールドは空にするか省略してください。

以下が解答です。
"""
        return [
            {
                "role": "user",
                "content": f"""{guidelines}

【解答】:
{solution_text}
"""
            },
        ]
