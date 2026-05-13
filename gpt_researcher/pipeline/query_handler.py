import logging
from typing import Any, Optional

from ..config.research_config import ResearchSafetyMode
from ..metadata.safety_info import SafetyInfo
from ..utils.query_safety import detect_unsafe_query
from .query_logger import query_logger

logger = logging.getLogger(__name__)


class ResearchMetadata:
    def __init__(self, original_query: str = "", subqueries_generated: Optional[list] = None):
        self.original_query = original_query
        self.subqueries_generated = subqueries_generated or []


class ResearchResult:
    def __init__(
        self,
        query: str,
        safety_info: SafetyInfo,
        subqueries_generated: Optional[list] = None,
        error: bool = False,
        error_type: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.metadata = ResearchMetadata(original_query=query)
        self.safety_info = safety_info
        self.research_metadata = ResearchMetadata(
            subqueries_generated=subqueries_generated or []
        )
        self.error = error
        self.error_type = error_type
        self.message = message


class ResearchPipeline:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        mode_str = "TRANSPARENT"
        if config is not None:
            mode_str = getattr(config, "research_safety_mode", "TRANSPARENT")
        self.mode = ResearchSafetyMode(mode_str)

    def process(self, query: str) -> ResearchResult:
        subqueries: list = [query]

        if self.mode == ResearchSafetyMode.TRANSPARENT:
            safety_info = SafetyInfo(
                checked=False,
                mode="TRANSPARENT",
                blocked=False,
                reason=None,
                action_taken="proceeded_by_configuration",
            )
        elif self.mode == ResearchSafetyMode.STRICT:
            decision = detect_unsafe_query(query)
            if decision is not None:
                safety_info = SafetyInfo(
                    checked=True,
                    mode="STRICT",
                    blocked=True,
                    reason=decision.reason,
                    action_taken="blocked",
                )
            else:
                safety_info = SafetyInfo(
                    checked=True,
                    mode="STRICT",
                    blocked=False,
                    reason=None,
                    action_taken="proceeded_clean",
                )
        elif self.mode == ResearchSafetyMode.WARN_ONLY:
            decision = detect_unsafe_query(query)
            if decision is not None:
                safety_info = SafetyInfo(
                    checked=True,
                    mode="WARN_ONLY",
                    blocked=False,
                    reason=decision.reason,
                    action_taken="proceeded_with_warning",
                )
            else:
                safety_info = SafetyInfo(
                    checked=True,
                    mode="WARN_ONLY",
                    blocked=False,
                    reason=None,
                    action_taken="proceeded_clean",
                )
        else:
            safety_info = SafetyInfo(
                checked=False,
                mode="TRANSPARENT",
                blocked=False,
                reason=None,
                action_taken="proceeded_by_configuration",
            )

        log_entry = query_logger.log_query_start(query, safety_info.to_dict())
        log_entry["research_metadata"]["subqueries_generated"] = subqueries

        return ResearchResult(
            query=query,
            safety_info=safety_info,
            subqueries_generated=subqueries,
            error=False,
        )


research_pipeline = ResearchPipeline()
