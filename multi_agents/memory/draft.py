from typing import TypedDict, List, Annotated
import operator


class DraftState(TypedDict):
    task: dict
    title: str
    topic: str
    draft: dict
    review: str
    revision_notes: str