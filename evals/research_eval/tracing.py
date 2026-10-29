"""
Lightweight span tracing for one research run.
----------------------------------------------
A run is a trace; every hooked step is a span with a parent. Spans are stored
flat and the tree is rebuilt on load. Field names follow OpenTelemetry
(trace_id / span_id / parent_id / name / attributes) so an archive can later be
exported to a trace viewer, but nothing here depends on the OTel SDK.

The current span lives in a ContextVar. Entering a span reads the current value
as its parent, makes itself current, and restores the previous value on exit.
`asyncio.gather` copies the context into each Task it creates, so concurrent
sub-queries cannot see each other's spans, and a researcher nested inside deep
research attaches itself under the span that launched it without any plumbing.

`asyncio.to_thread` also copies the context; a bare `run_in_executor` does not,
so a hook placed on a function that runs there would lose its parent. All the
hook points used by capture.py are coroutines on the event loop.
"""

from __future__ import annotations

import contextvars
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

_current_span: contextvars.ContextVar["Span | None"] = contextvars.ContextVar(
    "research_eval_current_span", default=None)


@dataclass
class Span:
    span_id: str
    parent_id: str | None
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float | None = None
    status: str = "ok"            # "ok" | "error"
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "attributes": self.attributes,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "error": self.error,
        }


class Tracer:
    """Collects the spans of one trace."""

    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self.spans: list[Span] = []
        self._by_id: dict[str, Span] = {}
        self._next = 0

    def _new_id(self) -> str:
        self._next += 1
        return f"s{self._next}"

    @staticmethod
    def current() -> Span | None:
        return _current_span.get()

    def get(self, span_id: str | None) -> Span | None:
        return self._by_id.get(span_id) if span_id else None

    @contextmanager
    def span(self, name: str, /, *, parent_id: str | None = None,
             **attributes: Any) -> Iterator[Span]:
        """Open a span under the current one (or under `parent_id` if given)."""
        if parent_id is None:
            cur = _current_span.get()
            parent_id = cur.span_id if cur else None
        sp = Span(span_id=self._new_id(), parent_id=parent_id, name=name,
                  attributes=dict(attributes), start_time=time.time())
        self.spans.append(sp)
        self._by_id[sp.span_id] = sp
        token = _current_span.set(sp)
        try:
            yield sp
        except BaseException as e:
            sp.status = "error"
            sp.error = f"{type(e).__name__}: {e}"
            raise
        finally:
            sp.end_time = time.time()
            _current_span.reset(token)

    def to_list(self) -> list[dict]:
        return [s.to_dict() for s in self.spans]
