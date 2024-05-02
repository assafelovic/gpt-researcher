from typing import TypedDict, List, Annotated
import operator


class ResearchState(TypedDict):
    task: dict
    initial_research: str
    sections: List[str]
    title: str
    date: str
    table_of_contents: str
    introduction: str
    research_data: List[dict]
    conclusion: str
    sources: List[str]
    report: str


