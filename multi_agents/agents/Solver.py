from typing import Dict, Any, List
from .utils.views import print_agent_output
from .utils.llms import call_model

class SolverAgent:
    """Agent responsible for solving the math problem based on the parsed problem details."""

    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def solve_problem(self, parsed_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the problem based on the parsed problem details.

        :param parsed_state: Dictionary containing the parsed problem details
        :return: Dictionary with the detailed solution
        """
        task = parsed_state.get("task")
        parsed_problem = parsed_state.get("parsed_problem")
        model = task.get("model", "gpt-4")

        if parsed_problem is None:
            print_agent_output("Error: parsed_problem is None", agent="SOLVER")
            return {"solutions": None}

        problem_text = task.get("problem")
        problem_type = parsed_problem.get("type")
        difficulty = parsed_problem.get("difficulty")
        elements = parsed_problem.get("elements")

        # 初回試行
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "solving_problem",
                "Solving the problem...",
                self.websocket,
            )
        else:
            print_agent_output("Solving the problem...", agent="SOLVER")

        # プロンプトを生成
        prompt = self._create_solving_prompt(
            problem_text,
            problem_type,
            difficulty,
            elements
        )

        try:
            solution = await call_model(
                prompt=prompt,
                model=model,
                response_format="json",
            )
        except Exception as e:
            print_agent_output(f"Error in solving problem: {e}", agent="SOLVER")
            return {"solutions": None}

        # モデルの応答が None または形式不正の場合
        if not solution or not isinstance(solution, dict):
            print_agent_output("Error: Model returned invalid solution", agent="SOLVER")
            return {"solutions": None}

        print_agent_output(f"Received solution: {solution}", agent="SOLVER")
        return {"solutions": [solution]}

    def _create_solving_prompt(self, problem_text: str, problem_type: str, difficulty: str, elements: List[str]) -> list:
        """Create the prompt for solving the problem using the parsed details."""
        elements_text = ", ".join(elements) if elements else "要素なし"

        # 証明のガイドラインを統一して記述
        guidelines = """
あなたは熟練した数学教師です。以下の数学の問題に対して、正式な証明と解答を提供してください。

**要件**:
- 証明は数学的慣習に従い、論理的な流れを明確に示すこと。
- 必要な定理や公式を明示的に使用すること。
- 記号や用語は適切に使用し、省略しないこと。
- [図形の証明問題]の場合のみについては以下の合同条件や相似条件、書式を活用してください。

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
JSON形式で解答を返してください。各ステップと最終結論を明確に記述してください。
"""

        return [
            {
                "role": "user",
                "content": f"""{guidelines}

**問題**:
{problem_text}

問題の種類: {problem_type}
難易度: {difficulty}
主要な要素: {elements_text}
"""
            },
        ]
