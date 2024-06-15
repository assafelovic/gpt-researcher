#prompts.py

from datetime import datetime, timezone
import warnings
from sf_researcher.utils.enum import ReportType

################################################################################################

# GENERAL PROMPTS

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

def generate_contacts_prompt() -> str:
    return """
    Company name:
    
    {company_name}
    
    Research data:
    
    {data}
    
    - Construct a list of full names (first name and last name) of all individuals mentioned in the research data who hold titles such as directors, officers, company owners, partners, executives, or managers related to the company name.
    - There should NOT be any duplicate names.
    
    "IMPORTANT!":
    - Every name MUST be mentioned in the provided research data ONLY!
    - Both first name and last name MUST be present and valid. Do not create placeholders like: unknown if you cannot find the first or last names. 
    - Exclude any contacts that you cannot get both first and last names.
    - Do not create any names that are not mentioned, if you can't find any name, leave the list empty.
    - Limit the number of contacts to a maximum of {max_contacts}
    """

def generate_search_analysis_prompt() -> str:
    return """
    Overall Goal:

    {overall_goal}
    
    Search result:

    {search_results}
    
    Given the above list of search results for each query, perform the following actions:

    1. Exclusion:
    - For each search result item, determine its relevance to the overall goal. If the search result item is not relevant exclude it from the results.
    - Assess the title, URL, and snippet (body) of each search result to determine if it contains relevant information about the company, such as its profile, funding, investors, executives, or other key details.
    - Only return search result items that are relevant to the overall goal.

    2. Categorization:
    - Categorize each search result item based on the type of information it provides about the company, such as company profile, funding details, executive information, competitor analysis, general overview, product details, market analysis, news mentions, financial performance, or customer reviews.
    - Additionally, categorize each search result item based on its source type (e.g., official website, news article, financial report, social media, industry blog).

    Provide the analysis results in a structured format, including the relevance scores, extracted entities, and assigned categories for each search result item.
    """


################################################################################################

# SF REPORT PROMPTS

def generate_compliance_report_prompt(
        company_name, 
        context, 
        report_format="apa", 
        total_words=100
    ):
    return f"""
    Using the latest information available about the company {company_name}, generate a compliance report focusing on key data points needed to assess if the company is viable to successfully onboard to BVNK's services from a legal and compliance perspective.
    
    The report should include:
    - Full legal company name and registration number
    - Incorporation date and jurisdiction 
    - List of all current active directors with full names
    - Regulatory licenses and registrations held, especially related to financial services
    - Any past regulatory actions, fines or investigations against the company
    - Adverse media or reports of financial crime, fraud or unethical business practices
    - Overall assessment of compliance risk level in onboarding this company as a BVNK client
    
    You must format the report with HTML format.
    Use an unbiased and journalistic tone. 
    You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions.
    You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
    Every url should be hyperlinked: [url website](url)
    Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report.
    You MUST write the report in {report_format} format.
    The report should have a minimum length of {total_words} words.
    Assume that the current date is {datetime.now().strftime('%B %d, %Y')}.
    
    Information to use:
    {context}
    """

def generate_compliance_contact_report_prompt(
        contact_name, 
        company_name, 
        context, 
        report_format="apa", 
        total_words=100,
    ) -> str:
    return f"""    
    Information to use:  
    {context}

    Using the latest information available, generate a short report on the director {contact_name} of the company {company_name}, capturing additional compliance data points, including:
    
    - Full name and any previous names/aliases
    - Overall assessment of compliance risk level of this individual, include relevant research urls
    
    You must format the report with HTML format.
    Use an unbiased and journalistic tone. 
    You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions.
    You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
    Every url should be hyperlinked: [url website](url)
    Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report.
    You MUST write the report in {report_format} format.
    The report should have a minimum length of {total_words} words.
    Assume that the current date is {datetime.now().strftime('%B %d, %Y')}.
    """

