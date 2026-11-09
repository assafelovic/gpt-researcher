"""Regression test: ReportGenerator.write_report() must honor the
researcher's websocket at call time, not the value captured once in
__init__.

ReportGenerator.__init__ builds self.research_params from
researcher.websocket at construction time (GPTResearcher.__init__
constructs self.report_generator = ReportGenerator(self) up front, long
before conduct_research() or write_report() ever run). A caller that
mutates researcher.websocket after construction -- e.g. to stream
progress only during conduct_research(), then disable streaming before
write_report() so a transient LLM failure gets its normal retry budget
back instead of being treated as an unreplayable live stream (see
utils/llm.py: max_attempts = 1 if (stream and websocket is not None)
else 10) -- had that change silently ignored: write_report() always
re-copied the frozen __init__-time value.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.skills.writer import ReportGenerator


def _make_researcher(websocket):
    return SimpleNamespace(
        query="q",
        cfg=SimpleNamespace(agent_role="role prompt"),
        role="role",
        report_type="research_report",
        report_source="web",
        tone="objective",
        websocket=websocket,
        headers={},
        verbose=False,
        context="some research context",
        kwargs={},
        add_costs=lambda *a, **kw: None,
        get_research_images=lambda: [],
    )


@pytest.mark.asyncio
async def test_write_report_uses_live_websocket_not_construction_time_value():
    researcher = _make_researcher(websocket="constructed-with-this")
    generator = ReportGenerator(researcher)

    # Mutate after construction, as a caller disabling streaming before
    # write_report() would.
    researcher.websocket = None

    with patch(
        "gpt_researcher.skills.writer.generate_report",
        AsyncMock(return_value="the report"),
    ) as mock_generate_report:
        report = await generator.write_report()

    assert report == "the report"
    assert mock_generate_report.call_args.kwargs["websocket"] is None, (
        "write_report() must read researcher.websocket live, not the value "
        "frozen in research_params at ReportGenerator construction time"
    )


@pytest.mark.asyncio
async def test_write_report_still_passes_a_live_non_none_websocket():
    sentinel = object()
    researcher = _make_researcher(websocket=sentinel)
    generator = ReportGenerator(researcher)

    with patch(
        "gpt_researcher.skills.writer.generate_report",
        AsyncMock(return_value="the report"),
    ) as mock_generate_report:
        await generator.write_report()

    assert mock_generate_report.call_args.kwargs["websocket"] is sentinel
