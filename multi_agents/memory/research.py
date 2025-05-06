from __future__ import annotations

from typing import Any, TypedDict

class ResearchState(TypedDict):
    human_feedback: str
    initial_research: str
    research_data: list[dict[str, Any]]
    sections: list[str]
    task: dict[str, Any]
    # Report layout
    conclusion: str
    date: str
    headers: dict
    introduction: str
    report: str
    sources: list[str]
    table_of_contents: str
    title: str
