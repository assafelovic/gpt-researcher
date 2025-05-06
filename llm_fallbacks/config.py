from __future__ import annotations

import os

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable

if __name__ == "__main__":
    import sys

    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from gpt_researcher.utils.logger import get_formatted_logger

from llm_fallbacks.core import (
    calculate_cost_per_token,
    get_litellm_models,
    sort_models_by_cost_and_limits,
)

if TYPE_CHECKING:
    import logging
logger: logging.Logger = get_formatted_logger(__name__)

if TYPE_CHECKING:
    from typing_extensions import Literal, TypedDict

    RoutingStrategies = Literal["simple-shuffle", "least-busy", "usage-based-routing", "latency-based-routing"]
    SupportedCallTypes = Literal["acompletion", "atext_completion", "aembedding", "atranscription"]
    ModelModes = Literal[
        "audio_speech",
        "audio_transcription",
        "chat",
        "completion",
        "embedding",
        "image_generation",
        "moderation",
        "moderations",
        "rerank",
    ]
    NotesKey = Literal["notes"]

    class RetryPolicy(TypedDict, total=False):
        AuthenticationErrorRetries: int  # Number of retries for authentication errors
        TimeoutErrorRetries: int  # Number of retries for timeout errors
        RateLimitErrorRetries: int  # Number of retries for rate limit errors
        ContentPolicyViolationErrorRetries: int  # Number of retries for content policy violations
        InternalServerErrorRetries: int  # Number of retries for internal server errors

    class AllowedFailsPolicy(TypedDict, total=False):
        BadRequestErrorAllowedFails: int  # Number of allowed bad request errors
        AuthenticationErrorAllowedFails: int  # Number of allowed authentication errors
        TimeoutErrorAllowedFails: int  # Number of allowed timeout errors
        RateLimitErrorAllowedFails: int  # Number of allowed rate limit errors
        ContentPolicyViolationErrorAllowedFails: int  # Number of allowed content policy violations
        InternalServerErrorAllowedFails: int  # Number of allowed internal server errors

    class RouterSettings(TypedDict, total=False):
        allowed_fails_policy: AllowedFailsPolicy  # Allowed failures policy
        allowed_fails: int  # Number of failures allowed before cooldown
        content_policy_fallbacks: list[dict[str, list[str]]]  # Fallback models for content policy violations
        cooldown_time: int  # Cooldown duration in seconds
        disable_cooldowns: bool  # Disable cooldowns for all models
        enable_pre_call_checks: bool  # Check if call is within model context window
        enable_tag_filtering: bool  # Use tag based routing
        fallbacks: list[dict[str, list[str]]]  # General fallback models
        redis_host: str  # Redis host for distributed state
        redis_password: str  # Redis password
        redis_port: str  # Redis port
        retry_policy: RetryPolicy  # Retry policy for different error types
        routing_strategy: RoutingStrategies  # Strategy for routing requests

    class CacheSettings(TypedDict, total=False):
        host: str  # Cache host
        mode: str  # Cache mode (e.g., "default_off")
        namespace: str  # Cache namespace
        password: str  # Cache password
        port: int  # Cache port
        supported_call_types: list[SupportedCallTypes]  # Supported call types for caching
        ttl: int  # Time to live for cache entries
        type: str  # Type of cache (e.g., "redis")

    class LiteLLMSettings(TypedDict, total=False):
        callbacks: list[str]  # List of general callbacks
        content_policy_fallbacks: list[dict[str, list[str]]]  # Content policy fallbacks
        context_window_fallbacks: list[dict[str, list[str]]]  # Context window fallbacks
        default_fallbacks: list[str]  # Default fallback models
        drop_params: bool
        failure_callback: list[str]  # List of failure callbacks
        force_ipv4: bool  # Force IPv4 for requests
        json_logs: bool  # Enable JSON logging
        langfuse_default_tags: list[str]  # Default tags for Langfuse logging
        redact_user_api_key_info: bool  # Redact user API key information
        request_timeout: int  # Request timeout in seconds
        service_callbacks: list[str]  # List of service callbacks
        set_verbose: bool  # Enable verbose logging
        success_callback: list[str]  # List of success callbacks
        turn_off_message_logging: bool  # Disable message logging

    class GeneralSettings(TypedDict, total=False):
        alerting_threshold: int  # Alerting threshold
        alerting: list[str]  # Alerting methods
        allow_requests_on_db_unavailable: bool  # Allow requests when DB is unavailable
        allowed_routes: list[str]  # Allowed API routes
        background_health_checks: bool  # Enable background health checks
        completion_model: str  # Default completion model
        custom_auth: str  # Custom authentication
        database_connection_pool_limit: int  # Database connection pool limit
        database_connection_timeout: int  # Database connection timeout
        database_url: str  # Database URL
        disable_adding_master_key_hash_to_db: bool  # Disable master key hash storage
        disable_master_key_return: bool  # Disable master key return
        disable_reset_budget: bool  # Disable budget reset
        disable_retry_on_max_parallel_request_limit_error: bool  # Disable retries on parallel request limit
        disable_spend_logs: bool  # Disable spend logging
        enable_jwt_auth: bool  # Enable JWT authentication
        enforce_user_param: bool  # Enforce user parameter
        global_max_parallel_requests: int  # Global maximum parallel requests
        health_check_interval: int  # Health check interval
        infer_model_from_keys: bool  # Infer model from keys
        key_management_settings: list[
            dict[str, Any]
        ]  # Settings for key management system (e.g. AWS KMS, Azure Key Vault). Doc on key management: https://docs.litellm.ai/docs/secret
        key_management_system: str  # Key management system
        master_key: str  # Master key
        max_parallel_requests: int  # Maximum parallel requests
        proxy_batch_write_at: int  # Batch write spend updates every n seconds
        use_client_credentials_pass_through_routes: bool  # Use client credentials for pass-through routes

    class LiteLLMBaseModelSpec(TypedDict, total=False):
        cache_creation_input_audio_token_cost: float  # cost per input audio token for cache creation

        cache_creation_input_token_cost: float  # cost per input token for cache creation
        cache_read_input_token_cost: float  # cost per input token for cache read
        input_cost_per_audio_per_second_above_128k_tokens: float  # cost per input audio per second above 128k tokens
        input_cost_per_audio_per_second: float  # cost per input audio per second
        input_cost_per_audio_token: float  # cost per input audio token
        input_cost_per_character_above_128k_tokens: float  # cost per input character above 128k tokens
        input_cost_per_character: float  # cost per input character
        input_cost_per_image_above_128k_tokens: float  # cost per input image above 128k tokens
        input_cost_per_image: float  # cost per input image
        input_cost_per_pixel: float  # cost per input pixel
        input_cost_per_query: float  # cost per input query
        input_cost_per_request: float  # cost per input request
        input_cost_per_second: float  # cost per input second
        input_cost_per_token_above_128k_tokens: float  # cost per input token above 128k tokens
        input_cost_per_token_batch_requests: float  # cost per input token for batch requests
        input_cost_per_token_batches: float  # cost per input token for batches
        input_cost_per_token_cache_hit: float  # cost per input token for cache hits
        input_cost_per_token: float  # cost per input token
        input_cost_per_video_per_second_above_128k_tokens: float  # cost per video per second above 128k tokens
        input_cost_per_video_per_second: float  # cost per video per second
        input_dbu_cost_per_token: float  # cost per input DBU token
        litellm_provider: str  # one of https://docs.litellm.ai/docs/providers
        max_audio_length_hours: float  # maximum length of audio in hours
        max_audio_per_prompt: int  # maximum number of audio per prompt
        max_images_per_prompt: int  # maximum number of images per prompt
        max_input_tokens: int  # max input tokens, if the provider specifies it. if not default to max_tokens
        max_output_tokens: int  # max output tokens, if the provider specifies it. if not default to max_tokens
        max_pdf_size_mb: int  # maximum PDF size in MB
        max_query_tokens: int  # maximum number of tokens for queries
        max_tokens: int  # LEGACY parameter. set to max_output_tokens if provider specifies it. IF not set to max_input_tokens, if provider specifies it.
        max_video_length: int  # maximum length of video
        max_videos_per_prompt: int  # maximum number of videos per prompt
        metadata: dict[NotesKey, str]  # metadata associated with the model
        mode: ModelModes  # mode of the model.
        output_cost_per_audio_token: float  # cost per output audio token
        output_cost_per_character_above_128k_tokens: float  # cost per output character above 128k tokens
        output_cost_per_character: float  # cost per output character
        output_cost_per_image: float  # cost per output image
        output_cost_per_pixel: float  # cost per output pixel
        output_cost_per_second: float  # cost per output second
        output_cost_per_token_above_128k_tokens: float  # cost per output token above 128k tokens
        output_cost_per_token_batches: float  # cost per output token for batches
        output_cost_per_token: float  # cost per output token
        output_dbu_cost_per_token: float  # cost per output DBU token. Sometimes typo'd to output_db_cost_per_token
        output_vector_size: int  # size of the output vector for embeddings
        rpd: int  # requests per day
        rpm: int  # requests per minute
        source: str  # source URL to the model
        supports_assistant_prefill: bool  # supports assistant prefill
        supports_audio_input: bool  # supports audio input
        supports_audio_output: bool  # supports audio output
        supports_embedding_image_input: bool  # supports embedding image input
        supports_function_calling: bool  # supports function calling
        supports_image_input: bool  # (DEPRECATED) use supports_embedding_image_input instead
        supports_parallel_function_calling: bool  # supports parallel function calling
        supports_pdf_input: bool  # supports PDF input
        supports_prompt_caching: bool  # supports prompt caching
        supports_response_schema: bool  # supports response schema
        supports_system_messages: bool  # supports system messages
        supports_tool_choice: bool  # supports tool choice
        supports_vision: bool  # supports vision
        tool_use_system_prompt_tokens: int  # number of tokens for tool use system prompt
        tpm: int  # tokens per minute

    class LiteLLMYAMLConfig(TypedDict):
        cache: CacheSettings
        general_settings: GeneralSettings
        litellm_settings: LiteLLMSettings
        model_list: list[LiteLLMBaseModelSpec]
        router_settings: RouterSettings

