import asyncio
import json
import logging
import re
from typing import Dict, List
import json_repair
import markdown

from gpt_researcher.master.prompts import *
from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.utils.enum import Tone
from gpt_researcher.utils.llm import *
from gpt_researcher.utils.logger import get_formatted_logger

logger = get_formatted_logger()

def get_retriever(retriever):
    """
    Gets the retriever
    Args:
        retriever: retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "google":
            from gpt_researcher.retrievers import GoogleSearch

            retriever = GoogleSearch
        case "searx":
            from gpt_researcher.retrievers import SearxSearch

            retriever = SearxSearch
        case "serpapi":
            from gpt_researcher.retrievers import SerpApiSearch

            retriever = SerpApiSearch
        case "serper":
            from gpt_researcher.retrievers import SerperSearch

            retriever = SerperSearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo

            retriever = Duckduckgo
        case "bing":
            from gpt_researcher.retrievers import BingSearch

            retriever = BingSearch
        case "arxiv":
            from gpt_researcher.retrievers import ArxivSearch

            retriever = ArxivSearch
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch

            retriever = TavilySearch
        case "exa":
            from gpt_researcher.retrievers import ExaSearch

            retriever = ExaSearch
        case "semantic_scholar":
            from gpt_researcher.retrievers import SemanticScholarSearch

            retriever = SemanticScholarSearch
        case "pubmed_central":
            from gpt_researcher.retrievers import PubMedCentralSearch

            retriever = PubMedCentralSearch
        case "custom":
            from gpt_researcher.retrievers import CustomRetriever

            retriever = CustomRetriever

        case _:
            retriever = None

    return retriever


def get_retrievers(headers, cfg):
    """
    Determine which retriever(s) to use based on headers, config, or default.

    Args:
        headers (dict): The headers dictionary
        cfg (Config): The configuration object

    Returns:
        list: A list of retriever classes to be used for searching.
    """
    # Check headers first for multiple retrievers
    if headers.get("retrievers"):
        retrievers = headers.get("retrievers").split(",")
    # If not found, check headers for a single retriever
    elif headers.get("retriever"):
        retrievers = [headers.get("retriever")]
    # If not in headers, check config for multiple retrievers
    elif cfg.retrievers:
        retrievers = cfg.retrievers
    # If not found, check config for a single retriever
    elif cfg.retriever:
        retrievers = [cfg.retriever]
    # If still not set, use default retriever
    else:
        retrievers = [get_default_retriever().__name__]

    # Convert retriever names to actual retriever classes
    # Use get_default_retriever() as a fallback for any invalid retriever names
    return [get_retriever(r) or get_default_retriever() for r in retrievers]


def get_default_retriever(retriever):
    from gpt_researcher.retrievers import TavilySearch

    return TavilySearch


async def choose_agent(
    query, cfg, parent_query=None, cost_callback: callable = None, headers=None
):
    """
    Chooses the agent automatically
    Args:
        parent_query: In some cases the research is conducted on a subtopic from the main query.
        The parent query allows the agent to know the main context for better reasoning.
        query: original query
        cfg: Config
        cost_callback: callback for calculating llm costs

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response = None  # Initialize response to ensure it's defined

    try:
        response = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            temperature=0.15,
            llm_provider=cfg.llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )

        agent_dict = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]

    except Exception as e:
        print("⚠️ Error in reading JSON, attempting to repair JSON")
        return await handle_json_error(response)


async def handle_json_error(response):
    try:
        agent_dict = json_repair.loads(response)
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):
            return agent_dict["server"], agent_dict["agent_role_prompt"]
    except Exception as e:
        print(f"Error using json_repair: {e}")

    json_string = extract_json_with_regex(response)
    if json_string:
        try:
            json_data = json.loads(json_string)
            return json_data["server"], json_data["agent_role_prompt"]
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    print("No JSON found in the string. Falling back to Default Agent.")
    return "Default Agent", (
        "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
        "critically acclaimed, objective and structured reports on given text."
    )


def extract_json_with_regex(response):
    json_match = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None


async def get_sub_queries(
    query: str,
    agent_role_prompt: str,
    cfg,
    parent_query: str,
    report_type: str,
    cost_callback: callable = None,
):
    """
    Gets the sub queries
    Args:
        query: original query
        agent_role_prompt: agent role prompt
        cfg: Config
        parent_query:
        report_type:
        cost_callback:

    Returns:
        sub_queries: List of sub queries

    """
    max_research_iterations = cfg.max_iterations if cfg.max_iterations else 1
    response = await create_chat_completion(
        model=cfg.smart_llm_model,
        messages=[
            {"role": "system", "content": f"{agent_role_prompt}"},
            {
                "role": "user",
                "content": generate_search_queries_prompt(
                    query,
                    parent_query,
                    report_type,
                    max_iterations=max_research_iterations,
                ),
            },
        ],
        temperature=0.1,
        llm_provider=cfg.llm_provider,
        llm_kwargs=cfg.llm_kwargs,
        cost_callback=cost_callback,
    )

    sub_queries = json_repair.loads(response)

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
    user_agent = (
        cfg.user_agent
        if cfg
        else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
    try:
        content = Scraper(urls, user_agent, cfg.scraper).run()
    except Exception as e:
        print(f"{Fore.RED}Error in scrape_urls: {e}{Style.RESET_ALL}")
    return content


async def write_conclusion(
    report, agent_role_prompt, cfg, cost_callback: callable = None
):
    conclusion_prompt = generate_report_conclusion(report_content=report)
    conclusion = ""
    try:
        conclusion = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": f"{conclusion_prompt}",
                },
            ],
            temperature=0.35,
            llm_provider=cfg.llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )
    except Exception as e:
        print(f"{Fore.RED}Error in generating report conclusion: {e}{Style.RESET_ALL}")
    return conclusion


