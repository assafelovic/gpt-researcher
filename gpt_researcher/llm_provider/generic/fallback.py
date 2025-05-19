"""LLM Provider with Fallback Support."""

from __future__ import annotations

import logging
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
        # Create fallback providers if specified
        fallback_providers: list[GenericLLMProvider] = []
        if fallback_models:
            for fallback_model in fallback_models:
                try:
                    provider_name, model_name = fallback_model.split(":", 1)
                    # Copy kwargs and update model name
                    fallback_kwargs: dict[str, Any] = kwargs.copy()
                    fallback_kwargs["model"] = model_name
                    fallback_provider: GenericLLMProvider = GenericLLMProvider.from_provider(
                        provider_name,
                        chat_log=chat_log,
                        verbose=verbose,
                        **fallback_kwargs,
                    )
                    fallback_providers.append(fallback_provider)
                except (ValueError, ImportError) as e:
                    logger.warning(f"Failed to initialize fallback provider {fallback_model}: {e}")

        return cls(
            GenericLLMProvider.from_provider(provider, chat_log=chat_log, verbose=verbose, **kwargs).llm,
            fallback_providers=fallback_providers,
            chat_log=chat_log,
            verbose=verbose,
        )

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
