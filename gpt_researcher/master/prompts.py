from datetime import datetime, timezone
import warnings
from gpt_researcher.utils.enum import ReportType


def generate_search_queries_prompt(question: str, parent_query: str, report_type: str, max_iterations: int=3,):
    """ Generates the search queries prompt for the given question.
    Args: 
        question (str): The question to generate the search queries prompt for
        parent_query (str): The main question (only relevant for detailed reports)
        report_type (str): The report type
        max_iterations (int): The maximum number of search queries to generate
    
    Returns: str: The search queries prompt for the given question
    """
    
    if report_type == ReportType.DetailedReport.value or report_type == ReportType.SubtopicReport.value:
        task = f"{parent_query} - {question}"
    else:
        task = question

    return f'Write {max_iterations} google search queries to search online that form an objective opinion from the following task: "{task}"' \
           f'Use the current date if needed: {datetime.now().strftime("%B %d, %Y")}.\n' \
           f'Also include in the queries specified task details such as locations, names, etc.\n' \
           f'You must respond with a list of strings in the following format: ["query 1", "query 2", "query 3"].'


def generate_report_prompt(question, context, report_format="apa", total_words=1000):
    """ Generates the report prompt for the given question and research summary.
    Args: question (str): The question to generate the report prompt for
            research_summary (str): The research summary to generate the report prompt for
    Returns: str: The report prompt for the given question and research summary
    """

    return f'Information: """{context}"""\n\n' \
           f'Using the above information, answer the following' \
           f' query or task: "{question}" in a detailed report --' \
           " The report should focus on the answer to the query, should be well structured, informative," \
           f" in depth and comprehensive, with facts and numbers if available and a minimum of {total_words} words.\n" \
           "You should strive to write the report as long as you can using all relevant and necessary information provided.\n" \
           "You must write the report with markdown syntax.\n " \
           f"Use an unbiased and journalistic tone. \n" \
           "You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions.\n" \
           f"You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.\n" \
           "Every url should be hyperlinked: [url website](url)"\
           """
            Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report : 
        
            eg:    
                # Report Header
                
                This is a sample text. ([url website](url))
            """\
            f"You MUST write the report in {report_format} format.\n " \
            f"Cite search results using inline notations. Only cite the most \
            relevant results that answer the query accurately. Place these citations at the end \
            of the sentence or paragraph that reference them.\n"\
            f"Please do your best, this is very important to my career. " \
            f"Assume that the current date is {datetime.now().strftime('%B %d, %Y')}"


def generate_resource_report_prompt(question, context, report_format="apa", total_words=700):
    """Generates the resource report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the resource report prompt for.
        context (str): The research summary to generate the resource report prompt for.

    Returns:
        str: The resource report prompt for the given question and research summary.
    """
    return f'"""{context}"""\n\nBased on the above information, generate a bibliography recommendation report for the following' \
           f' question or topic: "{question}". The report should provide a detailed analysis of each recommended resource,' \
           ' explaining how each source can contribute to finding answers to the research question.\n' \
           'Focus on the relevance, reliability, and significance of each source.\n' \
           'Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.\n' \
           'Include relevant facts, figures, and numbers whenever available.\n' \
           f'The report should have a minimum length of {total_words} words.\n' \
        'You MUST include all relevant source urls.'\
        'Every url should be hyperlinked: [url website](url)'


def generate_custom_report_prompt(query_prompt, context, report_format="apa", total_words=1000):
    return f'"{context}"\n\n{query_prompt}'


def generate_outline_report_prompt(question, context, report_format="apa", total_words=1200):
    """ Generates the outline report prompt for the given question and research summary.
    Args: question (str): The question to generate the outline report prompt for
            research_summary (str): The research summary to generate the outline report prompt for
    Returns: str: The outline report prompt for the given question and research summary
    """

    return f'"""{context}""" Using the above information, generate an outline for a research report in Markdown syntax' \
           f' for the following question or topic: "{question}". The outline should provide a well-structured framework' \
           ' for the research report, including the main sections, subsections, and key points to be covered.' \
           f' The research report should be detailed, informative, in-depth, and a minimum of {total_words} words.' \
           ' Use appropriate Markdown syntax to format the outline and ensure readability.'


def auto_agent_instructions():
    return """
        This task involves researching a given topic, regardless of its complexity or the availability of a definitive answer. The research is conducted by a specific server, defined by its type and role, with each server requiring distinct instructions.
        Agent
        The server is determined by the field of the topic and the specific name of the server that could be utilized to research the topic provided. Agents are categorized by their area of expertise, and each server type is associated with a corresponding emoji.

        examples:
        task: "should I invest in apple stocks?"
        response: 
        {
            "server": "💰 Finance Agent",
            "agent_role_prompt: "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends."
        }
        task: "could reselling sneakers become profitable?"
        response: 
        { 
            "server":  "📈 Business Analyst Agent",
            "agent_role_prompt": "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis."
        }
        task: "what are the most interesting sites in Tel Aviv?"
        response:
        {
            "server:  "🌍 Travel Agent",
            "agent_role_prompt": "You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and cultural insights."
        }
    """


