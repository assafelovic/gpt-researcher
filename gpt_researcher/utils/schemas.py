from __future__ import annotations

import importlib.util

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from litellm import BaseModel, Field

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


class ReportType(Enum):
    ResearchReport = "research_report"
    ResourceReport = "resource_report"
    OutlineReport = "outline_report"
    CustomReport = "custom_report"
    DetailedReport = "detailed_report"
    SubtopicReport = "subtopic_report"
    MultiAgents = "multi_agents"


class ReportFormat(Enum):
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "Chicago"
    HARVARD = "Harvard"
    IEEE = "IEEE"
    AMA = "AMA"
    CSE = "CSE"
    ASA = "ASA"
    AIP = "AIP"
    APSA = "APSA"
    BLUEBOOK = "Bluebook"
    CHICAGO17 = "Chicago17"
    MLA8 = "MLA8"
    MLA9 = "MLA9"
    NLM = "NLM"
    OSCOLA = "OSCOLA"
    IEEETRAN = "IEEEtran"
    AAG = "AAG"
    SBL = "SBL"
    TURABIAN = "Turabian"
    VANCOUVER = "Vancouver"


class OutputFileType(Enum):
    ASCIIDOC = "adoc"
    CBZ = "cbz"
    CSS = "css"
    CSV = "csv"
    DOC = "doc"
    DOCX = "docx"
    EMAIL = "email"
    EPUB = "epub"
    FB2 = "fb2"
    HTML = "html"
    HTTP = "http"
    IMAGE = "image"
    JSON = "json"
    JSONLD = "jsonld"
    LATEX = "tex"
    MARKDOWN = "markdown"
    MHTML = "mhtml"
    MOBI = "mobi"
    NDJSON = "ndjson"
    ODT = "odt"
    ORG = "org"
    OTF = "otf"
    PAGES = "pages"
    PDF = "pdf"
    PPT = "ppt"
    PPTX = "pptx"
    PUB = "pub"
    RST = "rst"
    RTF = "rtf"
    TOML = "toml"
    TSV = "tsv"
    TTF = "ttf"
    TXT = "txt"
    VSX = "vsx"
    WOFF = "woff"
    WOFF2 = "woff2"
    XLS = "xls"
    XLSX = "xlsx"
    XML = "xml"
    XPS = "xps"
    YAML = "yaml"


class ReportSource(Enum):
    HYBRID = "hybrid"
    LANGCHAIN_DOCUMENTS = "langchain_documents"
    LANGCHAIN_VECTOR_STORE = "langchain_vectorstore"
    LOCAL = "local"
    STATIC = "static"
    WEB = "web"


class Tone(Enum):
    Objective = "Objective (impartial and unbiased presentation of facts and findings)"
    Analytical = "Analytical (critical evaluation and detailed examination of data and theories)"
    Comparative = "Comparative (juxtaposing different theories, data, or methods to highlight differences and similarities)"
    Critical = "Critical (judging the validity and relevance of the research and its conclusions)"
    Descriptive = "Descriptive (detailed depiction of phenomena, experiments, or case studies)"
    Explanatory = "Explanatory (clarifying complex concepts and processes)"
    Format = "Formal (adheres to academic standards with sophisticated language and structure)"
    Humorous = "Humorous (light-hearted and engaging, usually to make the content more relatable)"
    Informative = "Informative (providing clear and comprehensive information on a topic)"
    Narrative = "Narrative (telling a story to illustrate research findings or methodologies)"
    Optimistic = "Optimistic (highlighting positive findings and potential benefits)"
    Persuasive = "Persuasive (convincing the audience of a particular viewpoint or argument)"
    Pessimistic = "Pessimistic (focusing on limitations, challenges, or negative outcomes)"
    Reflective = "Reflective (considering the research process and personal insights or experiences)"
    Speculative = "Speculative (exploring hypotheses and potential implications or future research directions)"


class SupportedLanguages(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"


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