def generate_sales_report_prompt(
        company_name, 
        context, 
        report_format="apa", 
        total_words=100
    ):
    return f"""
    Using the latest information available about the company {company_name}, generate a sales report to qualify the lead and assess viability for BVNK's products and services.
    
    The report should include:
    - Company website and main business activities
    - Estimated annual revenue and growth rate
    - Target markets and customer base
    - Current payment methods accepted
    - Use of cryptocurrencies or stablecoins
    - Potential use cases for BVNK's payments, treasury, and stablecoin infrastructure
    - Any major competitors or partners identified
    - Overall lead score and sales opportunity assessment
    
    You must format the report with HTML format.
    Use an unbiased and journalistic tone.
    You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions.
    You MUST write all used source URLs at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
    Every URL should be hyperlinked: [url website](url)
    Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report.
    You MUST write the report in {report_format} format.
    The report should have a minimum length of {total_words} words.
    Assume that the current date is {datetime.now().strftime('%B %d, %Y')}.
    
    Information to use:
    {context}
    """

def generate_sales_contact_report_prompt(
        contact_name, 
        company_name, 
        context, 
        report_format="apa", 
        total_words=100,
    ) -> str:
    return f"""    
    Information to use:  
    {context}

    Using the latest information available, generate a short report on the director {contact_name} of the company {company_name}, capturing additional compliance data points, including:
    
    - Full name and any previous names/aliases
    - Overall assessment of compliance risk level of this individual, include relevant research urls
    
    You must format the report with HTML format.
    Use an unbiased and journalistic tone. 
    You MUST determine your own concrete and valid opinion based on the given information. Do NOT deter to general and meaningless conclusions.
    You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
    Every url should be hyperlinked: [url website](url)
    Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report.
    You MUST write the report in {report_format} format.
    The report should have a minimum length of {total_words} words.
    Assume that the current date is {datetime.now().strftime('%B %d, %Y')}.
    """

################################################################################################

# CONSTRUCT SOBJECT PROMPTS

def generate_compliance_contact_sobject_prompt() -> str:
    return """
    Contact query:

    {contact_name}
    
    Company name:
    
    {company}
    
    Research context:
    
    {context}

    Visited urls:

    {visited_urls}
    
    Extract the following information for the director mentioned in the report:
    - First name
    - Last name
    - Company name
    - Email address (if available)
    - Mobile phone number (if available)
    - Job title
    - Source URL: The primary source URL used in collecting data
    
    Leave fields blank if you can't find the info.
    """

def generate_sales_contact_sobject_prompt() -> str:
    return """
    Contact query:

    {contact_name}
    
    Company name:
    
    {company}
    
    Research context:
    
    {context}

    Visited urls:

    {visited_urls}
    
    Extract the following information for the director mentioned in the report:
    - First name
    - Last name
    - Company name
    - Email address (if available)
    - Mobile phone number (if available)
    - Job title
    - Source URL: The primary source URL used in collecting data
    
    Leave fields blank if you can't find the info.
    """

def generate_compliance_company_sobject_prompt() -> str:
    return """
    from the given context:
    
    {context}
    
    from the given urls:
    
    {visited_urls}
    
    for company:
    
    {company}
    
    Extract the following information for the company:
    - Full legal company name
    - Company registration number
    - Incorporation date
    - Jurisdiction of incorporation
    - Registered office address
    - Regulatory licenses and registrations held, especially related to financial services
    - Any past regulatory actions, fines or investigations against the company
    - Adverse media or reports of financial crime, fraud or unethical business practices
    - Overall assessment of compliance risk level in onboarding this company as a client
    - source_url = The primary source URL used in collecting data

    Leave fields blank if you can't find the info.
    """



report_type_mapping = {
    ReportType.ComplianceReport.value: generate_compliance_report_prompt,
    ReportType.ContactReport.value: generate_compliance_contact_report_prompt,
    ReportType.SalesReport.value: generate_sales_report_prompt,
    ReportType.SalesContactReport.value: generate_sales_contact_report_prompt,
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
