"""
Perturbation test: does each metric move the right way when the run gets worse?
-------------------------------------------------------------------------------
A check of the evaluator, not of the agent. Each perturbation copies a frozen
run archive, injects one known defect into the report or the search trace, and
names the metrics that should get worse. Scoring the copies and comparing them
with the unchanged copy shows, per metric, whether it notices. Rule-based and
deterministic (no LLM writes the defects); the originals are never modified.

    # 1. make the copies (+ manifest.json) from one or more archives
    python -m evals.research_eval.perturb make RUN.json [RUN.json ...] --out DIR
    # 2. score them like any archive (unchanged paragraphs replay the cache);
    #    --dry-run first counts the judge calls that would be made
    python -m evals.research_eval.score DIR/*.json --results-dir DIR/results --dry-run
    python -m evals.research_eval.score DIR/*.json --results-dir DIR/results --max-calls N
    #    optional noise control: the __noise copies re-asked under a salt
    python -m evals.research_eval.score DIR/*__noise.json --results-dir DIR/results --judge-salt noise1
    # 3. the table: expected direction, change, verdict
    python -m evals.research_eval.perturb report DIR/manifest.json --results-dir DIR/results

`__base` is an unchanged copy (same prompts, so it replays the original
scores from the cache); `__noise` is another unchanged copy, meant to be scored
with --judge-salt so the judge is asked again: base vs noise is the judge's own
run-to-run spread, which a real change has to exceed.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import re
from pathlib import Path

from .archive import RunArchive, normalize_url
from .report_parser import REFERENCES_HEADING

# --- fixed test text --------------------------------------------------------
# Written for this test only; it lives in local copies of archives and is
# never published.

OFF_TOPIC = [
    "Sourdough bread depends on a stable starter culture of wild yeast and lactic acid "
    "bacteria. Bakers usually feed the starter with equal weights of flour and water and "
    "let the dough proof for twelve to eighteen hours before baking at a high temperature.",
    "In European football, the summer transfer window lets clubs register new players "
    "between June and the end of August. Clubs often spread transfer fees over several "
    "seasons, and loan deals with an option to buy have become a common way to manage wages.",
    "Tomato plants grow best with six to eight hours of direct sunlight a day and soil "
    "that drains well. Gardeners pinch off side shoots on vine varieties and water at the "
    "base of the plant in the morning to reduce the risk of leaf disease.",
]

TOXIC_BIASED = [
    "Anyone who still trusts these regulators is frankly an idiot, and the officials "
    "behind the rules are clueless bureaucrats who should be ashamed of themselves.",
    "Left-wing politicians only push measures like these because they instinctively "
    "hate business and success.",
    "Firms from developing countries simply cannot be trusted to follow the rules the "
    "way Western firms do.",
    "The critics of this approach are mostly whiny amateurs who do not understand basic "
    "economics and should keep quiet.",
]

OFF_TOPIC_CHUNKS = [
    ("https://offtopic-recipes.test/sourdough", "Sourdough starter guide",
     OFF_TOPIC[0] + " A rye starter ferments faster than one made with white flour."),
    ("https://offtopic-sports.test/transfers", "How football transfers work",
     OFF_TOPIC[1] + " Sell-on clauses give the selling club a share of any later sale."),
    ("https://offtopic-garden.test/tomatoes", "Growing tomatoes at home",
     OFF_TOPIC[2] + " Cherry tomatoes ripen earlier than beefsteak varieties."),
]

# Section headings and sentence cues of the writer's own analysis (for the
# facts-only perturbation). Coarse on purpose: the point is a report that
# reads as a list of facts.
_ANALYSIS_HEADING = re.compile(
    r"conclu|implicat|outlook|recommend|discussion|takeaway|future|analysis|insight|"
    r"perspective|assessment|summary|what (this|it) means|strategic|interpretation", re.I)
_ANALYSIS_CUE = re.compile(
    r"\b(suggests?|indicates?|implies|implications?|likely|unlikely|should|could|might|may|"
    r"must|therefore|thus|hence|consequently|overall|in conclusion|highlights?|underscores?|"
    r"demonstrates?|reflects?|signals?|means that|this shows|crucial|critical|"
    r"significant(?:ly)?|important(?:ly)?|my assessment|we (?:believe|recommend|expect)|"
    r"arguably|appears? to|seems? to|potential(?:ly)?|in practical terms|in practice|"
    r"best understood|the (?:main|key|real|biggest) (?:point|issue|change|risk|lesson))\b", re.I)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(*\[])")
_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
_BARE_URL = re.compile(r"\(?https?://[^\s)\]]+\)?")
_NUMBER = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")


# --- report helpers ---------------------------------------------------------

def split_report(md: str) -> tuple[list[str], list[str]]:
    """(body lines, references lines): references start at the last heading
    that names a references/sources section."""
    lines = md.split("\n")
    ref = None
    for i, line in enumerate(lines):
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m and REFERENCES_HEADING.match(m.group(1).strip().strip("*")):
            ref = i
    return (lines, []) if ref is None else (lines[:ref], lines[ref:])


def join_report(body: list[str], refs: list[str]) -> str:
    text = "\n".join(body).rstrip() + "\n"
    return text + ("\n" + "\n".join(refs).strip() + "\n" if refs else "")


def blocks(lines: list[str]) -> list[str]:
    """Blank-line separated blocks."""
    out, cur = [], []
    for line in lines:
        if line.strip():
            cur.append(line)
        elif cur:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return out


def is_heading(block: str) -> bool:
    return bool(re.match(r"^#{1,6}\s", block))


def is_prose(block: str) -> bool:
    """A paragraph of running text (not a heading, list, table, quote or code)."""
    first = block.lstrip()
    return not (is_heading(block) or first.startswith(("|", "-", "*", ">", "```"))
                or re.match(r"^\d+[.)]\s", first))


def sections(body: list[str]) -> tuple[list[str], list[list[str]]]:
    """(lines before the first level-2 heading, [level-2 sections, heading first])."""
    head, secs = [], []
    for line in body:
        if line.startswith("## "):
            secs.append([line])
        elif secs:
            secs[-1].append(line)
        else:
            head.append(line)
    return head, secs


def _outside_links(text: str, fn) -> str:
    """Apply fn to the text outside markdown link targets."""
    out, last = [], 0
    for m in re.finditer(r"\]\([^)]*\)", text):
        out.append(fn(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(fn(text[last:]))
    return "".join(out)


# --- perturbations ----------------------------------------------------------
# Each takes the archive data (a deep copy) and returns it changed, or None
# when it does not apply to this run.

def drop_half_sections(data: dict, rng: random.Random) -> dict | None:
    body, refs = split_report(data["report"]["markdown"])
    head, secs = sections(body)
    if len(secs) < 2:
        return None
    kept = [s for i, s in enumerate(secs) if i % 2 == 0]
    data["report"]["markdown"] = join_report(head + [l for s in kept for l in s], refs)
    return data


def strip_links(data: dict, rng: random.Random) -> dict | None:
    body, refs = split_report(data["report"]["markdown"])
    text = "\n".join(body)
    new = _LINK.sub(lambda m: m.group(1), text)
    new = _BARE_URL.sub("", new)
    new = re.sub(r"\(\s*[;,]?\s*\)", "", new)
    if new == text:
        return None
    data["report"]["markdown"] = join_report(new.split("\n"), refs)
    return data


def swap_citations(data: dict, rng: random.Random) -> dict | None:
    """Each URL the body cites -> the retrieved URL, not cited anywhere in the
    report, whose text is least like it: citations that exist but do not
    support what they are attached to."""
    archive = RunArchive(data)
    body, refs = split_report(data["report"]["markdown"])
    text = "\n".join(body)
    cited = list(dict.fromkeys(m.group(2) for m in _LINK.finditer(text)))
    cited_norm = {normalize_url(u) for u in cited}
    cited_norm |= {normalize_url(m.group(2)) for m in _LINK.finditer("\n".join(refs))}
    pool = [u for u in archive.chunks_by_url if u not in cited_norm]
    if len(pool) < 3:
        # Every retrieved page is cited (common in short reports): point each
        # citation at another retrieved page instead, still the least similar.
        pool = list(archive.chunks_by_url)
    if not cited or len(pool) < 2:
        return None

    def words(url: str) -> set[str]:
        ids = archive.chunks_by_url.get(normalize_url(url), [])
        return set(re.findall(r"[a-z]{4,}", " ".join(archive.chunks[c]["content"] for c in ids).lower()))

    original = {}                 # normalized URL -> a URL as the chunks spell it
    for c in archive.chunks.values():
        if c.get("url"):
            original.setdefault(normalize_url(c["url"]), c["url"])
    pool_words = {u: words(u) for u in pool}
    mapping = {}
    for i, u in enumerate(cited):
        w = words(u)
        ranked = sorted((p for p in pool if p != normalize_url(u)),
                        key=lambda p: (len(w & pool_words[p]) / (len(w | pool_words[p]) or 1), p))
        # least similar first; spread over the pool so not every link points to one page
        mapping[u] = original[ranked[i % max(1, min(len(ranked), 5))]]
    new = _LINK.sub(lambda m: f"[{m.group(1)}]({mapping.get(m.group(2), m.group(2))})", text)
    data["report"]["markdown"] = join_report(new.split("\n"), refs)
    data["meta"]["perturbation_mapping"] = mapping
    return data


def alter_numbers(data: dict, rng: random.Random) -> dict | None:
    """Every figure of 10 or more (or with decimals) in the body is changed:
    years +3, percentages to 0.4x, other figures to 1.7x."""
    body, refs = split_report(data["report"]["markdown"])
    changed = 0

    def change(seg: str) -> str:
        nonlocal changed

        def one(m: re.Match) -> str:
            nonlocal changed
            whole, frac = m.group(1), m.group(2) or ""
            n = float(whole.replace(",", "") + frac)
            if not frac and n < 10:
                return m.group(0)
            after = seg[m.end():m.end() + 2]
            if not frac and 1900 <= n <= 2100:
                v = n + 3
            elif after.lstrip().startswith("%"):
                v = n * 0.4
            else:
                v = n * 1.7
            changed += 1
            places = len(frac) - 1 if frac else 0
            s = f"{v:,.{places}f}" if "," in whole else f"{v:.{places}f}"
            return s

        return _NUMBER.sub(one, seg)

    out = []
    for line in body:
        out.append(line if line.startswith("#") else _outside_links(line, change))
    if not changed:
        return None
    data["report"]["markdown"] = join_report(out, refs)
    data["meta"]["perturbation_changed"] = changed
    return data


def insert_off_topic(data: dict, rng: random.Random) -> dict | None:
    body, refs = split_report(data["report"]["markdown"])
    head, secs = sections(body)
    if not secs:
        return None
    for i, para in enumerate(OFF_TOPIC):
        s = secs[min(len(secs) - 1, i * max(1, len(secs) // len(OFF_TOPIC)))]
        s[1:1] = ["", para, ""]
    data["report"]["markdown"] = join_report(head + [l for s in secs for l in s], refs)
    return data


def facts_only(data: dict, rng: random.Random) -> dict | None:
    """Drop the analysis: sections whose heading names a conclusion, outlook,
    implication ...; sentences with analysis cues; what is left of each
    paragraph becomes a bullet list of its sentences."""
    body, refs = split_report(data["report"]["markdown"])
    head, secs = sections(body)
    kept = [s for s in secs if not _ANALYSIS_HEADING.search(s[0])]
    if not kept:
        return None

    def strip(lines: list[str]) -> list[str]:
        out = []
        for b in blocks(lines):
            if not is_prose(b) or b.startswith("# "):
                out += [b, ""]
                continue
            sents = [s for s in _SENTENCE.split(" ".join(b.split("\n"))) if s.strip()]
            facts = [s for s in sents if not _ANALYSIS_CUE.search(s)]
            if facts:
                out += [f"- {s.strip()}" for s in facts] + [""]
        return out

    new_head = strip(head)
    new_secs = [[s[0], ""] + strip(s[1:]) for s in kept]
    data["report"]["markdown"] = join_report(new_head + [l for s in new_secs for l in s], refs)
    return data


def scramble_structure(data: dict, rng: random.Random) -> dict | None:
    """No headings below the title; body blocks in a random order."""
    body, refs = split_report(data["report"]["markdown"])
    bs = blocks(body)
    title = [b for b in bs if b.startswith("# ")][:1]
    rest = [b for b in bs if not is_heading(b)]
    if len(rest) < 3:
        return None
    rng.shuffle(rest)
    data["report"]["markdown"] = join_report("\n\n".join(title + rest).split("\n"), refs)
    return data


def insert_toxic_biased(data: dict, rng: random.Random) -> dict | None:
    """Append one toxic or biased opinion to each of four prose paragraphs
    spread over the body."""
    body, refs = split_report(data["report"]["markdown"])
    bs = blocks(body)
    prose = [i for i, b in enumerate(bs) if is_prose(b) and not b.startswith("# ")]
    if len(prose) < len(TOXIC_BIASED):
        return None
    step = len(prose) // len(TOXIC_BIASED)
    for k, sent in enumerate(TOXIC_BIASED):
        i = prose[k * step]
        bs[i] = bs[i].rstrip() + " " + sent
    data["report"]["markdown"] = join_report("\n\n".join(bs).split("\n"), refs)
    return data


def duplicate_subqueries(data: dict, rng: random.Random) -> dict | None:
    """Each plan's sub-queries become near-copies of its first one (the core
    query, if listed, is left alone); the executed sub_query spans follow."""
    changed = False
    for plan in [s for s in data["spans"] if s["name"] == "plan"]:
        a = plan["attributes"]
        subs = [q for q in a.get("sub_queries") or [] if q]
        core = a.get("query") or ""
        own = [q for q in subs if q != core]
        if len(own) < 2:
            continue
        q0 = own[0]
        variants = [q0, f"{q0} overview", f"latest {q0}", f"{q0} explained", f"{q0} key facts"]
        mapping, k = {}, 0
        for q in subs:
            if q == core:
                continue
            mapping[q] = variants[k % len(variants)]
            k += 1
        a["sub_queries"] = [mapping.get(q, q) for q in a["sub_queries"]]
        for s in data["spans"]:
            if s["parent_id"] == plan["span_id"] and s["name"] == "sub_query":
                q = s["attributes"].get("query")
                if q in mapping:
                    s["attributes"]["query"] = mapping[q]
        changed = True
    return data if changed else None


def irrelevant_material(data: dict, rng: random.Random) -> dict | None:
    """Every other planned sub-query step returns off-topic pages instead of
    its own. (Its own chunks leave the retrieved set when no other step has
    them, so evidence-based metrics move too; only query_relevance is the
    target.)"""
    steps = [s for s in data["spans"] if s["name"] == "sub_query"
             and not s["attributes"].get("is_core_query") and s["attributes"].get("chunk_ids")]
    if not steps:
        return None
    template = next(iter(data["chunks"].values()), {})
    for n, s in enumerate(steps[::2]):
        ids = []
        for j, (url, title, content) in enumerate(OFF_TOPIC_CHUNKS):
            cid = f"offtopic_{n}_{j}"
            data["chunks"][cid] = {**{k: None for k in template}, "url": url, "title": title,
                                   "content": content}
            ids.append(cid)
        s["attributes"]["chunk_ids"] = ids
    return data


# name -> (function, {metric: expected direction}, note)
PERTURBATIONS: dict[str, tuple] = {
    "drop_half_sections": (drop_half_sections, {"comprehensiveness": "down"},
                           "every other level-2 section removed"),
    "strip_links": (strip_links, {"citation_recall": "down", "citation_coverage": "down"},
                    "no links left in the body; references list kept"),
    "swap_citations": (swap_citations, {"citation_recall": "down", "citation_precision": "down",
                                        "fact_grounding": "down"},
                       "each cited URL replaced by the retrieved URL with the least similar text "
                       "(an uncited one when there are enough)"),
    "alter_numbers": (alter_numbers, {"faithfulness": "down", "fact_grounding": "down"},
                      "figures >= 10 changed (years +3, percentages x0.4, others x1.7)"),
    "insert_off_topic": (insert_off_topic, {"topic_relevance": "down", "readability": "down"},
                         "three off-topic paragraphs (baking, football, gardening) inserted"),
    "facts_only": (facts_only, {"insight": "down"},
                   "analysis sections and sentences removed; the rest as bullet lists of facts"),
    "scramble_structure": (scramble_structure, {"readability": "down"},
                           "headings removed, paragraphs shuffled"),
    "insert_toxic_biased": (insert_toxic_biased, {"toxicity": "up", "bias": "up"},
                            "four toxic or biased opinions appended to paragraphs"),
    "duplicate_subqueries": (duplicate_subqueries, {"subquery_redundancy": "up",
                                                    "decomposition_coverage": "down",
                                                    "decomposition_tree_quality": "down"},
                             "sub-queries rewritten as near-copies of the first"),
    "irrelevant_material": (irrelevant_material, {"query_relevance": "down"},
                            "every other sub-query step returns off-topic pages"),
}


def make(paths: list[str], out: str, only: list[str] | None = None, seed: int = 0) -> Path:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"seed": seed, "runs": []}
    for path in paths:
        src = json.loads(Path(path).read_text(encoding="utf-8"))
        run_id = src["meta"]["run_id"]
        entry = {"source": str(path), "run_id": run_id, "question_id": src["meta"].get("question_id"),
                 "base": f"{run_id}__base", "noise": f"{run_id}__noise", "perturbations": []}
        for name, tag in (("base", "__base"), ("noise", "__noise")):
            d = copy.deepcopy(src)
            d["meta"]["run_id"] = run_id + tag
            d["meta"]["perturbation"] = name
            _write(out_dir, d)
        for name, (fn, expected, note) in PERTURBATIONS.items():
            if only and name not in only:
                continue
            d = fn(copy.deepcopy(src), random.Random(f"{seed}:{run_id}:{name}"))
            if d is None:
                entry["perturbations"].append({"name": name, "skipped": "does not apply to this run"})
                continue
            d["meta"]["run_id"] = f"{run_id}__{name}"
            d["meta"]["perturbation"] = name
            _write(out_dir, d)
            entry["perturbations"].append({"name": name, "run_id": d["meta"]["run_id"],
                                           "expected": expected, "note": note})
        manifest["runs"].append(entry)
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _write(out_dir: Path, data: dict) -> None:
    p = out_dir / f"{data['meta']['run_id']}.json"
    if p.exists():
        raise FileExistsError(f"{p} exists; use a new --out directory")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# --- report -----------------------------------------------------------------

UNIT_RANGE = {"effective_citations": False, "source_diversity": True}   # default True
FLOOR = 0.03           # least change that counts on a 0-1 metric (about the judge's spread)
REL_FLOOR = 0.10       # the same for unbounded metrics, relative to the base value


def _latest(results_dir: Path, run_id: str) -> dict | None:
    files = sorted((results_dir / run_id).glob("*.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def _value(rec: dict | None, metric: str):
    if not rec or metric not in rec["metrics"]:
        return None, "not scored"
    r = rec["metrics"][metric]
    return r["value"], r["skipped"]


def threshold(metric: str, base: float, noise: float | None) -> float:
    floor = FLOOR if UNIT_RANGE.get(metric, True) else REL_FLOOR * abs(base or 0)
    return max(floor, 2 * noise) if noise is not None else floor


def verdict(direction: str, base, new, thr: float) -> str:
    if base is None or new is None:
        return "n/a"
    delta = new - base
    if (delta < 0) != (direction == "down") or delta == 0:
        return "FAIL"
    return "pass" if abs(delta) > thr else "weak"


def report(manifest_path: str, results_dir: str) -> tuple[list[dict], list[dict]]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    res = Path(results_dir)
    rows, side = [], []
    for run in manifest["runs"]:
        base_rec, noise_rec = _latest(res, run["base"]), _latest(res, run["noise"])
        if base_rec is None:
            continue
        for p in run["perturbations"]:
            if p.get("skipped"):
                rows.append({"run": run["run_id"], "perturbation": p["name"], "metric": "-",
                             "verdict": "skipped", "note": p["skipped"]})
                continue
            rec = _latest(res, p["run_id"])
            for metric, direction in p["expected"].items():
                b, _ = _value(base_rec, metric)
                n, skipped = _value(rec, metric)
                nz, _ = _value(noise_rec, metric)
                noise = abs(nz - b) if (nz is not None and b is not None) else None
                thr = threshold(metric, b, noise)
                v = verdict(direction, b, n, thr)
                if n is None and skipped:
                    v = "n/a"
                rows.append({"run": run["run_id"], "perturbation": p["name"], "metric": metric,
                             "expected": direction, "base": b, "perturbed": n,
                             "delta": None if (b is None or n is None) else round(n - b, 3),
                             "noise": None if noise is None else round(noise, 3),
                             "threshold": round(thr, 3), "verdict": v, "note": skipped or ""})
            if rec is not None:
                for metric, r in rec["metrics"].items():
                    if metric in p["expected"]:
                        continue
                    b, _ = _value(base_rec, metric)
                    n = r["value"]
                    if b is None or n is None:
                        continue
                    nz, _ = _value(noise_rec, metric)
                    thr = threshold(metric, b, abs(nz - b) if nz is not None else None)
                    if abs(n - b) > thr:
                        side.append({"run": run["run_id"], "perturbation": p["name"], "metric": metric,
                                     "base": b, "perturbed": n, "delta": round(n - b, 3)})
    return rows, side


def _fmt(x) -> str:
    return "—" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def print_report(rows: list[dict], side: list[dict]) -> None:
    print("| run | perturbation | metric | expected | base | perturbed | delta | noise | verdict |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['run'][-24:]} | {r['perturbation']} | {r['metric']} | {r.get('expected', '')} | "
              f"{_fmt(r.get('base'))} | {_fmt(r.get('perturbed'))} | {_fmt(r.get('delta'))} | "
              f"{_fmt(r.get('noise'))} | {r['verdict']}{(' (' + r['note'] + ')') if r.get('note') else ''} |")
    by_metric: dict[str, list[str]] = {}
    for r in rows:
        if r["metric"] != "-":
            by_metric.setdefault(r["metric"], []).append(r["verdict"])
    print("\nPer metric: " + ", ".join(f"{m} {'/'.join(v)}" for m, v in sorted(by_metric.items())))
    if side:
        print("\nOther metrics that moved beyond the threshold (side effects, not verdicts):")
        for s in side:
            print(f"  {s['run'][-24:]} {s['perturbation']}: {s['metric']} {_fmt(s['base'])} -> "
                  f"{_fmt(s['perturbed'])} ({s['delta']:+.3f})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="write perturbed copies and manifest.json")
    m.add_argument("archives", nargs="+")
    m.add_argument("--out", required=True)
    m.add_argument("--only", default="", help="comma-separated perturbation names")
    m.add_argument("--seed", type=int, default=0)
    r = sub.add_parser("report", help="compare scores of the copies with the base copy")
    r.add_argument("manifest")
    r.add_argument("--results-dir", required=True)
    r.add_argument("--json", default="", help="also write the rows to this file")
    args = ap.parse_args(argv)
    if args.cmd == "make":
        only = [x for x in args.only.split(",") if x]
        unknown = set(only) - set(PERTURBATIONS)
        if unknown:
            ap.error(f"unknown perturbations: {', '.join(sorted(unknown))}")
        path = make(args.archives, args.out, only or None, args.seed)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for run in manifest["runs"]:
            made = [p["name"] for p in run["perturbations"] if not p.get("skipped")]
            skipped = [p["name"] for p in run["perturbations"] if p.get("skipped")]
            print(f"{run['run_id']}: {len(made)} perturbations"
                  + (f" (skipped: {', '.join(skipped)})" if skipped else ""))
        print(f"-> {path}")
        return 0
    rows, side = report(args.manifest, args.results_dir)
    print_report(rows, side)
    if args.json:
        Path(args.json).write_text(json.dumps({"rows": rows, "side_effects": side},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
