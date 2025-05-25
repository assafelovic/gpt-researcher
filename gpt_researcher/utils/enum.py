from enum import Enum


class ReportType(Enum):
    ResearchReport = "research_report"
    ResourceReport = "resource_report"
    OutlineReport = "outline_report"
    CustomReport = "custom_report"
    DetailedReport = "detailed_report"
    SubtopicReport = "subtopic_report"
    DeepResearch = "deep_research"


class ReportSource(Enum):
    Web = "web"
    Local = "local"
    LangChainDocuments = "langchain_documents"
    LangChainVectorStore = "langchain_vectorstore"
    Static = "static"
    Hybrid = "hybrid"


class Tone(Enum):
    Objective = "Objective (impartial and unbiased presentation of facts and findings)"
    Professional = "Professional (formal, authoritative, business-appropriate)"
    Conversational = "Conversational (friendly, approachable, easy to understand)"
    Academic = "Academic (scholarly, rigorous, evidence-based)"
    Journalistic = "Journalistic (investigative, balanced, newsworthy)"
    Technical = "Technical (precise, detailed, expert-level)"
    Executive = "Executive (concise, strategic, decision-focused)"
    Educational = "Educational (clear, instructive, beginner-friendly)"
    Creative = "Creative (engaging, storytelling, memorable)"

    Narrative = "Narrative (telling a story to illustrate research findings or methodologies)"
    Humorous = "Humorous (light-hearted and engaging, usually to make the content more relatable)"
    Optimistic = "Optimistic (highlighting positive findings and potential benefits)"
    Pessimistic = "Pessimistic (focusing on limitations, challenges, or potential risks)"


class PromptFamily(Enum):
    """Supported prompt families by name"""
    Default = "default"
    Granite = "granite"
    Granite3 = "granite3"
    Granite31 = "granite3.1"
    Granite32 = "granite3.2"
    Granite33 = "granite3.3"
