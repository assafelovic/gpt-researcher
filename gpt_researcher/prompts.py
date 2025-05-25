from __future__ import annotations

import warnings

from datetime import datetime, timezone
from logging import Logger
from typing import Any, Callable, ClassVar

from langchain.docstore.document import Document

from gpt_researcher.config import Config
from gpt_researcher.utils.enum import PromptFamily as PromptFamilyEnum, ReportSource, ReportType, Tone


## Helper for Tone Descriptions
def get_tone_description(
    tone_enum_member: Tone | None = Tone.Objective,
) -> str:
    if not tone_enum_member:
        tone_enum_member = Tone.Objective

    tone_name_lower: str = tone_enum_member.name.lower()

    # Descriptions are keyed by the lowercase name of the Tone enum member.
    # Each description should guide the LLM on how to embody that tone based on the provided context.
    descriptions: dict[str, str] = {
        "objective": (
            "This report must be written in an Objective tone. This means you must present information factually, "
            "without personal bias, interpretation, or emotional language. Focus on evidence, data, and balanced perspectives "
            "from the provided context. Avoid making unsupported claims or using persuasive language. Stick to what the sources say. "
            f"(Enum Value Hint: '{Tone.Objective.value}')"
        ),
        "formal": (
            "Adopt a Formal tone for this report. Use precise language, proper grammar, and a structured approach. "
            "Avoid colloquialisms, slang, or overly casual phrasing. The writing should be professional and academic in style, "
            f"adhering to standards suitable for the content. (Enum Value Hint: '{Tone.Professional.value}')"
        ),
        "persuasive": (
            "Adopt a Persuasive tone. While basing all arguments on the provided context, structure the information to convincingly "
            "support a specific viewpoint or conclusion that can be derived from the sources. Use logical reasoning and evidence from "
            f"the context to guide the reader towards this viewpoint. (Enum Value Hint: '{Tone.Objective.value}')"
        ),
        "journalistic": (
            "Use a Journalistic tone. Provide a detailed and vivid account of phenomena, experiments, case studies, or subjects from the provided context. "
            "Focus on painting a clear picture for the reader, using specific details and characteristics found in the source material. "
            f"(Enum Value Hint: '{Tone.Journalistic.value}')"
        ),
        "academic": (
            "Use an Academic tone. Provide a detailed and vivid account of phenomena, experiments, case studies, or subjects from the provided context. "
            "Focus on painting a clear picture for the reader, using specific details and characteristics found in the source material. "
            f"(Enum Value Hint: '{Tone.Academic.value}')"
        ),
        "technical": (
            "Use a Technical tone. Provide a detailed and vivid account of phenomena, experiments, case studies, or subjects from the provided context. "
            "Focus on painting a clear picture for the reader, using specific details and characteristics found in the source material. "
            f"(Enum Value Hint: '{Tone.Technical.value}')"
        ),
        "narrative": (
            "Use a Narrative tone if appropriate for the content. Weave the information from the provided context into a coherent story to illustrate research findings or methodologies. "
            "Engage the reader by structuring the report with a clear plot or progression, ensuring all factual claims are backed by the sources. "
            f"(Enum Value Hint: '{Tone.Narrative.value}')"
        ),
        "humorous": (
            "If the topic and context allow, a Humorous tone can be used lightly. This means incorporating witty observations or phrasing where appropriate, "
            "but without undermining the seriousness of the information or becoming unprofessional. Humor should be derived from the context, not arbitrarily inserted. "
            f"(Enum Value Hint: '{Tone.Humorous.value}')"
        ),
        "optimistic": (
            "Adopt an Optimistic tone. Focus on positive findings, potential benefits, and constructive interpretations of the information in the provided context. "
            "While maintaining factual accuracy, frame the narrative in a way that highlights hopefulness and positive outlooks presented in the sources. "
            f"(Enum Value Hint: '{Tone.Optimistic.value}')"
        ),
        "pessimistic": (
            "Employ a Pessimistic tone if the context warrants it. Focus on limitations, challenges, negative outcomes, or potential risks discussed in the provided source material. "
            "Present these aspects clearly and factually, reflecting the concerns raised in the context. "
            f"(Enum Value Hint: '{Tone.Pessimistic.value}')"
        ),
        # Add any other tones from your enum here with their descriptions
    }
    return descriptions.get(
        tone_name_lower,
        f"Write the report in the tone described as: '{tone_enum_member.value}'."
        "Interpret this to the best of your ability based on this description.",
    )


## Prompt Families #############################################################


