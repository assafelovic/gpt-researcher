import os
import sys
from typing import Any, Awaitable, Callable

RunResearchTask = Callable[..., Awaitable[Any]]


def _ensure_repo_root_on_path() -> None:
    """Ensure top-level repo root is importable for multi-agent modules."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def _resolve_run_research_task() -> RunResearchTask:
    _ensure_repo_root_on_path()

    try:
        from multi_agents.main import run_research_task
        return run_research_task
    except Exception:
        try:
            from multi_agents_ag2.main import run_research_task
            return run_research_task
        except Exception as ag2_error:
            raise ImportError(
                "Could not import run_research_task from multi_agents or multi_agents_ag2"
            ) from ag2_error


async def run_multi_agent_task(*args, **kwargs) -> Any:
    run_research_task = _resolve_run_research_task()
    return await run_research_task(*args, **kwargs)
