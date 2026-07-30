import aiofiles
import asyncio
import json
import os
import traceback
from enum import Enum
from typing import Any

from colorama import Fore, Style

from gpt_researcher.utils.imports import check_pkg

_SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "azure_openai",
    "cohere",
    "google_vertexai",
    "google_genai",
    "fireworks",
    "ollama",
    "together",
    "mistralai",
    "huggingface",
    "groq",
    "bedrock",
    "dashscope",
    "xai",
    "deepseek",
    "litellm",
    "gigachat",
    "openrouter",
    "vllm_openai",
    "aimlapi",
    "netmind",
    "forge",
    "avian",
    "minimax",
}

NO_SUPPORT_TEMPERATURE_MODELS = [
    "deepseek/deepseek-reasoner",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1",
    "o1-2024-12-17",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o1-preview",
    "o3",
    "o3-2025-04-16",
    "o4-mini",
    "o4-mini-2025-04-16",
    # GPT-5 family: OpenAI enforces default temperature only
    "gpt-5",
    "gpt-5-mini",
    # Claude 4.x family: Anthropic deprecates temperature on these models
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
    "claude-sonnet-4-6",
    "claude-opus-4-5",
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
]

SUPPORT_REASONING_EFFORT_MODELS = [
    "o3-mini",
    "o3-mini-2025-01-31",
    "o3",
    "o3-2025-04-16",
    "o4-mini",
    "o4-mini-2025-04-16",
]

class ReasoningEfforts(Enum):
    High = "high"
    Medium = "medium"
    Low = "low"


class ChatLogger:
    """Helper utility to log all chat requests and their corresponding responses
    plus the stack trace leading to the call.
    """

    def __init__(self, fname: str):
        self.fname = fname
        self._lock = asyncio.Lock()

    async def log_request(self, messages, response):
        async with self._lock:
            async with aiofiles.open(self.fname, mode="a", encoding="utf-8") as handle:
                await handle.write(json.dumps({
                    "messages": messages,
                    "response": response,
                    "stacktrace": traceback.format_exc()
                }) + "\n")

