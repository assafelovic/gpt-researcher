"""
Capture layer: hooks that turn one research run into spans and chunks.
---------------------------------------------------------------------
`RunCapture` monkeypatches the library for the duration of a `with` block and
restores every original on exit, including on error. The library itself is
never edited. Hook points (see eval-design/infrastructure.md §2.1):

  run   GPTResearcher.conduct_research          span "research" (one per researcher)
  H1    ResearchConductor.plan_research         span "plan": query -> sub_queries
  H2    DeepResearchSkill.generate_research_plan    span "deep_plan": query -> questions
        DeepResearchSkill.deep_research             span "deep_level": one per level
        DeepResearchSkill.generate_search_queries   serp queries + goals on the level
        DeepResearchSkill.process_research_results  learnings / follow-ups on the
                                                    research span that produced them
  H3    ResearchConductor._get_new_urls         proposed_urls / new_urls on the
                                                current span
  H4    ResearchConductor._process_sub_query    span "sub_query": chunk_ids
  H5    ResearchConductor._get_context_from_initial_results
                                                span "initial_results": chunk_ids
  H6    context_manager.select_context          filter mode / pages on current span
  --    GPTResearcher.get_subtopics             span "subtopics" (detailed mode)
  --    GPTResearcher.add_costs                 run cost across nested researchers
  --    library log records                     health counters (fallbacks, errors)

Parent links come from the ContextVar in tracing.py, with two exceptions that
the call graph alone cannot express:

  * Sub-queries are attached to the "plan" span that proposed them. The plan
    span has closed by the time they run, so the plan's id is carried in a
    second ContextVar scoped to the researcher.
  * A deeper deep-research level is launched from the parent level's body, not
    from the branch that produced its follow-up questions. It is re-parented to
    that branch by matching the research goal embedded in its query.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any

from .chunks import split_context
from .tracing import Span, Tracer

# The plan span whose sub-queries are being executed by this researcher.
_current_plan: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "research_eval_current_plan", default=None)
# The research span most recently finished in this Task (deep mode: lets
# process_research_results find the branch it is summarising).
_last_research: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "research_eval_last_research", default=None)


# Library log messages that signal a degraded run. Matched by prefix.
HEALTH_EVENTS = {
    "jev_fallback":       ("gpt_researcher.context.select", "Jev context filter unavailable"),
    "embedding_fallback": ("gpt_researcher.context.select", "Embedding context filter unavailable"),
    "subquery_errors":    ("research", "Error processing sub-query"),
    "web_search_errors":  ("research", "Error during web search"),
    "mcp_fallback":       ("research", "MCP cache not available"),
}


class _HealthHandler(logging.Handler):
    def __init__(self, logger_name: str, capture: "RunCapture") -> None:
        super().__init__(level=logging.WARNING)
        self.logger_name = logger_name
        self.capture = capture

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
        except Exception:
            return
        for key, (name, prefix) in HEALTH_EVENTS.items():
            if name == self.logger_name and msg.startswith(prefix):
                self.capture.health[key] = self.capture.health.get(key, 0) + 1
                span = Tracer.current()
                if span is not None:
                    span.attributes.setdefault("health_events", []).append(key)


class RunCapture:
    """Context manager that records one run. Not re-entrant; do not nest."""

    def __init__(self, tracer: Tracer | None = None) -> None:
        self.tracer = tracer or Tracer()
        self.chunks: dict[str, dict] = {}
        self.health: dict[str, int] = {k: 0 for k in HEALTH_EVENTS}
        self.parse_warnings: list[str] = []
        self.cost_usd = 0.0
        self.context_filters: set[str] = set()
        self._restore: list[tuple[Any, str, Any]] = []
        self._handlers: list[tuple[logging.Logger, logging.Handler]] = []

    # --- recording helpers (no library imports; unit-testable) -------------

    def add_context(self, span: Span, text: Any) -> list[str]:
        """Split `text` into chunks, store them once, link them from `span`."""
        if isinstance(text, list):
            text = "\n".join(str(t) for t in text)
        chunks, warnings = split_context(text or "")
        ids = []
        for c in chunks:
            cid = c.pop("id")
            if cid not in self.chunks:
                self.chunks[cid] = {**c, "jev_score": None}
            ids.append(cid)
        span.attributes.setdefault("chunk_ids", []).extend(ids)
        for w in warnings:
            span.attributes.setdefault("parse_warnings", []).append(w)
            self.parse_warnings.append(w)
        return ids

    def _deep_parent_for(self, query: str, level: Span | None) -> str | None:
        """The research branch whose goal / follow-ups produced `query`."""
        if level is None or "Previous research goal:" not in (query or ""):
            return None
        for sp in reversed(self.tracer.spans):
            if (sp.name == "research" and sp.parent_id == level.span_id
                    and sp.attributes.get("research_goal")
                    and f"Previous research goal: {sp.attributes['research_goal']}" in query):
                return sp.span_id
        return None

    # --- patching ------------------------------------------------------------

    def _patch(self, owner: Any, name: str, replacement: Any) -> None:
        # Save the raw attribute (from the class dict for classes) so that
        # restoring it puts back exactly what was there.
        original = owner.__dict__[name] if isinstance(owner, type) else getattr(owner, name)
        self._restore.append((owner, name, original))
        setattr(owner, name, replacement)

    def __enter__(self) -> "RunCapture":
        from gpt_researcher.agent import GPTResearcher
        from gpt_researcher.context.select import resolve_context_filter
        from gpt_researcher.skills import context_manager as cm_module
        from gpt_researcher.skills.deep_research import DeepResearchSkill
        from gpt_researcher.skills.researcher import ResearchConductor

        cap, tracer = self, self.tracer

        # -- researcher ---------------------------------------------------------
        orig_conduct = GPTResearcher.conduct_research

        async def conduct_research(self, *a, **k):
            attrs = {"query": self.query, "report_type": self.report_type,
                     "parent_query": self.parent_query or None}
            parent = Tracer.current()
            if parent is not None and parent.name == "deep_level":
                for q in parent.attributes.get("serp_queries", []):
                    if q.get("query") == self.query:
                        attrs["research_goal"] = q.get("goal")
                        break
            plan_token = _current_plan.set(None)
            try:
                with tracer.span("research", **attrs) as sp:
                    out = await orig_conduct(self, *a, **k)
            finally:
                _current_plan.reset(plan_token)
            _last_research.set(sp.span_id)
            return out

        self._patch(GPTResearcher, "conduct_research", conduct_research)

        orig_add_costs = GPTResearcher.add_costs

        def add_costs(self, cost):
            orig_add_costs(self, cost)
            cap.cost_usd += float(cost)

        self._patch(GPTResearcher, "add_costs", add_costs)

        orig_subtopics = GPTResearcher.get_subtopics

        async def get_subtopics(self, *a, **k):
            with tracer.span("subtopics", query=self.query) as sp:
                out = await orig_subtopics(self, *a, **k)
                items = getattr(out, "subtopics", None) or []
                sp.attributes["subtopics"] = [getattr(s, "task", str(s)) for s in items]
            return out

        self._patch(GPTResearcher, "get_subtopics", get_subtopics)

        # -- H1 plan -------------------------------------------------------------
        orig_plan = ResearchConductor.plan_research

        async def plan_research(self, query, *a, **k):
            with tracer.span("plan", query=query) as sp:
                out = await orig_plan(self, query, *a, **k)
                # Copy: the caller appends the core query to this same list.
                sp.attributes["sub_queries"] = list(out or [])
            _current_plan.set(sp.span_id)
            return out

        self._patch(ResearchConductor, "plan_research", plan_research)

        # -- H4 sub-query --------------------------------------------------------
        orig_sub = ResearchConductor._process_sub_query

        async def process_sub_query(self, sub_query, *a, **k):
            with tracer.span("sub_query", parent_id=_current_plan.get(), query=sub_query,
                             is_core_query=(sub_query == self.researcher.query),
                             proposed_urls=[], new_urls=[]) as sp:
                out = await orig_sub(self, sub_query, *a, **k)
                cap.add_context(sp, out)
            return out

        self._patch(ResearchConductor, "_process_sub_query", process_sub_query)

        # -- H5 initial results --------------------------------------------------
        orig_initial = ResearchConductor._get_context_from_initial_results

        async def initial_results(self, query, *a, **k):
            # Belongs to the researcher's root query, not to the plan.
            research = Tracer.current()
            parent = research.span_id if research else None
            if research is not None and research.name == "plan":
                parent = research.parent_id
            with tracer.span("initial_results", parent_id=parent, query=query,
                             proposed_urls=[], new_urls=[]) as sp:
                out = await orig_initial(self, query, *a, **k)
                cap.add_context(sp, out)
            return out

        self._patch(ResearchConductor, "_get_context_from_initial_results", initial_results)

        # -- H3 URL de-duplication ----------------------------------------------
        orig_new_urls = ResearchConductor._get_new_urls

        async def get_new_urls(self, url_set_input, *a, **k):
            proposed = list(url_set_input or [])
            accepted = await orig_new_urls(self, url_set_input, *a, **k)
            sp = Tracer.current()
            if sp is not None:
                sp.attributes.setdefault("proposed_urls", []).extend(proposed)
                sp.attributes.setdefault("new_urls", []).extend(list(accepted or []))
            return accepted

        self._patch(ResearchConductor, "_get_new_urls", get_new_urls)

        # -- H6 context selection -----------------------------------------------
        orig_select = cm_module.select_context

        async def select_context(query, pages, cfg, *a, **k):
            mode = resolve_context_filter(getattr(cfg, "context_filter", None))
            cap.context_filters.add(mode)
            sp = Tracer.current()
            if sp is not None:
                sp.attributes["context_filter"] = mode
                sp.attributes["pages_in"] = sp.attributes.get("pages_in", 0) + len(pages or [])
            return await orig_select(query, pages, cfg, *a, **k)

        self._patch(cm_module, "select_context", select_context)

        # -- H2 deep research ----------------------------------------------------
        orig_deep_plan = DeepResearchSkill.generate_research_plan

        async def generate_research_plan(self, query, *a, **k):
            with tracer.span("deep_plan", query=query) as sp:
                out = await orig_deep_plan(self, query, *a, **k)
                sp.attributes["questions"] = list(out or [])
            return out

        self._patch(DeepResearchSkill, "generate_research_plan", generate_research_plan)

        orig_deep = DeepResearchSkill.deep_research

        async def deep_research(self, query, breadth, depth, *a, **k):
            level = Tracer.current()
            if level is not None and level.name != "deep_level":
                level = None
            parent = cap._deep_parent_for(query, level)
            with tracer.span("deep_level", parent_id=parent, query=query,
                             breadth=breadth, depth=depth, serp_queries=[]):
                return await orig_deep(self, query, breadth, depth, *a, **k)

        self._patch(DeepResearchSkill, "deep_research", deep_research)

        orig_serp = DeepResearchSkill.generate_search_queries

        async def generate_search_queries(self, query, *a, **k):
            out = await orig_serp(self, query, *a, **k)
            sp = Tracer.current()
            if sp is not None and sp.name == "deep_level":
                sp.attributes["serp_queries"] = [
                    {"query": q.get("query"), "goal": q.get("researchGoal")} for q in out or []]
            return out

        self._patch(DeepResearchSkill, "generate_search_queries", generate_search_queries)

        orig_process = DeepResearchSkill.process_research_results

        async def process_research_results(self, query, *a, **k):
            out = await orig_process(self, query, *a, **k)
            sp = tracer.get(_last_research.get())
            if sp is not None and sp.attributes.get("query") == query:
                sp.attributes["learnings"] = list((out or {}).get("learnings") or [])
                sp.attributes["follow_ups"] = list((out or {}).get("followUpQuestions") or [])
                sp.attributes["learning_sources"] = dict((out or {}).get("citations") or {})
            return out

        self._patch(DeepResearchSkill, "process_research_results", process_research_results)

        # -- health --------------------------------------------------------------
        for name in sorted({n for n, _ in HEALTH_EVENTS.values()}):
            lg = logging.getLogger(name)
            h = _HealthHandler(name, self)
            lg.addHandler(h)
            self._handlers.append((lg, h))
        return self

    def __exit__(self, *exc) -> None:
        for owner, name, original in reversed(self._restore):
            setattr(owner, name, original)
        self._restore = []
        for lg, h in self._handlers:
            lg.removeHandler(h)
        self._handlers = []
        return None
