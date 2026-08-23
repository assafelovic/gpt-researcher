"""Trace-based behavioural tests for gpt-researcher, using Monocle Test Tools.

Each test asserts against the Monocle trace a run emits -- which agent ran, what
it was asked, what it produced, and its token/duration cost. gpt-researcher's
``multi_agents`` flow is a LangGraph state graph: its web access surfaces as
``retrieval`` / ``embedding.modelapi`` spans rather than
``agentic.tool.invocation`` spans, so there are no tool-invocation spans to
assert on -- the tests assert the agent, the report input/output, and the
workflow budget the traces actually contain.

The three offline traces were captured by driving this fork's OWN agent (via
``conftest.run_gptresearcher`` -> the same ``ChiefEditorAgent`` path as
``multi_agents/main.py``) under monocle_apptrace 0.8.8; they live in
``tests/monocle-test/traces/`` and are loaded by file with
``with_trace_source("file", trace_path=...)``.

    # offline replay (no keys, no network) -- run under the shared testtools venv:
    pytest tests/monocle-test/ -k "not live"
    # full suite incl. the live run (needs OPENAI + a retriever key + gpt-researcher
    # deps) -- run under the fork's own venv:
    pytest tests/monocle-test/

Eval layer is intentionally omitted from the offline tests: on 0.8.8 the local
eval path does not compose with file-loaded traces, so the file-loaded suite is
structural-only. The Okahu eval block is left commented for when a key is wired.
"""
import pytest

from monocle_test_tools import TraceAssertion

from conftest import TRACES, run_gptresearcher

# Three recorded runs, one per curated question, captured from this fork's agent.
TRACE_HYPE = str(TRACES / "monocle_trace_gpt-researcher_27bfd5ba32266fa2139cb1a0bdd0f8a7_2026-07-09_12.29.22.json")
TRACE_ENERGY = str(TRACES / "monocle_trace_gpt-researcher_6dbc97f11510455934d719ce1d3e6dd9_2026-07-09_12.31.50.json")
TRACE_QUANTUM = str(TRACES / "monocle_trace_gpt-researcher_1f9c5ea5edbaa5d80e8ec015a2a9ec5f_2026-07-09_12.34.16.json")


# --- Offline: replay recorded good traces ---------------------------------

def test_ai_hype_cycle(monocle_trace_asserter: TraceAssertion):
    """Analytical question: "Is AI in a hype cycle?"

    Real trace: ~156,006 total tokens, ~134s workflow duration, a LangGraph
    multi-agent run (chief editor + researcher / writer / reviewer / reviser /
    publisher). The report frames AI against Gartner's hype-cycle model.
    """
    monocle_trace_asserter.with_trace_source("file", trace_path=TRACE_HYPE)

    monocle_trace_asserter.called_agent("LangGraph", min_count=2)
    monocle_trace_asserter.does_not_call_agent("CrewAI")
    monocle_trace_asserter.contains_input("hype")
    monocle_trace_asserter.contains_output("Gartner")
    monocle_trace_asserter.contains_any_output("hype cycle", "hype", "expectations")
    monocle_trace_asserter.under_token_limit(220_000)
    monocle_trace_asserter.under_duration(300, span_type="workflow")

    # Eval layer (deferred -- set OKAHU_API_KEY and uncomment to enable; note
    # evals do not compose with file-loaded traces on 0.8.8):
    # monocle_trace_asserter.with_evaluation("okahu").check_eval("hallucination", "no_hallucination") \
    #     .check_eval("contextual_precision", "high_precision")


def test_renewables_factcheck(monocle_trace_asserter: TraceAssertion):
    """Fact-check task: is renewable energy now cheaper than fossil fuels?

    Real trace: ~152,490 total tokens, ~134s workflow duration, a LangGraph
    multi-agent run. The report grounds the cost comparison in LCOE (levelized
    cost of energy).
    """
    monocle_trace_asserter.with_trace_source("file", trace_path=TRACE_ENERGY)

    monocle_trace_asserter.called_agent("LangGraph", min_count=2)
    monocle_trace_asserter.does_not_call_agent("CrewAI")
    monocle_trace_asserter.contains_input("renewable")
    monocle_trace_asserter.contains_output("LCOE")
    monocle_trace_asserter.contains_any_output("levelized cost", "renewable", "fossil")
    monocle_trace_asserter.under_token_limit(220_000)
    monocle_trace_asserter.under_duration(300, span_type="workflow")

    # monocle_trace_asserter.with_evaluation("okahu").check_eval("hallucination", "no_hallucination") \
    #     .check_eval("contextual_precision", "high_precision")


def test_quantum_computing(monocle_trace_asserter: TraceAssertion):
    """Technical survey: "What is the current state of quantum computing in 2025?"

    Real trace: ~99,066 total tokens, ~137s workflow duration, a LangGraph
    multi-agent run. The report surveys qubit hardware and the field's progress.
    """
    monocle_trace_asserter.with_trace_source("file", trace_path=TRACE_QUANTUM)

    monocle_trace_asserter.called_agent("LangGraph", min_count=2)
    monocle_trace_asserter.does_not_call_agent("CrewAI")
    monocle_trace_asserter.contains_input("quantum")
    monocle_trace_asserter.contains_output("quantum")
    monocle_trace_asserter.contains_any_output("qubit", "quantum", "computing")
    monocle_trace_asserter.under_token_limit(160_000)
    monocle_trace_asserter.under_duration(300, span_type="workflow")

    # monocle_trace_asserter.with_evaluation("okahu").check_eval("hallucination", "no_hallucination") \
    #     .check_eval("contextual_precision", "high_precision")


# --- Live: run the real multi-agent workflow (needs OPENAI + a retriever key) --
# One live research run. Output varies run to run, so it asserts the agent,
# phrasing-robust output terms, and generous budgets -- not exact text.

@pytest.mark.asyncio
async def test_quantum_computing_live(monocle_trace_asserter: TraceAssertion):
    """Live research run on a contrasting topic: state of quantum computing."""
    await monocle_trace_asserter.validator.test_workflow_async(
        run_gptresearcher,
        {"test_input": ("What is the current state of quantum computing in 2025? Give a brief, sourced overview.",)},
    )
    monocle_trace_asserter.called_agent("LangGraph", min_count=2)
    monocle_trace_asserter.contains_any_output("quantum", "qubit", "computing")
    monocle_trace_asserter.under_token_limit(1_000_000)
    monocle_trace_asserter.under_duration(400, span_type="workflow")

    # monocle_trace_asserter.with_evaluation("okahu").check_eval("hallucination", "no_hallucination") \
    #     .check_eval("contextual_precision", "high_precision")
