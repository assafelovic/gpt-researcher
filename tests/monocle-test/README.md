# gpt-researcher behavioural tests (Monocle Test Tools)

Trace-based tests that lock in gpt-researcher's behaviour. Monocle records each
run of the `multi_agents` workflow as a structured trace -- the LangGraph agent
invocations, retrieval and embedding calls, token usage, and timings -- and each
test asserts against that trace: which agent ran, what it was asked, what it
produced, and its token/duration cost. A later prompt, model, or graph change
that regresses the behaviour fails here.

## Layout

- `test_gptresearcher.py` — the suite: two offline tests
- `conftest.py` — Monocle setup, `.env` loading, and the async `run_gptresearcher()`
- `traces/` — recorded good-trace fixtures the offline tests replay
- `requirements.txt` — dependencies

## Tests

| Test | Scenario | What it shows |
|---|---|---|
| `test_ai_hype_cycle` | "Is AI in a hype cycle?" (analytical) | agent invocation count, input/output, `contains_any_output`, budget |
| `test_renewables_factcheck` | Renewables-vs-fossil-fuels fact-check (heaviest run) | input/output, a negative agent assertion, budget |

The two runs contrast: an open analytical question (the lightest run, ~121k
tokens) versus a fact-check/verification task (the most expensive, ~644k tokens).
Budgets are the real numbers measured from each trace, rounded up with headroom.

gpt-researcher's web access surfaces as `retrieval` / `embedding.modelapi` spans,
not `agentic.tool.invocation` spans, so there are no tool-invocation spans to
assert on -- the tests assert the agent, the report input/output, and the
workflow budget.

## Run

```bash
pip install -r requirements.txt
pytest tests/monocle-test/ -k "not live"   # offline replays, no network, no keys
pytest tests/monocle-test/                 # also the live test (needs OPENAI_API_KEY + SERPER_API_KEY)
```

## Live test

`test_quantum_computing_live` drives the real multi-agent workflow
(`ChiefEditorAgent`) and asserts on the emitted trace. It needs `OPENAI_API_KEY`
plus a web retriever: gpt-researcher defaults to Tavily, and `conftest` falls back
to `RETRIEVER=serper` when no `TAVILY_API_KEY` is set, so a `SERPER_API_KEY` is
enough. Output varies run to run, so it asserts structure + budget, not exact text.

## Add your own test

1. Run gpt-researcher under Monocle and capture a trace of a run you're happy with
   (Monocle writes trace JSON to `.monocle/` by default).
2. Move it into `traces/` and load it with
   `monocle_trace_asserter.validator.add_remote_spans(JSONSpanLoader.from_json(path))`.
3. Assert with the fluent API — `called_agent(...)`, `contains_input/output(...)`,
   `contains_any_output(...)`, `under_token_limit(...)`,
   `under_duration(..., span_type="workflow")` — then add it alongside the others.

## Evaluations (optional)

Each test carries a commented-out `check_eval("hallucination", ...)` chain.
Monocle can run evaluation checks against a trace; set `OKAHU_API_KEY` and
uncomment to enable.
