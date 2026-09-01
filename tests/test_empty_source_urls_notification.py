"""The empty-context notification for provided source_urls must fire (#1978).

`ResearchConductor.conduct_research()` guarded the "I was unable to find
relevant context in the provided sources" notification with

    if research_data and len(research_data) == 0 and self.researcher.verbose:

which is a contradiction: a truthy value is never length zero. The branch
could not execute, so a user passing `source_urls` that yielded nothing was
told nothing and simply received a thin report.

These tests drive the real `conduct_research` with `_get_context_by_urls`
stubbed, and assert on what actually reaches `stream_output`.
"""
import sys
import types
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.skills.researcher import ResearchConductor


def _researcher(*, source_urls, verbose=True):
    r = types.SimpleNamespace(
        source_urls=source_urls,
        complement_source_urls=False,
        verbose=verbose,
        websocket=None,
        report_source="web",
        query="anything",
        query_domains=[],
        retrievers=[],
        agent="agent",
        role="role",
        cfg=types.SimpleNamespace(),
        headers={},
        prompt_family=None,
        add_costs=lambda *a, **k: None,
    )
    return r


async def _run(research_data, verbose=True):
    """Run conduct_research with the URL path stubbed, capture notifications."""
    researcher = _researcher(source_urls=["https://example.com/a"], verbose=verbose)
    conductor = ResearchConductor(researcher)
    conductor.logger = types.SimpleNamespace(
        info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None
    )
    seen = []

    async def fake_stream_output(kind, key, message, websocket=None, *a, **kw):
        seen.append((kind, key, message))

    with patch.object(ResearchConductor, "_get_context_by_urls",
                      AsyncMock(return_value=research_data)), \
         patch("gpt_researcher.skills.researcher.stream_output", fake_stream_output), \
         patch.object(ResearchConductor, "plan_research", AsyncMock(return_value=[])):
        try:
            await conductor.conduct_research()
        except Exception:
            # Later stages of conduct_research are out of scope here; the
            # notification decision happens before them.
            pass
    return seen


@pytest.mark.asyncio
async def test_empty_context_emits_the_notification():
    seen = await _run(research_data=[])
    keys = [k for _, k, _ in seen]
    assert "answering_from_memory" in keys, (
        f"expected the empty-context notification, got {keys}"
    )


@pytest.mark.asyncio
async def test_nonempty_context_stays_quiet():
    seen = await _run(research_data=["some real scraped context"])
    keys = [k for _, k, _ in seen]
    assert "answering_from_memory" not in keys, (
        "the notification fired even though context was found"
    )


@pytest.mark.asyncio
async def test_quiet_when_not_verbose():
    seen = await _run(research_data=[], verbose=False)
    keys = [k for _, k, _ in seen]
    assert "answering_from_memory" not in keys


def test_no_self_contradictory_guard_in_conduct_research():
    """Guard the shape of the mistake, not its text: `x and len(x) == 0`.

    Matching the source as a string would also match the comment explaining
    the bug, so this walks the AST and looks for a real BoolOp of the form
    `<name> and len(<same name>) == 0`, which can never be true.
    """
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(ResearchConductor.conduct_research)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
            continue
        names = {ast.unparse(v) for v in node.values if isinstance(v, ast.Name)}
        for value in node.values:
            if not isinstance(value, ast.Compare):
                continue
            txt = ast.unparse(value)
            for name in names:
                if txt in (f"len({name}) == 0", f"0 == len({name})"):
                    raise AssertionError(
                        f"contradictory guard from #1978 is back: `{ast.unparse(node)}`"
                    )
