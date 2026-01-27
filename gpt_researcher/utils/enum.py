"""Enumeration types for GPT Researcher configuration."""

from enum import Enum


class ReportType(Enum):
    """Enumeration of available report types for research output.

    Defines the different types of reports that can be generated
    by the GPT Researcher agent.

    Attributes:
        ResearchReport: Standard research report with comprehensive analysis.
        ResourceReport: Report focused on listing and describing resources.
        OutlineReport: Report providing a structured outline of the topic.
        CustomReport: User-defined custom report format.
        DetailedReport: In-depth detailed analysis report.
        SubtopicReport: Report focused on a specific subtopic.
        DeepResearch: Deep research mode with extensive analysis.
    """
    ResearchReport = "research_report"
    ResourceReport = "resource_report"
    OutlineReport = "outline_report"
    CustomReport = "custom_report"
    DetailedReport = "detailed_report"
    SubtopicReport = "subtopic_report"
    DeepResearch = "deep"


class ReportSource(Enum):
    """Enumeration of available data sources for research.

    Defines the different sources from which the researcher
    can gather information for generating reports.

    Attributes:
        Web: Search and scrape content from the web.
        Local: Use local documents and files.
        Azure: Use Azure blob storage documents.
        LangChainDocuments: Use LangChain document objects.
        LangChainVectorStore: Use LangChain vector store for retrieval.
        Static: Use pre-defined static content.
        Hybrid: Combine multiple source types.
    """
    Web = "web"
    Local = "local"
    Azure = "azure"
    LangChainDocuments = "langchain_documents"
    LangChainVectorStore = "langchain_vectorstore"
    Static = "static"
    Hybrid = "hybrid"


class Tone(Enum):
    """Enumeration of available writing tones for reports.

    Defines the different tones that can be used when generating
    research reports to match the desired style and audience.

    Each tone value includes a description of the writing style
    it represents.
    """
    Objective = "Objective (impartial and unbiased presentation of facts and findings)"
    Formal = "Formal (adheres to academic standards with sophisticated language and structure)"
    Analytical = (
        "Analytical (critical evaluation and detailed examination of data and theories)"
    )
    Persuasive = (
        "Persuasive (convincing the audience of a particular viewpoint or argument)"
    )
    Informative = (
        "Informative (providing clear and comprehensive information on a topic)"
    )
    Explanatory = "Explanatory (clarifying complex concepts and processes)"
    Descriptive = (
        "Descriptive (detailed depiction of phenomena, experiments, or case studies)"
    )
    Critical = "Critical (judging the validity and relevance of the research and its conclusions)"
    Comparative = "Comparative (juxtaposing different theories, data, or methods to highlight differences and similarities)"
    Speculative = "Speculative (exploring hypotheses and potential implications or future research directions)"
    Reflective = "Reflective (considering the research process and personal insights or experiences)"
    Narrative = (
        "Narrative (telling a story to illustrate research findings or methodologies)"
    )
    Humorous = "Humorous (light-hearted and engaging, usually to make the content more relatable)"
    Optimistic = "Optimistic (highlighting positive findings and potential benefits)"
    Pessimistic = (
        "Pessimistic (focusing on limitations, challenges, or negative outcomes)"
    )
    Simple = "Simple (written for young readers, using basic vocabulary and clear explanations)"
    Casual = "Casual (conversational and relaxed style for easy, everyday reading)"


class PromptFamily(Enum):
    """Supported prompt families by name"""
    Default = "default"
    Granite = "granite"
    Granite3 = "granite3"
    Granite31 = "granite3.1"
    Granite32 = "granite3.2"
    Granite33 = "granite3.3"
