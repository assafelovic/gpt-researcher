AGENT_ROLE_PROMPT = "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."

def generate_agent_role_prompt():
    return AGENT_ROLE_PROMPT

def generate_report_prompt(question, research_summary):
    return f'"""{research_summary}""" Using the above information, answer the following'\
           f' question or topic: "{question}" in a detailed report --'\
           " The report should focus on the answer to the question, should be well structured, " \
           "informative, in depth, with facts and numbers if available, a minimum of 1,200 words and with markdown syntax. "\
            "Write all source urls at the end of the report, including urls that weren't used (explain why you didn't use them)."

def generate_search_queries_prompt(question):
    return f'Write 4 google search queries to search online that form an objective opinion from the following: "{question}"'\
           f'You must respond with a list of strings in the following format: ["query 1", "query 2", "query 3", "query 4"]'

