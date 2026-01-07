import aiofiles
import asyncio
import importlib
import json
import subprocess
import sys
import traceback
from typing import Any
from colorama import Fore, Style, init
import os
from enum import Enum

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
        # Best-effort usage tracking (prompt/completion/total tokens) from LangChain responses
        self.last_usage: dict[str, int] | None = None
        # Provider name (e.g. "openai", "azure_openai") for provider-specific behaviors
        self.provider_name: str | None = None

    def _set_last_usage_from_message(self, msg: Any) -> None:
        """
        Try to extract token usage from LangChain message objects.
        Supports both non-stream (AIMessage) and stream chunks (AIMessageChunk).
        """
        def _set(pt: Any, ct: Any, tt: Any = None) -> None:
            if isinstance(pt, int) and isinstance(ct, int):
                self.last_usage = {
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "total_tokens": int(tt) if isinstance(tt, int) else (pt + ct),
                }

        try:
            usage = getattr(msg, "usage_metadata", None)
            if isinstance(usage, dict):
                _set(usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens"))
                if self.last_usage:
                    return

            # Some LangChain integrations attach usage in response_metadata
            resp_meta = getattr(msg, "response_metadata", None)
            if isinstance(resp_meta, dict):
                token_usage = resp_meta.get("token_usage") or resp_meta.get("usage") or resp_meta.get("usage_metadata")
                if isinstance(token_usage, dict):
                    _set(token_usage.get("prompt_tokens"), token_usage.get("completion_tokens"), token_usage.get("total_tokens"))
        except Exception:
            return
    @classmethod
    def from_provider(cls, provider: str, chat_log: str | None = None, verbose: bool=True, **kwargs: Any):
        if provider == "openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            # Support custom OpenAI-compatible APIs via OPENAI_BASE_URL
            if "openai_api_base" not in kwargs and os.environ.get("OPENAI_BASE_URL"):
                kwargs["openai_api_base"] = os.environ["OPENAI_BASE_URL"]

            llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            _check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(**kwargs)
        elif provider == "azure_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI

            # 获取部署名称，用于查找对应的 endpoint 和 API 版本
            deployment_name = None
            if "model" in kwargs:
                deployment_name = kwargs.get("model", None)
                kwargs = {"azure_deployment": deployment_name, **kwargs}
            
            # 支持为每个部署单独配置 endpoint（如果不同部署在不同的 Azure 资源上）
            # 格式：AZURE_OPENAI_ENDPOINT_<deployment_name>
            if "azure_endpoint" not in kwargs:
                if deployment_name:
                    # 尝试多种格式：
                    # 1. 连字符替换为下划线，点号保留：gpt-5.2-chat -> gpt_5.2_chat
                    # 2. 连字符和点号都替换为下划线：gpt-5.2-chat -> gpt_5_2_chat
                    # 3. 原始格式（带连字符）：gpt-5.2-chat
                    deployment_name_underscore = deployment_name.replace('-', '_')  # gpt_5.2_chat
                    deployment_name_all_underscore = deployment_name.replace('-', '_').replace('.', '_')  # gpt_5_2_chat
                    
                    azure_endpoint = (
                        os.environ.get(f"AZURE_OPENAI_ENDPOINT_{deployment_name_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_ENDPOINT_{deployment_name_all_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_ENDPOINT_{deployment_name}")
                    )
                    if azure_endpoint:
                        kwargs["azure_endpoint"] = azure_endpoint
                
                # 如果没有部署特定的 endpoint，使用通用 endpoint
                if "azure_endpoint" not in kwargs:
                    kwargs["azure_endpoint"] = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            
            # 支持为每个部署单独配置 API Key（如果不同部署使用不同的 key）
            # 格式：AZURE_OPENAI_API_KEY_<deployment_name>
            if "openai_api_key" not in kwargs:
                if deployment_name:
                    # 尝试多种格式（与 endpoint 相同）
                    deployment_name_underscore = deployment_name.replace('-', '_')  # gpt_5.2_chat
                    deployment_name_all_underscore = deployment_name.replace('-', '_').replace('.', '_')  # gpt_5_2_chat
                    
                    api_key = (
                        os.environ.get(f"AZURE_OPENAI_API_KEY_{deployment_name_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_API_KEY_{deployment_name_all_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_API_KEY_{deployment_name}")
                    )
                    if api_key:
                        kwargs["openai_api_key"] = api_key
                
                # 如果没有部署特定的 key，使用通用 key
                if "openai_api_key" not in kwargs:
                    kwargs["openai_api_key"] = os.environ.get("AZURE_OPENAI_API_KEY", "")
            
            # 支持为每个部署单独配置 API 版本
            # 格式：AZURE_OPENAI_API_VERSION_<deployment_name>
            if "api_version" not in kwargs:
                if deployment_name:
                    # 尝试多种格式（与 endpoint 相同）
                    deployment_name_underscore = deployment_name.replace('-', '_')  # gpt_5.2_chat
                    deployment_name_all_underscore = deployment_name.replace('-', '_').replace('.', '_')  # gpt_5_2_chat
                    
                    api_version = (
                        os.environ.get(f"AZURE_OPENAI_API_VERSION_{deployment_name_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_API_VERSION_{deployment_name_all_underscore}") or
                        os.environ.get(f"AZURE_OPENAI_API_VERSION_{deployment_name}")
                    )
                else:
                    api_version = None
                
                # 如果没有部署特定的版本，使用通用版本
                if not api_version:
                    api_version = os.environ.get("AZURE_OPENAI_API_VERSION") or os.environ.get("OPENAI_API_VERSION", "2024-05-01-preview")
                
                kwargs["api_version"] = api_version

            # 添加超时设置，避免网络问题导致无限等待
            if "timeout" not in kwargs:
                kwargs["timeout"] = 180  # 3分钟超时
            if "request_timeout" not in kwargs:
                kwargs["request_timeout"] = 180  # 3分钟请求超时
            
            # Some models (e.g., gpt-5.2-chat) don't support custom temperature, only default (1)
            # Remove temperature from kwargs if model doesn't support it
            if deployment_name and "gpt-5.2" in deployment_name.lower():
                kwargs.pop("temperature", None)
            
            llm = AzureChatOpenAI(**kwargs)
        elif provider == "cohere":
            _check_pkg("langchain_cohere")
            from langchain_cohere import ChatCohere

            llm = ChatCohere(**kwargs)
        elif provider == "google_vertexai":
            _check_pkg("langchain_google_vertexai")
            from langchain_google_vertexai import ChatVertexAI

            llm = ChatVertexAI(**kwargs)
        elif provider == "google_genai":
            _check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(**kwargs)
        elif provider == "fireworks":
            _check_pkg("langchain_fireworks")
            from langchain_fireworks import ChatFireworks

            llm = ChatFireworks(**kwargs)
        elif provider == "ollama":
            _check_pkg("langchain_community")
            _check_pkg("langchain_ollama")
            from langchain_ollama import ChatOllama

            llm = ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)
        elif provider == "together":
            _check_pkg("langchain_together")
            from langchain_together import ChatTogether

            llm = ChatTogether(**kwargs)
        elif provider == "mistralai":
            _check_pkg("langchain_mistralai")
            from langchain_mistralai import ChatMistralAI

            llm = ChatMistralAI(**kwargs)
        elif provider == "huggingface":
            _check_pkg("langchain_huggingface")
            from langchain_huggingface import ChatHuggingFace

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, **kwargs}
            llm = ChatHuggingFace(**kwargs)
        elif provider == "groq":
            _check_pkg("langchain_groq")
            from langchain_groq import ChatGroq

            llm = ChatGroq(**kwargs)
        elif provider == "bedrock":
            _check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, "model_kwargs": kwargs}
            llm = ChatBedrock(**kwargs)
        elif provider == "dashscope":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
                     openai_api_key=os.environ["DASHSCOPE_API_KEY"],
                     **kwargs
                )
        elif provider == "xai":
            _check_pkg("langchain_xai")
            from langchain_xai import ChatXAI

            llm = ChatXAI(**kwargs)
        elif provider == "deepseek":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.deepseek.com',
                     openai_api_key=os.environ["DEEPSEEK_API_KEY"],
                     **kwargs
                )
        elif provider == "litellm":
            _check_pkg("langchain_community")
            from langchain_community.chat_models.litellm import ChatLiteLLM

            llm = ChatLiteLLM(**kwargs)
        elif provider == "gigachat":
            _check_pkg("langchain_gigachat")
            from langchain_gigachat.chat_models import GigaChat

            kwargs.pop("model", None) # Use env GIGACHAT_MODEL=GigaChat-Max
            llm = GigaChat(**kwargs)
        elif provider == "openrouter":
            _check_pkg("langchain_openai")
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
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                openai_api_key=os.environ["VLLM_OPENAI_API_KEY"],
                openai_api_base=os.environ["VLLM_OPENAI_API_BASE"],
                **kwargs
            )
        elif provider == "aimlapi":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.aimlapi.com/v1',
                             openai_api_key=os.environ["AIMLAPI_API_KEY"],
                             **kwargs
                             )
        elif provider == 'netmind':
            _check_pkg("langchain_netmind")
            from langchain_netmind import ChatNetmind

            llm = ChatNetmind(**kwargs)
        else:
            supported = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(
                f"Unsupported {provider}.\n\nSupported model providers are: {supported}"
            )
        inst = cls(llm, chat_log, verbose=verbose)
        inst.provider_name = provider
        return inst


    async def get_chat_response(self, messages, stream, websocket=None, **kwargs):
        # Reset usage per call
        self.last_usage = None
        # For OpenAI-compatible providers, request usage data in streaming mode when supported.
        # LangChain OpenAI supports stream_options={"include_usage": True}.
        if stream and self.provider_name in {"openai", "azure_openai"}:
            kwargs.setdefault("stream_options", {"include_usage": True})
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            output = await self.llm.ainvoke(messages, **kwargs)

            res = output.content
            self._set_last_usage_from_message(output)

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
            if content is not None:
                response += content
                paragraph += content
                if "\n" in paragraph:
                    await self._send_output(paragraph, websocket)
                    paragraph = ""
            # Some providers may only attach usage metadata on the final chunk
            self._set_last_usage_from_message(chunk)

        if paragraph:
            await self._send_output(paragraph, websocket)

        return response

    async def _send_output(self, content, websocket=None):
        if websocket is not None:
            await websocket.send_json({"type": "report", "output": content})
        elif self.verbose:
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")


def _check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        # Import colorama and initialize it
        init(autoreset=True)

        try:
            print(f"{Fore.YELLOW}Installing {pkg_kebab}...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg_kebab])
            print(f"{Fore.GREEN}Successfully installed {pkg_kebab}{Style.RESET_ALL}")

            # Try importing again after install
            importlib.import_module(pkg)

        except subprocess.CalledProcessError:
            raise ImportError(
                Fore.RED + f"Failed to install {pkg_kebab}. Please install manually with "
                f"`pip install -U {pkg_kebab}`"
            )
