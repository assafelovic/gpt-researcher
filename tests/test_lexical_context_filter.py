"""LexicalContextCompressor: BM25 ranking with no API, model or embeddings."""

import asyncio

from gpt_researcher.context.lexical import LexicalContextCompressor, bm25_scores, tokenize


def _page(url, text):
    return {"url": url, "title": url, "raw_content": text}


def _filler(n=30):
    return ("The committee met on Tuesday and discussed the agenda for the coming year. " * 12 + "\n\n") * n


ANSWER = "Solid-state batteries cost about $400 per kWh in 2026, roughly three times lithium-ion cells. "


def test_tokenize_drops_stopwords_and_matches_plurals():
    assert tokenize("The costs of the batteries") == ["cost", "battery"]


def test_tokenize_keeps_non_english_words():
    assert "батареи" in tokenize("Стоимость батареи")


def test_bm25_prefers_the_passage_that_matches():
    scores = bm25_scores("battery cost per kWh", [ANSWER, "The weather in Paris is mild.", "Battery chemistry"])
    assert scores[0] > scores[2] > scores[1] == 0


def test_relevant_chunk_ranks_first_among_filler():
    pages = [_page("filler", _filler()), _page("answer", _filler(3) + ANSWER * 8 + _filler(3))]
    selected = LexicalContextCompressor(pages).select("solid-state battery cost per kWh", max_results=3)
    assert "$400 per kWh" in selected[0].page_content
    assert selected[0].metadata["source"] == "answer"


def test_relative_threshold_drops_filler_instead_of_filling_the_budget():
    pages = [_page("filler", _filler()), _page("answer", ANSWER * 8)]
    loose = LexicalContextCompressor(pages).select("solid-state battery cost", max_results=10)
    strict = LexicalContextCompressor(pages, relative_threshold=0.5).select("solid-state battery cost", max_results=10)
    assert len(loose) == 10
    assert strict and all(c.metadata["source"] == "answer" for c in strict)


def test_no_keyword_overlap_falls_back_to_opening_chunks():
    pages = [_page("a", _filler())]
    selected = LexicalContextCompressor(pages, relative_threshold=0.5).select("quantum chromodynamics", max_results=2)
    assert len(selected) == 2


def test_context_is_formatted_like_the_other_filters():
    context = asyncio.run(LexicalContextCompressor([_page("answer", ANSWER * 20)]).async_get_context("battery cost", 2))
    assert context.startswith("Source: answer\nTitle: answer\nContent: ")


def test_rank_written_sections_finds_the_related_section():
    from gpt_researcher.context.lexical import rank_written_sections

    sections = [
        {"section_title": "Battery costs", "written_content": ANSWER * 3},
        {"section_title": "History", "written_content": _filler(1)},
    ]
    ranked = rank_written_sections("battery cost per kWh", sections)
    assert ranked and all(r.startswith("Title: Battery costs") for r in ranked)
    assert rank_written_sections("quantum chromodynamics", sections) == []
