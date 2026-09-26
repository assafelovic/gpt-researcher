"""Each top-level review loop in the multi_agents graph must declare its revision counter.

The graph langgraph.json serves has two top-level review loops, human <-> planner and
fact_checker <-> writer; tests/gebra_multi_agents.toml names the ResearchState counter
each loop's router compares against a maximum. gebra reads the graph's wiring and checks
that every loop has a declared counter and that each named key is in ResearchState; it
never invokes a node, router, tool or model, and never checks that a node moves its
counter. Importing multi_agents.agent runs its top-level code, so the test does that
in a temporary directory.

If P-02 termination-witness fails with cycle-without-termination-witness (FATAL,
DEFENSIBLE), the loop it names needs a [nodes.<node>] entry naming the counter the
loop increments and its router compares against a maximum; a variant-key-not-in-state
note means an entry's key has left ResearchState.
"""
from pathlib import Path

import pytest

gebra = pytest.importorskip("gebra")
verify = pytest.importorskip("gebra.verify").verify

SIDECAR = str(Path(__file__).resolve().parent / "gebra_multi_agents.toml")


def test_each_top_level_review_loop_declares_its_counter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # importing multi_agents.agent creates ./outputs/run_*
    from multi_agents.agent import graph

    loops = verify(gebra.extract(graph, sidecar=SIDECAR).ir).outcome_for("termination-witness")
    assert loops.result == "pass", loops.failure
