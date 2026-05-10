from gpt_researcher.skills.curator import _normalize_curated_sources


def test_normalize_curated_sources_handles_code_fenced_object_payload():
    response = """```json
sources: [
  {
    "title": "OpenAI API docs",
    "url": "https://developers.openai.com/api/docs",
    "content": "Official API reference"
  }
]
```"""

    normalized = _normalize_curated_sources(response)

    assert normalized is not None
    assert len(normalized) == 1
    assert normalized[0]["title"] == "OpenAI API docs"
