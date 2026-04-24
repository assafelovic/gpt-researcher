import os

import pytest
from dotenv import load_dotenv

from gpt_researcher.utils.llm import get_llm


load_dotenv()


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_LLM_TESTS") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Live OpenAI smoke requires RUN_LIVE_LLM_TESTS=1 and OPENAI_API_KEY",
)
@pytest.mark.asyncio
async def test_llm():
    llm = get_llm(
        "openai",
        model=os.getenv("TEST_OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7,
        max_tokens=1000,
    )

    response = await llm.get_chat_response(
        [{"role": "user", "content": "Reply with the word ok."}],
        stream=False,
    )

    assert response
