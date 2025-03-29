from __future__ import annotations

import os
import warnings

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, Tone

if TYPE_CHECKING:
    from collections.abc import Callable


PROMPT_CHAT_WITH_REPORT = """You are GPT Researcher, a autonomous research agent created by an open source community at https://github.com/assafelovic/gpt-researcher, homepage: https://gptr.dev.
To learn more about GPT Researcher you can suggest to check out: https://docs.gptr.dev.

This is a chat message between the user and you: GPT Researcher.
The chat is about a research reports that you created. Answer based on the given context and report.
You must include citations to your answer based on the report.

Report: {self.report}
User Message: {message}"""  # noqa: E501

# Global prompt variables
PROMPT_GENERATE_SEARCH_QUERIES = """Write {max_iterations} google search queries to search online that form an objective opinion from the following task: "{task}"

Assume the current date is {current_date} if required.

{context_prompt}
You must respond with a list of strings in the following format: [{dynamic_example}].
The response should contain ONLY the list."""  # noqa: E501

PROMPT_GENERATE_REPORT = """Information: "{context}"
---
Using the above information, answer the following query or task: "{question}" in a detailed report --
The report should focus on the answer to the query, should be well structured, informative,
in-depth, and comprehensive, with facts and numbers if available and at least {total_words} words.
You should strive to write the report as long as you can using all relevant and necessary information provided.

Please follow all of the following guidelines in your report:
- You MUST determine your own concrete and valid opinion based on the given information. Do NOT defer to general and meaningless conclusions.
- You MUST write the report with markdown syntax and {report_format} format.
- You MUST prioritize the relevance, reliability, and significance of the sources you use. Choose trusted sources over less reliable ones.
- You must also prioritize new articles over older articles if the source can be trusted.
- Use in-text citation references in {report_format} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
- Don't forget to add a reference list at the end of the report in {report_format} format and full url links without hyperlinks.
- {reference_prompt}
- {tone_prompt}

You MUST write the report in the following language: {language}.
Please do your best, this is very important to my career.
Assume that the current date is {current_date}.
Your response must start with the report itself, with no precursors or explanations."""  # noqa: E501

PROMPT_CURATE_SOURCES = """Your goal is to evaluate and curate the provided scraped content for the research task: {query} while prioritizing the inclusion of relevant and high-quality information, especially sources containing statistics, numbers, or concrete data.

The final curated list will be used as context for creating a research report, so prioritize:
- Retaining as much original information as possible, with extra emphasis on sources featuring quantitative data or unique insights
- Including a wide range of perspectives and insights
- Filtering out only clearly irrelevant or unusable content

EVALUATION GUIDELINES:
1. Assess each source based on:
    - RELEVANCE: Include sources directly or partially connected to the research query. Err on the side of inclusion.
    - CREDIBILITY: Favor authoritative sources but retain others unless clearly untrustworthy.
    - CURRENCY: Prefer recent information unless older data is essential or valuable.
    - OBJECTIVITY: Retain sources with bias if they provide a unique or complementary perspective.
    - QUANTITATIVE VALUE: Give higher priority to sources with statistics, numbers, or other concrete data.
2. SOURCE SELECTION:
    - Include as many relevant sources as possible, up to {max_results}, focusing on broad coverage and diversity.
    - Prioritize sources with statistics, numerical data, or verifiable facts.
    - Overlapping content is acceptable if it adds depth, especially when data is involved.
    - Exclude sources only if they are entirely irrelevant, severely outdated, or unusable due to poor content quality.
    - Exclude sources especially if they are not relevant to the research query.
3. CONTENT RETENTION:
    - DO NOT rewrite, summarize, generalize, or condense any source content.
    - Retain all usable information verbatim: ONLY clean up garbage or formatting issues.
    - Keep marginally relevant or incomplete sources if they contain valuable data or insights. Especially if it has been repeated multiple times in other locations.

SOURCES LIST TO EVALUATE:
{sources}

You MUST return your response in the EXACT sources JSON list format as the original sources.
The response MUST not contain any markdown format or additional text (like ```json), just the JSON list!"""  # noqa: E501