async def summarize_url(
    query, raw_data, agent_role_prompt, cfg, cost_callback: callable = None
):
    """
    Summarizes the text
    Args:
        query:
        raw_data:
        agent_role_prompt:
        cfg:
        cost_callback

    Returns:
        summary: str

    """
    summary = ""
    try:
        summary = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": f"{generate_summary_prompt(query, raw_data)}",
                },
            ],
            temperature=0.35,
            llm_provider=cfg.llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )
    except Exception as e:
        print(f"{Fore.RED}Error in summarize: {e}{Style.RESET_ALL}")
    return summary

async def generate_draft_section_titles(
    query: str,
    context,
    agent_role_prompt: str,
    report_type: str,
    websocket,
    cfg,
    main_topic: str = "",
    cost_callback: callable = None,
    headers=None
) -> str:
    assert report_type == "subtopic_report", "This function is only for subtopic reports"
    content = f"{generate_draft_titles_prompt(query, main_topic, context)}"
    try:
        draft_section_titles = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": content},
            ],
            temperature=0.15,
            llm_provider=cfg.llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )
    except Exception as e:
        print(f"{Fore.RED}Error in generate_draft_section_titles: {e}{Style.RESET_ALL}")
    
    return draft_section_titles

async def generate_report(
    query: str,
    context,
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket,
    cfg,
    main_topic: str = "",
    existing_headers: list = [],
    relevant_written_contents: list = [],
    cost_callback: callable = None,
    headers=None,
):
    """
    generates the final report
    Args:
        query:
        context:
        agent_role_prompt:
        report_type:
        websocket:
        tone:
        cfg:
        main_topic:
        existing_headers:
        relevant_written_contents:
        cost_callback:

    Returns:
        report:

    """
    generate_prompt = get_prompt_by_report_type(report_type)
    report = ""

    if report_type == "subtopic_report":
        content = f"{generate_prompt(query, existing_headers, relevant_written_contents, main_topic, context, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words)}"
    else:
        content = f"{generate_prompt(query, context, report_source, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words)}"
    try:
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": content},
            ],
            temperature=0.35,
            llm_provider=cfg.llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )
    except Exception as e:
        print(f"{Fore.RED}Error in generate_report: {e}{Style.RESET_ALL}")

    return report


async def stream_output(
    type, content, output, websocket=None, output_log=True, metadata=None
):
    """
    Streams output to the websocket
    Args:
        type:
        content:
        output:

    Returns:
        None
    """
    if not websocket or output_log:
        try:
            logger.info(output)
        except UnicodeEncodeError:
            # Option 1: Replace problematic characters with a placeholder
            logger.error(output.encode('cp1252', errors='replace').decode('cp1252'))

    if websocket:
        await websocket.send_json(
            {"type": type, "content": content, "output": output, "metadata": metadata}
        )


async def get_report_introduction(
    query, context, role, config, websocket=None, cost_callback: callable = None
):
    try:
        introduction = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {
                    "role": "user",
                    "content": generate_report_introduction(query, context),
                },
            ],
            temperature=0.25,
            llm_provider=config.llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )

        return introduction
    except Exception as e:
        print(
            f"{Fore.RED}Error in generating report introduction: {e}{Style.RESET_ALL}"
        )

    return ""


def extract_headers(markdown_text: str):
    # Function to extract headers from markdown text

    headers = []
    parsed_md = markdown.markdown(markdown_text)  # Parse markdown text
    lines = parsed_md.split("\n")  # Split text into lines

    stack = []  # Initialize stack to keep track of nested headers
    for line in lines:
        # Check if the line starts with an HTML header tag
        if line.startswith("<h") and len(line) > 2 and line[2].isdigit():
            level = int(line[2])  # Extract header level
            header_text = line[
                line.index(">") + 1 : line.rindex("<")
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

def extract_sections(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extract all written sections from subtopic report
    Args:
        markdown_text: subtopic report text
    Returns:
        List of sections, each section is dictionary and contain following information
        [
            {
                "section_title": "Pruning",
                "written_content": "Pruning involves removing redundant or less ..."
            },
        ]
    """
    sections = []
    parsed_md = markdown.markdown(markdown_text)
    
    # Use regex to find all headers and their content
    pattern = r'<h\d>(.*?)</h\d>(.*?)(?=<h\d>|$)'
    matches = re.findall(pattern, parsed_md, re.DOTALL)
    
    for title, content in matches:
        # Clean up the content
        clean_content = re.sub(r'<.*?>', '', content).strip()
        if clean_content:
            sections.append({
                "section_title": title.strip(),
                "written_content": clean_content
            })
    
    return sections

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


def add_references(report_markdown: str, visited_urls: set):
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
