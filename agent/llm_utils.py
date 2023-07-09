from __future__ import annotations
from fastapi import WebSocket
import time

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
        result = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.choices[0].message["content"]
    else:
        return stream_response(model, messages, temperature, max_tokens, websocket)



def create_embedding_with_ada(text) -> list:
    """Create an embedding with text-ada-002 using the OpenAI SDK"""
    num_retries = 10
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            return openai.Embedding.create(
                input=[text], model="text-embedding-ada-002"
            )["data"][0]["embedding"]
        except RateLimitError:
            pass
        except APIError as e:
            if e.http_status == 502:
                pass
            else:
                raise
            if attempt == num_retries - 1:
                raise
        if CFG.debug_mode:
            print(
                Fore.RED + "Error: ",
                f"API Bad gateway. Waiting {backoff} seconds..." + Fore.RESET,
            )
        time.sleep(backoff)

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
