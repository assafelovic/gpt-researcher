from enum import Enum
class ReportType(Enum):
    ResearchReport = 'research_report'
    ResourceReport = 'resource_report'
    OutlineReport = 'outline_report'
    CustomReport = 'custom_report'
    DetailedReport = 'detailed_report'
    SubtopicReport = 'subtopic_report'
    
class ReportSource(Enum):
    Web = 'web'
    Local = 'local'
    LangChainDocuments = 'langchain_documents'
