from typing import TypedDict, List, Annotated
import operator


class ResearchState(TypedDict):
    task: dict
    initial_research: str
    sections: List[str]
    research_data: List[dict]
    human_feedback: str
    # Report layout
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[str]
    report: str

class ResearchStateMath(TypedDict):
    task: dict  # タスク情報（問題の詳細、使用するモデルなど）
    parsed_problem: dict  # ParserAgent による問題の解析結果
    solution_plan: dict  # PlannerAgent による解法の計画
    solutions: List[dict]  # SolverAgent による解法の詳細と結果
    explanations: List[dict]  # ExplainerAgent による解法の説明


