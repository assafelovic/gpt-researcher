"""The key point method comparison runs end to end on a scripted judge."""

import json
import re

import pytest

from evals.research_eval.cache import EvalCache
from evals.research_eval.judge import Judge
from evals.research_eval.key_points_methods import METHODS, compare_question

pytestmark = pytest.mark.asyncio

THINGS = ("prices", "recycling", "scope", "chemistry")


async def fake(prompt):
    if "Find the single things they name" in prompt:
        # A point goes in the group of every thing word it contains.
        ids = re.findall(r"^(L\d+\.\d+) (.+)$", prompt, re.M)
        return json.dumps({"groups": [
            {"name": w, "points": [pid for pid, text in ids if w in text], "about_report": w == "scope"}
            for w in THINGS if any(w in text for _, text in ids)]})
    if "Work in two steps" in prompt:
        return json.dumps({"asked": ["prices"], "key_points": ["prices of cells", "recycling plants"]})
    if "in two layers" in prompt:
        return json.dumps({"aspects": [{"aspect": "cell prices", "sub_points": ["prices by chemistry"]}]})
    if "list 2 to 4 sub-points" in prompt:
        kps = re.findall(r"^\d+\. (.+)$", prompt.split("Key points:")[1], re.M)
        return json.dumps({"aspects": [{"aspect": k, "sub_points": [k + " detail"]} for k in kps]})
    if "outline of an excellent answer" in prompt:
        return json.dumps({"sections": [{"heading": "Prices", "points": ["prices now", "chemistry mix"]}]})
    return json.dumps({"key_points": ["prices and recycling", "scope of the comparison"]})


async def test_compare_question_scores_every_method():
    judge = Judge(EvalCache(":memory:"), model="m", complete=fake)
    res = await compare_question(judge, "q1", "How are EV battery prices changing?")
    assert set(res["stats"]) == set(METHODS)
    # Pool things: named by 2+ lists and not about the report.
    assert sorted(g["name"] for g in res["pool"]) == ["chemistry", "prices", "recycling"]
    cur = res["stats"]["current"][0]
    # "prices and recycling" names two things: compound 1.5 over its two points.
    assert cur["compound"] == 1.5 and cur["about_report"] == 1 and cur["stability"] == 1.0
    assert cur["coverage"] == pytest.approx(2 / 3, abs=1e-3)
    # The layered sub-point reaches "chemistry", which the outline names too.
    layered = res["stats"]["layered"][0]
    assert layered["coverage"] == pytest.approx(2 / 3, abs=1e-3) and layered["sub_points"] == 1
    assert layered["outline_coverage"] == 1.0
    plus = res["methods"]["consensus+"][0]
    assert plus["key_points"] == res["methods"]["consensus"][0]["key_points"]
    assert all(plus["sub_points"][k] for k in plus["key_points"])