PROMPT_GENERATE_RESOURCE_REPORT = """"{context}"\n\nBased on the above information, generate a bibliography recommendation report for the following question or topic: "{question}". The report should provide a detailed analysis of each recommended resource, explaining how each source can contribute to finding answers to the research question.
Focus on the relevance, reliability, and significance of each source.
Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.
Include relevant facts, figures, and numbers whenever available.
The report should have a minimum length of {total_words} words.
You MUST include all relevant source urls.
Every url should be hyperlinked: [url website](url)
{reference_prompt}"""  # noqa: E501

PROMPT_GENERATE_CUSTOM_REPORT = """"{context}"\n\n{query_prompt}"""

PROMPT_GENERATE_OUTLINE_REPORT = """"{context}" Using the above information, generate an outline for a research report in Markdown syntax for the following question or topic: "{question}". The outline should provide a well-structured framework for the research report, including the main sections, subsections, and key points to be covered. The research report should be detailed, informative, in-depth, and a minimum of {total_words} words. Use appropriate Markdown syntax to format the outline and ensure readability."""  # noqa: E501

PROMPT_AUTO_AGENT_INSTRUCTIONS = """
This task involves researching a given topic, regardless of its complexity or the availability of a definitive answer.
The research is conducted by a specific server, defined by its type and role.
Each server requires distinct instructions and a unique prompt.

Agent Types:
The server is determined by the field of the topic and the specific name of the server that could be utilized to research the topic provided.
Each server type will be associated with a corresponding emoji.

Examples:
task: "should I invest in apple stocks?"
response:
{
    "server": "💰 Finance Agent 💰",
    "agent_role_prompt": "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends."
}
task: "could reselling sneakers become profitable?"
response:
{
    "server": "📈 Business Analyst Agent 📈",
    "agent_role_prompt": "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis."
}
task: "what are the most interesting sites in Tel Aviv?"
response:
{
    "server": "🌍 Travel Agent 🌍",
    "agent_role_prompt": "You are a well-traveled and culturally-aware AI tour guide assistant. Your primary directive is to create engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and potentially cultural insights."
}
"""  # noqa: E501

PROMPT_CONDENSE_INFORMATION = """{data}\n Using EXCLUSIVELY the above text, condense it as much as possible based on the following task or query: "{query}".\n If the query cannot be answered using the text, YOU MUST summarize the text in short.\n Include all factual information such as numbers, stats, quotes, etc if available. DO NOT under ANY circumstances 'summarize' or 'generalize': you MUST be highly accurate and specific to the query!"""  # noqa: E501

PROMPT_GENERATE_SUBTOPICS = """
Provided the main topic:

{task}

Providerarch data:

{data}

- Construct a list of subtopics which indicate the headers of a report document to be generated on the task.
- These are a possible list of subtopics: {subtopics}.
- There should NOT be any duplicate subtopics.
- Limit the number of subtopics to a maximum of {max_subtopics}
- Finally order the subtopics by their tasks, in a relevant and meaningful order which is presentable in a detailed report

"IMPORTANT!":
- Every subtopic MUST be relevant to the main topic and task and provided research data ONLY!
- Consider what subtopics will likely dive into the proper rabbitholes that would uncover the most relevant information.

{format_instructions}
"""  # noqa: E501

