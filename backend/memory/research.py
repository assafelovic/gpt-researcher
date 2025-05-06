from __future__ import annotations

from typing import TypedDict


class ResearchState(TypedDict):
    task: dict
    initial_research: str
    sections: list[str]
    research_data: list[dict]
    # Report layout
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: list[str]
    report: str