else:
    LiteLLMBaseModelSpec = dict
    LiteLLMYAMLConfig = dict
    RetryPolicy = dict
    AllowedFailsPolicy = dict
    RouterSettings = dict
    CacheSettings = dict
    LiteLLMSettings = dict
    GeneralSettings = dict

    Literal = str
    RoutingStrategies = str
    SupportedCallTypes = str
    ModelModes = str


class BaseProviderConfig:
    ALL_KNOWN_MODELS: ClassVar[dict[str, LiteLLMBaseModelSpec]] = get_litellm_models()
    FREE_COSTS: ClassVar[LiteLLMBaseModelSpec] = {
        "cache_creation_input_token_cost": 0.0,
        "cache_read_input_token_cost": 0.0,
        "input_cost_per_audio_per_second_above_128k_tokens": 0.0,
        "input_cost_per_audio_per_second": 0.0,
        "input_cost_per_audio_token": 0.0,
        "input_cost_per_character_above_128k_tokens": 0.0,
        "input_cost_per_character": 0.0,
        "input_cost_per_image_above_128k_tokens": 0.0,
        "input_cost_per_image": 0.0,
        "input_cost_per_pixel": 0.0,
        "input_cost_per_query": 0.0,
        "input_cost_per_request": 0.0,
        "input_cost_per_second": 0.0,
        "input_cost_per_token_above_128k_tokens": 0.0,
        "input_cost_per_token_batch_requests": 0.0,
        "input_cost_per_token_batches": 0.0,
        "input_cost_per_token_cache_hit": 0.0,
        "input_cost_per_token": 0.0,
        "input_cost_per_video_per_second_above_128k_tokens": 0.0,
        "input_cost_per_video_per_second": 0.0,
        "input_dbu_cost_per_token": 0.0,
        "output_cost_per_audio_token": 0.0,
        "output_cost_per_character_above_128k_tokens": 0.0,
        "output_cost_per_character": 0.0,
        "output_cost_per_image": 0.0,
        "output_cost_per_pixel": 0.0,
        "output_cost_per_second": 0.0,
        "output_cost_per_token_above_128k_tokens": 0.0,
        "output_cost_per_token_batches": 0.0,
        "output_cost_per_token": 0.0,
        "output_dbu_cost_per_token": 0.0,
    }


