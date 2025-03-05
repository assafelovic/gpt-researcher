from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    class DraftState(TypedDict):
        task: dict[str, Any]
        topic: str
        draft: dict[str, Any]
        review: str
        revision_notes: str
