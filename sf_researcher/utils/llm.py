# llm.py
# libraries
from __future__ import annotations

import os
import json
import logging
from typing import Optional

from colorama import Fore, Style
from fastapi import WebSocket
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from sf_researcher.master.prompts import *
from .validators import *
from dotenv import load_dotenv

load_dotenv()
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

################################################################################################

# INITIAL SETUP

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


################################################################################################

# STRUCTURED OUTPUT CALLS 

async def construct_contacts(company_name: str, data: str, config) -> Contacts:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), 
             ("user", generate_contacts_prompt())]
        )
        parser = PydanticToolsParser(tools=[Contacts], first_tool_only=True)

        print(f"\n🤖 llm.py construct_contacts Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([Contacts], tool_choice="Contacts")
    
        chain = prompt | model | parser
        output = chain.invoke({
            "company_name": company_name,
            "data": data,
            "max_contacts": config.max_contacts
        })
        return output
    except Exception as e:
        print("Exception in parsing directors name list: ", e)
        return []

async def analyze_search_result(search_results, overall_goal: str, config) -> InitialSearchResults:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are a helpful assistant analyzing the relevance of search results."), 
             ("user", generate_search_analysis_prompt())]
        )
        parser = PydanticToolsParser(tools=[InitialSearchResults], first_tool_only=True)

        print(f"\n🤖 llm.py analyze_search_result Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([InitialSearchResults], tool_choice="InitialSearchResults")
    
        chain = prompt | model | parser
        output = chain.invoke({
            "overall_goal": overall_goal,
            "search_results": search_results
        })
        return output
    except Exception as e:
        print("Exception in analyzing search result: ", e)
        return []

################################################################################################

# CONSTRUCT SOBJECT TOOL CALLS        

async def construct_contact_sobject(contact_name: str, visited_urls: str, company: str, context: str, report_type: str, config) -> ContactSobject:
    if report_type == "compliance_contact_report":
        generate_prompt = generate_compliance_contact_sobject_prompt()
    else:
        generate_prompt = generate_sales_contact_sobject_prompt()
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of contacts names"), ("user", generate_prompt)]
        )
        parser = PydanticToolsParser(tools=[ContactSobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([ContactSobject], tool_choice="ContactSobject")

        chain = prompt | model | parser

        output = chain.invoke({
            "contact_name": contact_name,
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print(f"\n🤖 llm.py Compliance Contact SObject: {output}\n")
        return output

    except Exception as e:
        print("\n🤖 llm.py Exception in parsing Compliance Contact SObjects: ", e)
        return []

async def construct_contact_sobject(contact_name: str, visited_urls: str, company: str, context: str, report_type: str, config) -> ContactSobject:
    if report_type == "compliance_contact_report":
        generate_prompt = generate_compliance_contact_sobject_prompt()
    else:
        generate_prompt = generate_sales_contact_sobject_prompt()
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of contacts names"), ("user", generate_prompt)]
        )
        parser = PydanticToolsParser(tools=[ContactSobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([ContactSobject], tool_choice="ContactSobject")

        chain = prompt | model | parser
        
        output = chain.invoke({
            "contact_name": contact_name,
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print(f"\n🤖 llm.py Construct Compliance Contact SObject : {output}\n")
        return output

    except Exception as e:
        print("\n🤖 llm.py Exception in parsing Compliance Contact SObjects: ", e)
        return []

async def construct_compliance_company_sobject(visited_urls: str, company: str, context: str, config) -> ComplianceCompanySobject:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), ("user", generate_compliance_company_sobject_prompt())]
        )
        parser = PydanticToolsParser(tools=[ComplianceCompanySobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([ComplianceCompanySobject], tool_choice="ComplianceCompanySobject")

        chain = prompt | model | parser

        output = chain.invoke({
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print(f"\n🤖 llm.py Construct Compliance Company SObject Output: {output}\n")
        return output
    except Exception as e:
        print("Exception in parsing company SObject: ", e)
        return None
    
async def construct_sales_company_sobject(visited_urls: str, company: str, context: str, config) -> SalesCompanySobject:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are helpful assistant, helping to extract a list of directors names"), ("user", generate_compliance_company_sobject_prompt())]
        )
        parser = PydanticToolsParser(tools=[SalesCompanySobject], first_tool_only=True)

        print(f"\n🤖 Calling {config.fast_llm_model}...\n")
        model = ChatOpenAI(model=config.fast_llm_model, temperature=0).bind_tools([SalesCompanySobject], tool_choice="SalesCompanySobject")

        chain = prompt | model | parser

        output = chain.invoke({
            "visited_urls": visited_urls,
            "company": company,
            "context": context
        })
        print(f"\n🤖 llm.py Construct Sales Company SObject Output: {output}\n")
        return output
    except Exception as e:
        print("Exception in parsing company SObject: ", e)
        return None