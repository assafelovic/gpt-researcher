from __future__ import annotations

import json

from fastapi import WebSocket
import time
from litellm import completion
import openai
from colorama import Fore, Style
from openai.error import APIError, RateLimitError

from config import Config

CFG = Config()

openai.api_key = CFG.openai_api_key

from typing import Optional
import logging

def create_chat_completion(
    messages: list,  # type: ignore
    model: Optional[str] = None,
    temperature: float = CFG.temperature,
    max_tokens: Optional[int] = None,
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
    Returns:
        str: The response from the chat completion
    """

    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 8001:
        raise ValueError(f"Max tokens cannot be more than 8001, but got {max_tokens}")
    if stream and websocket is None:
        raise ValueError("Websocket cannot be None when stream is True")

    # create response
    for attempt in range(10):  # maximum of 10 attempts
        try:
            response = send_chat_completion_request(
                messages, model, temperature, max_tokens, stream, websocket
            )
            return response
        except RateLimitError:
            logging.warning("Rate limit reached, backing off...")
            time.sleep(2 ** (attempt + 2))  # exponential backoff
        except APIError as e:
            if e.http_status != 502 or attempt == 9:  # if not Bad Gateway error or final attempt
                raise
            logging.error("API Error: Bad gateway, backing off...")
            time.sleep(2 ** (attempt + 2))  # exponential backoff

    logging.error("Failed to get response after 10 attempts")
    raise RuntimeError("Failed to get response from OpenAI API")


def send_chat_completion_request(
    messages, model, temperature, max_tokens, stream, websocket
):
    if not stream:
        model_fallback_list = ["claude-instant-1", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
        model_fallback_list = [model] + model_fallback_list
        for model in model_fallback_list:
            try:
                result = completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return result.choices[0].message["content"]
            except:
                pass
    else:
        return stream_response(model, messages, temperature, max_tokens, websocket)


async def stream_response(model, messages, temperature, max_tokens, websocket):
    paragraph = ""
    response = ""
    print(f"streaming response...")

    for chunk in openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
    ):
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content is not None:
            response += content
            paragraph += content
            if "\n" in paragraph:
                await websocket.send_json({"type": "report", "output": paragraph})
                paragraph = ""
    print(f"streaming response complete")
    return response


def choose_agent(task: str) -> str:
    """Determines what agent should be used
    Args:
        task (str): The research question the user asked
    Returns:
        agent - The agent that will be used
        agent_role_prompt (str): The prompt for the agent
    """
    try:
        configuration = choose_agent_configuration()

        response = completion(
            model=CFG.smart_llm_model,
            messages=[
                {"role": "user", "content": f"{task}"}],
            functions=configuration,
            temperature=0,
        )
        message = response["choices"][0]["message"]

        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            return {"agent": json.loads(message["function_call"]["arguments"]).get("agent"),
                    "agent_role_prompt": json.loads(message["function_call"]["arguments"]).get("instructions")}
        else:
            return {"agent": "Default Agent",
             "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."}
    except Exception as e:
        print(f"{Fore.RED}Error in choose_agent: {e}{Style.RESET_ALL}")
        return {"agent": "Default Agent",
                "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."}

def choose_agent_configuration():
    configuration = [
        {
            "name": "research",
            "description": "Researches the given topic even if it can't be answered",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description":
                            """
                                Determines the field of the topic and the name of the agent we could use in order to research 
                                about the topic provided.
                                
                                Example of agents:
                                    "Business Analyst Agent", "Finance Agent", "Travel Agent",
                                 "Academic Research Agent", "Computer Security Analyst Agent"
                                 
                                 if an agent for the field required doesn't exist make one up
                                 fit an emoji to every agent before the agent name
                            """,
                    },
                    "instructions": {
                        "type": "string",
                        "description":
                            """
                            each provided agent needs instructions in order to start working,
                            examples for agents and their instructions:
                                    "Finance Agent": "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, impartial, and methodically arranged financial reports based on provided data and trends.",
                                    "Travel Agent": "You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, unbiased, and well-structured travel reports on given locations, including history, attractions, and cultural insights.",
                                    "Academic Research Agent": "You are an AI academic research assistant. Your primary responsibility is to create thorough, academically rigorous, unbiased, and systematically organized reports on a given research topic, following the standards of scholarly work.",
                                    "Business Analyst": "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, insightful, impartial, and systematically structured business reports based on provided business data, market trends, and strategic analysis.",
                                    "Computer Security Analyst Agent": "You are an AI specializing in computer security analysis. Your principal duty is to generate comprehensive, meticulously detailed, impartial, and systematically structured reports on computer security topics. This includes Exploits, Techniques, Threat Actors, and Advanced Persistent Threat (APT) Groups. All produced reports should adhere to the highest standards of scholarly work and provide in-depth insights into the complexities of computer security.",
                                    
                            """,
                    },
                },
                "required": ["agent", "instructions"],
            },
        }
    ]
    return configuration