class PromptFamily:
    """General purpose class for prompt formatting.

    This may be overwritten with a derived class that is model specific. The
    methods are broken down into two groups:

    1. Prompt Generators: These follow a standard format and are correlated with
        the ReportType enum. They should be accessed via
        get_prompt_by_report_type

    2. Prompt Methods: These are situation-specific methods that do not have a
        standard signature and are accessed directly in the agent code.

    All derived classes must retain the same set of method names, but may
    override individual methods.
    """

    def __init__(
        self,
        config: Config | None = None,
    ):
        """Initialize with a config instance.

        This may be used by derived classes to select the correct prompting
        based on configured models and/or providers

        Args:
            config (Config): The config instance
        """
        self.cfg: Config = Config() if config is None else config

    @staticmethod
    def generate_search_queries_prompt(
        question: str,
        parent_query: str,
        report_type: str,
        max_iterations: int = 3,
        context: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generates concise search queries for a given question.

        Args:
            question: The question for which to generate search queries.
            parent_query: The main question (for detailed reports).
            report_type: The type of report.
            max_iterations: Maximum number of search queries.
            context: Optional context for refining queries.

        Returns:
            The search queries prompt.
        """
        context = [] if context is None else context

        task: str = (
            f"{parent_query} - {question}"
            if (
                report_type == ReportType.DetailedReport.value
                or report_type == ReportType.SubtopicReport.value
            )
            else question
        )

        context_prompt: str = (
            f"""
You are a seasoned research assistant tasked with generating search queries to find relevant information for the following task: '''{task}'''
Context: '''{context}'''

Use this context to inform and refine your search queries. The context provides real-time web information that can help you generate more specific and relevant queries. Consider any current events, recent developments, or specific details mentioned in the context that could enhance the search queries."""
            if context
            else ""
        )

        dynamic_example: str = ", ".join([f'"query {i+1}"' for i in range(max_iterations)])

        return f"""Write {max_iterations} google search queries to search online that form an objective opinion from the following task: '''{task}'''

Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.

{context_prompt}

Search Query Principles:
- **Relevance & Focus:** Queries must directly target essential aspects of the refined task and its scope.
- **Diverse Angles:** Explore different facets (definitions, examples, causes, effects, solutions, opinions, related concepts, controversies).
- **Avoid Redundancy:** Queries must be distinct and seek unique information.
- **Appropriate Specificity:** Balance broadness (irrelevant results) and narrowness (missing key info).
- **Strategic Keywords:** Use precise keywords/phrases; consider synonyms.
- **Researcher Mindset:** What questions would you ask to understand this topic thoroughly?

Principles for Generating Search Queries:
-   **Relevance & Focus:** Each query must directly target an essential aspect of the refined research task and its defined scope.
-   **Diversity of Angles:** Aim for queries that explore different facets: e.g., definitions, examples, causes, effects, solutions, expert opinions, related concepts, controversies.
-   **Avoid Redundancy:** Ensure queries are distinct and not minor variations of each other. Each should seek unique information.
-   **Appropriate Specificity:** Balance between being too broad (yielding irrelevant results) and too narrow (missing key information).
-   **Strategic Keywords:** Use precise keywords and phrases. Consider synonyms or alternative phrasings.
-   **Action-Oriented (Implicit):** Think like a researcher: What questions would you ask to understand this topic thoroughly?

Query Generation Process:
1.  **Analyze the Task (as guided above if multi-word, otherwise ensure deep understanding of ```{task}"```).**
2.  **Brainstorm potential questions related to the task.**
3.  **Convert these questions into effective search queries.**
4.  **Self-Critique & Refine:** Before finalizing, review your queries against the principles above. Ask yourself: "Will this set of queries lead to a comprehensive understanding of ```{task}```? Are there any gaps?"

You MUST respond with a Python-style list of strings in the following format: [{dynamic_example}].
The response should contain ONLY the list, with no other text before or after it."""

    @staticmethod
    def generate_report_prompt(
        question: str,
        context: str,
        report_source: str,
        report_format: str = "apa",
        total_words: int = 1000,
        tone: Tone | str | None = None,
        language: str = "english",
    ) -> str:
        """Generates a prompt for creating a standard research report.
        Args:
            question: The research question.
            context: The research summary/context.
            report_source: Source of the report (e.g., web, local).
            report_format: Citation style (e.g., apa, mla).
            total_words: Desired word count for the report.
            tone: The tone of the report.
            language: The language of the report.

        Returns:
            The report generation prompt.
        """

        reference_prompt: str = (
            f"""
Regarding Sources and Citations ({report_format.upper()} style):
-   **References Section:** At the end of the report, list each unique source URL (for web) or document name/identifier (for documents) from the context once.
-   **Web Source Referencing:** In the "References" section, format web URLs as hyperlinks, preferably with the webpage title or site name as clickable text (e.g., [Page Title](url_here)).
-   **In-Text Citations (Web):** When citing web sources in the report body, use a Markdown hyperlink to the source URL at the end of the sentence/paragraph (e.g., ...as stated ([finding](url_to_source))).
-   **In-Text Citations (Documents):** For documents, clearly indicate the source, like (Document Name, Section X) or similar, per {report_format.upper()} style.
-   **CRITICAL:** All citation details (author, year, title, URL/identifier) MUST be from the provided context.  DO NOT use generic placeholders.
-   **Example Web Reference:** Specific Author (if available). (Year, if available). *Title of Web Page*. Website Name. [URL](actual_url_from_context)"""
            if report_source == ReportSource.Web.value
            else f"""
heading Sources and Citations ({report_format.upper()} style):
-   **References Section:** List names/identifiers of all unique source documents from context.
-   With the main body of the report, clearly indicate when information is drawn from a specific document. You might use a parenthetical citation like (Document Name, Section X) or similar, as appropriate for the {report_format.upper()} style and the nature of the document.
-   **CRITICAL:** All citation details (author, year, title, URL/identifier) MUST be from the provided context.  DO NOT use generic placeholders."""
        )

        tone_prompt: str = get_tone_description(tone)

        return f"""Information: '''{context}'''

Using the above information, answer the following query or task: '''{question}'''

Please follow all of the following guidelines:
1. Make sure the report is detailed, informative, in-depth, and comprehensive, with facts and numbers if available.
2. Make sure to use an unbiased and journalistic tone.
3. Make sure to cite the results using an in-text citation for the sources you use, e.g. ([url website](url)).
4. Please do your best to write a well-structured report with markdown syntax.
5. Please write the report in apa format.
6. Use markdown syntax (## headers) for sections.
7. Please write a minimum of {total_words} words.
8. Please write the report in *{language}*.
{tone_prompt}
{reference_prompt}
Please do your best, this is very important to my career."""

    @staticmethod
    def curate_sources(
        query: str,
        sources: str,
        max_results: int = 10,
    ) -> str:
        """Curates and filters web sources based on relevance and data quality.
        Args:
            query: The research query.
            sources: A string containing the list of sources to evaluate.
            max_results: Maximum number of sources to return.

        Returns:
            A JSON string list of curated sources in the original format.
        """
        return f"""Evaluate and select the best web content for the research task: '''{query}'''.
Objective: Identify high-quality, relevant information. Prioritize sources with statistics, numbers, or concrete data.
This curated list will form the basis of a research report.
Prioritize:
- Retaining original information, especially from sources with quantitative data or unique insights.
- Ensuring diverse perspectives.
- Removing only clearly irrelevant or unusable content.

EVALUATION GUIDELINES:
- Relevance: Include if directly or partially related. When in doubt, include.
- Credibility: Prefer authoritative sources, but keep others unless clearly untrustworthy.
- Currency: Recent is generally better, unless older data is specifically valuable.
- Objectivity: Keep biased sources if they offer unique or complementary viewpoints.
- Quantitative Value: Sources with stats, numbers, or concrete data are highly valuable; prioritize them.

SELECTION PRINCIPLES:
- Aim for up to {max_results} relevant sources, covering the topic broadly with diverse viewpoints.
- Strongly prefer sources with statistics, numerical data, or verifiable facts.
- Overlapping info is acceptable if it adds depth or involves data.
- Exclude only if completely irrelevant, hopelessly outdated, or content quality is too poor.

CONTENT PRESERVATION:
- IMPORTANT: Do NOT rewrite, summarize, or shorten source content.
- Keep all usable information. Clean up only obvious "garbage" text or severe formatting problems.
- Retain marginally relevant or incomplete sources if they contain valuable data or unique insights.

SOURCES TO EVALUATE:
'''{sources}'''

Please return a JSON list of the selected sources in the exact same format as provided, limiting to a maximum of {max_results} sources.

Return only the JSON list, no additional text."""

    @staticmethod
    def generate_resource_report_prompt(
        question: str,
        context: str,
        report_source: str,
        report_format: str = "apa",
        tone: Tone | str | None = None,
        total_words: int = 1000,
        language: str = "english",
    ) -> str:
        """Generates a prompt for creating a bibliography/resource recommendation report.

        Args:
            question: The research question or topic.
            context: Research summary/context.
            report_source: Source of the report (web or local).
            report_format: Citation style.
            tone: Tone of the report.
            total_words: Desired word count.
            language: Language of the report.

        Returns:
            The resource report prompt.
        """

        reference_prompt: str = (
            """You must write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)"""
            if report_source == ReportSource.Web.value
            else """
You must write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."""
        )

        tone_prompt: str = get_tone_description(tone)

        return f"""Information: '''{context}'''

Based on the above information, generate a bibliography recommendation report for the following question or topic: '''{question}'''
The report should provide a detailed analysis of each recommended resource, explaining how each source can contribute to understanding the research question.
Focus on the relevance, reliability, and significance of each source.

Please follow all of the following guidelines:
1. Make sure the report is detailed, informative, in-depth, and comprehensive, with facts and numbers if available.
2. Make sure to use an unbiased and journalistic tone.
3. Please do your best to write a well-structured report with markdown syntax.
4. Please write the report in apa format.
5. Use markdown syntax (## headers) for sections.
6. Please write a minimum of {total_words} words.
7. Please write the report in the language: *{language}*.
{tone_prompt}
{reference_prompt}
Please do your best, this is very important to my career."""

    @staticmethod
    def generate_custom_report_prompt(
        query_prompt: str,
        context: str,
        report_source: str,  # Not directly used here, but available if query_prompt needs it
        report_format: str = "apa",  # Not directly used here
        tone: Tone | str | None = None,  # Not directly used here
        total_words: int = 1000,  # Not directly used here
        language: str = "english",  # Not directly used here
    ) -> str:
        """Generates a prompt for a custom report based on user-defined instructions.
        Args:
            query_prompt: User's detailed instructions for the report.
            context: Research summary/context.
            report_source: Source of the report.
            report_format: Citation style.
            tone: Tone of the report.
            total_words: Desired word count.
            language: Language of the report.

        Returns:
            The custom report prompt.
        """
        return f"""Context Information:
```{context}```

Follow these instructions to generate a custom report:
```{query_prompt}```"""

    @staticmethod
    def generate_outline_report_prompt(
        question: str,
        context: str,
        report_source: str,  # Unused, but kept for signature consistency
        report_format: str = "apa",  # Unused
        tone: Tone | None = None,  # Unused
        total_words: int = 1000,
        language: str = "english",
    ) -> str:
        """Generates a prompt for creating a research report outline.
        Args:
            question: The research question or topic.
            context: Research summary/context.
            report_source: Source of the report (unused in this prompt).
            report_format: Citation style (unused).
            tone: Tone of the report (unused).
            total_words: Target word count for the final report.
            language: Language of the report outline.

        Returns:
            The outline report prompt.
        """

        return f"""Context Information:
```{context}```

Task: Create a detailed Markdown outline for a research report on: ```{question}```.

Outline Requirements:
- Serve as a well-structured framework for the final report.
- Clearly define main sections, subsections, and key points.
- Use Markdown for headings (e.g., ## Main Section, ### Subsection) and bullet points for key ideas.
- Pave the way for a comprehensive, informative, in-depth report of at least {total_words} words.
- Language: *{language}*. If context is not in *{language}*, translate or reference a translation.
- Suggest where Markdown tables or other formatting might be used in the full report if helpful.

Formatting guidance for the outline:
- Use appropriate Markdown for headings (e.g., ## for main sections, ### for subsections).
- You can use bullet points for key ideas under each heading.

Please ensure the outline is of high quality, as this is very important.
Assume today's date is {datetime.now(timezone.utc).strftime('%B %d, %Y')}."""

    @staticmethod
    def generate_deep_research_prompt(
        question: str,
        context: str,
        report_source: str,
        report_format: str = "apa",
        tone: Tone | str | None = None,
        total_words: int = 2000,
        language: str = "english",
    ) -> str:
        """Generates a prompt for a deep research report, handling hierarchical results.
        Args:
            question: The research question.
            context: Hierarchically researched information and citations.
            report_source: Source of the research (e.g., web).
            report_format: Report formatting and citation style.
            tone: Tone for writing the report.
            total_words: Minimum word count.
            language: Output language for the report.

        Returns:
            The deep research report prompt.
        """
        reference_prompt: str = (
            f"""
Regarding Sources and Citations ({report_format.upper()} style):
-   **References Section:** At the end, list each unique source URL (web) or document name/identifier (docs) from context once.
-   **Web Source Referencing (References):** Format web URLs as hyperlinks: [Page Title/Site Name](url_here).
-   **In-Text Citations (Web):** Use Markdown hyperlink to source URL at end of sentence/paragraph: ...as stated ([finding](url_to_source)).
-   **In-Text Citations (Documents):** Clearly indicate source: (Document Name, Section X) or similar, per {report_format.upper()} style.
-   **CRITICAL:** All citation details (author, year, title, URL/identifier) MUST be from provided context. NO placeholders.
-   **Example Web Reference:** Specific Author (if available). (Year, if available). *Title of Web Page*. Website Name. [URL](actual_url_from_context)"""
            if report_source == ReportSource.Web.value
            else f"""
Regarding Sources and Citations ({report_format.upper()} style):
-   **References Section:** List names/identifiers of all unique source documents from context.
-   **In-Text Citations:** Clearly indicate information source within report body (e.g., (Document Name, Section X)) per {report_format.upper()} style.
-   **CRITICAL:** All citation details MUST be from actual source information. NO placeholders."""
        )

        tone_instruction: str = get_tone_description(tone)

        return f"""Provided hierarchically researched information and citations:
'''{context}'''

Task: Write a comprehensive research report answering: ```{question}```

Core Objectives:
1.  **Synthesize & Integrate:** Combine info from multiple research levels/branches in context into a coherent narrative.
2.  **Build Narrative:** Present a clear, logical story from foundational to advanced insights from context.
3.  **Cite Sources:** Accurately cite all sources per guidelines below.
4.  **Structure:** Organize with well-defined Markdown sections/subsections. NO Table of Contents.
5.  **Length:** At least {total_words} words, using provided info comprehensively.
6.  **Formatting:** Markdown syntax, *{report_format.upper()}* citation style.
7.  **Data Presentation:** Use Markdown tables, lists for comparative data, stats, or structured info from context.

Additional Guidelines:
-   **Prioritize Deep Insights:** Weight information from deeper research levels if context indicates.
-   **Highlight Connections:** Show relationships between different pieces of information/findings from context.
-   **Include Specifics:** Incorporate relevant stats, data points, and concrete examples from context.
-   **Formulate Opinion (Context-Based):** Based *solely* on provided context, state concrete, valid conclusions. No vague statements or external knowledge.
-   **Source Quality (Context-Based):** If context offers clues, prioritize info from more relevant, reliable, significant sources. Prefer newer articles if comparable.
-   **Tone:** {tone_instruction}
-   **Language:** Written in the language: *{language}*.

{reference_prompt}

Produce a thorough, well-researched report synthesizing all gathered information from context into a cohesive, insightful document.
Please do your best, this is very important to my career."""

    @staticmethod
    def auto_agent_instructions() -> str:
        """Generates instructions for an auto-agent to define a research agent role.

        Returns:
            The auto-agent instructions prompt.
        """
        return """
Determine the AI agent type and generate a role-defining prompt for thorough research on a given topic, regardless of complexity or whether a single definitive answer exists.

Your task: Set up another AI agent for research.
1.  **Identify Agent Type ("server"):** Based on the topic's field, choose a descriptive name (e.g., "💰 Finance Agent", "📈 Business Analyst Agent", "🌍 Travel Agent"). Include a relevant emoji.
2.  **Create Role Prompt ("agent_role_prompt"):** Write a detailed instruction for this agent, defining its behavior and goal. Guide it to produce comprehensive, insightful, well-structured reports based on provided data.

Response Format (JSON object):
{
    "server": "CATEGORY_EMOJI Agent Type Name",
    "agent_role_prompt": "Detailed prompt for the research agent..."
}

Examples:
Input task: "should I invest in apple stocks?"
Output JSON:
{
    "server": "💰 Finance Agent",
    "agent_role_prompt": "You are a seasoned finance analyst AI. Your goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports. Analyze provided data and trends, focusing on actionable insights, balanced risk/reward views, and clear, evidence-based justifications."
}

Input task: "could reselling sneakers become profitable?"
Output JSON:
{
    "server": "📈 Business Analyst Agent",
    "agent_role_prompt": "You are an experienced AI business analyst. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports. Evaluate provided data, market trends, and strategic analyses to assess a business concept's viability, challenges, and success factors, ensuring all claims are data-driven."
}

Input task: "what are the most interesting sites in Tel Aviv?"
Output JSON:
{
    "server": "🌍 Travel Agent",
    "agent_role_prompt": "You are a world-travelled AI tour guide. Your purpose is to draft engaging, insightful, unbiased, and well-structured travel reports. Based on provided information, detail history, attractions, cultural significance, local tips, and practical travel info, making it vivid and informative."
}

Ensure 'agent_role_prompt' clearly defines the agent's persona, objectives for high-quality research output, and emphasizes reliance on the data/context it will be given.
"""

    @staticmethod
    def generate_summary_prompt(
        query: str,
        data: str,
    ) -> str:
        """Generates a prompt to summarize text with a specific focus.

        Args:
            query (str): The specific task or query to focus the summary on.
            data (str): The text to be summarized.

        Returns:
            The summary generation prompt.
        """

        return f"""Text:
```{data}```

Summarize this text focusing on: ```{query}```

Instructions:
- If text directly answers the query, focus summary on those aspects.
- If text doesn't directly answer query, provide a general, concise summary of the text.
- Include factual info (numbers, stats, quotes, specific data) if present."""

    @staticmethod
    def pretty_print_docs(
        docs: list[Document],
        top_n: int | None = None,
    ) -> str:
        """Compress the list of documents into a context string.

        Args:
            docs (list[Document]): The list of documents to compress
            top_n (int | None): The maximum number of documents to return

        Returns:
            str: The compressed context string
        """
        return "\n".join(
            f"Source: {d.metadata.get('source')}\n" f"Title: {d.metadata.get('title')}\n" f"Content: {d.page_content}\n"
            for i, d in enumerate(docs)
            if top_n is None or i < top_n
        )

    @staticmethod
    def join_local_web_documents(
        docs_context: str,
        web_context: str,
    ) -> str:
        """Joins local web documents with context scraped from the internet.

        Args:
            docs_context (str): The context from local documents
            web_context (str): The context from web sources

        Returns:
            str: The joined context string
        """
        return f"""Context from local documents:
'''{docs_context}'''

Context from web sources:
'''{web_context}'''"""

    ################################################################################################

    # DETAILED REPORT PROMPTS

    @staticmethod
    def generate_subtopics_prompt() -> str:
        return """
I need you to help me structure a detailed report.
Main Topic: '''{task}'''

Available Research Data:
'''{data}'''

Your task is to generate a list of subtopics that will serve as the main headers for this report.
Here's what to keep in mind:
- You might consider these potential subtopics as a starting point or for ideas: '''{subtopics}'''.
- Ensure there are NO duplicate subtopics in your final list.
- Please limit the list to a maximum of {max_subtopics} subtopics.
- Arrange the subtopics in a logical and meaningful order suitable for a comprehensive report.
- CRITICALLY IMPORTANT: Every subtopic you choose MUST be directly relevant to the Main Topic ("'''{task}'''")
- CRITICALLY IMPORTANT: Every subtopic you choose MUST be supported by the Available Research Data. Do not invent subtopics that go beyond this scope.

## FORMATTING INSTRUCTIONS
'''{format_instructions}'''
Please provide your response according to these formatting instructions:"""

    @staticmethod
    def generate_draft_titles_prompt(
        current_subtopic: str,
        main_topic: str,
        context: str,
        max_subsections: int = 5,
        language: str = "english",
    ) -> str:
        """Generates prompt for drafting section titles (headers) for a subtopic.
        Args:
            current_subtopic: The subtopic for these headers.
            main_topic: Main topic of the report.
            context: Research context for this subtopic.
            max_subsections: Max number of titles/subsections to generate.
            language: Language for the titles.
        Returns:
            Prompt for generating draft titles.
        """
        return f"""
Main Report Topic: '''{main_topic}'''
Subtopic for these Headers: '''{current_subtopic}'''

Context for this Subtopic:
'''{context}'''

Task: Generate a list of draft section titles (H3 Markdown headers) for the report section about '''{current_subtopic}''', based on the "Context".

Title Guidelines:
1.  **Relevance & Conciseness:** Concise and directly relevant to '''{current_subtopic}'''.
2.  **Specificity:** Detailed enough to indicate specific aspect covered, not too vague.
3.  **Coverage:** Aim to cover main aspects of '''{current_subtopic}'''.
4.  **Format:** H3 Markdown (e.g., `### My Section Title`). Output as a list of these headers.
    Example:
    ```
    ### Example Header 1
    ### Another Example Header
    ### Header 3
    ```

Constraints:
-   **Focus:** Titles must relate directly to '''{main_topic}''' and '''{current_subtopic}'''. NO unrelated titles.
-   **Language:** Written in the language: *{language}*.
-   **Limit:** Max {max_subsections} titles.

"IMPORTANT!":
- The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
- Must NOT have any introduction, conclusion, summary or reference section.
- Focus solely on creating headers, not content."""

    @staticmethod
    def generate_report_introduction(
        question: str,
        research_summary: str = "",
        language: str = "english",
        report_format: str = "apa",
    ) -> str:
        """Generates prompt for writing a report introduction.

        Args:
            question: The main question/topic of the report.
            research_summary: Summary of research findings.
            language: Language for the introduction.
            report_format: Citation style.

        Returns:
            Prompt for generating the report introduction.
        """
        return f"""
Research Summary:
'''{research_summary}'''

Using the above `Research Summary`, prepare a detailed report introduction on the topic -- '''{question}'''
- The introduction should be succinct, well-structured, informative with markdown syntax.
- As this introduction will be part of a larger report, do NOT include any other sections, which are generally present in a report.
- The introduction should be preceded by an H1 heading with a suitable topic for the entire report.
- You must use in-text citation references in *{report_format.upper()}* format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
Assume that the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.
- The output must be written in the language: *{language}*."""

    @staticmethod
    def generate_report_conclusion(
        query: str,
        report_content: str,
        language: str = "english",
        report_format: str = "apa",
    ) -> str:
        """Generate a concise conclusion summarizing the main findings and implications of a research report.

        Args:
            query (str): The research task or question.
            report_content (str): The content of the research report.
            language (str): The language in which the conclusion should be written.
            report_format (str): The format of the report.
        Returns:
            str: A concise conclusion summarizing the report's main findings and implications."""
        return f"""
I need you to write a concise conclusion for a research report.
Research Task/Query: '''{query}'''

Full Research Report Content:
<<BEGIN REPORT CONTENT>>{report_content}<<END REPORT CONTENT>>

Based on the "Research Task/Query" and the "Full Research Report Content" provided above, please write a conclusion that effectively summarizes the report's main findings and their implications.

Your conclusion should adhere to these points:
1.  **Summarize Key Points:** Briefly recap the main arguments or points covered in the research report.
2.  **Highlight Core Findings:** Emphasize the most important discoveries or outcomes of the research.
3.  **Discuss Implications/Next Steps:** Touch upon any significant implications of these findings or suggest potential next steps for research or action.
4.  **Length:** Aim for approximately 2-3 paragraphs.
5.  **Formatting and Titling:**
    *   If the provided "Full Research Report Content" does NOT already end with a "## Conclusion" (H2) heading, please add `## Conclusion` at the very beginning of your response, before the conclusion text.
    *   Use Markdown for any formatting.
    *   If you include citations within the conclusion, they must follow the *{report_format.upper()}* style and be hyperlinked using Markdown (e.g., `([relevant citation](url_or_identifier))`).
6.  **Language:** The entire conclusion, including the "## Conclusion" heading if you add it, MUST be written in the language: *{language}*.

If there is no "## Conclusion" section title written at the end of the report, please add it to the top of your conclusion.
You must use in-text citation references in *{report_format.upper()}* format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).

IMPORTANT: The entire conclusion MUST be written in the language: *{language}*.

Write the conclusion:"""


class GranitePromptFamily(PromptFamily):
    """Prompts for IBM's granite models"""

    def _get_granite_class(self) -> type[PromptFamily]:
        """Get the right granite prompt family based on the version number.

        Returns:
            type[PromptFamily]: The right granite prompt family
        """
        if "3.3" in self.cfg.smart_llm:  # pyright: ignore[reportAttributeAccessIssue]
            return Granite33PromptFamily
        if "3" in self.cfg.smart_llm:  # pyright: ignore[reportAttributeAccessIssue]
            return Granite3PromptFamily
        # If not a known version, return the default
        return PromptFamily

    def pretty_print_docs(self, *args, **kwargs) -> str:
        """Pretty print the documents.

        Returns:
            str: The pretty printed documents
        """
        return self._get_granite_class().pretty_print_docs(*args, **kwargs)

    def join_local_web_documents(self, *args, **kwargs) -> str:
        """Join the local and web documents.

        Returns:
            str: The joined documents
        """
        return self._get_granite_class().join_local_web_documents(*args, **kwargs)


class Granite3PromptFamily(PromptFamily):
    """Prompts for IBM's granite 3.X models (before 3.3)"""

    _DOCUMENTS_PREFIX: ClassVar[str] = "<|start_of_role|>documents<|end_of_role|>\n"
    _DOCUMENTS_SUFFIX: ClassVar[str] = "\n<|end_of_text|>"

    @classmethod
    def pretty_print_docs(
        cls,
        docs: list[Document] | None = None,
        top_n: int | None = None,
    ) -> str:
        """Pretty print the documents.

        Returns:
            str: The pretty printed documents
        """
        if not docs:
            return ""
        all_documents: str = "\n\n".join(
            [
                f"Document {doc.metadata.get('source', i)}\n"
                + f"Title: {doc.metadata.get('title')}\n"
                + doc.page_content
                for i, doc in enumerate(docs)
                if top_n is None or i < top_n
            ]
        )
        return "".join([cls._DOCUMENTS_PREFIX, all_documents, cls._DOCUMENTS_SUFFIX])

    @classmethod
    def join_local_web_documents(
        cls,
        docs_context: str | list[str],
        web_context: str | list[str],
    ) -> str:
        """Joins local web documents using Granite's preferred format.

        Returns:
            str: The joined documents
        """
        if isinstance(docs_context, str) and docs_context.startswith(cls._DOCUMENTS_PREFIX):
            docs_context = docs_context[len(cls._DOCUMENTS_PREFIX) :]
        if isinstance(web_context, str) and web_context.endswith(cls._DOCUMENTS_SUFFIX):
            web_context = web_context[: -len(cls._DOCUMENTS_SUFFIX)]
        combined_context: list[str] = [str(docs_context or ""), str(web_context or "")]
        return "".join(
            [
                cls._DOCUMENTS_PREFIX,
                "\n\n".join(combined_context),
                cls._DOCUMENTS_SUFFIX,
            ]
        )


class Granite33PromptFamily(PromptFamily):
    """Prompts for IBM's granite 3.3 models"""

    _DOCUMENT_TEMPLATE: ClassVar[str] = """<|start_of_role|>document {{"document_id": "{document_id}"}}<|end_of_role|>
{document_content}<|end_of_text|>
"""

    @staticmethod
    def _get_content(doc: Document) -> str:
        doc_content: str = doc.page_content
        title: str | None = doc.metadata.get("title")
        if str(title or "").strip():
            doc_content = f"Title: {title}\n{doc_content}"
        return doc_content.strip()

    @classmethod
    def pretty_print_docs(
        cls,
        docs: list[Document],
        top_n: int | None = None,
    ) -> str:
        return "\n".join(
            [
                cls._DOCUMENT_TEMPLATE.format(
                    document_id=doc.metadata.get("source", i),
                    document_content=cls._get_content(doc),
                )
                for i, doc in enumerate(docs)
                if top_n is None or i < top_n
            ]
        )

    @classmethod
    def join_local_web_documents(
        cls,
        docs_context: str | list[str],
        web_context: str | list[str],
    ) -> str:
        """Joins local web documents using Granite's preferred format.

        Returns:
            str: The joined documents
        """
        if isinstance(docs_context, str):
            docs_context = [docs_context]
        if isinstance(web_context, str):
            web_context = [web_context]
        combined_context: list[str] = [*docs_context, *web_context]
        return "\n\n".join(combined_context)


## Factory ######################################################################

# This is the function signature for the various prompt generator functions
PROMPT_GENERATOR = Callable[
    [
        str,         # question
        str,         # context
        str,         # report_source
        str,         # report_format
        str | None,  # tone
        int,         # total_words
        str,         # language
    ],
    str,
]

report_type_mapping: dict[str, str] = {
    ReportType.ResearchReport.value: "generate_report_prompt",
    ReportType.ResourceReport.value: "generate_resource_report_prompt",
    ReportType.OutlineReport.value: "generate_outline_report_prompt",
    ReportType.CustomReport.value: "generate_custom_report_prompt",
    ReportType.SubtopicReport.value: "generate_subtopic_report_prompt",
    ReportType.DeepResearch.value: "generate_deep_research_prompt",
}


def get_prompt_by_report_type(
    report_type: str,
    prompt_family: type[PromptFamily] | PromptFamily,
) -> Callable[..., Any] | None:
    """Get the prompt by report type.

    Args:
        report_type (str): The report type
        prompt_family (type[PromptFamily] | PromptFamily): The prompt family

    Returns:
        Callable[..., Any] | None: The prompt by report type
    """
    # DEBUG: Log function entry
    from gpt_researcher.utils.logger import get_formatted_logger

    logger: Logger = get_formatted_logger()
    logger.info(f"[DEBUG-PROMPTS] Getting prompt for report_type: {report_type}")

    prompt_method_name = report_type_mapping.get(report_type, "")
    logger.info(f"[DEBUG-PROMPTS] Mapped to prompt method: {prompt_method_name}")

    prompt_by_type: Callable[..., Any] | None = getattr(
        prompt_family,
        prompt_method_name,
        None,
    )

    default_report_type: str = ReportType.ResearchReport.value
    if not prompt_by_type:
        warnings.warn(
            f"Invalid report type: `{report_type}`.\n"
            f"Please use one of the following: [{', '.join(report_type_mapping.keys())}]\n"
            f"Using default report type: `{default_report_type}` prompt.",
            UserWarning,
        )
        logger.warning(f"[DEBUG-PROMPTS] Invalid report type: {report_type}, using default: {default_report_type}")
        prompt_by_type = getattr(
            prompt_family,
            report_type_mapping.get(default_report_type),
        )

    # DEBUG: Log prompt method found
    if prompt_by_type:
        logger.info(f"[DEBUG-PROMPTS] Found prompt method: {prompt_by_type.__name__}")
    else:
        logger.error(f"[DEBUG-PROMPTS] Failed to find prompt method for {report_type}")

    return prompt_by_type


prompt_family_mapping: dict[str, type[PromptFamily]] = {
    PromptFamilyEnum.Default.value: PromptFamily,
    PromptFamilyEnum.Granite.value: GranitePromptFamily,
    PromptFamilyEnum.Granite3.value: Granite3PromptFamily,
    PromptFamilyEnum.Granite31.value: Granite3PromptFamily,
    PromptFamilyEnum.Granite32.value: Granite3PromptFamily,
    PromptFamilyEnum.Granite33.value: Granite33PromptFamily,
}


def get_prompt_family(
    prompt_family_name: PromptFamilyEnum | str,
    config: Config,
) -> PromptFamily:
    """Get a prompt family by name or value.

    Args:
        prompt_family_name (PromptFamilyEnum | str): The prompt family name or value
        config (Config): The config instance

    Returns:
        PromptFamily: The prompt family
    """
    if isinstance(prompt_family_name, PromptFamilyEnum):
        prompt_family_name = prompt_family_name.value
    prompt_family: type[PromptFamily] | None = prompt_family_mapping.get(prompt_family_name)
    if prompt_family is not None:
        return prompt_family(config)

    warnings.warn(
        f"Invalid prompt family: `{prompt_family_name}`.\n"
        f"Please use one of the following: [{', '.join(prompt_family_mapping.keys())}]\n"
        f"Using default prompt family: `{PromptFamilyEnum.Default.value}` prompt.",
        UserWarning,
    )
    return PromptFamily(config)
