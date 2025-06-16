"""LLM Provider with Fallback Support."""

from __future__ import annotations

import logging
import os
import traceback
from typing import Any, TypeVar

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.utils.llm_debug_logger import LLMDebugLogger, get_llm_debug_logger

logger: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T")


class FallbackGenericLLMProvider(GenericLLMProvider):
    """LLM Provider with fallback support."""

    def __init__(
        self,
        llm: Any,
        fallback_providers: list[GenericLLMProvider] | None = None,
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
                    logger.warning(f"Failed to initialize fallback provider {fallback_model}: {e.__class__.__name__}: {str(e)}")

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
            logger.error(f"Failed to initialize primary provider {provider}: {e.__class__.__name__}: {str(e)}")

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
        primary_model_name: str = getattr(self.llm, 'model_name', None) or getattr(self.llm, 'model', 'unknown')

        if self.verbose:
            logger.info(f"[FALLBACK-DEBUG] Starting fallback-enabled request with primary model: {primary_model_name}")
#            logger.info(f"[FALLBACK-DEBUG] Available fallback providers: {len(self.fallback_providers)}")
#            for i, fb in enumerate(self.fallback_providers):
#                fb_model: str = getattr(fb.llm, 'model_name', None) or getattr(fb.llm, 'model', 'unknown')
#                logger.info(f"[FALLBACK-DEBUG]   Fallback {i+1}: {fb_model}")

        # Get debug logger
        debug_logger: LLMDebugLogger = get_llm_debug_logger()

        # Try primary provider first
        try:
            if self.verbose:
                logger.info(f"[FALLBACK-DEBUG] Attempting primary provider: {primary_model_name}")

            response: str = await super().get_chat_response(messages, stream, websocket)

            if self.verbose:
                logger.info(f"[FALLBACK-DEBUG] Primary provider succeeded: {primary_model_name}")

            return response

        except Exception as e:
            if self.verbose:
                logger.warning(f"[FALLBACK-DEBUG] Primary provider failed: {primary_model_name}")
                logger.warning(f"[FALLBACK-DEBUG] Primary error: {e.__class__.__name__}: {str(e)[:300]}...")

            if not self.fallback_providers:
                if self.verbose:
                    logger.error("[FALLBACK-DEBUG] No fallback providers available. Re-raising primary error.")
                raise

            if self.verbose:
                logger.info(f"[FALLBACK-DEBUG] Trying {len(self.fallback_providers)} fallback providers...")

            # Try each fallback in order
            last_error: Exception = e
            for i, fallback_provider in enumerate(self.fallback_providers):
                try:
                    fallback_model: str = getattr(fallback_provider.llm, 'model_name', None) or getattr(fallback_provider.llm, 'model', 'unknown')

                    if self.verbose:
                        logger.info(f"[FALLBACK-DEBUG] Trying fallback provider {i+1}/{len(self.fallback_providers)}: {fallback_model}")

                    # Log fallback attempt to debug logger
                    if debug_logger.current_interaction:
                        debug_logger.current_interaction.is_fallback = True
                        debug_logger.current_interaction.fallback_attempt = i + 1
                        debug_logger.current_interaction.primary_provider = primary_model_name
                        debug_logger.current_interaction.model = fallback_model
                        debug_logger.current_interaction.provider = getattr(fallback_provider, 'provider', 'unknown')

                        debug_logger.log_retry_attempt(
                            attempt_number=i + 1,
                            reason=f"Primary provider {primary_model_name} failed, trying fallback",
                            details={
                                "primary_error": f"{e.__class__.__name__}: {str(e)}",
                                "fallback_model": fallback_model,
                                "total_fallbacks": len(self.fallback_providers)
                            }
                        )

                    response: str = await fallback_provider.get_chat_response(messages, stream, websocket)

                    if self.verbose:
                        logger.info(f"[FALLBACK-DEBUG] Fallback provider {i+1} succeeded: {fallback_model}")

                    return response

                except Exception as fallback_error:
                    if self.verbose:
                        logger.warning(f"[FALLBACK-DEBUG] Fallback provider {i+1} failed: {fallback_model} Fallback error: {fallback_error.__class__.__name__}: {str(fallback_error)[:300] if len(str(fallback_error)) > 300 else str(fallback_error)}")
                    last_error = fallback_error

            # All fallbacks failed
            if self.verbose:
                logger.error(f"[FALLBACK-DEBUG] All providers failed. Primary: {primary_model_name}, Fallbacks: {len(self.fallback_providers)}")
                logger.error(f"[FALLBACK-DEBUG] Last error: {last_error.__class__.__name__}: {traceback.format_exception(last_error)}")

            raise Exception(f"All providers failed. Primary: {primary_model_name}, Fallbacks: {len(self.fallback_providers)}. Last error: {traceback.format_exception(last_error)}") from last_error
