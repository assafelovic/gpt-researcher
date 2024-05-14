import asyncio
import json

import markdown

from gpt_researcher.master.prompts import *
from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.utils.llm import *

def get_retriever(retriever):
    """
    Gets the retriever
    Args:
        retriever: retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch
            retriever = TavilySearch
        case "tavily_news":
            from gpt_researcher.retrievers import TavilyNews
            retriever = TavilyNews
        case "google":
            from gpt_researcher.retrievers import GoogleSearch
            retriever = GoogleSearch
        case "searx":
            from gpt_researcher.retrievers import SearxSearch
            retriever = SearxSearch
        case "serpapi":
            from gpt_researcher.retrievers import SerpApiSearch
            retriever = SerpApiSearch
        case "googleSerp":
            from gpt_researcher.retrievers import SerperSearch
            retriever = SerperSearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo
            retriever = Duckduckgo
        case "BingSearch":
            from gpt_researcher.retrievers import BingSearch
            retriever = BingSearch

        case _:
            raise Exception("Retriever not found.")

    return retriever


async def choose_agent(query, cfg, parent_query=None):
    """
    Chooses the agent automatically
    Args:
        parent_query: In some cases the research is conducted on a subtopic from the main query.
        Tge parent query allows the agent to know the main context for better reasoning.
        query: original query
        cfg: Config

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    try:
        response = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"}],
            temperature=0,
            llm_provider=cfg.llm_provider
        )
        agent_dict = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]
    except Exception as e:
        return "Default Agent", "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."


async def get_sub_queries(query: str, agent_role_prompt: str, cfg, parent_query: str, report_type:str):
    """
    Gets the sub queries
    Args:
        query: original query
        agent_role_prompt: agent role prompt
        cfg: Config

    Returns:
        sub_queries: List of sub queries

    """
    max_research_iterations = cfg.max_iterations if cfg.max_iterations else 1
    response = await create_chat_completion(
        model=cfg.smart_llm_model,
        messages=[
            {"role": "system", "content": f"{agent_role_prompt}"},
            {"role": "user", "content": generate_search_queries_prompt(query, parent_query, report_type, max_iterations=max_research_iterations)}],
        temperature=0,
        llm_provider=cfg.llm_provider
    )
    sub_queries = json.loads(response)
    return sub_queries


def scrape_urls(urls, cfg=None):
    """
    Scrapes the urls
    Args:
        urls: List of urls
        cfg: Config (optional)

    Returns:
        text: str

    """
    content = []
    user_agent = cfg.user_agent if cfg else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    try:
        content = Scraper(urls, user_agent, cfg.scraper).run()
    except Exception as e:
        print(f"{Fore.RED}Error in scrape_urls: {e}{Style.RESET_ALL}")
    return content


async def summarize(query, content, agent_role_prompt, cfg, websocket=None):
    """
    Asynchronously summarizes a list of URLs.

    Args:
        query (str): The search query.
        content (list): List of dictionaries with 'url' and 'raw_content'.
        agent_role_prompt (str): The role prompt for the agent.
        cfg (object): Configuration object.

    Returns:
        list: A list of dictionaries with 'url' and 'summary'.
    """

    # Function to handle each summarization task for a chunk
    async def handle_task(url, chunk):
        summary = await summarize_url(query, chunk, agent_role_prompt, cfg)
        if summary:
            await stream_output("logs", f"🌐 Summarizing url: {url}", websocket)
            await stream_output("logs", f"📃 {summary}", websocket)
        return url, summary

    # Function to split raw content into chunks of 10,000 words
    def chunk_content(raw_content, chunk_size=10000):
        words = raw_content.split()
        for i in range(0, len(words), chunk_size):
            yield ' '.join(words[i:i+chunk_size])

    # Process each item one by one, but process chunks in parallel
    concatenated_summaries = []
    for item in content:
        url = item['url']
        raw_content = item['raw_content']

        # Create tasks for all chunks of the current URL
        chunk_tasks = [handle_task(url, chunk)
                       for chunk in chunk_content(raw_content)]

        # Run chunk tasks concurrently
        chunk_summaries = await asyncio.gather(*chunk_tasks)

        # Aggregate and concatenate summaries for the current URL
        summaries = [summary for _, summary in chunk_summaries if summary]
        concatenated_summary = ' '.join(summaries)
        concatenated_summaries.append(
            {'url': url, 'summary': concatenated_summary})

    return concatenated_summaries


