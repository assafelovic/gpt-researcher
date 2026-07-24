"""_parse_analysis_response should accept fenced/repaired LLM JSON."""

from gpt_researcher.skills.image_generator import ImageGenerator


SECTIONS = [
    {
        "header": "Intro",
        "content": "About widgets " * 20,
        "start_line": 3,
    }
]


def _ig():
    # ImageGenerator needs a researcher-like object only for other paths;
    # _parse_analysis_response does not touch self beyond being a method.
    return ImageGenerator.__new__(ImageGenerator)


def test_parse_analysis_raw_json():
    ig = _ig()
    resp = '{"suggestions":[{"section_number":1,"image_prompt":"diagram","reason":"clarity"}]}'
    out = ig._parse_analysis_response(resp, SECTIONS)
    assert len(out) == 1
    assert out[0]["section_header"] == "Intro"
    assert out[0]["image_prompt"] == "diagram"


def test_parse_analysis_fenced_json():
    ig = _ig()
    resp = """```json
{"suggestions":[{"section_number":1,"image_prompt":"chart","reason":"viz"}]}
```"""
    out = ig._parse_analysis_response(resp, SECTIONS)
    assert len(out) == 1
    assert out[0]["image_prompt"] == "chart"


def test_parse_analysis_trailing_comma_repaired():
    ig = _ig()
    resp = '{"suggestions":[{"section_number":1,"image_prompt":"map","reason":"geo",}],}'
    out = ig._parse_analysis_response(resp, SECTIONS)
    assert len(out) == 1
    assert out[0]["image_prompt"] == "map"


def test_parse_analysis_skips_non_dict_suggestions():
    ig = _ig()
    resp = '{"suggestions":["bad",{"section_number":1,"image_prompt":"ok","reason":"r"}]}'
    out = ig._parse_analysis_response(resp, SECTIONS)
    assert len(out) == 1
    assert out[0]["image_prompt"] == "ok"


def test_parse_analysis_empty():
    ig = _ig()
    assert ig._parse_analysis_response("", SECTIONS) == []
    assert ig._parse_analysis_response(None, SECTIONS) == []  # type: ignore[arg-type]
