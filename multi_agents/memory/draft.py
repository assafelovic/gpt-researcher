from typing import TypedDict, List, Annotated
import operator


class DraftState(TypedDict):
    task: dict
    title: str
    topic: str
    draft: str
    review: str