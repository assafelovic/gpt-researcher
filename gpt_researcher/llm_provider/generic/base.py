import importlib
import subprocess
import sys
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
    "openrouter"
}

NO_SUPPORT_TEMPERATURE_MODELS = [
    "deepseek/deepseek-reasoner",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1",
    "o1-2024-12-17",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o1-preview"
]

SUPPORT_REASONING_EFFORT_MODELS = [
    "o3-mini",
    "o3-mini-2025-01-31"
]

class ReasoningEfforts(Enum):
    High = "high"
    Medium = "medium"
    Low = "low"

class GenericLLMProvider:

    def __init__(self, llm):
        self.llm = llm

    @classmethod
    def from_provider(cls, provider: str, **kwargs: Any):
        if provider == "openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            _check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(**kwargs)
        elif provider == "azure_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI

            if "model" in kwargs:
                model_name = kwargs.get("model", None)
                kwargs = {"azure_deployment": model_name, **kwargs}

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
            _check_pkg("langchain_dashscope")
            from langchain_dashscope import ChatDashScope

            llm = ChatDashScope(**kwargs)
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
                     openai_api_key=os.environ["OPENROUTER_API_KEY"],
                     rate_limiter=rate_limiter,
                     **kwargs
                )
        
        else:
            supported = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(
                f"Unsupported {provider}.\n\nSupported model providers are: {supported}"
            )
        return cls(llm)


    async def get_chat_response(self, messages, stream, websocket=None):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            output = await self.llm.ainvoke(messages)

            return output.content

        else:
            return await self.stream_response(messages, websocket)

    async def stream_response(self, messages, websocket=None):
        paragraph = ""
        response = ""

        # Streaming the response using the chain astream method from langchain
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content is not None:
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
        else:
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