@dataclass
class CustomProviderConfig(BaseProviderConfig):
    provider_name: str
    base_url: str
    raw_models: Iterable[str] | dict[str, LiteLLMBaseModelSpec | dict[str, Any]] | None = None
    api_env_key_name: str | None = None
    api_key: str | None = None
    api_key_required: bool = False
    api_version: str | None = None  # e.g. "2024-10-21"
    custom_get_models_from_api: (
        Callable[[str | None], list[str] | dict[str, LiteLLMBaseModelSpec | dict[str, Any]]] | None
    ) = None
    parse_models_function: Callable[[str, dict[str, Any]]] | None = None
    auto_fetch_models: bool = True
    model_specs: dict[str, LiteLLMBaseModelSpec] = field(default_factory=dict)
    free_models: dict[str, LiteLLMBaseModelSpec] = field(default_factory=dict)

    def __post_init__(self):
        self._requested_models: Any = None
        self._parse_api_key()
        self._parse_models()

    def to_dict(self) -> dict[str, Any]:
        """Convert the CustomProviderConfig to a dictionary for JSON serialization."""
        return {
            "provider_name": self.provider_name,
            "base_url": self.base_url,
            "api_env_key_name": self.api_env_key_name,
            "api_key_required": self.api_key_required,
            "model_specs": {k: v for k, v in self.model_specs.items()},
            "free_models": {model_name: config for model_name, config in self.free_models.items()},
        }

    def _parse_api_key(self):
        env_key_name = self.api_env_key_name
        if not env_key_name or not env_key_name.strip():
            self.api_env_key_name = f"{self.provider_name.upper()}_API_KEY"
        else:
            self.api_env_key_name = env_key_name.upper()

        if (not self.api_env_key_name or not self.api_env_key_name.strip()) and self.api_key_required:
            raise ValueError(f"API environment key name for {self.provider_name} is not set.")
        self.api_key = os.getenv(self.api_env_key_name)
        if (not self.api_key or not self.api_key.strip()) and self.api_key_required:
            raise ValueError(
                f"API key for '{self.provider_name}' is not set. Set '{self.api_env_key_name}' in your environment."
            )

    @classmethod
    def _parse_standard_model_response(
        cls,
        provider_name: str,
        requested_models: dict[str, Any],
    ) -> dict[str, LiteLLMBaseModelSpec]:
        data = requested_models.get("data", [])
        if not isinstance(data, list):
            return {}
        parsed_requested_models: dict[str, LiteLLMBaseModelSpec] = {
            f"{provider_name}/{model['id']}": {"litellm_provider": provider_name} for model in data
        }
        return parsed_requested_models

    def _update_model_specs_with_cost(
        self,
        models: dict[str, LiteLLMBaseModelSpec],
    ):
        for model_name, model_spec in models.items():
            model_key = model_name if f"{self.provider_name}/" in model_name else f"{self.provider_name}/{model_name}"
            try:
                key = model_key if model_key in self.ALL_KNOWN_MODELS else model_name
                entry: LiteLLMBaseModelSpec = self.ALL_KNOWN_MODELS.setdefault(key, model_spec.copy())
                self.model_specs.setdefault(model_name, entry.copy()).update(model_spec)
                entry.update(model_spec)
            except Exception:
                logger.warning(
                    f"Failed to register model '{model_name}' from '{self.provider_name}'.",
                    exc_info=True,
                )

    def _set_free_model_costs(
        self,
        models: dict[str, LiteLLMBaseModelSpec],
    ):
        for model_name, model_spec in models.items():
            self.model_specs[model_name].setdefault(  # pyright: ignore[reportCallIssue]
                model_name,  # pyright: ignore[reportArgumentType]
                model_spec.copy(),  # pyright: ignore[reportArgumentType]
            ).update(model_spec)
            if model_name in self.free_models:
                model_spec.update(self.FREE_COSTS)
            if calculate_cost_per_token(model_spec) == 0.0:
                self.free_models.setdefault(model_name, model_spec.copy()).update(model_spec)

    def _process_requested_models(
        self,
        models: dict[str, LiteLLMBaseModelSpec],
    ):
        if self.parse_models_function is not None:
            parsed_requested_models: dict[str, LiteLLMBaseModelSpec] = self.parse_models_function(
                self.provider_name,
                self._requested_models,
            )
            models.update(parsed_requested_models)
        elif isinstance(self._requested_models, list) and self._requested_models:
            first_entry = next(iter(self._requested_models))
            if not isinstance(first_entry, str):
                print(repr(models))
                print(f"unsupported format from '{self.base_url}' ({self.provider_name}) see above")
                return
            models.update({model.get("name", model.get("model_name")): {} for model in self._requested_models})
        elif isinstance(self._requested_models, dict):
            object_models_list = self._requested_models.get("object")
            if object_models_list == "list":
                models.update(self._parse_standard_model_response(self.provider_name, self._requested_models))
            else:
                models.update(self._requested_models)

    def _parse_models(self):
        models: dict[str, LiteLLMBaseModelSpec] = (  # pyright: ignore[reportAssignmentType]
            self.raw_models
            if isinstance(self.raw_models, dict)
            else {model: {} for model in self.raw_models}
            if self.raw_models is not None
            else {}
        )

        if self.auto_fetch_models:
            if self.custom_get_models_from_api is not None:
                try:
                    self._requested_models = self.custom_get_models_from_api(self.api_key)
                except Exception:
                    logger.warning(
                        f"Failed to get models from '{self.custom_get_models_from_api}'.",
                        exc_info=True,
                    )
            if self._requested_models is None and self.base_url and self.base_url.strip():
                self._get_models_from_api()
            self._process_requested_models(models)

        self._update_model_specs_with_cost(models)
        self._set_free_model_costs(models)

    def _get_models_from_api(self):
        try:
            import requests

            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
        except Exception:
            logger.warning(
                f"Failed to get models from '{self.base_url}/models'. Cached models will be used instead.",
                exc_info=True,
            )
        else:
            self._requested_models = response.json()


