from gpt_researcher.utils.llm import *
from gpt_researcher.config.config import Config
from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.master.prompts import *
import json

cfg = Config()


def get_retriever():
    if cfg.retriver == "duckduckgo":
        from gpt_researcher.retrievers.duckduckgo.duckduckgo import Duckduckgo
        retriever = Duckduckgo
    elif cfg.retriver == "tavily":
        from gpt_researcher.retrievers.tavily_search.tavily_search import TavilySearch
        retriever = TavilySearch
    else:
        raise Exception("Retriever not found.")
    return retriever


def choose_agent(query):
    try:
        response = create_chat_completion(
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


def get_sub_queries(query, agent_role_prompt):
    response = create_chat_completion(
        model=cfg.smart_llm_model,
        messages=[
            {"role": "system", "content": f"{agent_role_prompt}"},
            {"role": "user", "content": generate_search_queries_prompt(query)}],
        temperature=0,
        llm_provider=cfg.llm_provider
    )
    sub_queries = json.loads(response)
    return sub_queries


def scrape_urls(urls):
    text = ""
    try:
        text = Scraper(urls).run()
    except Exception as e:
        print(f"{Fore.RED}Error in scrape_urls: {e}{Style.RESET_ALL}")
    return text


def summarize(query, text, agent_role_prompt):
    summary = ""
    try:
        summary = create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": f"{generate_summary_prompt(query, text)}"}],
            temperature=0,
            llm_provider=cfg.llm_provider
        )
    except Exception as e:
        print(f"{Fore.RED}Error in summarize: {e}{Style.RESET_ALL}")
    return summary


def generate_report(query, context, agent_role_prompt, report_type):
    generate_prompt = get_report_by_type(report_type)
    report = ""
    try:
        response = create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": f"{generate_prompt(query, context)}"}],
            temperature=0,
            llm_provider=cfg.llm_provider
        )
        report = json.loads(response)
    except Exception as e:
        print(f"{Fore.RED}Error in generate_report: {e}{Style.RESET_ALL}")
    return report
