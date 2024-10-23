import json_repair
from ..utils.llm import create_chat_completion
from ..prompts import generate_search_queries_prompt
from typing import Any


async def plan_research_outline(
    query: str,
    retriever: Any,
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
        retriever: retriever instance
        agent_role_prompt: agent role prompt
        cfg: Config
        parent_query: parent query
        report_type: report type
        cost_callback: callback for cost calculation

    Returns:
        sub_queries: List of sub queries
    """
    # Get web search results prior to generating subqueries for improved context around real time data tasks
    search_retriever = retriever(query)
    search_results = search_retriever.search()

    max_research_iterations = cfg.max_iterations if cfg.max_iterations else 1
    gen_queries_prompt = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=max_research_iterations,
        context=search_results
    )
    response = await create_chat_completion(
        model=cfg.strategic_llm_model,
        messages=[
            {
                "role": "user",
                "content": gen_queries_prompt,
            },
        ],
        # Please note o1 model does not support max_tokens and other params
        max_tokens=None,
        temperature=1,
        llm_provider=cfg.strategic_llm_provider,
        llm_kwargs=cfg.llm_kwargs,
        cost_callback=cost_callback,
    )

    sub_queries = json_repair.loads(response)

    return sub_queries
