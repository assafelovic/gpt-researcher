"""
Versioned judge prompts: one skill per metric group, one file per prompt.
--------------------------------------------------------------------------
Each metric group is a folder (`query-quality/`, `source-quality/`, ...)
holding a `SKILL.md` and that group's prompts, one `<id>.md` each: a short
header (id, version, the metrics that use it) and the prompt text below it.
`{name}` marks a value filled in when the prompt is sent; any other brace is
literal text (the JSON the judge must return). A line
`@include <group>#<section>` is replaced by that `## <section>` of
`<group>/SKILL.md`, so prompts that share a definition share one text.

Change the text (or a skill section a prompt includes) -> bump the prompt's
version. The version is part of every cache key and is recorded with each
score, so old verdicts are never mixed with new ones. `versions.json` holds
each prompt's version and text hash; a test fails when the text changed but
the version did not. After bumping, run

    python -m evals.research_eval.prompts --lock

to record the new hash.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
SKILL = "SKILL.md"
LOCK = HERE / "versions.json"
PLACEHOLDER = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
INCLUDE = re.compile(r"^@include[ \t]+([\w-]+)#([\w-]+)[ \t]*$", re.M)
SECTION = re.compile(r"^##[ \t]+([\w-]+)[ \t]*$")
HEADER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
# Folder order is the order of the metric groups in the README table.
GROUPS = ("query-quality", "source-quality", "retrieval-quality", "writing-quality", "writing-authority")


@dataclass(frozen=True)
class Prompt:
    id: str
    version: str
    template: str
    used_by: tuple[str, ...] = field(default=(), compare=False)
    group: str = field(default="", compare=False)
    includes: tuple[str, ...] = field(default=(), compare=False)    # skill sections pulled in
    path: str = field(default="", compare=False)                     # relative to this folder

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.template.encode("utf-8")).hexdigest()[:12]

    @property
    def placeholders(self) -> list[str]:
        return list(dict.fromkeys(PLACEHOLDER.findall(self.template)))

    def render(self, **kw) -> str:
        missing = [p for p in self.placeholders if p not in kw]
        if missing:
            raise KeyError(f"prompt {self.id} needs {', '.join(missing)}")
        # One pass: a filled-in value is never scanned for placeholders again.
        return PLACEHOLDER.sub(lambda m: str(kw[m.group(1)]) if m.group(1) in kw else m.group(0),
                               self.template)


def groups() -> list[Path]:
    """The group folders: every folder here with a SKILL.md."""
    return sorted((d for d in HERE.iterdir() if (d / SKILL).is_file()),
                  key=lambda d: (GROUPS.index(d.name) if d.name in GROUPS else len(GROUPS), d.name))


def _front(path: Path) -> tuple[dict[str, str], str]:
    m = HEADER.match(path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"{path.relative_to(HERE)}: missing the --- header ---")
    head = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in head.items()}, m.group(2)


def skill_sections(group: str) -> dict[str, str]:
    """The `## <section>` parts of <group>/SKILL.md, each with its text.

    A section runs to the next heading of any level, so a maintainers' note
    under a heading such as `## How to edit` is never sent to the judge.
    """
    _, body = _front(HERE / group / SKILL)
    out, current, lines = {}, None, []
    for line in body.splitlines() + ["#"]:
        if line.startswith("#"):
            if current:
                out[current] = "\n".join(lines).strip()
            m = SECTION.match(line)
            current, lines = (m.group(1) if m else None), []
        elif current:
            lines.append(line)
    return out


def _expand(body: str, source: Path) -> str:
    def include(m):
        sections = skill_sections(m.group(1))
        if m.group(2) not in sections:
            raise KeyError(f"{source.name}: skill {m.group(1)} has no section {m.group(2)!r}")
        return sections[m.group(2)]
    return INCLUDE.sub(include, body)


def _files() -> dict[str, Path]:
    out = {}
    for g in groups():
        for f in sorted(g.glob("*.md")):
            if f.name != SKILL:
                if f.stem in out:
                    raise ValueError(f"prompt id {f.stem} is in both {out[f.stem].parent.name} and {g.name}")
                out[f.stem] = f
    return out


def load(prompt_id: str, path: Path | None = None) -> Prompt:
    path = path or _files().get(prompt_id)
    if path is None:
        raise KeyError(f"no prompt {prompt_id}.md in any group folder")
    head, body = _front(path)
    if head.get("id") != prompt_id:
        raise ValueError(f"{path.name}: id {head.get('id')!r} does not match the file name")
    used_by = tuple(u.strip() for u in head.get("used_by", "").split(",") if u.strip())
    return Prompt(prompt_id, head["version"], _expand(body, path).strip(), used_by, path.parent.name,
                  tuple(f"{s}#{n}" for s, n in INCLUDE.findall(body)), str(path.relative_to(HERE)))


def all_prompts() -> dict[str, Prompt]:
    return {pid: load(pid, f) for pid, f in _files().items()}


def lock_problems(prompts: dict[str, Prompt] | None = None) -> list[str]:
    """Prompts whose text changed without a version bump, or whose bump is not locked."""
    prompts = prompts or all_prompts()
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    out = []
    for pid, p in prompts.items():
        held = lock.get(pid)
        if held is None:
            out.append(f"{pid}: not in versions.json")
        elif held["version"] == p.version and held["hash"] != p.hash:
            out.append(f"{pid}: text changed but version is still {p.version}; bump it")
        elif held["version"] != p.version:
            out.append(f"{pid}: version {held['version']} -> {p.version} not locked yet")
    out += [f"{pid}: in versions.json but no {pid}.md" for pid in lock if pid not in prompts]
    return out


def write_lock() -> None:
    """Record every prompt's version and hash, and rewrite the README table."""
    prompts = all_prompts()
    LOCK.write_text(json.dumps({pid: {"version": p.version, "hash": p.hash}
                                for pid, p in prompts.items()}, indent=2) + "\n", encoding="utf-8")
    rank = lambda p: (GROUPS.index(p.group) if p.group in GROUPS else len(GROUPS), p.id)
    rows = ["| Group | File | Version | Used by | Skill sections | Filled in |", "|---|---|---|---|---|---|"]
    for p in sorted(prompts.values(), key=rank):
        rows.append(f"| [{p.group}]({p.group}/{SKILL}) | [`{p.id}.md`]({p.path}) | {p.version} | {', '.join(p.used_by)} | "
                    f"{', '.join(p.includes) or '-'} | {', '.join('`' + x + '`' for x in p.placeholders)} |")
    readme = HERE / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- prompts:start (written by --lock) -->", "<!-- prompts:end -->"
    i, j = text.index(start) + len(start), text.index(end)
    readme.write_text(text[:i] + "\n" + "\n".join(rows) + "\n" + text[j:], encoding="utf-8")


KEY_POINTS = load("key_points")
DECOMPOSITION_COVERAGE = load("decomposition_coverage")
TREE_QUALITY = load("tree_quality")
PARENT_ASPECTS = load("parent_aspects")
SUBQUERY_REDUNDANCY = load("subquery_redundancy")
QUERY_RELEVANCE = load("query_relevance")
DOMAIN_AUTHORITY = load("domain_authority")
PARAGRAPH_AUDIT = load("paragraph_audit")
CLAIM_RECHECK = load("claim_recheck")
COMPREHENSIVENESS = load("comprehensiveness")
MATERIAL_COVERAGE = load("material_coverage")
QUALITY_RUBRIC = load("quality_rubric")
QUALITY_SCORE = load("quality_score")
TOPIC_RELEVANCE = load("topic_relevance")
TOXICITY_BIAS = load("toxicity_bias")

