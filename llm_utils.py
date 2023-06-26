from __future__ import annotations

import time
from ast import List

import openai
from colorama import Fore, Style
from openai.error import APIError, RateLimitError

from config import Config

CFG = Config()

openai.api_key = CFG.openai_api_key

# Overly simple abstraction until we create something better
# simple retry mechanism when getting a rate error or a bad gateway
def create_chat_completion(
    messages: list,  # type: ignore
    model: str | None = None,
    temperature: float = CFG.temperature,
    max_tokens: int | None = None,
    stream: bool | None = False,
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
    response = None
    num_retries = 10
    warned_user = False
    result = ""
    if CFG.debug_mode:
        print(
            Fore.GREEN
            + f"Creating chat completion with model {model}, temperature {temperature},"
            f" max_tokens {max_tokens}" + Fore.RESET
        )
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            if not stream:
                result = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                response = result.choices[0].message["content"]
            else:
                response = stream_response(model, messages, temperature, max_tokens)
            break
        except RateLimitError:
            if CFG.debug_mode:
                print(
                    Fore.RED + "Error: ",
                    f"Reached rate limit, passing..." + Fore.RESET,
                )
            if not warned_user:
                warned_user = True
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
    if response is None:
        if CFG.debug_mode:
            raise RuntimeError(f"Failed to get response after {num_retries} retries")
        else:
            quit(1)

    return response


def create_embedding_with_ada(text) -> list:
    """Create an embedding with text-ada-002 using the OpenAI SDK"""
    num_retries = 10
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            if CFG.use_azure:
                return openai.Embedding.create(
                    input=[text],
                    engine=CFG.get_azure_deployment_id_for_model(
                        "text-embedding-ada-002"
                    ),
                )["data"][0]["embedding"]
            else:
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

def stream_response(model, messages, temperature, max_tokens):
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
                print(f"{paragraph}\nTotal response words: {len(response.split())}")
                paragraph = ""
    print(f"streaming response complete")
    return response
