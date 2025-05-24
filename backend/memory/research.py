from __future__ import annotations

import operator

from typing import Annotated, Any, TypedDict


class ResearchState(TypedDict):
    task: dict[str, Any]
    initial_research: str
    sections: list[str]
    research_data: list[dict[str, Any]]
    # Report layout
    title: str
    headers: dict[str, Any]
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: list[str]
    report: str
