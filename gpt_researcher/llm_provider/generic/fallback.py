"""LLM Provider with Fallback Support."""

from __future__ import annotations

import logging
import os
from typing import Any, TypeVar

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

logger: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T")


class FallbackGenericLLMProvider(GenericLLMProvider):
    """LLM Provider with fallback support."""

    def __init__(
        self,
        llm: Any,
        fallback_providers: list[GenericLLMProvider] = None,
        chat_log: str | None = None,
        verbose: bool = True,
    ):
        """Initialize the fallback LLM provider.

        Args:
            llm: Primary LLM provider
            fallback_providers: List of fallback LLM providers
            chat_log: Path to chat log
            verbose: Verbosity level
        """
        super().__init__(llm, chat_log=chat_log, verbose=verbose)
        self.fallback_providers: list[GenericLLMProvider] = [] if fallback_providers is None else fallback_providers

    @classmethod
    def from_provider_with_fallbacks(
        cls,
        provider: str,
        fallback_models: list[str] = None,
        chat_log: str | None = None,
        verbose: bool = True,
        **kwargs: Any,
    ) -> FallbackGenericLLMProvider:
        """Create a fallback LLM provider from a provider name and fallback model list.

        Args:
            provider: Primary provider name
            fallback_models: List of fallback model strings in format 'provider:model'
            chat_log: Path to chat log
            verbose: Verbosity level
            **kwargs: Additional keyword arguments for the primary provider

        Returns:
            FallbackGenericLLMProvider instance
        """
        # Handle OpenRouter models
        primary_kwargs: dict[str, Any] = kwargs.copy()
        if provider == "openrouter":
            if not os.environ.get("OPENROUTER_API_KEY"):
                logger.warning("OPENROUTER_API_KEY not set. OpenRouter models may not work.")

            # OpenRouter uses the OpenAI API format with a different base URL
            # Pass through to the OpenAI provider with proper configuration
            provider = "openai"
            primary_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            primary_kwargs["api_key"] = os.environ.get("OPENROUTER_API_KEY")

            # Set up model_kwargs (removed transforms as it's not supported by OpenAI client)
            primary_kwargs["model_kwargs"] = primary_kwargs.get("model_kwargs", {})

            # Log the configuration
            logger.info(f"Using OpenRouter as {provider} with custom base_url. Model: {primary_kwargs.get('model')}")

        # Create fallback providers if specified
        fallback_providers: list[GenericLLMProvider] = []
        if fallback_models:
            for fallback_model in fallback_models:
                try:
                    # Standard format "provider:model"
                    if ":" not in fallback_model:
                        logger.warning(f"Skipping invalid fallback model format: {fallback_model}. Expected format: 'provider:model'")
                        continue

                    provider_name, model_name = fallback_model.split(":", 1)

                    # Skip vertexai models if not configured properly
                    if provider_name in ["google_vertexai", "vertexai"]:
                        if not (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GOOGLE_CLOUD_PROJECT")):
                            logger.warning(f"Skipping Google VertexAI model {model_name} because Google Cloud is not configured")
                            continue

                    # Handle provider name mappings and aliases
                    if provider_name == "gemini":
                        provider_name = "google_genai"
                        logger.info(f"Mapping 'gemini' to 'google_genai' provider for {model_name}")

                    # Special handling for OpenRouter models
                    fallback_kwargs: dict[str, Any] = kwargs.copy()
                    if provider_name == "openrouter":
                        if not os.environ.get("OPENROUTER_API_KEY"):
                            logger.warning(f"Skipping OpenRouter model {model_name} because OPENROUTER_API_KEY is not set")
                            continue

                        # OpenRouter models use OpenAI's API with a different base URL
                        provider_name = "openai"
                        fallback_kwargs["base_url"] = "https://openrouter.ai/api/v1"
                        fallback_kwargs["api_key"] = os.environ.get("OPENROUTER_API_KEY")

                        # Set up model_kwargs (removed transforms as it's not supported by OpenAI client)
                        fallback_kwargs["model_kwargs"] = fallback_kwargs.get("model_kwargs", {})

                        logger.info(f"Using OpenRouter model {model_name} via OpenAI provider with custom base_url")

                    # Set the model name and create the provider
                    fallback_kwargs["model"] = model_name

                    # Log the fallback configuration
                    logger.info(f"Initializing fallback provider {provider_name} with model {model_name}")

                    fallback_provider: GenericLLMProvider = GenericLLMProvider.from_provider(
                        provider_name,
                        chat_log=chat_log,
                        verbose=verbose,
                        **fallback_kwargs,
                    )
                    fallback_providers.append(fallback_provider)
                except (ValueError, ImportError) as e:
                    logger.warning(f"Failed to initialize fallback provider {fallback_model}: {e}")

        # Initialize the primary provider
        try:
            primary_provider: GenericLLMProvider = GenericLLMProvider.from_provider(
                provider,
                chat_log=chat_log,
                verbose=verbose,
                **primary_kwargs
            )

            return cls(
                primary_provider.llm,
                fallback_providers=fallback_providers,
                chat_log=chat_log,
                verbose=verbose,
            )
        except Exception as e:
            logger.error(f"Failed to initialize primary provider {provider}: {e}")

            # If we have fallbacks, try to use the first one as primary
            if fallback_providers:
                logger.warning("Using first fallback provider as primary due to initialization failure")
                primary: GenericLLMProvider = fallback_providers.pop(0)
                return cls(
                    primary.llm,
                    fallback_providers=fallback_providers,
                    chat_log=chat_log,
                    verbose=verbose,
                )
            else:
                # No fallbacks available, re-raise the exception
                raise

    async def get_chat_response(
        self,
        messages: list[dict[str, str]],
        stream: bool,
        websocket: Any | None = None,
    ) -> str:
        """Generate LLM response with fallback support.

        Attempts to generate using the primary LLM, and if it fails, tries each fallback in order.

        Args:
            messages: The messages to send to the chat completion
            stream: Whether to stream the response
            websocket: The websocket to use for streaming responses

        Returns:
            The response from the chat completion

        Raises:
            Exception: If all providers fail
        """
        # Try primary provider first
        try:
            return await super().get_chat_response(messages, stream, websocket)
        except Exception as e:
            if not self.fallback_providers:
                # No fallbacks available, re-raise the original exception
                raise

            logger.warning(f"Primary provider failed: {e}. Trying fallbacks...")

            # Try each fallback in order
            last_error: Exception = e
            for i, fallback_provider in enumerate(self.fallback_providers):
                try:
                    logger.warning(f"Trying fallback provider {i+1}/{len(self.fallback_providers)}: {getattr(fallback_provider.llm, 'model_name', None)}")
                    return await fallback_provider.get_chat_response(messages, stream, websocket)
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider {i+1} failed: {fallback_error}")
                    last_error = fallback_error

            # All fallbacks failed
            raise Exception(f"All providers failed. Last error: {last_error}") from last_error
