from datetime import datetime
import json5 as json
from .utils.views import print_agent_output
from .utils.llms import call_model
# 必要に応じて不要なインポートを削除
# from langchain.vectorstores import FAISS

class MathTeacherAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers

    async def explain_concepts(self, math_topic: str, task: dict):
        model = task.get("model", "gpt-4")
        follow_guidelines = task.get("follow_guidelines", False)
        guidelines = task.get("guidelines", "")

        prompt = [
            {
                "role": "system",
                "content": "あなたは親切な数学の先生です。数学の概念をわかりやすく説明し、ステップバイステップの解説を提供します。"
            },
            {
                "role": "user",
                "content": f"次の数学の概念について詳しく説明してください: {math_topic}。"
                            f"{f' 指示に従ってください: {guidelines}' if follow_guidelines else ''}"
            },
        ]

        response = await call_model(
            prompt,
            model,
            response_format="text",
        )
        return response

    async def solve_problem(self, problem_statement: str, task: dict):
        model = task.get("model", "gpt-4")
        follow_guidelines = task.get("follow_guidelines", False)
        guidelines = task.get("guidelines", "")

        prompt = [
            {
                "role": "system",
                "content": "あなたは親切な数学の先生です。数学の問題をステップバイステップで解き、各ステップを詳しく説明します。"
            },
            {
                "role": "user",
                "content": f"次の問題を解いてください:\n{problem_statement}\n"
                            f"{f' 指示に従ってください: {guidelines}' if follow_guidelines else ''}"
            },
        ]

        response = await call_model(
            prompt,
            model,
            response_format="text",
        )
        return response

    async def run(self, interaction_state: dict):
        task = interaction_state.get("task")
        action = task.get("action")  # "explain" または "solve"
        topic_or_problem = task.get("topic_or_problem")

        if action == "explain":
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "explaining_concept",
                    f"{topic_or_problem} の概念を説明しています...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    f"{topic_or_problem} の概念を説明しています...",
                    agent="MATH_TEACHER",
                )

            explanation = await self.explain_concepts(topic_or_problem, task)
            return {"explanation": explanation}

        elif action == "solve":
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "solving_problem",
                    f"問題を解いています: {topic_or_problem}...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    f"問題を解いています: {topic_or_problem}...",
                    agent="MATH_TEACHER",
                )

            solution = await self.solve_problem(topic_or_problem, task)
            return {"solution": solution}

        else:
            raise ValueError("タスクに無効なアクションが指定されています。")

