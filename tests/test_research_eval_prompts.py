"""The prompt folder: every prompt loads from its own file, renders only its
own placeholders, and cannot change its text without a version bump."""

import pytest

from evals.research_eval import prompts as P
from evals.research_eval.metrics import all_metrics


def test_every_prompt_file_loads_and_is_locked():
    ps = P.all_prompts()
    assert len(ps) == 15 and all(p.used_by for p in ps.values())
    assert P.lock_problems(ps) == [], "run: python -m evals.research_eval.prompts --lock (after bumping versions)"


def test_metrics_use_the_prompts_from_the_folder():
    ps = P.all_prompts()
    for m in all_metrics():
        for p in m.prompts:
            assert ps[p.id] == p, (m.name, p.id)


def test_text_change_without_a_version_bump_is_caught():
    ps = P.all_prompts()
    edited = P.Prompt("tree_quality", ps["tree_quality"].version, ps["tree_quality"].template + "\nmore")
    assert P.lock_problems({**ps, "tree_quality": edited}) == [
        f"tree_quality: text changed but version is still {edited.version}; bump it"]


def test_render_fills_placeholders_once_and_leaves_json_braces():
    p = P.Prompt("x", "1", 'Q: {question}\nReturn {"a": [{"b": 1}]} for {question}')
    assert p.placeholders == ["question"]
    assert p.render(question="{question} and {x}") == \
        'Q: {question} and {x}\nReturn {"a": [{"b": 1}]} for {question} and {x}'
    with pytest.raises(KeyError):
        p.render()


def test_include_pulls_one_skill_section(tmp_path, monkeypatch):
    (tmp_path / "g").mkdir()
    (tmp_path / "g" / "SKILL.md").write_text(
        "---\nname: g\ndescription: d\n---\n\n# G\n\nintro\n\n## alpha\n\nA text.\n\n"
        "## beta\n\nB text.\n\n## How to edit\n\nnot for the judge\n")
    monkeypatch.setattr(P, "HERE", tmp_path)
    assert P.skill_sections("g") == {"alpha": "A text.", "beta": "B text."}
    assert P._expand("x\n@include g#beta\ny", tmp_path / "p.md") == "x\nB text.\ny"
    with pytest.raises(KeyError):
        P._expand("@include g#gamma", tmp_path / "p.md")


def test_one_skill_per_group_and_every_section_is_used():
    ps = P.all_prompts()
    assert [g.name for g in P.groups()] == list(P.GROUPS)
    used = {inc for p in ps.values() for inc in p.includes}
    for g in P.groups():
        head, _ = P._front(g / P.SKILL)
        assert head["name"] == g.name and head["description"]
        assert any(p.group == g.name for p in ps.values()), g.name
        # A section no prompt includes is text nobody reads.
        assert {f"{g.name}#{s}" for s in P.skill_sections(g.name)} <= used, g.name


def test_query_quality_prompts_share_the_skill_definitions():
    skill = P.skill_sections("query-quality")
    assert set(skill) == {"principles", "aspect", "aimed_at", "narrower", "searchable", "serves_parent",
                          "drift", "repeat"}
    for pid, sections in {"tree_quality": ["narrower", "searchable", "serves_parent", "drift", "aimed_at"],
                          "parent_aspects": ["aspect"],
                          "subquery_redundancy": ["repeat"], "decomposition_coverage": ["aimed_at"]}.items():
        t = P.load(pid).template
        assert "@include" not in t and P.load(pid).group == "query-quality"
        for sec in ["principles"] + sections:
            assert skill[sec] in t, (pid, sec)
