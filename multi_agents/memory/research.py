from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    class ResearchState(TypedDict):
        human_feedback: str
        initial_research: str
        research_data: list[dict]
        sections: list[str]
        task: dict
        # Report layout
        conclusion: str
        date: str
        headers: dict
        introduction: str
        report: str
        sources: list[str]
        table_of_contents: str
        title: str
