AGENT_ROLE_PROMPT = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."

def generate_agent_role_prompt():
    """ Generates the agent role prompt.
    Args: None
    Returns: str: The agent role prompt
    """
    return AGENT_ROLE_PROMPT

def generate_report_prompt(question, research_summary):
    """ Generates the report prompt for the given question and research summary.
    Args: question (str): The question to generate the report prompt for
            research_summary (str): The research summary to generate the report prompt for
    Returns: str: The report prompt for the given question and research summary
    """

    return f'"""{research_summary}""" Using the above information, answer the following'\
           f' question or topic: "{question}" in a detailed report --'\
           " The report should focus on the answer to the question, should be well structured, " \
           "informative, in depth, with facts and numbers if available, a minimum of 1,200 words and with markdown syntax. "\
            "Write all source urls at the end of the report, including urls that weren't used (explain why you didn't use them)."

def generate_search_queries_prompt(question):
    """ Generates the search queries prompt for the given question.
    Args: question (str): The question to generate the search queries prompt for
    Returns: str: The search queries prompt for the given question
    """

    return f'Write 4 google search queries to search online that form an objective opinion from the following: "{question}"'\
           f'You must respond with a list of strings in the following format: ["query 1", "query 2", "query 3", "query 4"]'


def generate_resource_report_prompt(question, research_summary):
    """Generates the resource report prompt for the given question and research summary.

    Args:
        question (str): The question to generate the resource report prompt for.
        research_summary (str): The research summary to generate the resource report prompt for.

    Returns:
        str: The resource report prompt for the given question and research summary.
    """
    return f'"""{research_summary}""" Based on the above information, generate a bibliography recommendation report for the following' \
           f' question or topic: "{question}". The report should provide a detailed analysis of each recommended resource,' \
           ' explaining how each source can contribute to finding answers to the research question.' \
           ' Focus on the relevance, reliability, and significance of each source.' \
           ' Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.' \
           ' Include relevant facts, figures, and numbers whenever available.' \
           ' The report should have a minimum length of 1,200 words.'


def generate_outline_report_prompt(question, research_summary):
    """ Generates the outline report prompt for the given question and research summary.
    Args: question (str): The question to generate the outline report prompt for
            research_summary (str): The research summary to generate the outline report prompt for
    Returns: str: The outline report prompt for the given question and research summary
    """

    return f'"""{research_summary}""" Using the above information, generate an outline for a research report in Markdown syntax'\
           f' for the following question or topic: "{question}". The outline should provide a well-structured framework'\
           ' for the research report, including the main sections, subsections, and key points to be covered.' \
           ' The research report should be detailed, informative, in-depth, and a minimum of 1,200 words.' \
           ' Use appropriate Markdown syntax to format the outline and ensure readability.'
