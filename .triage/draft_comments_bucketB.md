# Bucket B — Draft close-comments for your review

**Nothing below is posted yet.** Review, then tell me "post all", "post all except #X, #Y", or edit any wording. I'll then use `gh issue comment` + `gh issue close` for each.

Legend: 🟢 = safe to close · 🟡 = borderline, recommend a look · ⚪ = recommend KEEP OPEN (real request buried in promo)

---

## 1) Stale / already-fixed (10) — all verified on current `master`

> Template: confirm the fix + invite reopen. Then close as completed.

**🟢 #1079** — LLM retry loop returned on first attempt
> This has been resolved — the LLM provider layer (`gpt_researcher/utils/llm.py` / `llm_provider/generic/base.py`) was rewritten with a proper retry/attempt loop and exception handling. Closing as fixed; please reopen if you still hit this on the latest version. Thanks for the report!

**🟢 #1098** — o3 / reasoning models reject `temperature`
> Reasoning models are now handled via `NO_SUPPORT_TEMPERATURE_MODELS` in `gpt_researcher/llm_provider/generic/base.py`, which strips the unsupported `temperature` arg for o1/o3/o4/gpt-5. Closing as fixed — note that for LiteLLM you'll need the exact model name to match. Reopen if it persists.

**🟢 #1105** — Inconsistent required Python versions
> Resolved — `pyproject.toml` now declares `requires-python = ">=3.11"`, matching the README. Closing.

**🟢 #1131** — Long prompts → FileNotFoundError (filename too long)
> Fixed — `sanitize_filename()` in `backend/server/server_utils.py` now hashes the task portion (`md5[:10]`) instead of embedding the full prompt, so filenames stay short. Closing as fixed.

**🟡 #1232** — npm package doesn't support https/wss host
> A contributor noted https/wss support was since added to the npm package. Closing as resolved — please reopen if you still see `ws://` being forced on an https host. _(Note: I verified the Python side but not the published npm package version — wording kept soft.)_

**🟢 #1254** — `parse_dimension` incorrect on decimals
> Fixed — `parse_dimension()` in `gpt_researcher/scraper/utils.py` now does `int(float(value))`, handling decimal values like `409.12`. (Percent values are still out of scope.) Closing.

**🟢 #1279** — `'list' object has no attribute 'split'` in count_words
> Fixed — `count_words()` in `gpt_researcher/skills/deep_research.py` now detects list input and joins it before counting. Closing as fixed; reopen if you reproduce on the latest version.

**🟢 #1391** — Could not connect to MCP Server via HTTP
> The MCP server moved to its own repo: https://github.com/assafelovic/gptr-mcp. Closing here — please file MCP-server issues in that repo. Thanks!

**🟢 #1398** — Runtime error (temperature None for ChatOpenAI)
> Same root cause as #1098 — reasoning models now strip `temperature` via `NO_SUPPORT_TEMPERATURE_MODELS` in `base.py`. Closing as fixed; reopen if it persists on the latest version.

**🟢 #1415** — `'PromptFamily' object has no attribute 'curate_soures'` (typo)
> Fixed — the typo is gone; the codebase consistently uses `curate_sources` now. Closing as resolved.

---

## 2) Duplicates (5)

**🟢 #1685** — anybrowse MCP integration
> Duplicate of #1684 — consolidating there. Closing.

**🟢 #1707** — Security audit findings (tool description injection)
> Duplicate of #1706 — same report. Closing to keep it in one place.

**🟢 #1744** — Merxex Integration: Agent-to-Agent Commerce
> Duplicate of #1736 — closing, let's keep one thread.

**🟢 #1745** — Proposal: Agent-to-Agent Commerce via Merxex
> Duplicate of #1736 — closing.

**🟢 #1747** — Standardizing Agent Commerce: Merxex Proposal
> Duplicate of #1736 — closing.

---

## 3) Promotional / out-of-scope (22)

> Template (polite decline): "Thanks for reaching out. This reads as a promotion for an external product/service rather than a bug or a concrete, open feature request, so I'm closing it to keep the tracker focused. If there's a specific, open-source integration you'd like to propose, a PR or a Discussions thread is the best path. 🙏"

🟢 Close as promo (apply template): **#1629** (MoltBridge), **#1687** (WheatCoin), **#1689** (AgentID), **#1699** (AI Village), **#1702** (ResearchClawBench — _or redirect to Discussions_), **#1706** (paid "$29 audit"), **#1711** (AgentFolio), **#1714** (Clarvia badge), **#1716** (Clarvia MCP), **#1728** (veritasacta receipts), **#1729** (Loaditout badge), **#1732** (trust-score promos), **#1733** (AgentWeb), **#1736** (Merxex), **#1789** (HVTracker), **#1796** (Agent Magnet), **#1801** (USDC federation), **#1808** (BGPT)

### Borderline — recommend a quick look before closing:

**⚪ #1076 — Add open-source provider AI/ML API** — RECOMMEND KEEP OPEN. This is a real, generic LLM-provider request (aimlapi.com). GPTR already supports many providers via LiteLLM; could be a clean community PR. Suggest labeling `good-first-issue`/`provider` and inviting a PR rather than closing.

**🟡 #1684 — anybrowse for Cloudflare-protected scraping** — The *product* pitch is promo, but the *underlying bug is real*: scrapers silently return on Cloudflare 403s. Suggested reply:
> The specific tool is out of scope, but the underlying problem — scrapers silently failing on Cloudflare-protected (403) pages — is valid. I'll repurpose this as a tracked bug for a generic fallback/clear-error path. _(Then relabel as bug instead of closing.)_

**🟡 #1704 — Plasmate extraction** / **🟡 #1751 — SerpBase SERP** — Vendor self-promos (SerpBase had a sockpuppet comment). Recommend close as promo unless you want generic "cheaper scraper/SERP option" tracked. Default: close.

---

## Proposed actions summary
- **Close now (32):** all 10 stale + 5 duplicates + 17 clear promo (#1702 your call on redirect-to-Discussions).
- **Keep open / relabel (3):** #1076 (provider PR invite), #1684 (convert to bug), + your call on #1704/#1751.
