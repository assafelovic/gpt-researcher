from __future__ import annotations

import warnings

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, SupportedLanguages, Tone

if TYPE_CHECKING:
    from collections.abc import Callable


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

Use this context to inform and refine your search queries. The context provides real-time web information that can help you generate more specific and relevant queries. Consider any current events, recent developments, or specific details mentioned in the context that could enhance the search queries."""
        if context
        else ""
    )

    dynamic_example = ", ".join([f'"query {i + 1}"' for i in range(max_iterations)])

    return f"""Write {max_iterations} google search queries to search online that form an objective opinion from the following task: "{task}"

Assume the current date is {datetime.now(timezone.utc).strftime("%B %d, %Y")} if required.

{context_prompt}
You must respond with a list of strings in the following format: [{dynamic_example}].
The response should contain ONLY the list."""


def generate_report_prompt(
    question: str,
    context: str,
    report_source: ReportSource,
    report_format: ReportFormat = ReportFormat.APA,
    total_words: int = 1000,
    tone: Tone | None = None,
    language: SupportedLanguages = SupportedLanguages.ENGLISH,
):
    """Generates the report prompt for the given question and research summary.
    Args: question (str): The question to generate the report prompt for
            research_summary (str): The research summary to generate the report prompt for
    Returns: str: The report prompt for the given question and research summary.
    """

    reference_prompt = ""
    if report_source == ReportSource.Web:
        reference_prompt = """
You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report:

eg: Author, A. A. (Year, Month Date). Title of web page. Website Name. [url website](url)
"""
    else:
        reference_prompt = """You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."""

    tone_prompt = f"Write the report in a {tone.value} tone." if tone else ""

    return f"""Information: "{context}"
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

