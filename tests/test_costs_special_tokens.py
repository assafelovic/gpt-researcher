import pytest
import tiktoken

from gpt_researcher.utils.costs import (
    EMBEDDING_COST,
    ENCODING_MODEL,
    INPUT_COST_PER_TOKEN,
    OUTPUT_COST_PER_TOKEN,
    calculate_llm_cost,
    estimate_embedding_cost,
    estimate_llm_cost,
)
from gpt_researcher.utils.llm import create_chat_completion


@pytest.mark.parametrize("text", ["ordinary text", "<|endoftext|>", "<|fim_suffix|>"])
@pytest.mark.parametrize("position", ["input", "output"])
def test_llm_cost_counts_special_token_spellings_as_text(text, position):
    prompt = text if position == "input" else "prompt"
    answer = text if position == "output" else "answer"
    encoding = tiktoken.get_encoding(ENCODING_MODEL)
    expected = (
        len(encoding.encode_ordinary(prompt)) * INPUT_COST_PER_TOKEN
        + len(encoding.encode_ordinary(answer)) * OUTPUT_COST_PER_TOKEN
    )

    assert estimate_llm_cost(prompt, answer) == pytest.approx(expected)
    assert calculate_llm_cost("ollama", "local", prompt, answer) == pytest.approx(
        expected
    )


@pytest.mark.parametrize("model", ["text-embedding-3-small", "local-embedding"])
@pytest.mark.parametrize("text", ["ordinary text", "<|endoftext|>", "<|fim_suffix|>"])
def test_embedding_cost_counts_special_token_spellings_as_text(model, text):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding(ENCODING_MODEL)
    docs = ["first document", text]
    expected = sum(len(encoding.encode_ordinary(doc)) for doc in docs) * EMBEDDING_COST

    assert estimate_embedding_cost(model, docs) == pytest.approx(expected)


@pytest.mark.asyncio
async def test_completion_returns_special_token_text_with_cost_callback(monkeypatch):
    answer = "The literal token is <|endoftext|>."

    class Provider:
        last_response_metadata = {}
        last_usage_metadata = {}

        async def get_chat_response(self, messages, stream, websocket, **kwargs):
            return answer

    monkeypatch.setattr("gpt_researcher.utils.llm.get_llm", lambda *a, **kw: Provider())
    costs = []
    response = await create_chat_completion(
        messages=[{"role": "user", "content": "Explain token spellings"}],
        llm_provider="ollama",
        model="local",
        cost_callback=costs.append,
    )

    assert response == answer
    assert len(costs) == 1
    assert costs[0] > 0
