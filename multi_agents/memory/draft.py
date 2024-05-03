from typing import TypedDict, List, Annotated
import operator


class DraftState(TypedDict):
    task: dict
    draft: str
    review: str