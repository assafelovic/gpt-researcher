"""Comprehensive LLM Debug Logger for GPT Researcher

This module provides detailed logging of all LLM interactions including:
- All prompts and responses
- Failover attempts and errors
- Token usage and performance metrics
- Debugging information for troubleshooting

The logger creates separate files from the main application logging
specifically for LLM interaction debugging.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LLMInteractionRecord:
    """Complete record of an LLM interaction for debugging"""

    # Basic identification
    interaction_id: str
    timestamp: float
    session_id: str
    step_name: str

    # Model and provider info
    model: str
    provider: str
    is_fallback: bool = False
    fallback_attempt: int = 0
    primary_provider: str | None = None

    # Request details
    system_message: str = ""
    user_message: str = ""
    full_messages: list[dict[str, Any]] = field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None
    other_params: dict[str, Any] = field(default_factory=dict)

    # Response details
    response: str = ""
    success: bool = True
    error_message: str | None = None
    error_type: str | None = None
    full_error_traceback: str | None = None

    # Performance metrics
    duration_seconds: float | None = None
    estimated_prompt_tokens: int = 0
    estimated_completion_tokens: int = 0
    estimated_total_tokens: int = 0

    # Context and debugging info
    context_info: dict[str, Any] = field(default_factory=dict)
    retry_history: list[dict[str, Any]] = field(default_factory=list)
    token_reduction_attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class LLMDebugLogger:
    """Comprehensive LLM interaction logger for debugging"""

    def __init__(self, session_id: str | None = None, log_dir: str = "llm_debug_logs"):
        self.session_id: str = session_id or f"session_{int(time.time())}"
        self.log_dir: Path = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create timestamped log files
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_log_file: Path = self.log_dir / f"llm_debug_{timestamp}_{self.session_id}.json"
        self.text_log_file: Path = self.log_dir / f"llm_debug_{timestamp}_{self.session_id}.txt"
        self.csv_log_file: Path = self.log_dir / f"llm_debug_{timestamp}_{self.session_id}.csv"

        # Initialize log files
        self._initialize_log_files()

        # In-memory storage for current session
        self.interactions: list[LLMInteractionRecord] = []
        self.current_interaction: LLMInteractionRecord | None = None

        # Performance tracking
        self.total_interactions: int = 0
        self.successful_interactions: int = 0
        self.failed_interactions: int = 0
        self.total_tokens_used: int = 0

        print("🔍 LLM Debug Logger initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   JSON Log: {self.json_log_file}")
        print(f"   Text Log: {self.text_log_file}")
        print(f"   CSV Log: {self.csv_log_file}")

    def _initialize_log_files(self) -> None:
        """Initialize the log files with headers"""
        # JSON file - start with empty array
        with open(self.json_log_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

        # Text file - add header
        with open(self.text_log_file, 'w', encoding='utf-8') as f:
            f.write(f"LLM Debug Log - Session: {self.session_id}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

        # CSV file - add headers
        with open(self.csv_log_file, 'w', encoding='utf-8') as f:
            headers: list[str] = [
                "interaction_id", "timestamp", "step_name", "model", "provider",
                "is_fallback", "fallback_attempt", "success", "duration_seconds",
                "estimated_total_tokens", "error_type", "system_message_length",
                "user_message_length", "response_length"
            ]
            f.write(",".join(headers) + "\n")

    def start_interaction(
        self,
        step_name: str,
        model: str,
        provider: str,
        is_fallback: bool = False,
        fallback_attempt: int = 0,
        primary_provider: str | None = None,
        context_info: dict[str, Any] | None = None
    ) -> str:
        """Start logging a new LLM interaction"""

        interaction_id: str = f"{self.session_id}_{int(time.time())}_{len(self.interactions)}"

        self.current_interaction = LLMInteractionRecord(
            interaction_id=interaction_id,
            timestamp=time.time(),
            session_id=self.session_id,
            step_name=step_name,
            model=model,
            provider=provider,
            is_fallback=is_fallback,
            fallback_attempt=fallback_attempt,
            primary_provider=primary_provider,
            context_info=context_info or {}
        )

        self.total_interactions += 1

        # Log the start
        self._log_to_text(f"\n{'='*80}")
        self._log_to_text(f"INTERACTION START: {interaction_id}")
        self._log_to_text(f"Step: {step_name}")
        self._log_to_text(f"Model: {model} (Provider: {provider})")
        if is_fallback:
            self._log_to_text(f"FALLBACK ATTEMPT #{fallback_attempt} (Primary: {primary_provider})")
        self._log_to_text(f"Timestamp: {datetime.fromtimestamp(self.current_interaction.timestamp).isoformat()}")
        self._log_to_text(f"{'='*80}")

        return interaction_id

    def log_request(
        self,
        system_message: str = "",
        user_message: str = "",
        full_messages: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **other_params
    ) -> None:
        """Log the request details"""
        if not self.current_interaction:
            return

        self.current_interaction.system_message = system_message
        self.current_interaction.user_message = user_message
        self.current_interaction.full_messages = full_messages or []
        self.current_interaction.temperature = temperature
        self.current_interaction.max_tokens = max_tokens
        self.current_interaction.other_params = other_params

        # Estimate tokens
        self.current_interaction.estimated_prompt_tokens = self._estimate_tokens(system_message + user_message)

        # Log request details
        self._log_to_text("\nREQUEST DETAILS:")
        self._log_to_text(f"Temperature: {temperature}")
        self._log_to_text(f"Max Tokens: {max_tokens}")
        self._log_to_text(f"Other Params: {other_params}")
        self._log_to_text(f"Estimated Prompt Tokens: {self.current_interaction.estimated_prompt_tokens}")

        self._log_to_text(f"\nSYSTEM MESSAGE ({len(system_message)} chars):")
        self._log_to_text(f"{'-'*40}")
        self._log_to_text(system_message[:1000] + ("..." if len(system_message) > 1000 else ""))

        self._log_to_text(f"\nUSER MESSAGE ({len(user_message)} chars):")
        self._log_to_text(f"{'-'*40}")
        self._log_to_text(user_message[:1000] + ("..." if len(user_message) > 1000 else ""))

        if full_messages:
            self._log_to_text(f"\nFULL MESSAGE HISTORY ({len(full_messages)} messages):")
            self._log_to_text(f"{'-'*40}")
            for i, msg in enumerate(full_messages):
                role: str = msg.get("role", "unknown")
                content: str = str(msg.get("content", ""))
                self._log_to_text(f"Message {i+1} ({role}): {content[:200]}...")

    def log_response(
        self,
        response: str,
        success: bool = True,
        error_message: str | None = None,
        error_type: str | None = None,
        duration_seconds: float | None = None
    ) -> None:
        """Log the response details"""
        if not self.current_interaction:
            return

        self.current_interaction.response = response
        self.current_interaction.success = success
        self.current_interaction.error_message = error_message
        self.current_interaction.error_type = error_type
        self.current_interaction.duration_seconds = duration_seconds

        if error_message:
            self.current_interaction.full_error_traceback = traceback.format_exc()

        # Estimate completion tokens
        self.current_interaction.estimated_completion_tokens = self._estimate_tokens(response)
        self.current_interaction.estimated_total_tokens = (
            self.current_interaction.estimated_prompt_tokens +
            self.current_interaction.estimated_completion_tokens
        )

        # Update counters
        if success:
            self.successful_interactions += 1
        else:
            self.failed_interactions += 1

        self.total_tokens_used += self.current_interaction.estimated_total_tokens

        # Log response details
        self._log_to_text("\nRESPONSE DETAILS:")
        self._log_to_text(f"Success: {success}")
        self._log_to_text(f"Duration: {duration_seconds:.2f}s" if duration_seconds else "Duration: N/A")
        self._log_to_text(f"Estimated Completion Tokens: {self.current_interaction.estimated_completion_tokens}")
        self._log_to_text(f"Estimated Total Tokens: {self.current_interaction.estimated_total_tokens}")

        if success:
            self._log_to_text(f"\nRESPONSE ({len(response)} chars):")
            self._log_to_text(f"{'-'*40}")
            self._log_to_text(response[:1000] + ("..." if len(response) > 1000 else ""))
        else:
            self._log_to_text("\nERROR:")
            self._log_to_text(f"Type: {error_type}")
            self._log_to_text(f"Message: {error_message}")
            if self.current_interaction.full_error_traceback:
                self._log_to_text(f"Traceback:\n{self.current_interaction.full_error_traceback}")

    def log_token_reduction_attempt(
        self,
        strategy: str,
        original_tokens: int,
        target_tokens: int,
        final_tokens: int,
        success: bool,
        details: dict[str, Any] | None = None
    ) -> None:
        """Log token reduction attempts"""
        if not self.current_interaction:
            return

        reduction_info: dict[str, Any] = {
            "strategy": strategy,
            "original_tokens": original_tokens,
            "target_tokens": target_tokens,
            "final_tokens": final_tokens,
            "success": success,
            "reduction_achieved": original_tokens - final_tokens,
            "reduction_percentage": ((original_tokens - final_tokens) / original_tokens * 100) if original_tokens > 0 else 0,
            "details": details or {},
            "timestamp": time.time()
        }

        self.current_interaction.token_reduction_attempts.append(reduction_info)

        self._log_to_text("\nTOKEN REDUCTION ATTEMPT:")
        self._log_to_text(f"Strategy: {strategy}")
        self._log_to_text(f"Original: {original_tokens} → Target: {target_tokens} → Final: {final_tokens}")
        self._log_to_text(f"Reduction: {reduction_info['reduction_achieved']} tokens ({reduction_info['reduction_percentage']:.1f}%)")
        self._log_to_text(f"Success: {success}")

    def log_retry_attempt(
        self,
        attempt_number: int,
        reason: str,
        details: dict[str, Any] | None = None
    ) -> None:
        """Log retry attempts"""
        if not self.current_interaction:
            return

        retry_info: dict[str, Any] = {
            "attempt_number": attempt_number,
            "reason": reason,
            "details": details or {},
            "timestamp": time.time()
        }

        self.current_interaction.retry_history.append(retry_info)

        self._log_to_text(f"\nRETRY ATTEMPT #{attempt_number}:")
        self._log_to_text(f"Reason: {reason}")
        if details:
            self._log_to_text(f"Details: {details}")

    def finish_interaction(self) -> str | None:
        """Finish the current interaction and save to files"""
        if not self.current_interaction:
            return None

        # Add to interactions list
        self.interactions.append(self.current_interaction)

        # Save to files
        self._save_to_json()
        self._save_to_csv()

        interaction_id: str = self.current_interaction.interaction_id

        # Log completion
        self._log_to_text(f"\nINTERACTION COMPLETED: {interaction_id}")
        self._log_to_text(f"Final Status: {'SUCCESS' if self.current_interaction.success else 'FAILED'}")
        self._log_to_text(f"{'='*80}\n")

        # Clear current interaction
        self.current_interaction = None

        return interaction_id

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of the current session"""
        return {
            "session_id": self.session_id,
            "total_interactions": self.total_interactions,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,
            "success_rate": (self.successful_interactions / self.total_interactions * 100) if self.total_interactions > 0 else 0,
            "total_tokens_used": self.total_tokens_used,
            "log_files": {
                "json": str(self.json_log_file),
                "text": str(self.text_log_file),
                "csv": str(self.csv_log_file)
            }
        }

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)"""
        return len(text) // 4

    def _log_to_text(self, message: str) -> None:
        """Append message to text log file"""
        with open(self.text_log_file, 'a', encoding='utf-8') as f:
            f.write(message + "\n")

    def _save_to_json(self) -> None:
        """Save all interactions to JSON file"""
        data: list[dict[str, Any]] = [interaction.to_dict() for interaction in self.interactions]
        with open(self.json_log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _save_to_csv(self) -> None:
        """Append latest interaction to CSV file"""
        if not self.current_interaction:
            return

        interaction: LLMInteractionRecord = self.interactions[-1]  # Latest interaction

        row_data: list[Any] = [
            interaction.interaction_id,
            interaction.timestamp,
            interaction.step_name,
            interaction.model,
            interaction.provider,
            interaction.is_fallback,
            interaction.fallback_attempt,
            interaction.success,
            interaction.duration_seconds or "",
            interaction.estimated_total_tokens,
            interaction.error_type or "",
            len(interaction.system_message),
            len(interaction.user_message),
            len(interaction.response)
        ]

        with open(self.csv_log_file, 'a', encoding='utf-8') as f:
            # Escape commas and quotes in data
            escaped_data: list[str] = []
            for item in row_data:
                if isinstance(item, str) and (',' in item or '"' in item):
                    escaped_data.append(f'"{item.replace('"', '""')}"')
                else:
                    escaped_data.append(str(item))
            f.write(",".join(escaped_data) + "\n")


# Global logger instance
_global_llm_debug_logger: LLMDebugLogger | None = None


def get_llm_debug_logger() -> LLMDebugLogger:
    """Get or create the global LLM debug logger"""
    global _global_llm_debug_logger
    if _global_llm_debug_logger is None:
        _global_llm_debug_logger = LLMDebugLogger()
    return _global_llm_debug_logger


def initialize_llm_debug_logger(
    session_id: str | None = None,
    log_dir: str = "llm_debug_logs",
) -> LLMDebugLogger:
    """Initialize a new LLM debug logger"""
    global _global_llm_debug_logger
    _global_llm_debug_logger = LLMDebugLogger(session_id=session_id, log_dir=log_dir)
    return _global_llm_debug_logger


def log_llm_interaction(
    step_name: str,
    model: str,
    provider: str,
    system_message: str = "",
    user_message: str = "",
    response: str = "",
    success: bool = True,
    error_message: str | None = None,
    duration_seconds: float | None = None,
    is_fallback: bool = False,
    fallback_attempt: int = 0,
    **kwargs
) -> str:
    """Convenience function to log a complete LLM interaction"""
    logger: LLMDebugLogger = get_llm_debug_logger()

    interaction_id: str = logger.start_interaction(
        step_name=step_name,
        model=model,
        provider=provider,
        is_fallback=is_fallback,
        fallback_attempt=fallback_attempt,
        **kwargs
    )

    logger.log_request(
        system_message=system_message,
        user_message=user_message,
        **kwargs
    )

    logger.log_response(
        response=response,
        success=success,
        error_message=error_message,
        duration_seconds=duration_seconds
    )

    logger.finish_interaction()
    return interaction_id
