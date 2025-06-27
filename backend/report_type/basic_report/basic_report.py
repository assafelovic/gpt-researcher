from fastapi import WebSocket
from typing import Any

from gpt_researcher import GPTResearcher


class BasicReport:
    def __init__(
        self,
        query: str,
        query_domains: list,
        report_type: str,
        report_source: str,
        source_urls,
        document_urls,
        tone: Any,
        config_path: str,
        websocket: WebSocket,
        headers=None,
        mcp_configs=None,
        mcp_strategy=None,
    ):
        self.query = query
        self.query_domains = query_domains
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.document_urls = document_urls
        self.tone = tone
        self.config_path = config_path
        self.websocket = websocket
        # self.headers = headers or {}
        self.headers = {"retrievers": "pubmed_central, tavily"}

        # Initialize researcher with optional MCP parameters
        gpt_researcher_params = {
            "query": self.query,
            "query_domains": self.query_domains,
            "report_type": self.report_type,
            "report_source": self.report_source,
            "source_urls": self.source_urls,
            "document_urls": self.document_urls,
            "tone": self.tone,
            "config_path": self.config_path,
            "websocket": self.websocket,
            "headers": self.headers,
        }
        
        # Add MCP parameters if provided
        if mcp_configs is not None:
            gpt_researcher_params["mcp_configs"] = mcp_configs
        if mcp_strategy is not None:
            gpt_researcher_params["mcp_strategy"] = mcp_strategy
            
        self.gpt_researcher = GPTResearcher(**gpt_researcher_params)

    async def run(self):
        report = await self.gpt_researcher.conduct_research()
        # await self.gpt_researcher.conduct_research()

#         custom_prompt = """
# **Agent Persona:** You are an experienced physician (MD, PhD) with specialization in [DISEASE INDICATION] and deep expertise in the relevant biological pathways.

# **Task:** Generate a comprehensive disease overview for [DISEASE NAME] using the provided context from medical literature, clinical guidelines, and research databases.

# **Required Structure:**
# 1. **Etiology** - Provide detailed pathophysiology, genetic factors, environmental triggers, and molecular mechanisms
# 2. **Symptoms** - List primary and secondary symptoms, including systemic manifestations
# 3. **Diagnostic Algorithm** - Detail clinical criteria, laboratory tests, imaging requirements, and classification systems
# 4. **Key Patient Segments** - Segment patients by severity, biomarkers, treatment response, and disease progression
# 5. **Current Treatment Paradigm** - Outline first-line through advanced treatment options, including guidelines from major medical associations
# 6. **Key Unmet Needs** - Identify gaps in diagnosis, treatment efficacy, safety concerns, and accessibility issues

# **Instructions:**
# - Synthesize information from the provided context to create a cohesive overview
# - Focus on clinically relevant information that would inform drug development decisions
# - Include specific biomarkers, pathways, and therapeutic targets mentioned in the literature
# - Highlight any recent advances or changing paradigms in disease understanding
# - Ensure medical accuracy and use appropriate clinical terminology

# **sources To use**
#     • PubMed
#     • GlobalData

# **General Instructions for All Sections**
# 1. **Context Integration:** Synthesize information from all provided sources (GlobalData, web search, PubMed) into a cohesive analysis
# 2. **Data Quality:** When data conflicts between sources, prioritize more recent and authoritative sources
# 3. **Completeness:** If information is missing from the provided context, note "ND" (not disclosed/determined) rather than speculating
# 4. **Professional Tone:** Maintain the perspective of the assigned expert persona throughout
# 5. **Actionable Insights:** Focus on information that would inform business and clinical development decisions
# 6. **Current Information:** Prioritize the most recent data available in the provided context
# 7. **Cross-Referencing:** Ensure consistency across sections (e.g., epidemiology numbers should align with market model assumptions)
# 8. **Refereces Section** Use in-text citation references in last of report and make it with markdown hyperlink placed at the end of the report that references them like this: ([in-text citation](url)).
# """
#         report = await self.gpt_researcher.write_report(custom_prompt=custom_prompt)
        return report
