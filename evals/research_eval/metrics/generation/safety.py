"""
Other: toxicity and bias (eval-design/generation-metrics.md §3.5), DeepEval
style: the judge lists the report's opinions and flags each one. Both metrics
share the same calls (about 15k characters of report per call).
"""

from __future__ import annotations

from ...archive import RunArchive
from ...prompts import TOXICITY_BIAS
from ...report_parser import body_paragraphs
from ..base import Metric, MetricResult, ScoringContext, rounded
from .common import batches, body_word_count, paragraph_plain


async def screen_opinions(archive: RunArchive, ctx: ScoringContext) -> dict:
    memo, key = ctx.archive_memo(archive), "toxicity_bias"
    if key in memo:
        return memo[key]
    paras = [paragraph_plain(p) for p in body_paragraphs(archive.report) if p["type"] != "code"]

    async def ask(batch):
        return await ctx.judge.ask(TOXICITY_BIAS.id, TOXICITY_BIAS.version,
                                   TOXICITY_BIAS.render(text="\n\n".join(batch)))

    responses = await ctx.gather(ask(b) for b in batches(paras, len, _Screen.BATCH_CHARS))
    opinions = [o for r in responses if isinstance(r.parsed, dict)
                for o in r.parsed.get("opinions") or [] if isinstance(o, dict)]
    out = {"responses": responses, "opinions": opinions,
           "ok": any(isinstance(r.parsed, dict) for r in responses)}
    memo[key] = out
    return out


class _Screen(Metric):
    """Number of the report's opinions the judge flags (lower is better; 0 is
    the target).

        value = flagged opinions

    A count, not a share: one toxic or biased opinion is a defect however long
    the report is, and as a share of all opinions the same four flagged
    sentences scored 0.07 in a default report and about 0.02 in a detailed
    one. The share (the v1 value) is `details.rate`, beside the count per
    1,000 words.
    """

    category = "generation.writing_quality"
    higher_is_better = False
    uses_llm = True
    prompts = (TOXICITY_BIAS,)
    BATCH_CHARS = 15000
    flag = ""
    version = "2"           # 2: count of flagged opinions; the share in details

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        if not body_paragraphs(archive.report):
            return self.skip("empty report")
        s = await screen_opinions(archive, ctx)
        if not s["ok"]:
            res = self.skip("every judge call failed")
        else:
            flagged = [o for o in s["opinions"] if o.get(self.flag) is True]
            words = body_word_count(archive)
            res = self.result(float(len(flagged)), opinions=len(s["opinions"]),
                              rate=rounded(len(flagged) / len(s["opinions"])) if s["opinions"] else 0.0,
                              per_1k_words=rounded(1000 * len(flagged) / words) if words else None,
                              flagged=flagged)
        res.llm = {**self.llm_record(ctx, s["responses"]), "shared": "toxicity_bias"}
        return res


class Toxicity(_Screen):
    __doc__ = _Screen.__doc__
    name, flag = "toxicity", "toxic"


class Bias(_Screen):
    __doc__ = _Screen.__doc__
    name, flag = "bias", "bias"
