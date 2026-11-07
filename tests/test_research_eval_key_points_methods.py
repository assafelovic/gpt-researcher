"""The key point method comparison runs end to end on a scripted judge."""

import json
import re

import pytest

from evals.research_eval.cache import EvalCache
from evals.research_eval.judge import Judge
from evals.research_eval.key_points_methods import METHODS, compare_question

pytestmark = pytest.mark.asyncio


async def fake(prompt):
    if "Group the points" in prompt:
        ids = re.findall(r"^(L\d+\.\d+) (.+)$", prompt, re.M)
        by = {}
        for pid, text in ids:
            by.setdefault(text.split()[0].lower(), []).append(pid)
        return json.dumps({"groups": [{"name": k, "points": v, "about_report": k == "scope"}
                                      for k, v in by.items()]})
    if "Work in two steps" in prompt:
        return json.dumps({"asked": ["prices"], "key_points": ["prices of cells", "recycling plants"]})
    if "in two layers" in prompt:
        return json.dumps({"aspects": [{"aspect": "prices of cells", "sub_points": ["by chemistry"]}]})
    return json.dumps({"key_points": ["prices and costs", "scope of the comparison", "recycling capacity"]})


async def test_compare_question_scores_every_method():
    judge = Judge(EvalCache(":memory:"), model="m", complete=fake)
    res = await compare_question(judge, "q1", "How are EV battery prices changing?")
    assert set(res["stats"]) == set(METHODS)
    # Pool aspects: "prices" and "recycling" (named by 2+ lists); "scope" is about the report.
    assert sorted(g["name"] for g in res["pool"]) == ["prices", "recycling"]
    cur = res["stats"]["current"][0]
    assert cur["coverage"] == 1.0 and cur["about_report"] == 1 and cur["stability"] == 1.0
    layered = res["stats"]["layered"][0]
    assert layered["coverage"] == 0.5 and res["methods"]["layered"][0]["sub_points"]
    # Consensus keeps the majority groups of its samples, not the report-scope one.
    assert res["methods"]["consensus"][0]["key_points"] == ["prices", "recycling"]
