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
