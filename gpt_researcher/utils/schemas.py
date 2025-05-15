from __future__ import annotations


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from gpt_researcher.utils.validators import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Literal, TypedDict

    class ResearchDocument(TypedDict, total=False):
        raw_content: str
        source_type: Literal["local", "online"]

    class LocalResearchDocument(ResearchDocument):
        filepath: Path
        source_type: Literal["local"]

    class OnlineResearchDocument(ResearchDocument):
        url: str
        source_type: Literal["online"]


T = TypeVar("T")


class LogHandler(ABC, Generic[T]):
    @abstractmethod
    async def on_tool_start(self, tool_name: str, **kwargs):
        pass

    @abstractmethod
    async def on_agent_action(self, action: str, **kwargs):
        pass

    @abstractmethod
    async def on_research_step(self, step: str, details: dict[str, Any], **kwargs):
        pass


class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)


class Subtopics(BaseModel):
    subtopics: list[Subtopic] = []
