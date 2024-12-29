"""Configuration for API providers and their details."""

from __future__ import annotations

import logging
import os
import random

from typing import Any


class APIProviderManager:
    """Manages API providers with fallback and retry mechanisms."""

    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger: logging.Logger = logging.getLogger(__name__)

        # Free LLM API providers with no or minimal requirements
        self.free_llm_providers: list[dict[str, Any]] = [
            {
                "name": "Cloudflare Workers AI",
                "models": ["Llama 3 8B Instruct", "Mistral 7B Instruct v0.2", "Gemma 7B Instruct"],
                "rate_limit": "10,000 tokens/day",
                "setup_required": False,
                "priority": 1,  # Highest priority for completely free providers
            },
            {
                "name": "Groq",
                "models": ["Llama 3 8B", "Mixtral 8x7B", "Gemma 2 9B Instruct"],
                "rate_limit": "14,400 requests/day",
                "setup_required": True,
                "key_name": "GROQ_API_KEY",
                "priority": 2,
            },
            {
                "name": "OpenRouter",
                "models": ["Gemini 2.0 Flash Experimental", "Llama 3 8B Instruct", "Mistral 7B Instruct", "Phi-3 Mini 128k Instruct"],
                "rate_limit": "20 requests/minute, 200 requests/day",
                "setup_required": False,
                "priority": 1,
            },
            {
                "name": "Google AI Studio",
                "models": ["Gemini 1.5 Pro", "Gemini 1.0 Pro", "Gemini 2.0 Flash"],
                "rate_limit": "1,500 requests/day",
                "setup_required": False,
                "priority": 1,
            },
            {
                "name": "HuggingFace Serverless",
                "models": ["Various open models"],
                "rate_limit": "1,000 requests/day",
                "setup_required": True,
                "key_name": "HUGGINGFACE_API_KEY",
                "priority": 3,
            },
            {
                "name": "Ollama",
                "models": ["Local open-source models"],
                "rate_limit": "Unlimited",
                "setup_required": False,
                "priority": 1,  # High priority for local providers
            },
            {
                "name": "OVH AI Endpoints",
                "models": ["Llama 3 70B Instruct", "Mistral 7B Instruct", "Mixtral 8x7B Instruct"],
                "rate_limit": "12 requests/minute",
                "setup_required": False,
                "priority": 2,
            },
            {
                "name": "Scaleway Generative APIs",
                "models": ["Llama 3.1 70B Instruct", "Mistral Nemo 2407", "Qwen2.5 Coder 32B Instruct"],
                "rate_limit": "300 requests/minute",
                "setup_required": False,
                "priority": 2,
            },
        ]

        # Existing API providers
        self.api_providers: dict[str, Any] = {
            "required": {
                "openai": {"key_name": "OPENAI_API_KEY", "display_name": "OpenAI API Key", "description": "Required for language model functionality"},
                "tavily": {"key_name": "TAVILY_API_KEY", "display_name": "Tavily API Key", "description": "Required for web search functionality"},
            },
            "optional": {
                "anthropic": {"key_name": "ANTHROPIC_API_KEY", "display_name": "Anthropic API Key", "description": "For Claude models"},
                "google": {"key_name": "GOOGLE_API_KEY", "display_name": "Google API Key", "description": "For Google Custom Search"},
                "bing": {"key_name": "BING_API_KEY", "display_name": "Bing API Key", "description": "For Bing Web Search"},
                "searchapi": {"key_name": "SEARCHAPI_API_KEY", "display_name": "SearchAPI Key", "description": "For SearchAPI.io"},
                "serpapi": {"key_name": "SERPAPI_API_KEY", "display_name": "SerpAPI Key", "description": "For SerpAPI search"},
                "serper": {"key_name": "SERPER_API_KEY", "display_name": "Serper API Key", "description": "For Serper.dev search"},
                "exa": {"key_name": "EXA_API_KEY", "display_name": "Exa API Key", "description": "For Exa.ai search"},
                "ncbi": {"key_name": "NCBI_API_KEY", "display_name": "NCBI API Key", "description": "For PubMed searches"},
                "langchain": {"key_name": "LANGCHAIN_API_KEY", "display_name": "LangChain API Key", "description": "For LangChain integration"},
                "cohere": {"key_name": "COHERE_API_KEY", "display_name": "Cohere API Key", "description": "For Cohere models"},
                "perplexity": {"key_name": "PERPLEXITY_API_KEY", "display_name": "Perplexity API Key", "description": "For Perplexity AI"},
                "huggingface": {"key_name": "HUGGINGFACE_API_KEY", "display_name": "HuggingFace API Key", "description": "For HuggingFace models"},
                "metaphor": {"key_name": "METAPHOR_API_KEY", "display_name": "Metaphor API Key", "description": "For Metaphor search"},
                "you": {"key_name": "YOU_API_KEY", "display_name": "You.com API Key", "description": "For You.com search"},
                "browserless": {"key_name": "BROWSERLESS_API_KEY", "display_name": "Browserless API Key", "description": "For web scraping"},
                "prodia": {"key_name": "PRODIA_API_KEY", "display_name": "Prodia API Key", "description": "For image generation"},
                "arxiv": {"key_name": "ARXIV_API_KEY", "display_name": "arXiv API Key", "description": "For academic papers"},
                "groq": {"key_name": "GROQ_API_KEY", "display_name": "Groq API Key", "description": "For Groq LLM models"},
            },
        }

    def _parse_rate_limit(self, rate_limit: str) -> dict[str, int]:
        """Parse rate limit string into structured format.

        Args:
            rate_limit: Rate limit string (e.g. "20 requests/minute, 200 requests/day")

        Returns:
            Dictionary with rate limit details
        """
        limits: dict[str, int] = {}
        try:
            for limit in rate_limit.split(","):
                limit = limit.strip()
                if not limit:
                    continue

                parts = limit.split()
                if len(parts) >= 2:
                    count = int(parts[0].replace(",", ""))
                    if "minute" in parts[1]:
                        limits["per_minute"] = count
                    elif "day" in parts[1]:
                        limits["per_day"] = count
                    elif "tokens" in parts[1]:
                        limits["tokens"] = count
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Failed to parse rate limit '{rate_limit}': {e}")

        return limits

    def _check_rate_limits(self, provider: dict[str, Any]) -> bool:
        """Check if provider is within rate limits.

        Args:
            provider: Provider configuration dictionary

        Returns:
            True if within limits, False otherwise
        """
        try:
            rate_limit = provider.get("rate_limit", "")
            if not rate_limit or rate_limit.lower() == "unlimited":
                return True

            limits = self._parse_rate_limit(rate_limit)

            # For now just check if limits exist - in production would track actual usage
            return bool(limits)

        except Exception as e:
            self.logger.warning(f"Rate limit check failed for {provider.get('name')}: {e}")
            return False

    def get_free_providers(
        self,
        include_setup_required: bool = True,
    ) -> list[dict[str, str]]:
        """
        Get free LLM providers that can be used without or with minimal setup.

        Args:
            include_setup_required: Whether to include providers that require setup

        Returns:
            List of free provider dictionaries
        """
        providers: list[dict[str, Any]] = []
        for provider in self.free_llm_providers:
            # Check if provider meets setup requirements
            if not provider.get("setup_required") or (include_setup_required and provider.get("setup_required") and os.getenv(provider.get("key_name", ""))):
                # Check rate limits
                if self._check_rate_limits(provider):
                    providers.append(provider)

        # Sort providers by priority (lower number = higher priority)
        providers.sort(key=lambda x: x.get("priority", float("inf")))

        return providers

    def select_provider(
        self,
        providers: list[dict[str, str]] | None = None,
        preferred_models: list[str] | None = None,
        max_attempts: int = 3,
    ) -> dict[str, str] | None:
        """
        Select a provider with advanced fallback logic.

        Args:
            providers: Optional list of providers to select from
            preferred_models: Optional list of preferred model names
            max_attempts: Maximum number of provider selection attempts

        Returns:
            Selected provider or None
        """
        if providers is None:
            # First try providers without setup
            providers = self.get_free_providers(include_setup_required=False)

            # If no providers found, include those with setup
            if not providers:
                providers = self.get_free_providers(include_setup_required=True)

        # Filter by preferred models if specified
        if preferred_models:
            providers = [p for p in providers if any(model.strip() in p.get("models", []) for model in preferred_models)]

        if not providers:
            self.logger.warning("No suitable providers found")
            return None

        # Randomize provider selection with priority weighting
        attempts: int = 0
        tried_providers: set[str] = set()

        while attempts < max_attempts and providers:
            try:
                # Weighted random selection favoring higher priority providers
                weights = [1 / float(p.get("priority", float("inf"))) for p in providers]
                selected_provider = random.choices(providers, weights=weights)[0]

                provider_name = selected_provider.get("name", "")
                if provider_name in tried_providers:
                    continue

                tried_providers.add(provider_name)
                self.logger.info(f"Selected provider: {provider_name}")
                return selected_provider

            except Exception as e:
                self.logger.warning(f"Provider selection failed: {e}")
                if selected_provider in providers:
                    providers.remove(selected_provider)
                attempts += 1

        self.logger.error("No suitable providers found after %s attempts. Tried: %s", max_attempts, ", ".join(tried_providers))
        return None


# Instantiate the manager
API_PROVIDERS_MANAGER = APIProviderManager()

# Maintain the original API_PROVIDERS structure for backwards compatibility
API_PROVIDERS = API_PROVIDERS_MANAGER.api_providers