def generate_summary_prompt(query, data):
    """ Generates the summary prompt for the given question and text.
    Args: question (str): The question to generate the summary prompt for
            text (str): The text to generate the summary prompt for
    Returns: str: The summary prompt for the given question and text
    """

    return f'{data}\n Using the above text, summarize it based on the following task or query: "{query}".\n If the ' \
           f'query cannot be answered using the text, YOU MUST summarize the text in short.\n Include all factual ' \
           f'information such as numbers, stats, quotes, etc if available. '


################################################################################################

# DETAILED REPORT PROMPTS

def generate_subtopics_prompt() -> str:
    return """
                Provided the main topic:
                
                {task}
                
                and research data:
                
                {data}
                
                - Construct a list of subtopics which indicate the headers of a report document to be generated on the task. 
                - These are a possible list of subtopics : {subtopics}.
                - There should NOT be any duplicate subtopics.
                - Limit the number of subtopics to a maximum of {max_subtopics}
                - Finally order the subtopics by their tasks, in a relevant and meaningful order which is presentable in a detailed report
                
                "IMPORTANT!":
                - Every subtopic MUST be relevant to the main topic and provided research data ONLY!
                
                {format_instructions}
            """


def generate_subtopic_report_prompt(
    current_subtopic,
    existing_headers,
    main_topic,
    context,
    report_format="apa",
    total_words=800,
    max_subsections=5,
) -> str:

    return f"""
    "Context":
    "{context}"
    
    "Main Topic and Subtopic":
    Using the latest information available, construct a detailed report on the subtopic: {current_subtopic} under the main topic: {main_topic}.
    You must limit the number of subsections to a maximum of {max_subsections}.
    
    "Content Focus":
    - The report should focus on answering the question, be well-structured, informative, in-depth, and include facts and numbers if available.
    - Use markdown syntax and follow the {report_format.upper()} format.
    
    "Structure and Formatting":
    - As this sub-report will be part of a larger report, include only the main body divided into suitable subtopics without any introduction or conclusion section.
    
    - You MUST include markdown hyperlinks to relevant source URLs wherever referenced in the report, for example:
    
        # Report Header
        
        This is a sample text. ([url website](url))
    
    "Existing Subtopic Reports":
    - This is a list of existing subtopic reports and their section headers:
    
        {existing_headers}.
    
    - Do not use any of the above headers or related details to avoid duplicates. Use smaller Markdown headers (e.g., H2 or H3) for content structure, avoiding the largest header (H1) as it will be used for the larger report's heading.
    
    "Date":
    Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.
    
    "IMPORTANT!":
    - The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
    - Must NOT have any introduction, conclusion, summary or reference section.
    - You MUST include hyperlinks with markdown syntax ([url website](url)) related to the sentences wherever necessary.
    - The report should have a minimum length of {total_words} words.
    """


def generate_report_introduction(question: str, research_summary: str = "") -> str:
    return f"""{research_summary}\n 
        Using the above latest information, Prepare a detailed report introduction on the topic -- {question}.
        - The introduction should be succinct, well-structured, informative with markdown syntax.
        - As this introduction will be part of a larger report, do NOT include any other sections, which are generally present in a report.
        - The introduction should be preceded by an H1 heading with a suitable topic for the entire report.
        - You must include hyperlinks with markdown syntax ([url website](url)) related to the sentences wherever necessary.
        Assume that the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.
    """


report_type_mapping = {
    ReportType.ResearchReport.value: generate_report_prompt,
    ReportType.ResourceReport.value: generate_resource_report_prompt,
    ReportType.OutlineReport.value: generate_outline_report_prompt,
    ReportType.CustomReport.value: generate_custom_report_prompt,
    ReportType.SubtopicReport.value: generate_subtopic_report_prompt
}


def get_prompt_by_report_type(report_type):
    prompt_by_type = report_type_mapping.get(report_type)
    default_report_type = ReportType.ResearchReport.value
    if not prompt_by_type:
        warnings.warn(f"Invalid report type: {report_type}.\n"
                        f"Please use one of the following: {', '.join([enum_value for enum_value in report_type_mapping.keys()])}\n"
                        f"Using default report type: {default_report_type} prompt.",
                        UserWarning)
        prompt_by_type = report_type_mapping.get(default_report_type)
    return prompt_by_type
