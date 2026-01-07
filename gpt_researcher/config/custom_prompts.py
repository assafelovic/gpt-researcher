from typing import Any, Dict, List, Protocol, runtime_checkable
from dataclasses import dataclass


# Protocol classes for custom prompt callables with named parameters
@runtime_checkable
class AutoAgentInstructionsCallable(Protocol):
    def __call__(self) -> str: ...


@runtime_checkable
class GenerateSearchQueriesPromptCallable(Protocol):
    def __call__(
        self,
        question: str,
        parent_query: str,
        report_type: str,
        max_iterations: int,
        context: List[Dict[str, Any]],
    ) -> str: ...


@runtime_checkable
class GenerateReportPromptCallable(Protocol):
    def __call__(
        self,
        question: str,
        context: Any,
        report_source: str,
        report_format: str,
        tone: Any,
        total_words: int,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateResourceReportPromptCallable(Protocol):
    def __call__(
        self,
        question: str,
        context: str,
        report_source: str,
        report_format: str,
        tone: Any,
        total_words: int,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateCustomReportPromptCallable(Protocol):
    def __call__(
        self,
        query_prompt: str,
        context: str,
        report_source: str,
        report_format: str,
        tone: Any,
        total_words: int,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateOutlineReportPromptCallable(Protocol):
    def __call__(
        self,
        question: str,
        context: str,
        report_source: str,
        report_format: str,
        tone: Any,
        total_words: int,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateDeepResearchPromptCallable(Protocol):
    def __call__(
        self,
        question: str,
        context: str,
        report_source: str,
        report_format: str,
        tone: Any,
        total_words: int,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateSubtopicReportPromptCallable(Protocol):
    def __call__(
        self,
        current_subtopic: str,
        existing_headers: List,
        relevant_written_contents: List,
        main_topic: str,
        context: str,
        report_format: str,
        max_subsections: int,
        total_words: int,
        tone: Any,
        language: str,
    ) -> str: ...


@runtime_checkable
class GenerateReportIntroductionCallable(Protocol):
    def __call__(
        self, question: str, research_summary: str, language: str, report_format: str
    ) -> str: ...


@runtime_checkable
class GenerateReportConclusionCallable(Protocol):
    def __call__(
        self, query: str, report_content: str, language: str, report_format: str
    ) -> str: ...


@runtime_checkable
class CurateSourcesCallable(Protocol):
    def __call__(self, query: str, sources: Any, max_results: int) -> str: ...


@runtime_checkable
class GenerateSummaryPromptCallable(Protocol):
    def __call__(self, query: str, data: Any) -> str: ...


@runtime_checkable
class GenerateSubtopicsPromptCallable(Protocol):
    def __call__(self) -> str: ...


@runtime_checkable
class GenerateDraftTitlesPromptCallable(Protocol):
    def __call__(
        self, current_subtopic: str, main_topic: str, context: str, max_subsections: int
    ) -> str: ...


@dataclass
class CustomPrompts:
    """Override any prompt with a callable or template string.

    Each attribute can be either:
    - A string template with {placeholder} formatting
    - A callable function with the same signature as the original prompt method
    - None to use the default implementation

    Example:
        # String template
        custom = CustomPrompts(
            generate_report_prompt="Write a {language} report about {question}..."
        )

        # Callable function
        def my_report_prompt(question, context, report_source, report_format, tone, total_words, language):
            return f"Custom prompt for {question}..."

        custom = CustomPrompts(generate_report_prompt=my_report_prompt)
    """

    auto_agent_instructions: str | AutoAgentInstructionsCallable | None = None
    generate_search_queries_prompt: str | GenerateSearchQueriesPromptCallable | None = (
        None
    )
    generate_report_prompt: str | GenerateReportPromptCallable | None = None
    generate_resource_report_prompt: (
        str | GenerateResourceReportPromptCallable | None
    ) = None
    generate_custom_report_prompt: str | GenerateCustomReportPromptCallable | None = (
        None
    )
    generate_outline_report_prompt: str | GenerateOutlineReportPromptCallable | None = (
        None
    )
    generate_deep_research_prompt: str | GenerateDeepResearchPromptCallable | None = (
        None
    )
    generate_subtopic_report_prompt: (
        str | GenerateSubtopicReportPromptCallable | None
    ) = None
    generate_report_introduction: str | GenerateReportIntroductionCallable | None = None
    generate_report_conclusion: str | GenerateReportConclusionCallable | None = None
    curate_sources: str | CurateSourcesCallable | None = None
    generate_summary_prompt: str | GenerateSummaryPromptCallable | None = None
    generate_subtopics_prompt: str | GenerateSubtopicsPromptCallable | None = None
    generate_draft_titles_prompt: str | GenerateDraftTitlesPromptCallable | None = None
