from __future__ import annotations

import importlib.util

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from requests import Session
from typing_extensions import Literal


class BaseScraperABC(ABC):
    """ABC for all scrapers."""

    @abstractmethod
    def __init__(self, link: str | None = None, session: Session | None = None) -> None:
        ...

    @abstractmethod
    def scrape(self) -> tuple[str, list[dict[str, Any]], str]: ...


# TODO: Finish this improved class
class BaseScraper(BaseScraperABC):
    """Base class for all scrapers."""

    API_KEY_NAME: ClassVar[str | None] = None
    MODULE_NAME: ClassVar[Literal["tavily", "arxiv", "bs", "pdf", "web"] | None] = None

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
