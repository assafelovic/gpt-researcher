# llm.py
# libraries
from __future__ import annotations

import json
import logging
from typing import Optional

from colorama import Fore, Style
from fastapi import WebSocket
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from sf_researcher.master.prompts import auto_agent_instructions, generate_subtopics_prompt, generate_directors_prompt, generate_director_sobject_prompt, generate_company_sobject_prompt

from .validators import Subtopics, Directors, DirectorSobject, CompanySobject

from langchain_core.output_parsers.openai_tools import PydanticToolsParser, JsonOutputToolsParser
from langchain_core.prompts import ChatPromptTemplate


def get_provider(llm_provider):
    match llm_provider:
        case "openai":
            from ..llm_provider import OpenAIProvider
            llm_provider = OpenAIProvider
        case "azureopenai":
            from ..llm_provider import AzureOpenAIProvider
            llm_provider = AzureOpenAIProvider
        case "google":
            from ..llm_provider import GoogleProvider
            llm_provider = GoogleProvider

        case _:
            raise Exception("LLM provider not found.")

    return llm_provider

async def create_chat_completion(
        messages: list,  # type: ignore
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        llm_provider: Optional[str] = None,
        stream: Optional[bool] = False,
        websocket: WebSocket | None = None,
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.
        stream (bool, optional): Whether to stream the response. Defaults to False.
        llm_provider (str, optional): The LLM Provider to use.
        webocket (WebSocket): The websocket used in the currect request
    Returns:
        str: The response from the chat completion
    """

    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 8001:
        raise ValueError(
            f"Max tokens cannot be more than 8001, but got {max_tokens}")

    # Get the provider from supported providers
    ProviderClass = get_provider(llm_provider)
    provider = ProviderClass(
        model,
        temperature,
        max_tokens
    )

    # create response
    for _ in range(10):  # maximum of 10 attempts
        response = await provider.get_chat_response(
            messages, stream, websocket
        )
        return response

    logging.error("Failed to get response from OpenAI API")
    raise RuntimeError("Failed to get response from OpenAI API")

def choose_agent(smart_llm_model: str, llm_provider: str, task: str) -> dict:
    """Determines what server should be used
    Args:
        task (str): The research question the user asked
        smart_llm_model (str): the llm model to be used
        llm_provider (str): the llm provider used
    Returns:
        server - The server that will be used
        agent_role_prompt (str): The prompt for the server
    """
    try:
        response = create_chat_completion(
            model=smart_llm_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {task}"}],
            temperature=0,
            llm_provider=llm_provider
        )
        agent_dict = json.loads(response)
        print(f"Agent: {agent_dict.get('server')}")
        return agent_dict
    except Exception as e:
        print(f"{Fore.RED}Error in choose_agent: {e}{Style.RESET_ALL}")
        return {"server": "Default Agent",
                "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."}

async def construct_subtopics(task: str, data: str, config, subtopics: list = []) -> list:
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=generate_subtopics_prompt(),
            input_variables=["task", "data", "subtopics", "max_subtopics"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()},
        )

        print(f"\n🤖 Calling {config.smart_llm_model}...\n")

        if config.llm_provider == "openai":
            model = ChatOpenAI(model=config.smart_llm_model)
        elif config.llm_provider == "azureopenai":
            from langchain_openai import AzureChatOpenAI
            model = AzureChatOpenAI(model=config.smart_llm_model)
        else:
            return []

        chain = prompt | model | parser

        output = chain.invoke({
            "task": task,
            "data": data,
            "subtopics": subtopics,
            "max_subtopics": config.max_subtopics
        })
        print("LLM input for construct_subtopics:")
        print(f"Task: {task}")
        print(f"Data: {data}")
        print(f"Subtopics: {subtopics}")
        print(f"Max Subtopics: {config.max_subtopics}")
        print("LLM output for construct_subtopics:")
        print(output)
        return output

    except Exception as e:
        print("Exception in parsing subtopics : ", e)
        return subtopics
        
async def construct_directors2(task: str, data: str, config) -> list:
    try:
        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        if config.llm_provider == "openai":
            model = ChatOpenAI(model=config.fast_llm_model)
        elif config.llm_provider == "azureopenai":
            from langchain_openai import AzureChatOpenAI
            model = AzureChatOpenAI(model=config.fast_llm_model)
        else:
            return []
        
        llm = ChatOpenAI(model, temperature=0.55)
        
        # Bind Directors tool to LLM, forcing it to always be called
        llm_with_tools = llm.bind_tools([Directors], tool_choice="Directors")

        query = generate_directors_prompt(task, data)

        chain = llm_with_tools | PydanticToolsParser(tools=[Directors])
        output = chain.invoke(query)
        
        print("LLM input for construct_directors:")
        print(f"Task: {task}") 
        print(f"Data: {data}")
        print("LLM output for construct_directors:")
        print(output)

        return output
    except Exception as e:
        print("Exception in parsing directors : ", e)
        return []

async def construct_directors(task: str, data: str, config) -> Directors:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), ("user", generate_directors_prompt())]
        )
        parser = PydanticToolsParser(tools=[Directors], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([Directors], tool_choice="Directors")
        
        print("Construct Directors Output Tool Schema: ", model.kwargs["tools"])
        chain = prompt | model | parser
        output = chain.invoke({
            "task": task,
            "data": data
        })

        print(output)
        return output
    except Exception as e:
        print("Exception in parsing directors name list: ", e)
        return []

async def construct_director_sobject(sub_query: str, visited_urls: str, company: str, context: str, config) -> DirectorSobject:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), ("user", generate_director_sobject_prompt())]
        )
        parser = PydanticToolsParser(tools=[DirectorSobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([DirectorSobject], tool_choice="DirectorSobject")

        chain = prompt | model | parser
        print("Construct Director SObject Output Tool Schema: ", model.kwargs["tools"])
        output = chain.invoke({
            "sub_query": sub_query,
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print("Construct Director SObject Output: ", output)
        return output

    except Exception as e:
        print("Exception in parsing director SObjects: ", e)
        return []

async def construct_company_sobject(subtopic_report: str, visited_urls: str, company: str, context: str, config) -> CompanySobject:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), ("user", generate_company_sobject_prompt())]
        )
        parser = PydanticToolsParser(tools=[CompanySobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([CompanySobject], tool_choice="CompanySobject")

        chain = prompt | model | parser
        print("Construct Company SObject Output Tool Schema: ", model.kwargs["tools"])
        output = chain.invoke({
            "subtopic_report": subtopic_report, 
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print("Construct Company SObject Output: ", output)
        return output
    except Exception as e:
        print("Exception in parsing company SObject: ", e)
        return None