from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gpt_researcher.skills.context_manager import ContextManager


@pytest.mark.asyncio
@pytest.mark.parametrize("first", [["best", "next"], ["next", "best"]])
@pytest.mark.parametrize("max_results", [1, 3, 10])
async def test_written_context_keeps_retrieval_rank(first, max_results):
    manager = ContextManager(SimpleNamespace(kwargs={}))
    retrieve = AsyncMock(side_effect=[first, ["next", "shared", "last"]])
    manager._ContextManager__get_similar_written_contents_by_query = retrieve

    result = await manager.get_similar_written_contents_by_draft_section_titles(
        "current section", ["draft section"], [], max_results=max_results
    )

    assert result == [*first, "shared", "last"][:max_results]


@pytest.mark.asyncio
async def test_written_context_with_no_matches():
    manager = ContextManager(SimpleNamespace(kwargs={}))
    manager._ContextManager__get_similar_written_contents_by_query = AsyncMock(
        return_value=[]
    )

    assert await manager.get_similar_written_contents_by_draft_section_titles(
        "current section", [], []
    ) == []