class GenericLLMProvider:

    def __init__(self, llm, chat_log: str | None = None,  verbose: bool = True):
        self.llm = llm
        self.chat_logger = ChatLogger(chat_log) if chat_log else None
        self.verbose = verbose
    @classmethod
    def from_provider(cls, provider: str, chat_log: str | None = None, verbose: bool=True, **kwargs: Any):
        if provider == "openai":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            # Support custom OpenAI-compatible APIs via OPENAI_BASE_URL
            if "openai_api_base" not in kwargs and os.environ.get("OPENAI_BASE_URL"):
                kwargs["openai_api_base"] = os.environ["OPENAI_BASE_URL"]

            llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(**kwargs)
        elif provider == "azure_openai":
            check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI

            if "model" in kwargs:
                model_name = kwargs.get("model", None)
                kwargs = {"azure_deployment": model_name, **kwargs}

            llm = AzureChatOpenAI(**kwargs)
        elif provider == "cohere":
            check_pkg("langchain_cohere")
            from langchain_cohere import ChatCohere

            llm = ChatCohere(**kwargs)
        elif provider == "google_vertexai":
            check_pkg("langchain_google_vertexai")
            from langchain_google_vertexai import ChatVertexAI

            llm = ChatVertexAI(**kwargs)
        elif provider == "google_genai":
            check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(**kwargs)
        elif provider == "fireworks":
            check_pkg("langchain_fireworks")
            from langchain_fireworks import ChatFireworks

            llm = ChatFireworks(**kwargs)
        elif provider == "ollama":
            check_pkg("langchain_community")
            check_pkg("langchain_ollama")
            from langchain_ollama import ChatOllama

            llm = ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)
        elif provider == "together":
            check_pkg("langchain_together")
            from langchain_together import ChatTogether

            llm = ChatTogether(**kwargs)
        elif provider == "mistralai":
            check_pkg("langchain_mistralai")
            from langchain_mistralai import ChatMistralAI

            llm = ChatMistralAI(**kwargs)
        elif provider == "huggingface":
            check_pkg("langchain_huggingface")
            from langchain_huggingface import ChatHuggingFace

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, **kwargs}
            llm = ChatHuggingFace(**kwargs)
        elif provider == "groq":
            check_pkg("langchain_groq")
            from langchain_groq import ChatGroq

            llm = ChatGroq(**kwargs)
        elif provider == "bedrock":
            check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, "model_kwargs": kwargs}
            llm = ChatBedrock(**kwargs)
        elif provider == "dashscope":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
                     openai_api_key=os.environ["DASHSCOPE_API_KEY"],
                     **kwargs
                )
        elif provider == "xai":
            check_pkg("langchain_xai")
            from langchain_xai import ChatXAI

            llm = ChatXAI(**kwargs)
        elif provider == "deepseek":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.deepseek.com',
                     openai_api_key=os.environ["DEEPSEEK_API_KEY"],
                     **kwargs
                )
        elif provider == "litellm":
            check_pkg("langchain_community")
            from langchain_community.chat_models.litellm import ChatLiteLLM

            llm = ChatLiteLLM(**kwargs)
        elif provider == "gigachat":
            check_pkg("langchain_gigachat")
            from langchain_gigachat.chat_models import GigaChat

            kwargs.pop("model", None) # Use env GIGACHAT_MODEL=GigaChat-Max
            llm = GigaChat(**kwargs)
        elif provider == "openrouter":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            from langchain_core.rate_limiters import InMemoryRateLimiter

            rps = float(os.environ["OPENROUTER_LIMIT_RPS"]) if "OPENROUTER_LIMIT_RPS" in os.environ else 1.0

            rate_limiter = InMemoryRateLimiter(
                requests_per_second=rps,
                check_every_n_seconds=0.1,
                max_bucket_size=10,
            )

            llm = ChatOpenAI(openai_api_base='https://openrouter.ai/api/v1',
                     request_timeout=180,
                     openai_api_key=os.environ["OPENROUTER_API_KEY"],
                     rate_limiter=rate_limiter,
                     **kwargs
                )
        elif provider == "vllm_openai":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                openai_api_key=os.environ["VLLM_OPENAI_API_KEY"],
                openai_api_base=os.environ["VLLM_OPENAI_API_BASE"],
                **kwargs
            )
        elif provider == "aimlapi":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.aimlapi.com/v1',
                             openai_api_key=os.environ["AIMLAPI_API_KEY"],
                             **kwargs
                             )
        elif provider == "forge":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.forge.tensorblock.co/v1',
                     openai_api_key=os.environ["FORGE_API_KEY"],
                     **kwargs
                )
        elif provider == "avian":
            check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.avian.io/v1',
                     openai_api_key=os.environ["AVIAN_API_KEY"],
                     **kwargs
                )
        elif provider == "minimax":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.minimax.io/v1',
                     openai_api_key=os.environ["MINIMAX_API_KEY"],
                     **kwargs
                )
        elif provider == 'netmind':
            check_pkg("langchain_netmind")
            from langchain_netmind import ChatNetmind

            llm = ChatNetmind(**kwargs)
        else:
            supported = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(
                f"Unsupported {provider}.\n\nSupported model providers are: {supported}"
            )
        return cls(llm, chat_log, verbose=verbose)


    async def get_chat_response(self, messages, stream, websocket=None, **kwargs):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            output = await self.llm.ainvoke(messages, **kwargs)

            res = output.content

        else:
            res = await self.stream_response(messages, websocket, **kwargs)

        if self.chat_logger:
            await self.chat_logger.log_request(messages, res)

        return res

    async def stream_response(self, messages, websocket=None, **kwargs):
        paragraph = ""
        response = ""

        # Streaming the response using the chain astream method from langchain
        async for chunk in self.llm.astream(messages, **kwargs):
            content = chunk.content
            if not content:
                continue
            response += content
            paragraph += content
            if "\n" in paragraph:
                await self._send_output(paragraph, websocket)
                paragraph = ""

        if paragraph:
            await self._send_output(paragraph, websocket)

        return response

    async def _send_output(self, content, websocket=None):
        if websocket is not None:
            await websocket.send_json({"type": "report", "output": content})
        elif self.verbose:
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}", flush=True)

