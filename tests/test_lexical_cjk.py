"""Keyword (BM25) filter on Chinese, Japanese and Korean text.

These scripts don't separate words with spaces, so ``\\w+`` made a whole
sentence one token: queries and chunks shared no terms, every score was 0 and
the filter fell back to the pages' opening chunks.
"""

import re

from gpt_researcher.context.lexical import _STOPWORDS, _stem, LexicalContextCompressor, bm25_scores, tokenize


def _old_tokenize(text: str) -> list[str]:
    """``tokenize`` before CJK support, for the no-change regression check."""
    return [_stem(t) for t in re.findall(r"\w+", text.lower()) if len(t) > 1 and t not in _STOPWORDS]


def _page(url, text):
    return {"url": url, "title": url, "raw_content": text}


ZH_RELEVANT = "2024年中国新能源汽车销量增长了百分之三十。"
ZH_UNRELATED = "今天天气很好，我们去公园散步。"


def test_chinese_is_split_into_overlapping_bigrams():
    assert tokenize("2024年中国新能源汽车销量增长") == [
        "2024", "年中", "中国", "国新", "新能", "能源", "源汽", "汽车", "车销", "销量", "量增", "增长",
    ]


def test_single_cjk_character_is_kept_as_unigram():
    assert tokenize("的") == ["的"]
    assert tokenize("A股 和 B股") == ["股", "和", "股"]


def test_chinese_relevant_chunk_scores_above_unrelated():
    scores = bm25_scores("新能源汽车销量", [ZH_RELEVANT, ZH_UNRELATED])
    assert scores[0] > 0 and scores[1] == 0


def test_japanese_mixed_scripts():
    assert tokenize("電池のコスト") == ["電池", "池の", "のコ", "コス", "スト"]
    scores = bm25_scores("全固体電池のコスト", [
        "東京の天気は晴れです。",
        "全固体電池のコストは2030年までに大幅に下がる見込みです。",
    ])
    assert scores[1] > scores[0] == 0


def test_korean():
    assert tokenize("전고체 배터리 가격") == ["전고", "고체", "배터", "터리", "가격"]
    scores = bm25_scores("전고체 배터리 가격", [
        "오늘 서울 날씨는 맑습니다.",
        "전고체 배터리 가격은 2030년까지 크게 하락할 전망이다.",
    ])
    assert scores[1] > scores[0] == 0


def test_mixed_english_and_cjk():
    assert tokenize("Tesla在中国的sales增长") == ["tesla", "在中", "中国", "国的", "sale", "增长"]
    scores = bm25_scores("Tesla 中国 sales", ["Tesla在中国的sales增长", "Tesla sales in Europe", ZH_UNRELATED])
    assert scores[0] > scores[1] > scores[2] == 0


def test_chinese_relevant_chunk_ranks_first_not_opening_chunks():
    filler = (ZH_UNRELATED * 60 + "\n\n") * 6
    pages = [_page("filler", filler), _page("answer", filler[:2000] + "\n\n" + ZH_RELEVANT * 20 + "\n\n" + filler)]
    selected = LexicalContextCompressor(pages, relative_threshold=0.5).select("新能源汽车销量", max_results=25)
    assert selected[0].metadata["source"] == "answer"
    assert "新能源汽车销量" in selected[0].page_content
    assert all("新能源汽车销量" in c.page_content for c in selected)


NON_CJK_SAMPLES = [
    "The costs of the batteries are falling, says the IEA's 2024 report.",
    "Solid-state batteries cost about $400 per kWh in 2026, roughly three times lithium-ion cells.",
    "snake_case_names, CamelCase, e-mail, U.S.A., 3.14159, 1,000,000 and #hashtags @handles",
    "Стоимость батареи упала; café naïve façade Straße ΣΊΣΥΦΟΣ İstanbul",
    "العربية والعبرية עברית हिन्दी ไทย",
    "Ünïcödé — dashes – “quotes” ‘single’ … ellipsis\ttabs\nnewlines",
    "a an the of to is be it I x y z 12 1",
    "",
]


def test_text_without_cjk_tokenizes_exactly_as_before():
    for text in NON_CJK_SAMPLES:
        assert tokenize(text) == _old_tokenize(text), text


def test_non_cjk_words_in_mixed_text_tokenize_as_before():
    cjk = re.compile(r"[぀-ヿ一-鿿가-힯]")
    for text in [
        "Tesla 在中国 sales rose; BYD's batteries 电池 cost less",
        "全固体電池 (all-solid-state batteries) のコスト costs",
        "삼성 Samsung 배터리 batteries",
    ]:
        non_cjk = [t for t in tokenize(text) if not cjk.search(t)]
        assert non_cjk == _old_tokenize(cjk.sub(" ", text)), text