def _parse_openrouter_models_response(
    provider_name: str,
    requested_models: dict[str, Any],
) -> dict[str, LiteLLMBaseModelSpec]:
    data = requested_models.get("data", [])
    if not isinstance(data, list):
        return {}

    parsed_requested_models: dict[str, LiteLLMBaseModelSpec] = {}
    for model in data:
        model_id = model.get("id", "")
        if not model_id:
            continue

        # start with the main provider's template if exists.
        model_spec: LiteLLMBaseModelSpec = get_litellm_models().get(model_id, {})

        # Parse pricing information
        pricing = model.get("pricing", {})
        if pricing:
            prompt_cost = pricing.get("prompt", 0)
            if prompt_cost:
                model_spec["input_cost_per_token"] = float(prompt_cost)
            completion_cost = pricing.get("completion", 0)
            if completion_cost:
                model_spec["output_cost_per_token"] = float(completion_cost)
            image_cost = pricing.get("image", 0)
            if image_cost:
                model_spec["input_cost_per_image"] = float(image_cost)
            request_cost = pricing.get("request", 0)
            if request_cost:
                model_spec["input_cost_per_query"] = float(request_cost)

        # Parse architecture and modality details
        arch = model.get("architecture", {})
        top_provider = model.get("top_provider", {})
        modality = arch.get("modality", "")

        # Context length and max tokens
        if top_provider:
            context_length = top_provider.get("context_length")
            if context_length:
                model_spec["max_input_tokens"] = int(context_length)
            max_completion_tokens = top_provider.get("max_completion_tokens")
            if max_completion_tokens:
                model_spec["max_output_tokens"] = int(max_completion_tokens)

        # Modality-specific capabilities
        if modality == "text+image->text":
            model_spec["mode"] = "chat"
            model_spec["supports_vision"] = True
        elif modality == "text->image":
            model_spec["mode"] = "image_generation"
        elif modality == "text->embedding":
            model_spec["mode"] = "embedding"
        elif modality == "audio->text":
            model_spec["mode"] = "audio_transcription"

        # Function calling support
        if arch.get("instruct_type") == "Function":
            model_spec["supports_function_calling"] = True

        description = model.get("description", "")
        if description:
            model_spec["metadata"] = {"notes": description}
            if "function call" in description.lower():
                model_spec["supports_function_calling"] = True

        model_spec["litellm_provider"] = provider_name
        parsed_requested_models[model_id] = model_spec

    return parsed_requested_models


