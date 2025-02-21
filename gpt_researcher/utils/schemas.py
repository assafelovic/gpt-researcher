from __future__ import annotations

import importlib.util

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from gpt_researcher.utils.validators import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path

    from requests import Session
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
    async def on_research_step(self, step: str, details: dict, **kwargs):
        pass

    @abstractmethod
    async def on_logs(self, content: str, output: str, metadata: dict, **kwargs):
        pass

    @abstractmethod
    async def on_images(self, images: list, **kwargs):
        pass


class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)


class Subtopics(BaseModel):
    subtopics: list[Subtopic] = []


class BaseScraper(ABC):
    """Base class for all scrapers."""

    API_KEY_NAME: ClassVar[str | None] = None
    MODULE_NAME: ClassVar[Literal["tavily", "arxiv", "bs", "pdf", "web"]] = "web"

    def __init__(
        self,
        link: str,
        session: Session,
        scraper: str,
    ) -> None:
        self.link: str = link
        self.session: Session = session
        self.scraper: str = scraper
        self.check_package_installed()

    def check_package_installed(self) -> None:
        if not self.MODULE_NAME or not self.MODULE_NAME.strip():
            return
        if not importlib.util.find_spec(self.MODULE_NAME):
            raise ModuleNotFoundError(f"Package '{self.MODULE_NAME}' not found in environment. Might need to install with `pip`")

    @abstractmethod
    def extract_data_from_url(
        self,
        link: str,
        session: Session,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def scrape(self) -> tuple[str, list[dict[str, Any]], str]: ...
