from typing import TypedDict, List, Annotated
import operator


class DraftState(TypedDict):
    task: dict
    topic: str
    sibling_sections: List[str]
    draft: dict
    review: str
    revision_notes: str
    draft_revision_count: int
