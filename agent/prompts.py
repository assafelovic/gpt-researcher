from config.config import Config

def generate_agent_role_prompt(agent):
    """ Generates the agent role prompt.
    Args: agent (str): The type of the agent.
    Returns: str: The agent role prompt.
    """
    prompts = {
        "Finance Agent": "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends.",
        "Travel Agent": "You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and cultural insights.",
        "Academic Research Agent": "You are an AI academic research assistant. Your primary responsibility is to create thorough, academically rigorous, unbiased, and systematically organized reports on a given research topic, following the standards of scholarly work.",
        "Business Analyst": "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis.",
        "Computer Security Analyst Agent": "You are an AI specializing in computer security analysis. Your principal duty is to generate comprehensive, meticulously detailed, impartial, and systematically structured reports on computer security topics. This includes Exploits, Techniques, Threat Actors, and Advanced Persistent Threat (APT) Groups. All produced reports should adhere to the highest standards of scholarly work and provide in-depth insights into the complexities of computer security.",
        "Default Agent": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    }

    return prompts.get(agent, "No such agent")


def generate_report_prompt(question, research_summary):
    """ Generates the report prompt for the given question and research summary.
    Args: question (str): The question to generate the report prompt for
            research_summary (str): The research summary to generate the report prompt for
    Returns: str: The report prompt for the given question and research summary
    """

    return f'"""{research_summary}""" Using the above information, answer the following'\
           f' question or topic: "{question}" in a detailed report --'\
           " The report should focus on the answer to the question, should be well structured, informative," \
           " in depth, with facts and numbers if available, a minimum of 1,200 words and with markdown syntax and apa format. "\
            "You MUST determine your own concrete and valid opinion based on the information found. Do NOT deter to general and meaningless conclusions." \
           "Write all source urls at the end of the report in apa format"

def generate_search_queries_prompt(question):
    """ Generates the search queries prompt for the given question.
    Args: question (str): The question to generate the search queries prompt for
    Returns: str: The search queries prompt for the given question
    """
    num_search_queries = Config().num_search_queries
    queries = [f'query {i+1}' for i in range(num_search_queries)]
    queries_str = ', '.join(queries)
    return f'Write {num_search_queries} google search queries to search online that form an objective opinion from the following: "{question}"'\
           f'You must respond only with a list of strings in the following json format: {queries_str}'

def generate_architecture_report_prompt(software_name, research_summary):
    """
    Generates the architecture report prompt for the given software and research summary.

    Args:
        software_name (str): The name of the software to generate the architecture report prompt for.
        research_summary (str): The research summary to generate the architecture report prompt for.

    Returns:
        str: The architecture report prompt for the given software and research summary.
    """
    
    return f'"""{research_summary}""" Based on the provided information, create an in-depth software architecture report'\
           f' for the software "{software_name}". The report should cover the software\'s overall structure, components,'\
           ' modules, interactions, and design decisions. Utilize appropriate architectural diagrams and explanations'\
           ' to clearly convey the software\'s architecture. The report should also discuss considerations like'\
           ' scalability, maintainability, security, and performance. Ensure that the report is well-structured,'\
           ' informative, and follows Markdown syntax. Include relevant facts, figures, and technical details.'\
           ' The report should have a minimum length of 1,200 words.'

def generate_market_analysis_report_prompt(market_name, research_summary):
    """
    Generates the market analysis report prompt for the given market and research summary.

    Args:
        market_name (str): The name of the market to generate the report prompt for.
        research_summary (str): The research summary to generate the report prompt for.

    Returns:
        str: The market analysis report prompt for the given market and research summary.
    """
    
    return f'"""{research_summary}""" Based on the provided information, create a comprehensive market analysis report for'\
           f' the "{market_name}" market. The report should delve into current market trends, competitive landscape,'\
           ' target demographics, consumer preferences, and potential growth opportunities. Utilize both qualitative'\
           ' and quantitative data to provide a thorough analysis. Consider factors such as market size, market share,'\
           ' industry challenges, and emerging technologies. Ensure that the report is well-structured, informative,'\
           ' and follows appropriate formatting. Include relevant facts, figures, charts, and graphs to support your'\
           ' analysis. The report should have a minimum length of 1,200 words.'