async def summarize_url(query, raw_data, agent_role_prompt, cfg):
    """
    Summarizes the text
    Args:
        query:
        raw_data:
        agent_role_prompt:
        cfg:

    Returns:
        summary: str

    """
    summary = ""
    try:
        summary = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": f"{generate_summary_prompt(query, raw_data)}"}],
            temperature=0,
            llm_provider=cfg.llm_provider
        )
    except Exception as e:
        print(f"{Fore.RED}Error in summarize: {e}{Style.RESET_ALL}")
    return summary


async def generate_report(
    query,
    context,
    agent_role_prompt,
    report_type,
    websocket,
    cfg,
    main_topic: str = "",
    existing_headers: list = []
):
    """
    generates the final report
    Args:
        query:
        context:
        agent_role_prompt:
        report_type:
        websocket:
        cfg:
        main_topic:
        existing_headers:

    Returns:
        report:

    """
    generate_prompt = get_prompt_by_report_type(report_type)
    report = ""

    if report_type == "subtopic_report":
        content = f"{generate_prompt(query, existing_headers, main_topic, context, cfg.report_format, cfg.total_words)}"
    else:
        content = (
            f"{generate_prompt(query, context, cfg.report_format, cfg.total_words)}")

    try:
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": content}],
            temperature=0,
            llm_provider=cfg.llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit
        )
    except Exception as e:
        print(f"{Fore.RED}Error in generate_report: {e}{Style.RESET_ALL}")

    return report


async def stream_output(type, output, websocket=None, logging=True):
    """
    Streams output to the websocket
    Args:
        type:
        output:

    Returns:
        None
    """
    if not websocket or logging:
        print(output)

    if websocket:
        await websocket.send_json({"type": type, "output": output})

async def get_report_introduction(query, context, role, config, websocket=None):
    try:
        introduction = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": generate_report_introduction(query, context)}],
            temperature=0,
            llm_provider=config.llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit
        )

        return introduction
    except Exception as e:
        print(f"{Fore.RED}Error in generating report introduction: {e}{Style.RESET_ALL}")

    return ""

def extract_headers(markdown_text: str):
    # Function to extract headers from markdown text

    headers = []
    parsed_md = markdown.markdown(markdown_text)  # Parse markdown text
    lines = parsed_md.split("\n")  # Split text into lines

    stack = []  # Initialize stack to keep track of nested headers
    for line in lines:
        if line.startswith("<h") and len(line) > 1:  # Check if the line starts with an HTML header tag
            level = int(line[2])  # Extract header level
            header_text = line[
                line.index(">") + 1: line.rindex("<")
            ]  # Extract header text

            # Pop headers from the stack with higher or equal level
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            header = {
                "level": level,
                "text": header_text,
            }  # Create header dictionary
            if stack:
                stack[-1].setdefault("children", []).append(
                    header
                )  # Append as child if parent exists
            else:
                # Append as top-level header if no parent exists
                headers.append(header)

            stack.append(header)  # Push header onto the stack

    return headers  # Return the list of headers


def table_of_contents(markdown_text: str):
    try:
        # Function to generate table of contents recursively
        def generate_table_of_contents(headers, indent_level=0):
            toc = ""  # Initialize table of contents string
            for header in headers:
                toc += (
                    " " * (indent_level * 4) + "- " + header["text"] + "\n"
                )  # Add header text with indentation
                if "children" in header:  # If header has children
                    toc += generate_table_of_contents(
                        header["children"], indent_level + 1
                    )  # Generate TOC for children
            return toc  # Return the generated table of contents

        # Extract headers from markdown text
        headers = extract_headers(markdown_text)
        toc = "## Table of Contents\n\n" + generate_table_of_contents(
            headers
        )  # Generate table of contents

        return toc  # Return the generated table of contents

    except Exception as e:
        print("table_of_contents Exception : ", e)  # Print exception if any
        return markdown_text  # Return original markdown text if an exception occurs

def add_source_urls(report_markdown: str, visited_urls: set):
    """
    This function takes a Markdown report and a set of visited URLs as input parameters.

    Args:
      report_markdown (str): The `add_source_urls` function takes in two parameters:
      visited_urls (set): Visited_urls is a set that contains URLs that have already been visited. This
    parameter is used to keep track of which URLs have already been included in the report_markdown to
    avoid duplication.
    """
    try:
        url_markdown = "\n\n\n## References\n\n"

        url_markdown += "".join(f"- [{url}]({url})\n" for url in visited_urls)

        updated_markdown_report = report_markdown + url_markdown

        return updated_markdown_report

    except Exception as e:
        print(f"Encountered exception in adding source urls : {e}")
        return report_markdown