PROMPT_GENERATE_SUBTOPIC_REPORT = """
Context:
"{context}"

MAIN TOPIC AND SUBTOPIC:
Using the latest information available, construct a DETAILED Report on the following subtopic: {current_subtopic} UNDERNEATH the main topic: {main_topic}.
You absolutely must limit the number of subsections to a maximum of {max_subsections}.

CONTENT FOCUS:
- The report should focus on answering the question, be well-structured, informative, in-depth, and include facts and numbers if available.
- Use markdown syntax and follow the {report_format_value} format.

IMPORTANT: CONTENT AND SECTIONS UNIQUENESS:
- This is the most important and crucial portion of the instructions to ensure the content is unique and does not overlap with existing reports.
- Carefully review the existing headers and existing written contents provided below before writing any new subsections.
- Prevent any content that is already covered in the existing reports.
- Do not use any of the existing headers as the new subsection headers.
- Do not repeat any information already covered in the existing written contents or closely related variations to avoid duplicates.
- If you have nested subsections, ensure they are unique and not covered in the existing written contents.
- Ensure that your content is entirely new and does not overlap with any information already covered in the previous subtopic reports.

"EXISTING SUBTOPIC REPORTS":
- Existing subtopic reports and their section headers:

    {existing_headers}

- Existing written contents from previous subtopic reports:

    {relevant_written_contents}

"STRUCTURE AND FORMATTING":
- This sub-report will obviously be part of a significantly larger article/essay, therefore you will include only the main body divided into suitable subtopics without any introduction or conclusion section.

- You MUST include markdown hyperlinks for relevant source URLs at the exact location they are referenced in the report!! For example:

    ### Section Header

    This is a an example sentence, hyperlinked for convenience. ([url website](url))

- Use `H2` for the main subtopic header (##) and `H3` for subsections (###).
- Use smaller Markdown headers (e.g., `H2` or `H3`) for content structure, avoiding the largest header (`H1`) as it will be used for the larger report's heading.
- Organize your content into Distinct sections that complement but do not overlap with existing reports.
- When adding similar or identical subsections to your report, you should clearly indicate the differences between and the new content and the existing written content from previous subtopic reports. For example:

    ### New header (similar to existing header)

    While the previous section discussed [topic A], this section will explore [topic B]."

"WHEN? DATE AND TIME, CURRENT":
Assume the current date is {current_date} if required.

"IMPORTANT RESTRICTIONS AND GUIDELINES!":
- You MUST write the report in the following language: {language}.
- The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
- Must NOT have any introduction, conclusion, summary or reference section.
- You MUST include hyperlinks with markdown syntax ([url website](url)) related to the sentences wherever necessary.
- If you add similar or identical subsections, you MUST clearly indicate how the new content differs from the existing content.
- The report should have a minimum length of {total_words} words.
- Use an {tone_value} tone throughout the report.

DO NOT create a 'conclusion' section under any circumstances.
"""  # noqa: E501

PROMPT_GENERATE_DRAFT_TITLES = """
"Context":
"{context}"

"MAIN TOPIC AND SUBTOPIC":
Using the latest invocation available, construct a draft section title headers for a DETAILED Report on the subtopic: {current_subtopic} under the main topic: {main_topic}.

"TASK":
1. Create a list of draft section title headers for the subtopic report.
2. Each header should be concise and relevant to the subtopic.
3. The header should't be too high level, but detailed enough to cover the main aspects of the subtopic.
4. Use markdown syntax for the headers, using H3 (###) as H1 and H2 will be used for the larger report's heading.
5. Ensure the headers cover main aspects of the subtopic.

"STRUCTURE AND FORMATTING":
Provide the draft headers in a list format using markdown syntax, for example:

### Header 1
### Header 2
### Header 3

"IMPORTANT RESTRICTIONS AND GUIDELINES!":
- Focus EXCLUSIVELY and SPECIFICALLY ONLY on the **MAIN TOPIC**! DO NOT BECOME DISTRACTED BY IRRELEVANT INFORMATION. Stay HIGHLY FIXATED AND FOCUSED ON EXCLUSIVELY AND HIGHLY SPECIFICALLY THE MAIN TOPIC AT ALL TIMES.
- **DO NOT** write any introduction, conclusion, summary or reference section.
- Focus solely explicitly on creating HEADERS, not content.
"""  # noqa: E501

PROMPT_GENERATE_REPORT_INTRODUCTION = """{research_summary}\n
Using the above latest reference information, prepare a detailed report introduction on the topic -- {question}.
- Your introduction will be succinct, well-structured, and informative utilizing markdown syntax.
- DO NOT include any other sections, which are generally present in a report because your introduction will be part of a larger report! Focus on your responsibility!
- Your introduction will be preceded with an H1 heading with a suitable topic for the entire report.
- You must include authentic hyperlinks with correct and valid markdown syntax ([url website](url)) appropriately for the relevant sentences.
Assume that the current date is {current_date} if required.
Write the report in the following language: {language}.
"""  # noqa: E501

PROMPT_GENERATE_REPORT_CONCLUSION = """
    Using the following resource report below, you are now tasked to write a concise conclusion that summarizes the main findings and their implications:

    Main Research Task: {query}

    Research Report: {report_content}

    Your conclusion will ultimately:
    1. Recap the main talking points of the research
    2. Highlight the most qualitative and important findings
    3. Discuss any implications or next steps
    4. Be approximately 2-3 paragraphs long

    If there is no "## Conclusion" section title written at the end of the report, please add it to the top of your conclusion.
    You must include authentic hyperlinks with correct and valid markdown syntax ([url website](url)) appropriately for any and all sentences relevant to the URL.
    Write the conclusion in the following language: {language}.

    Write the conclusion now:
    """  # noqa: E501