You MUST write the report in the following language: {language.value}.
Please do your best, this is very important to my career.
Assume that the current date is {date.today()}."""


def curate_sources(
    query: str,
    sources: list[str],
    max_results: int = 10,
) -> str:
    return f"""Your goal is to evaluate and curate the provided scraped content for the research task: {query} while prioritizing the inclusion of relevant and high-quality information, especially sources containing statistics, numbers, or concrete data.

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
The response MUST not contain any markdown format or additional text (like ```json), just the JSON list!
"""


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
    reference_prompt = ""
    if report_source == ReportSource.Web:
        reference_prompt = """
            You MUST include all relevant source urls.
            Every url should be hyperlinked: [url website](url)
            """
    else:
        reference_prompt = """
            You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
        """

    return (
        f'"""{context}"""\n\nBased on the above information, generate a bibliography recommendation report for the following'
        f' question or topic: "{question}". The report should provide a detailed analysis of each recommended resource,'
        " explaining how each source can contribute to finding answers to the research question.\n"
        "Focus on the relevance, reliability, and significance of each source.\n"
        "Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.\n"
        "Include relevant facts, figures, and numbers whenever available.\n"
        f"The report should have a minimum length of {total_words} words.\n"
        "You MUST include all relevant source urls."
        "Every url should be hyperlinked: [url website](url)"
        f"{reference_prompt}"
    )


def generate_custom_report_prompt(
    query_prompt: str,
    context: str,
):
    return f'"{context}"\n\n{query_prompt}'


def generate_outline_report_prompt(
    question: str,
    context: str,
    total_words: int = 1000,
):
    """Generates the outline report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the outline report prompt for research_summary (str):
                        The research summary to generate the outline report prompt for
        total_words (int): The total words of the research report
    Returns: str: The outline report prompt for the given question and research summary.
    """

    return (
        f'"""{context}""" Using the above information, generate an outline for a research report in Markdown syntax'
        f' for the following question or topic: "{question}". The outline should provide a well-structured framework'
        " for the research report, including the main sections, subsections, and key points to be covered."
        f" The research report should be detailed, informative, in-depth, and a minimum of {total_words} words."
        " Use appropriate Markdown syntax to format the outline and ensure readability."
    )


def get_report_by_type(
    report_type: str | ReportType,
) -> Callable[..., str]:
    report_type_mapping: dict[ReportType, Callable[..., str]] = {
        ReportType.ResearchReport: generate_report_prompt,
        ReportType.ResourceReport: generate_resource_report_prompt,
        ReportType.OutlineReport: generate_outline_report_prompt,
        ReportType.CustomReport: generate_custom_report_prompt,
        ReportType.SubtopicReport: generate_subtopic_report_prompt,
    }
    return report_type_mapping[ReportType.__members__[report_type] if isinstance(report_type, str) else report_type]


def auto_agent_instructions() -> str:
    return """
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
"""


def generate_summary_prompt(
    query: str,
    data: str,
) -> str:
    """Generates the summary prompt for the given question and text.

    Args:
    ----
        query (str): The question to generate the summary prompt for
        data (str): The text to generate the summary prompt for

    Returns:
    -------
        (str): The summary prompt for the given question and text.
    """

    return (
        f'{data}\n Using EXCLUSIVELY the above text, condense it as much as possible based on the following task or query: "{query}".\n If the '
        f"query cannot be answered using the text, YOU MUST summarize the text in short.\n Include all factual "
        f"information such as numbers, stats, quotes, etc if available. DO NOT under ANY circumstances 'summarize' or 'generalize': you MUST be highly accurate and specific to the query!"
    )


################################################################################################

# DETAILED REPORT PROMPTS


def generate_subtopics_prompt() -> str:
    return """
Provided the main topic:

{task}

and research data:

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
"""


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
    language: SupportedLanguages = SupportedLanguages.ENGLISH,
) -> str:
    return f"""
Context:
"{context}"

MAIN TOPIC AND SUBTOPIC:
Using the latest information available, construct a DETAILED Report on the following subtopic: {current_subtopic} UNDERNEATH the main topic: {main_topic}.
You absolutely must limit the number of subsections to a maximum of {max_subsections}.

CONTENT FOCUS:
- The report should focus on answering the question, be well-structured, informative, in-depth, and include facts and numbers if available.
- Use markdown syntax and follow the {report_format.value} format.

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
Assume the current date is {datetime.now(timezone.utc).strftime("%B %d, %Y")} if required.

"IMPORTANT RESTRICTIONS AND GUIDELINES!":
- You MUST write the report in the following language: {language.value}.
- The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
- Must NOT have any introduction, conclusion, summary or reference section.
- You MUST include hyperlinks with markdown syntax ([url website](url)) related to the sentences wherever necessary.
- If you add similar or identical subsections, you MUST clearly indicate how the new content differs from the existing content.
- The report should have a minimum length of {total_words} words.
- Use an {tone.value} tone throughout the report.

DO NOT create a 'conclusion' section under any circumstances, assume that the report will be part of a larger essay/article.
"""  # TODO: Move the tone to either the beginning of the prompt or the end to ensure the LLM follows it.


def generate_draft_titles_prompt(
    current_subtopic: str,
    main_topic: str,
    context: str,
) -> str:
    return f"""
"Context":
"{context}"

"MAIN TOPIC AND SUBTOPIC":
Using the latest information available, construct a draft section title headers for a DETAILED Report on the subtopic: {current_subtopic} under the main topic: {main_topic}.

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
"""


def generate_report_introduction(
    question: str,
    research_summary: str = "",
) -> str:
    return f"""{research_summary}\n
Using the above latest reference information, prepare a detailed report introduction on the topic -- {question}.
- Your introduction will be succinct, well-structured, and informative utilizing markdown syntax.
- DO NOT include any other sections, which are generally present in a report because your introduction will be part of a larger report! Focus on your responsibility!
- Your introduction will be preceded with an H1 heading with a suitable topic for the entire report.
- You must include authentic hyperlinks with correct and valid markdown syntax ([url website](url)) appropriately for the relevant sentences.
Assume that the current date is {datetime.now(timezone.utc).strftime("%B %d, %Y")} if required.
"""


def generate_report_conclusion(
    query: str,
    report_content: str,
) -> str:
    """Generate a concise conclusion summarizing the main findings and implications of a research report.

    Args:
    ----
        query (str): The research task to generate the conclusion for.
        report_content (str): The content of the research report.

    Returns:
    -------
        str: A concise conclusion summarizing the report's main findings and implications.
    """
    prompt = f"""
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

    Write the conclusion now:
    """

    return prompt


report_type_mapping: dict[ReportType, Callable[..., str]] = {
    ReportType.ResearchReport: generate_report_prompt,
    ReportType.ResourceReport: generate_resource_report_prompt,
    ReportType.OutlineReport: generate_outline_report_prompt,
    ReportType.CustomReport: generate_custom_report_prompt,
    ReportType.SubtopicReport: generate_subtopic_report_prompt,
}


def get_prompt_by_report_type(
    report_type: ReportType,
) -> Callable[..., str]:
    prompt_by_type: Callable[..., str] | None = report_type_mapping.get(report_type)
    default_report_type = ReportType.ResearchReport
    if prompt_by_type is None:
        warnings.warn(
            f"Invalid report type: {report_type}.\n"
            f"Please use one of the following: {', '.join([enum_value.value for enum_value in report_type_mapping.keys()])}\n"
            f"Using default report type: {default_report_type} prompt.",
            UserWarning,
        )
        prompt_by_type = report_type_mapping[default_report_type]
    return prompt_by_type