def generate_risk_assessment_report_prompt(project_name, research_summary):
    """
    Generates the risk assessment report prompt for the given project and research summary.

    Args:
        project_name (str): The name of the project to generate the report prompt for.
        research_summary (str): The research summary to generate the report prompt for.

    Returns:
        str: The risk assessment report prompt for the given project and research summary.
    """
    
    return f'"""{research_summary}""" Based on the provided information, create a comprehensive risk assessment report for'\
           f' the "{project_name}" project. The report should identify potential risks, vulnerabilities, and threats'\
           ' that could impact the success of the project. Evaluate the potential consequences of each risk and'\
           ' propose mitigation strategies to minimize their impact. Consider factors such as technical, financial,'\
           ' operational, and external risks. Utilize both qualitative and quantitative data to support your analysis.'\
           ' Include relevant facts, figures, and examples to illustrate the identified risks. Ensure that the report'\
           ' is well-structured, informative, and follows appropriate formatting. The report should have a minimum'\
           ' length of 1,200 words.'

def generate_medical_research_paper_prompt(topic, research_summary):
    """
    Generates the medical research paper prompt for the given research topic.

    Args:
        topic (str): The research topic for the research paper.
        research_summary (str): The research summary to generate the research paper prompt for.

    Returns:
        str: The medical research paper prompt for the given research topic.
    """
    
    return f'"""{research_summary}""" Based on the provided information, conduct an original medical research study on the topic'\
           f' of {topic}. Develop a clear research question, hypothesis, and methodology for your study. Collect and analyze'\
           f' relevant data, present your findings, and draw conclusions based on the results. Discuss the implications of'\
           f' your research findings for medical practice or knowledge. Ensure that the research paper is well-structured,'\
           f' adheres to scientific writing standards, and follows appropriate citation formats. The paper should have a'\
           f' minimum length of 1,200 words.'
def generate_ux_report_prompt(product_name, research_summary):
    """
    Generates the user experience (UX) report prompt for the given product and research summary.

    Args:
        product_name (str): The name of the product to generate the report prompt for.
        research_summary (str): The research summary to generate the report prompt for.

    Returns:
        str: The user experience (UX) report prompt for the given product and research summary.
    """
    
    return f'"""{research_summary}""" Based on the provided information, create a comprehensive user experience (UX) report'\
           f' for the "{product_name}" product. The report should focus on assessing the usability, accessibility, and'\
           ' overall user satisfaction of the product. Evaluate user interactions, user flows, visual design, and'\
           ' navigation. Provide recommendations for improvements that enhance the user experience. Utilize both'\
           ' qualitative and quantitative data, such as user feedback, usability testing, and analytics. Include'\
           ' relevant facts, figures, and examples to support your analysis. Ensure that the report is well-structured,'\
           ' informative, and follows appropriate formatting. The report should have a minimum length of 1,200 words.'

                  
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

def generate_concepts_prompt(question, research_summary):
    """ Generates the concepts prompt for the given question.
    Args: question (str): The question to generate the concepts prompt for
            research_summary (str): The research summary to generate the concepts prompt for
    Returns: str: The concepts prompt for the given question
    """

    return f'"""{research_summary}""" Using the above information, generate a list of 5 main concepts to learn for a research report'\
           f' on the following question or topic: "{question}". The outline should provide a well-structured framework'\
           'You must respond with a list of strings in the following format: ["concepts 1", "concepts 2", "concepts 3", "concepts 4, concepts 5"]'


def generate_lesson_prompt(concept):
    """
    Generates the lesson prompt for the given question.
    Args:
        concept (str): The concept to generate the lesson prompt for.
    Returns:
        str: The lesson prompt for the given concept.
    """

    prompt = f'generate a comprehensive lesson about {concept} in Markdown syntax. This should include the definition'\
    f'of {concept}, its historical background and development, its applications or uses in different'\
    f'fields, and notable events or facts related to {concept}.'

    return prompt

def get_report_by_type(report_type):
    report_type_mapping = {
        'research_report': generate_report_prompt,
        'resource_report': generate_resource_report_prompt,
        'ux_report': generate_ux_report_prompt,
        'risk_report': generate_risk_assessment_report_prompt,
        'market_report': generate_market_analysis_report_prompt,
        'architecture_report': generate_architecture_report_prompt,
        'medical_report': generate_medical_research_paper_prompt,
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