PROMPT_POST_RETRIEVAL_PROCESSING = """
You are processing retrieved web content for a research task on: "{query}"

CONTENT TO PROCESS:
{content}

PROCESSING INSTRUCTIONS:
{processing_instructions}

Apply the above processing instructions to the content and return the processed result.
"""

PROMPT_DEEP_RESEARCH = """
Using the following hierarchically researched information and citations:

"{context}"

Write a comprehensive research report answering the query: "{question}"

The report should:
1. Synthesize information from multiple levels of research depth
2. Integrate findings from various research branches
3. Present a coherent narrative that builds from foundational to advanced insights
4. Maintain proper citation of sources throughout
5. Be well-structured with clear sections and subsections
6. Have a minimum length of {total_words} words
7. Follow {report_format} format with markdown syntax

Additional requirements:
- Prioritize insights that emerged from deeper levels of research
- Highlight connections between different research branches
- Include relevant statistics, data, and concrete examples
- You MUST determine your own concrete and valid opinion based on the given information. Do NOT defer to general and meaningless conclusions.
- You MUST prioritize the relevance, reliability, and significance of the sources you use. Choose trusted sources over less reliable ones.
- You must also prioritize new articles over older articles if the source can be trusted.
- Use in-text citation references in {report_format} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
- {tone_prompt}
- Write in {language}

{reference_prompt}

Please write a thorough, well-researched report that synthesizes all the gathered information into a cohesive whole.

"""  # noqa: E501