if "CUSTOM_PROVIDERS" not in globals():
    CUSTOM_PROVIDERS: list[CustomProviderConfig] = [
        #        CustomProviderConfig(
        #            provider_name="arliai",
        #            base_url="https://api.arliai.com/v1",
        #            api_key_required=True,
        #        ),
        #        CustomProviderConfig(
        #            provider_name="awanllm",
        #            base_url="https://api.awanllm.com/v1",
        #            api_key_required=True,
        #        ),
        CustomProviderConfig(
            provider_name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key_required=True,
            parse_models_function=_parse_openrouter_models_response,
        ),
        CustomProviderConfig(
            provider_name="vertexai",
            base_url="https://us-central1-aiplatform.googleapis.com/v1",
            api_key_required=False,
            auto_fetch_models=False,
        ),
        CustomProviderConfig(
            provider_name="yandex",
            base_url="https://llm.api.cloud.yandex.net",
            api_key_required=False,
            auto_fetch_models=False,
        ),
    ]

if "FREE_MODELS" not in globals():  # don't waste time and energy redefining these anytime config.py is imported.
    all_configs: dict[str, LiteLLMBaseModelSpec] = {
        model_name: config for provider in CUSTOM_PROVIDERS for model_name, config in provider.model_specs.items()
    }
    all_configs.update(
        {
            model_name: config
            for model_name, config in BaseProviderConfig.ALL_KNOWN_MODELS.items()
            if model_name not in all_configs
        }
    )
    ALL_MODELS: list[tuple[str, LiteLLMBaseModelSpec]] = sort_models_by_cost_and_limits(all_configs)
    FREE_MODELS: list[tuple[str, LiteLLMBaseModelSpec]] = sort_models_by_cost_and_limits(
        all_configs,
        free_only=True,
    )
    ALL_EMBEDDING_MODELS: list[tuple[str, LiteLLMBaseModelSpec]] = sort_models_by_cost_and_limits(
        {k: v for k, v in all_configs.items() if v.get("mode") == "embedding"},
    )
    FREE_EMBEDDING_MODELS: list[tuple[str, LiteLLMBaseModelSpec]] = sort_models_by_cost_and_limits(
        {k: v for k, v in all_configs.items() if v.get("mode") == "embedding"},
        free_only=True,
    )
