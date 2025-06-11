from __future__ import annotations

import traceback

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from gpt_researcher.config.config import Config
from gpt_researcher.prompts import PromptFamily, get_prompt_by_report_type
from gpt_researcher.utils.enum import Tone
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = get_formatted_logger()


async def write_report_introduction(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> str:
    """Generate an introduction for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated introduction.
    """
    try:
        introduction: str = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": prompt_family.generate_report_introduction(question=query, research_summary=context, language=config.language)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return introduction
    except Exception:
        logger.error(f"Error in generating report introduction: {traceback.format_exc()}")
    return ""


async def write_conclusion(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> str:
    """Write a conclusion for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated conclusion.
    """
    try:
        conclusion: str = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": prompt_family.generate_report_conclusion(query=query, report_content=context, language=config.language),
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return conclusion
    except Exception:
        logger.error(f"Error in writing conclusion: {traceback.format_exc()}")
    return ""


async def summarize_url(
    url: str,
    content: str,
    role: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
) -> str:
    """Summarize the content of a URL.

    Args:
        url (str): The URL to summarize.
        content (str): The content of the URL.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
        str: The summarized content.
    """
    try:
        summary: str = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {
                    "role": "user",
                    "content": f"Summarize the following content from {url}:\n\n{content}",
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return summary
    except Exception:
        logger.error(f"Error in summarizing URL: {traceback.format_exc()}")
    return ""


async def generate_draft_section_titles(
    query: str,
    current_subtopic: str,
    context: str,
    role: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> list[str]:
    """Generate draft section titles for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        list[str]: A list of generated section titles.
    """
    try:
        section_titles: list[str] = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": prompt_family.generate_draft_titles_prompt(current_subtopic, query, context)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=None,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return str(section_titles).split("\n")
    except Exception:
        logger.error(f"Error in generating draft section titles: {traceback.format_exc()}")
    return []


async def generate_report(
    query: str,
    context: str,
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket: WebSocket,
    cfg: Config,
    main_topic: str = "",
    existing_headers: list[str] | None = None,
    relevant_written_contents: list[str] | None = None,
    cost_callback: Callable | None = None,
    custom_prompt: str | None = None,
    headers: dict[str, str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs: dict[str, Any],
) -> str:
    """Generates the final report.

    Args:
        query: The research query.
        context: The context for the report.
        agent_role_prompt: The role of the agent.
        report_type: The type of report.
        tone: The tone of the report.
        report_source: The source of the report.
        websocket: The WebSocket connection for streaming output.
        cfg: The configuration object.
        main_topic: The main topic of the report.
        existing_headers: The existing headers of the report.
        relevant_written_contents: The relevant written contents of the report.
        cost_callback: The callback for calculating the cost of the report.
        custom_prompt: A custom prompt for the report.
        headers: The headers of the report.
        prompt_family: The family of prompts.
        **kwargs: Additional keyword arguments.

    Returns:
        report: The final report.
    """
    # DEBUG: Log function start and params
    logger.info(f"[DEBUG] Starting generate_report for query: {query[:50]}...")
    logger.info(f"[DEBUG] Report type: {report_type}, context length: {len(str(context))}, has custom prompt: {custom_prompt is not None}")

    existing_headers = [] if existing_headers is None else existing_headers
    relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
    generate_prompt: Any = get_prompt_by_report_type(
        report_type,
        prompt_family,
    )
    report: str = ""
    generated_prompt: str = ""

    try:
        # DEBUG: Log prompt generation
        logger.info(f"[DEBUG] Generating prompt with report_type: {report_type}")

        if report_type == "subtopic_report":
            generated_prompt = generate_prompt(
                query,
                existing_headers,
                relevant_written_contents,
                main_topic,
                context,
                report_format=cfg.report_format,  # pyright: ignore[reportAttributeAccessIssue]
                tone=tone,
                total_words=cfg.total_words,  # pyright: ignore[reportAttributeAccessIssue]
                language=cfg.language,  # pyright: ignore[reportAttributeAccessIssue]
            )
        else:
            generated_prompt = generate_prompt(
                query,
                context,
                report_source,
                report_format=cfg.report_format,  # pyright: ignore[reportAttributeAccessIssue]
                tone=tone,
                total_words=cfg.total_words,  # pyright: ignore[reportAttributeAccessIssue]
                language=cfg.language,  # pyright: ignore[reportAttributeAccessIssue]
            )

        # DEBUG: Log prompt generation success and length
        logger.info(f"[DEBUG] Generated prompt successfully, length: {len(generated_prompt)}")
        logger.info(f"[DEBUG] Prompt starts with: {generated_prompt[:100]}...")

    except Exception as e:
        logger.error(f"[DEBUG] Error generating prompt: {e.__class__.__name__}: {e}")
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        # Default empty prompt in case of error
        generated_prompt = f"Please generate a report about {query} based on the provided context."

    content: str = f"{generated_prompt}"

    # DEBUG: Log message structure before API call
    messages: list[dict[str, str]] = [
        {"role": "system", "content": f"{agent_role_prompt or ''} "},
        {"role": "user", "content": content},
    ]
    logger.info(f"[DEBUG] Preparing to call LLM with model: {cfg.smart_llm_model}, provider: {cfg.smart_llm_provider}")
    logger.info(f"[DEBUG] System message length: {len(agent_role_prompt or '')}")
    logger.info(f"[DEBUG] User message length: {len(content)}")

    try:
        logger.info("[DEBUG] Making first create_chat_completion attempt")

        # Calculate appropriate max_tokens based on model context limit
        # Estimate input tokens to leave room for output
        from gpt_researcher.utils.llm import estimate_token_count
        input_tokens: int = estimate_token_count(messages, cfg.smart_llm_model)

        # Get model context limit (conservative estimates)
        model_context_limits: dict[str, int] = {
            "google/gemini-2.0-flash-exp:free": 16385,
            "google/gemini-pro": 32000,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
        }

        model_context_limit: int = model_context_limits.get(cfg.smart_llm_model) or 4096

        # Reserve space for input tokens and some buffer
        max_output_tokens: int = max(512, min(cfg.smart_token_limit, model_context_limit - input_tokens - 500))

        logger.info(f"[DEBUG] Input tokens: {input_tokens}, Model limit: {model_context_limit}, Max output: {max_output_tokens}")

        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=messages,
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=max_output_tokens,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            cfg=cfg,
        )
        # DEBUG: Log successful completion
        logger.info(f"[DEBUG] First attempt successful, report length: {len(report)}")
        logger.info(f"[DEBUG] Report starts with: {report[:100]}...")

        # DEBUG: Check for problematic responses
        if "I'm sorry, but I cannot provide a response to this task" in report:
            logger.warning("[DEBUG] Detected error pattern in report response")
            logger.warning(f"[DEBUG] Full response: {report}")

    except Exception as e:
        logger.error(f"[DEBUG] First attempt failed: {e.__class__.__name__}: {e}")
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        try:
            # Try with a simplified approach by combining system and user messages
            logger.info("[DEBUG] Making fallback create_chat_completion attempt")
            simplified_messages: list[dict[str, str]] = [
                {
                    "role": "user",
                    "content": f"{agent_role_prompt or ''}\n\n{content}",
                },
            ]
            logger.info(f"[DEBUG] Simplified message length: {len(simplified_messages[0]['content'])}")

            # Calculate max_tokens for fallback attempt too
            fallback_input_tokens: int = estimate_token_count(simplified_messages, cfg.smart_llm_model)
            fallback_max_output_tokens: int = max(512, min(cfg.smart_token_limit, model_context_limit - fallback_input_tokens - 500))
            logger.info(f"[DEBUG] Fallback input tokens: {fallback_input_tokens}, Max output: {fallback_max_output_tokens}")

            report = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=simplified_messages,
                temperature=0.35,
                llm_provider=cfg.smart_llm_provider,
                stream=True,
                websocket=websocket,
                max_tokens=fallback_max_output_tokens,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
                cfg=cfg,
            )
            # DEBUG: Log successful fallback completion
            logger.info(f"[DEBUG] Fallback attempt successful, report length: {len(report)}")
            logger.info(f"[DEBUG] Report starts with: {report[:100]}...")

            # DEBUG: Check for problematic responses in fallback
            if "I'm sorry, but I cannot provide a response to this task" in report:
                logger.warning("[DEBUG] Detected error pattern in fallback report response")
                logger.warning(f"[DEBUG] Full fallback response: {report}")

        except Exception as e2:
            print(f"Error in generate_report fallback: {e2.__class__.__name__}: {e2}")
            logger.error(f"[DEBUG] Fallback attempt also failed: {e2.__class__.__name__}: {e2}")
            logger.error(f"[DEBUG] Fallback traceback: {traceback.format_exc()}")

    # DEBUG: Log function end
    logger.info(f"[DEBUG] Finished generate_report, returning report of length: {len(report)}")
    return report


async def generate_report_with_rag(
    query: str,
    context: str | list[dict[str, Any]],
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket: WebSocket,
    cfg: Config,
    memory: Any,  # Memory/VectorStore instance
    main_topic: str = "",
    existing_headers: list[str] | None = None,
    relevant_written_contents: list[str] | None = None,
    cost_callback: Callable | None = None,
    custom_prompt: str | None = None,
    headers: dict[str, str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs: dict[str, Any],
) -> str:
    """Generates a comprehensive report using RAG (Retrieval-Augmented Generation).

    This function implements proper RAG architecture by:
    1. Storing all research data in vector store
    2. Generating report sections iteratively
    3. Retrieving relevant context for each section
    4. Building comprehensive reports without token limit constraints

    Args:
        query: The research query
        context: The research context (can be massive)
        memory: Memory/VectorStore instance for RAG
        ... (other args same as generate_report)

    Returns:
        A comprehensive report generated using RAG
    """
    import logging

    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import InMemoryVectorStore

    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"[RAG] Starting RAG-based report generation for query: {query[:50]}...")

    existing_headers = [] if existing_headers is None else existing_headers
    relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents

    # Step 1: Prepare and store all research data in vector store
    logger.info("[RAG] Preparing vector store with context data...")

    # Convert context to text chunks for vector storage
    if isinstance(context, str):
        text_content: str = context
    elif isinstance(context, list):
        # Extract text from list of dicts
        text_parts: list[str] = []
        for item in context:
            if isinstance(item, dict):
                if 'raw_content' in item:
                    text_parts.append(item['raw_content'])
                elif 'content' in item:
                    text_parts.append(item['content'])
                else:
                    text_parts.append(str(item))
            else:
                text_parts.append(str(item))
        text_content = "\n\n".join(text_parts)
    else:
        text_content = str(context)

    logger.info(f"[RAG] Total context length: {len(text_content)} characters")

    # Create vector store if not provided
    vector_store = None
    if hasattr(memory, 'get_embeddings'):
        embeddings: Any = memory.get_embeddings()
        vector_store = InMemoryVectorStore(embeddings)

        # Split text into chunks for vector storage
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=getattr(cfg, 'rag_chunk_size', 2000),  # Use config value
            chunk_overlap=getattr(cfg, 'rag_chunk_overlap', 200),  # Use config value
            length_function=len,
        )
        chunks: list[str] = text_splitter.split_text(text_content)
        logger.info(f"[RAG] Split context into {len(chunks)} chunks")

        # Add chunks to vector store
        vector_store.add_texts(chunks)
        logger.info(f"[RAG] Added {len(chunks)} chunks to vector store")

    # Step 2: Generate report outline/structure
    logger.info("[RAG] Generating report structure...")

    outline_prompt: str = f"""Based on the research query: "{query}"

Generate a detailed outline for a comprehensive report. Include:
1. Introduction
2. 5-8 main sections with descriptive titles
3. Conclusion

Format as a simple list:
- Introduction
- Section 1: [Title]
- Section 2: [Title]
...
- Conclusion

Focus on creating logical, comprehensive coverage of the topic."""

    try:
        outline_response: str = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": agent_role_prompt},
                {"role": "user", "content": outline_prompt}
            ],
            temperature=0.3,
            llm_provider=cfg.smart_llm_provider,
            max_tokens=1000,  # Small limit for outline only
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            cfg=cfg,
        )

        # Parse outline into sections
        sections: list[str] = []
        for line in outline_response.split('\n'):
            line: str = line.strip()
            if line and (line.startswith('-') or line.startswith('•')):
                section_title = line.lstrip('- •').strip()
                if section_title:
                    sections.append(section_title)

        logger.info(f"[RAG] Generated outline with {len(sections)} sections: {sections}")

    except Exception as e:
        logger.error(f"[RAG] Error generating outline: {e}")
        # Fallback to basic structure
        sections = [
            "Introduction",
            "Background and Context",
            "Key Findings",
            "Analysis and Discussion",
            "Implications and Impact",
            "Conclusion"
        ]

    # Step 3: Generate each section using RAG
    report_sections: list[str] = []

    for i, section_title in enumerate(sections):
        logger.info(f"[RAG] Generating section {i+1}/{len(sections)}: {section_title}")

        # Retrieve relevant context for this section
        if vector_store:
            try:
                # Create search query for this section
                section_query: str = f"{query} {section_title}"

                # Retrieve relevant chunks (more than default)
                max_chunks: int = getattr(cfg, 'rag_max_chunks_per_section', 10)
                relevant_docs: list = vector_store.similarity_search(section_query, k=max_chunks)
                section_context: str = "\n\n".join([doc.page_content for doc in relevant_docs])

                logger.info(f"[RAG] Retrieved {len(relevant_docs)} relevant chunks for section: {section_title}")

            except Exception as e:
                logger.error(f"[RAG] Error retrieving context for section {section_title}: {e}")
                # Fallback to truncated original context
                section_context = text_content[:8000]  # Use first 8k chars as fallback
        else:
            # Fallback if no vector store
            section_context = text_content[:8000]

        # Generate this section
        section_prompt: str = f"""Write a comprehensive section for a research report.

Section Title: {section_title}
Main Query: {query}
Report Type: {report_type}

Context Information:
{section_context}

Instructions:
1. Write a detailed, informative section about "{section_title}"
2. Use the provided context information extensively
3. Include specific facts, data, and examples from the context
4. Write 300-800 words for this section
5. Use markdown formatting with appropriate headers
6. Cite sources when possible using markdown links
7. Focus specifically on the "{section_title}" aspect of the topic

Write the section now:"""

        try:
            section_content = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": agent_role_prompt},
                    {"role": "user", "content": section_prompt}
                ],
                temperature=0.4,
                llm_provider=cfg.smart_llm_provider,
                max_tokens=cfg.smart_token_limit,  # Use full token limit per section
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
                cfg=cfg,
            )

            if section_content and len(section_content.strip()) > 50:
                report_sections.append(f"## {section_title}\n\n{section_content}")
                logger.info(f"[RAG] Generated section '{section_title}': {len(section_content)} characters")
            else:
                logger.warning(f"[RAG] Section '{section_title}' generated insufficient content")

        except Exception as e:
            logger.error(f"[RAG] Error generating section '{section_title}': {e}")
            continue

    # Step 4: Combine all sections into final report
    if report_sections:
        final_report: str = f"# {query}\n\n" + "\n\n".join(report_sections)
        logger.info(f"[RAG] Generated comprehensive report: {len(final_report)} characters, {len(report_sections)} sections")
    else:
        logger.error("[RAG] No sections generated, falling back to original method")
        # Fallback to original method
        return await generate_report(
            query, context, agent_role_prompt, report_type, tone,
            report_source, websocket, cfg, main_topic, existing_headers,
            relevant_written_contents, cost_callback, custom_prompt,
            headers, prompt_family, **kwargs
        )

    return final_report