def generate_search_queries_prompt(
    question: str,
    parent_query: str,
    report_type: str | ReportType,
    max_iterations: int = 3,
    context: list[dict[str, Any]] | None = None,
) -> str:
    """Generates the search queries prompt for the given question.
    Args:
        question (str): The question to generate the search queries prompt for
        parent_query (str): The main question (only relevant for detailed reports)
        report_type (str | ReportType): The report type
        max_iterations (int): The maximum number of search queries to generate
        context (str): Context for better understanding of the task with realtime web information.

    Returns: str: The search queries prompt for the given question
    """

    context = [] if context is None else context

    if report_type == ReportType.DetailedReport or report_type == ReportType.SubtopicReport:
        task = f"{parent_query} - {question}"
    else:
        task = question

    context_prompt = (
        f"""You are a seasoned research assistant tasked with generating search queries to find relevant information for the following task: "{task}".
Context: {context}

Use this context to inform and refine your search queries. The context provides real-time web information that can help you generate more specific and relevant queries. Consider any current events, recent developments, or specific details mentioned in the context that could enhance the search queries."""  # noqa: E501
        if context
        else ""
    )

    dynamic_example = ", ".join([f'"query {i + 1}"' for i in range(max_iterations)])

    default_prompt = PROMPT_GENERATE_SEARCH_QUERIES
    custom_prompt = os.environ.get("PROMPT_GENERATE_SEARCH_QUERIES", "")
    if custom_prompt:
        try:
            return custom_prompt.format(
                question=question,
                parent_query=parent_query,
                report_type=report_type,
                max_iterations=max_iterations,
                context=context,
                task=task,
                context_prompt=context_prompt,
                dynamic_example=dynamic_example,
                current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(
        max_iterations=max_iterations,
        task=task,
        current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
        context_prompt=context_prompt,
        dynamic_example=dynamic_example,
    )


def generate_report_prompt(
    question: str,
    context: str,
    report_source: ReportSource,
    report_format: ReportFormat = ReportFormat.APA,
    total_words: int = 1000,
    tone: Tone | None = None,
    language: str = "ENGLISH",
):
    """Generates the report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the report prompt for
        context (str): The research summary to generate the report prompt for
        report_source (str): The report source (web or document)
        report_format (str): The report format (APA or MLA)
        total_words (int): The total words of the research report
        tone (Tone): The tone of the report (Informative, Conversational, etc.)
        language (str): The language of the report (default is English)

    Returns:
        str: The report prompt for the given question and research summary.
    """

    reference_prompt: str = ""
    if report_source == ReportSource.Web:
        reference_prompt = """
You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report:

eg: Author, A. A. (Year, Month Date). Title of web page. Website Name. [url website](url)
"""  # noqa: E501
    else:
        reference_prompt = """You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."""  # noqa: E501

    tone_prompt: str = f"Write the report using the {tone.name} tone ({tone.value})." if tone else ""

    default_prompt = PROMPT_GENERATE_REPORT
    custom_prompt: str = os.environ.get("PROMPT_GENERATE_REPORT", "")
    if custom_prompt:
        try:
            return custom_prompt.format(
                question=question,
                context=context,
                report_source=report_source,
                report_format=report_format,
                total_words=total_words,
                tone=tone,
                tone_value=tone.value if tone else "objective",
                language=language,
                reference_prompt=reference_prompt,
                tone_prompt=tone_prompt,
                current_date=date.today(),
            )
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(
        question=question,
        context=context,
        report_format=report_format,
        total_words=total_words,
        reference_prompt=reference_prompt,
        tone_prompt=tone_prompt,
        language=language,
        current_date=date.today(),
    )


def curate_sources(
    query: str,
    sources: list[str],
    max_results: int = 10,
) -> str:
    default_prompt = PROMPT_CURATE_SOURCES
    custom_prompt: str = os.environ.get("PROMPT_CURATE_SOURCES", "")
    if custom_prompt:
        try:
            return custom_prompt.format(query=query, sources=sources, max_results=max_results)
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(query=query, sources=sources, max_results=max_results)


def generate_resource_report_prompt(
    question: str,
    context: str,
    report_source: ReportSource,
    total_words: int = 1000,
):
    """Generates the resource report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the resource report prompt for.
        context (str): The research summary to generate the resource report prompt for.

    Returns:
        str: The resource report prompt for the given question and research summary.
    """
    report_source = ReportSource(report_source) if isinstance(report_source, str) else report_source
    reference_prompt: str = ""
    if report_source == ReportSource.Web:
        reference_prompt = """
            You MUST include all relevant source urls.
            Every url should be hyperlinked: [url website](url)
            """
    else:
        reference_prompt = """
            You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
        """  # noqa: E501

    default_prompt = PROMPT_GENERATE_RESOURCE_REPORT
    custom_prompt = os.environ.get("PROMPT_GENERATE_RESOURCE_REPORT", "")
    if custom_prompt:
        try:
            return custom_prompt.format(
                question=question,
                context=context,
                report_source=report_source,
                report_source_value=report_source.value,
                total_words=total_words,
                reference_prompt=reference_prompt,
            )
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(question=question, context=context, total_words=total_words, reference_prompt=reference_prompt)  # noqa: E501


def generate_custom_report_prompt(
    query_prompt: str,
    context: str,
):
    default_prompt = PROMPT_GENERATE_CUSTOM_REPORT

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_GENERATE_CUSTOM_REPORT", "")
    if custom_prompt:
        try:
            return custom_prompt.format(query_prompt=query_prompt, context=context)
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(query_prompt=query_prompt, context=context)


def generate_outline_report_prompt(
    question: str,
    context: str,
    total_words: int = 1000,
):
    """Generates the outline report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the outline report prompt for
        context (str): The research summary to generate the outline report prompt for
        total_words (int): The total words of the research report
    Returns: str: The outline report prompt for the given question and research summary.
    """

    default_prompt = PROMPT_GENERATE_OUTLINE_REPORT

    # Get prompt from environment variable or use default
    custom_prompt: str = os.environ.get("PROMPT_GENERATE_OUTLINE_REPORT", "")
    if custom_prompt:
        try:
            return custom_prompt.format(question=question, context=context, total_words=total_words)
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(question=question, context=context, total_words=total_words)


def generate_deep_research_prompt(
    question: str,
    context: str,
    report_source: ReportSource,
    report_format: ReportFormat = ReportFormat.APA,
    tone: Tone | None = None,
    total_words: int = 2000,
    language: str = "ENGLISH",
) -> str:
    """Generates the deep research report prompt, specialized for handling hierarchical research results.

    Args:
        question (str): The research question.
        context (str): The research context containing detailed information and citations.
        report_source (ReportSource): Source of the research (e.g., Web).
        report_format (ReportFormat): Report formatting style.
        tone (Tone | None): The tone to use in writing.
        total_words (int): Minimum word count for the report.
        language (str): The language in which to write the report.

    Returns:
        str: The deep research report prompt.
    """
    reference_prompt = ""
    if report_source == ReportSource.Web:
        reference_prompt = """
You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report:

For example:
```
Author, A. A. (Year, Month Date). Title of web page. Website Name. [url website](url)
```
Think about where the information in the report came from, and cite your sources using the above format.
"""  # noqa: E501
    else:
        reference_prompt = """
You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
"""  # noqa: E501
    tone_prompt: str = f"Write the report using the {tone.name} tone ({tone.value})." if tone else ""

    return os.environ.get("PROMPT_DEEP_RESEARCH", PROMPT_DEEP_RESEARCH).format(
        question=question,
        context=context,
        report_format=report_format,
        tone=tone_prompt,
        total_words=total_words,
        language=language,
        reference_prompt=reference_prompt,
    ) + f"\nAssume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')}"


def get_report_by_type(
    report_type: str | ReportType,
) -> Callable[..., str]:
    report_type_mapping: dict[ReportType, Callable[..., str]] = {
        ReportType.ResearchReport: generate_report_prompt,
        ReportType.ResourceReport: generate_resource_report_prompt,
        ReportType.OutlineReport: generate_outline_report_prompt,
        ReportType.CustomReport: generate_custom_report_prompt,
        ReportType.SubtopicReport: generate_subtopic_report_prompt,
        ReportType.DeepResearch: generate_deep_research_prompt,
    }
    return report_type_mapping[ReportType.__members__[report_type] if isinstance(report_type, str) else report_type]


def auto_agent_instructions() -> str:
    default_prompt = PROMPT_AUTO_AGENT_INSTRUCTIONS

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_AUTO_AGENT_INSTRUCTIONS", "")
    if custom_prompt and custom_prompt.strip():
        try:
            # Auto agent instructions don't have parameters to format
            return custom_prompt
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt


def condense_information(
    query: str,
    data: str,
) -> str:
    """Generates a prompt for condensing provided information based on a query.

    This function constructs a prompt that instructs an AI to condense the given `data`
    as much as possible, focusing specifically on answering the provided `query`.
    If the query cannot be answered directly from the data, the AI is instructed
    to summarize the text concisely. The prompt emphasizes the inclusion of factual
    information and discourages summarization or generalization if the query can be answered.
    It stresses high accuracy and specificity to the query.

    Args:
        query: The task or question to be answered using the provided data.
        data: The text to be condensed or summarized.

    Returns:
        A string containing the formatted prompt.
    """

    default_prompt = PROMPT_CONDENSE_INFORMATION

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_CONDENSE_INFORMATION", "")
    if custom_prompt:
        try:
            # Use string formatting with named parameters for template
            return custom_prompt.format(query=query, data=data)
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt.format(query=query, data=data)


################################################################################################

# DETAILED REPORT PROMPTS


def generate_subtopics_prompt() -> str:
    default_prompt = PROMPT_GENERATE_SUBTOPICS

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_GENERATE_SUBTOPICS", "")
    if custom_prompt:
        # No parameters since this is usually used as a template itself
        return custom_prompt

    return default_prompt


def generate_subtopic_report_prompt(
    current_subtopic: str,
    existing_headers: list[str],
    relevant_written_contents: list[str],
    main_topic: str,
    context: str,
    report_format: ReportFormat = ReportFormat.APA,
    max_subsections: int = 5,
    total_words: int = 800,
    tone: Tone = Tone.Objective,
    language: str = "ENGLISH",
) -> str:
    default_prompt = PROMPT_GENERATE_SUBTOPIC_REPORT

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_GENERATE_SUBTOPIC_REPORT", "")
    if custom_prompt:
        try:
            # Use string formatting with named parameters for template
            return custom_prompt.format(
                current_subtopic=current_subtopic,
                existing_headers=existing_headers,
                relevant_written_contents=relevant_written_contents,
                main_topic=main_topic,
                context=context,
                report_format=report_format,
                report_format_value=report_format.value,
                max_subsections=max_subsections,
                total_words=total_words,
                tone=tone,
                tone_value=tone.value,
                language=language,
                current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt.format(
        current_subtopic=current_subtopic,
        existing_headers=existing_headers,
        relevant_written_contents=relevant_written_contents,
        main_topic=main_topic,
        context=context,
        report_format_value=report_format.value,
        max_subsections=max_subsections,
        total_words=total_words,
        tone_value=tone.value,
        language=language,
        current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )


def generate_draft_titles_prompt(
    current_subtopic: str,
    main_topic: str,
    context: str,
) -> str:
    """Generate draft section title headers for a detailed report.

    Args:
    ----
        current_subtopic (str): The current subtopic to generate draft headers for.
        main_topic (str): The main topic of the report.
        context (str): The context of the report.

    Returns:
    -------
        str: A list of draft section title headers for the subtopic report.
    """
    default_prompt = PROMPT_GENERATE_DRAFT_TITLES

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_GENERATE_DRAFT_TITLES", "")
    if custom_prompt:
        try:
            # Use string formatting with named parameters for template
            return custom_prompt.format(current_subtopic=current_subtopic, main_topic=main_topic, context=context)
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt.format(current_subtopic=current_subtopic, main_topic=main_topic, context=context)


def generate_report_introduction(
    question: str,
    research_summary: str = "",
    language: str = "ENGLISH",
) -> str:
    """Generate a detailed report introduction.

    Args:
    ----
        question (str): The research task to generate the introduction for.
        research_summary (str): The latest reference information.
        language (str): The language of the report.

    Returns:
    -------
        str: A detailed report introduction.
    """
    default_prompt = PROMPT_GENERATE_REPORT_INTRODUCTION

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_GENERATE_REPORT_INTRODUCTION", "")
    if custom_prompt:
        try:
            # Use string formatting with named parameters for template
            return custom_prompt.format(
                question=question,
                research_summary=research_summary,
                language=language,
                current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt.format(
        question=question,
        research_summary=research_summary,
        language=language,
        current_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )


def generate_report_conclusion(
    query: str,
    report_content: str,
    language: str = "ENGLISH",
) -> str:
    """Generate a concise conclusion summarizing the main findings and implications of a research report.

    Args:
    ----
        query (str): The research task to generate the conclusion for.
        report_content (str): The content of the research report.
        language (str): The language of the report.

    Returns:
    -------
        str: A concise conclusion summarizing the report's main findings and implications.
    """
    default_prompt = PROMPT_GENERATE_REPORT_CONCLUSION

    custom_prompt = os.environ.get("PROMPT_GENERATE_REPORT_CONCLUSION", "")
    if custom_prompt:
        try:
            return custom_prompt.format(query=query, report_content=report_content, language=language)
        except (KeyError, ValueError):
            return default_prompt

    return default_prompt.format(query=query, report_content=report_content, language=language)


report_type_mapping: dict[ReportType, Callable[..., str]] = {
    ReportType.ResearchReport: generate_report_prompt,
    ReportType.ResourceReport: generate_resource_report_prompt,
    ReportType.OutlineReport: generate_outline_report_prompt,
    ReportType.CustomReport: generate_custom_report_prompt,
    ReportType.SubtopicReport: generate_subtopic_report_prompt,
    ReportType.DeepResearch: generate_deep_research_prompt,
}


def get_prompt_by_report_type(
    report_type: ReportType,
) -> Callable[..., str]:
    prompt_by_type: Callable[..., str] | None = report_type_mapping.get(report_type)
    default_report_type = ReportType.ResearchReport
    if prompt_by_type is None:
        warnings.warn(
            f"Invalid report type: {report_type}.\n"
            f"Please use one of the following: {', '.join([enum_value.value for enum_value in report_type_mapping.keys()])}\n"  # noqa: E501
            f"Using default report type: {default_report_type} prompt.",
            UserWarning,
            stacklevel=2,
        )
        prompt_by_type = report_type_mapping[default_report_type]
    return prompt_by_type


def post_retrieval_processing(
    query: str,
    content: str,
    processing_instructions: str,
) -> str:
    """Applies custom processing instructions to retrieved content.

    This function allows for additional processing of retrieved web content
    before it's used in the research report. It can be used to extract specific
    information, format content in a particular way, or highlight the most
    important parts of the retrieved information.

    Args:
        query (str): The original research query
        content (str): The retrieved content to process
        processing_instructions (str): Custom instructions for processing the content

    Returns:
        str: The processed content
    """
    default_prompt = PROMPT_POST_RETRIEVAL_PROCESSING

    # Get prompt from environment variable or use default
    custom_prompt = os.environ.get("PROMPT_POST_RETRIEVAL_PROCESSING", default_prompt)
    if custom_prompt:
        try:
            # Use string formatting with named parameters for template
            return custom_prompt.format(query=query, content=content, processing_instructions=processing_instructions)
        except (KeyError, ValueError):
            # If formatting fails, fall back to default prompt
            return default_prompt

    return default_prompt.format(query=query, content=content, processing_instructions=processing_instructions)
