def generate_agent_role_prompt(agent, language):
    """ Generates the agent role prompt.
    Args: 
        agent (str): The type of the agent.
        language (str): The language in which the answers should be provided.
    Returns: 
        str: The agent role prompt.
    """
    prompts = {
        "Finance Agent": f"You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends. All answers must be in {language}.",
        "Travel Agent": f"You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and cultural insights. All answers must be in {language}.",
        "Academic Research Agent": f"You are an AI academic research assistant. Your primary responsibility is to create thorough, academically rigorous, unbiased, and systematically organized reports on a given research topic, following the standards of scholarly work. All answers must be in {language}.",
        "Business Analyst": f"You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis. All answers must be in {language}.",
        "Computer Security Analyst Agent": f"You are an AI specializing in computer security analysis. Your principal duty is to generate comprehensive, meticulously detailed, impartial, and systematically structured reports on computer security topics. This includes Exploits, Techniques, Threat Actors, and Advanced Persistent Threat (APT) Groups. All produced reports should adhere to the highest standards of scholarly work and provide in-depth insights into the complexities of computer security. All answers must be in {language}.",
        "Default Agent": f"You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text. All answers must be in {language}."
    }

    return prompts.get(agent, f"No such agent. All answers must be in {language}.")



def generate_report_prompt(question, research_summary,language):
    """ Generates the report prompt for the given question and research summary.
    Args: question (str): The question to generate the report prompt for
            research_summary (str): The research summary to generate the report prompt for
    Returns: str: The report prompt for the given question and research summary
    """

    return f'"""{research_summary}""" Using the above information, answer  in "{language}" the following'\
           f' question or topic: "{question}" in a detailed report --'\
           " The report should focus on the answer to the question, should be well structured, informative," \
           " in depth, with facts and numbers if available, a minimum of 1,200 words and with markdown syntax and apa format. "\
            "You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions." \
           "Write all used source urls at the end of the report in apa format"

def generate_search_queries_prompt(question, language):
    """ Generates the search queries prompt for the given question.
    Args: question (str): The question to generate the search queries prompt for
    Returns: str: The search queries prompt for the given question
    """

    return f'For the topic "{question}", list 4 search queries in English and 4 in {language}.'


def generate_resource_report_prompt(question, research_summary, language):
    return (f'"""{research_summary}""" Based on the above information, generate '
            f'in {language} a bibliography recommendation report for the following' 
            f' question or topic: "{question}". The report should provide a detailed analysis of each recommended resource,' 
            ' explaining how each source can contribute to finding answers to the research question.' 
            ' Focus on the relevance, reliability, and significance of each source.' 
            ' Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.' 
            ' Include relevant facts, figures, and numbers whenever available.' 
            ' The report should have a minimum length of 1,200 words.')


def generate_outline_report_prompt(question, research_summary,language):
    """ Generates the outline report prompt for the given question and research summary.
    Args: question (str): The question to generate the outline report prompt for
            research_summary (str): The research summary to generate the outline report prompt for
    Returns: str: The outline report prompt for the given question and research summary
    """
    return (f'"""{research_summary}""" Using the above information, generate  '
            'an outline in {language} for a research report in Markdown syntax'
            f' for the following question or topic: "{question}". The outline should provide a well-structured framework'
            ' for the research report, including the main sections, subsections, and key points to be covered.'
            ' The research report should be detailed, informative, in-depth, and a minimum of 1,200 words.' 
            ' Use appropriate Markdown syntax to format the outline and ensure readability.')

def generate_concepts_prompt(question, research_summary,language):
    """ Generates the concepts prompt for the given question.
    Args: question (str): The question to generate the concepts prompt for
            research_summary (str): The research summary to generate the concepts prompt for
    Returns: str: The concepts prompt for the given question
    """
    return (f'"""{research_summary}""" Using the above information, generate in {language}, '
            ' a list of 5 main concepts to learn for a research report'
            f' on the following question or topic: "{question}". The outline should provide a well-structured framework'
            'You must respond with a list of strings in the following format: ["concepts 1", "concepts 2", "concepts 3", "concepts 4, concepts 5"]')


def generate_lesson_prompt(concept,language):
    """
    Generates the lesson prompt for the given question.
    Args:
        concept (str): The concept to generate the lesson prompt for.
    Returns:
        str: The lesson prompt for the given concept.
    """

    prompt = f'generate  a comprehensive lesson in {language} about {concept} in Markdown syntax. This should include the definition'\
    f'of {concept}, its historical background and development, its applications or uses in different'\
    f'fields, and notable events or facts related to {concept}.'

    return prompt

def get_report_by_type(report_type):
    report_type_mapping = {
        'research_report': generate_report_prompt,
        'resource_report': generate_resource_report_prompt,
        'outline_report': generate_outline_report_prompt
    }
    return report_type_mapping[report_type]

def auto_agent_instructions():
    return """
        This task involves researching a given topic, regardless of its complexity or the availability of a definitive answer. The research is conducted by a specific agent, defined by its type and role, with each agent requiring distinct instructions.
        Agent
        The agent is determined by the field of the topic and the specific name of the agent that could be utilized to research the topic provided. Agents are categorized by their area of expertise, and each agent type is associated with a corresponding emoji.

        examples:
        task: "should I invest in apple stocks?"
        response: 
        {
            "agent": "💰 Finance Agent",
            "agent_role_prompt: "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends."
        }
        task: "could reselling sneakers become profitable?"
        response: 
        { 
            "agent":  "📈 Business Analyst Agent",
            "agent_role_prompt": "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis."
        }
        task: "what are the most interesting sites in Tel Aviv?"
        response:
        {
            "agent:  "🌍 Travel Agent",
            "agent_role_prompt": "You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and cultural insights."
        }
    """
