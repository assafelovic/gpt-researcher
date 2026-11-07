"""
Versioned judge prompts: one skill per metric group, one file per prompt.
--------------------------------------------------------------------------
Each metric group is a folder (`query-quality/`, `source-quality/`, ...)
holding a `SKILL.md` and that group's prompts, one `<id>.md` each: a short
header (id, version, the metrics that use it) and the prompt text below it.
A line `@user` splits the text into two messages: above it the system
message (the task, the definitions and the answer format, the same on every
call), below it the user message (the data of this call). `{name}` marks a
value filled in when the prompt is sent, and only the user message may hold
one; any other brace is literal text (the JSON the judge must return). A line
`@include <group>#<section>` is replaced by that `## <section>` of
`<group>/SKILL.md`, so prompts that share a definition share one text.

A group whose SKILL.md header says `system_prompt: true` works the other
way: its whole skill is the group's system prompt. Its text (without the
header and without `<!-- ... -->` comments, which hold the maintainers'
notes) goes in front of the system part of every prompt in the folder, so
the judge reads the shared background, definitions and principles first and
then the task of this one metric. A prompt that must not get it says
`skill: none` in its header. Such a group's prompts use no @include.

`<id>.schema.json` beside the prompt is the JSON schema of its answer. The
judge is called in strict structured-output mode with it, so a reply is
always valid JSON of that shape.

Change the text (or a skill section a prompt includes) -> bump the prompt's
version. The version is part of every cache key and is recorded with each
score, so old verdicts are never mixed with new ones. `versions.json` holds
each prompt's version and the hash of its text and schema; a test fails when
either changed but the version did not. After bumping, run

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
USER = re.compile(r"^@user[ \t]*$", re.M)
INCLUDE = re.compile(r"^@include[ \t]+([\w-]+)#([\w-]+)[ \t]*$", re.M)
SECTION = re.compile(r"^##[ \t]+([\w-]+)[ \t]*$")
HEADER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
# Folder order is the order of the metric groups in the README table.
GROUPS = ("query-quality", "source-quality", "retrieval-quality", "writing-quality", "writing-authority")


@dataclass(frozen=True)
class Rendered:
    """One judge request: the system message, the filled-in user message and
    the answer schema (JSON text, "" for none)."""
    system: str
    user: str
    schema_json: str = ""
    name: str = "answer"

    @property
    def schema(self) -> dict | None:
        return json.loads(self.schema_json) if self.schema_json else None

    @property
    def text(self) -> str:
        """Both messages as one text (what test and dry-run backends see)."""
        return f"{self.system}\n\n{self.user}" if self.system else self.user

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class Prompt:
    id: str
    version: str
    system: str
    user: str
    schema_json: str = ""
    used_by: tuple[str, ...] = field(default=(), compare=False)
    group: str = field(default="", compare=False)
    includes: tuple[str, ...] = field(default=(), compare=False)    # skill sections pulled in, or the whole skill
    path: str = field(default="", compare=False)                     # relative to this folder

    @property
    def template(self) -> str:
        return f"{self.system}\n\n{self.user}" if self.system else self.user

    @property
    def schema(self) -> dict | None:
        return json.loads(self.schema_json) if self.schema_json else None

    @property
    def hash(self) -> str:
        text = f"{self.system}\n@user\n{self.user}\n@schema\n{self.schema_json}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

    @property
    def placeholders(self) -> list[str]:
        return list(dict.fromkeys(PLACEHOLDER.findall(self.user)))

    def render(self, **kw) -> Rendered:
        missing = [p for p in self.placeholders if p not in kw]
        if missing:
            raise KeyError(f"prompt {self.id} needs {', '.join(missing)}")
        # One pass: a filled-in value is never scanned for placeholders again.
        user = PLACEHOLDER.sub(lambda m: str(kw[m.group(1)]) if m.group(1) in kw else m.group(0), self.user)
        return Rendered(self.system, user, self.schema_json, self.id)


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


def skill_prompt(group: str) -> str | None:
    """The system prompt of a `system_prompt: true` group: its SKILL.md
    without the header and the `<!-- -->` comments; None for other groups."""
    head, body = _front(HERE / group / SKILL)
    if head.get("system_prompt", "").lower() != "true":
        return None
    return re.sub(r"\n{3,}", "\n\n", COMMENT.sub("", body)).strip()


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
    parts = USER.split(body)
    if len(parts) > 2:
        raise ValueError(f"{path.name}: more than one @user line")
    system, user = ("", parts[0]) if len(parts) == 1 else parts
    skill = skill_prompt(path.parent.name) if (path.parent / SKILL).is_file() else None
    if skill is not None and INCLUDE.search(body):
        raise ValueError(f"{path.name}: {path.parent.name} sends its whole skill; drop the @include lines")
    system, user = _expand(system, path).strip(), _expand(user, path).strip()
    prefixed = skill is not None and head.get("skill", "").lower() != "none"
    if prefixed:
        system = f"{skill}\n\n{system}".strip()
    if PLACEHOLDER.search(system):
        raise ValueError(f"{path.name}: the system part must be the same on every call, "
                         f"but holds {PLACEHOLDER.search(system).group(0)}; move it below @user")
    schema = path.with_suffix(".schema.json")
    schema_json = json.dumps(json.loads(schema.read_text(encoding="utf-8")), separators=(",", ":")) \
        if schema.exists() else ""
    includes = (f"{path.parent.name} (whole skill)",) if prefixed else \
        tuple(f"{s}#{n}" for s, n in INCLUDE.findall(body))
    return Prompt(prompt_id, head["version"], system, user, schema_json, used_by, path.parent.name,
                  includes, str(path.relative_to(HERE)))


def strict_schema_problems(schema: dict, where: str = "$") -> list[str]:
    """What keeps a schema from OpenAI's strict structured-output mode: every
    object must list all its properties as required and allow no others."""
    out = []
    if schema.get("type") == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        if schema.get("additionalProperties") is not False:
            out.append(f"{where}: additionalProperties must be false")
        if list(schema.get("required") or []) != list(props):
            out.append(f"{where}: required must list every property, in order")
        for k, v in props.items():
            out += strict_schema_problems(v, f"{where}.{k}")
    if "items" in schema:
        out += strict_schema_problems(schema["items"], f"{where}[]")
    return out


def schema_errors(value, schema: dict, where: str = "$") -> list[str]:
    """Where `value` breaks `schema` (the subset our schemas use: type, enum,
    properties, required, additionalProperties, items)."""
    kinds = schema.get("type")
    kinds = kinds if isinstance(kinds, list) else [kinds] if kinds else []
    check = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
             "string": lambda v: isinstance(v, str), "boolean": lambda v: isinstance(v, bool),
             "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
             "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
             "null": lambda v: v is None}
    if kinds and not any(check[k](value) for k in kinds):
        return [f"{where}: {value!r} is not {'/'.join(kinds)}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{where}: {value!r} not in {schema['enum']}"]
    out = []
    if isinstance(value, dict):
        props = schema.get("properties") or {}
        out += [f"{where}: missing {k}" for k in schema.get("required") or [] if k not in value]
        if schema.get("additionalProperties") is False:
            out += [f"{where}: unexpected {k}" for k in value if k not in props]
        for k, v in value.items():
            if k in props:
                out += schema_errors(v, props[k], f"{where}.{k}")
    if isinstance(value, list) and "items" in schema:
        for n, v in enumerate(value):
            out += schema_errors(v, schema["items"], f"{where}[{n}]")
    return out


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
    rows = ["| Group | File | Version | Used by | Skill sections | Filled in | Schema |",
            "|---|---|---|---|---|---|---|"]
    for p in sorted(prompts.values(), key=rank):
        schema = Path(p.path).with_suffix(".schema.json").as_posix()
        rows.append(f"| [{p.group}]({p.group}/{SKILL}) | [`{p.id}.md`]({p.path}) | {p.version} | {', '.join(p.used_by)} | "
                    f"{', '.join(p.includes) or '-'} | {', '.join('`' + x + '`' for x in p.placeholders)} | "
                    + (f"[json]({schema}) |" if p.schema_json else "- |"))
    readme = HERE / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- prompts:start (written by --lock) -->", "<!-- prompts:end -->"
    i, j = text.index(start) + len(start), text.index(end)
    readme.write_text(text[:i] + "\n" + "\n".join(rows) + "\n" + text[j:], encoding="utf-8")


KEY_POINTS = load("key_points")
KEY_POINTS_STRUCTURED = load("key_points_structured")
KEY_POINTS_LAYERED = load("key_points_layered")
KEY_POINTS_MERGE = load("key_points_merge")
DECOMPOSITION_COVERAGE = load("decomposition_coverage")
TREE_QUALITY = load("tree_quality")
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

