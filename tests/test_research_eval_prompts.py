"""The prompt folder: every prompt loads from its own file, renders only its
own placeholders, and cannot change its text without a version bump."""

import pytest

from evals.research_eval import prompts as P
from evals.research_eval.metrics import all_metrics


def test_every_prompt_file_loads_and_is_locked():
    ps = P.all_prompts()
    assert len(ps) == 14 and all(p.used_by for p in ps.values())
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
    (tmp_path / "s.md").write_text("# S\n\nintro\n\n## alpha\n\nA text.\n\n## beta\n\nB text.\n")
    monkeypatch.setattr(P, "SKILLS", tmp_path)
    assert P._expand("x\n@include s#beta\ny", tmp_path / "p.md") == "x\nB text.\ny"
    with pytest.raises(KeyError):
        P._expand("@include s#gamma", tmp_path / "p.md")
