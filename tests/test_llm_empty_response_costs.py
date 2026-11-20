from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.utils.llm import create_chat_completion


@pytest.mark.asyncio
async def test_empty_llm_response_is_counted_before_retry():
    provider = MagicMock()
    provider.get_chat_response = AsyncMock(side_effect=["", "research result"])
    costs = []

    with (
        patch("gpt_researcher.utils.llm.get_llm", return_value=provider),
        patch(
            "gpt_researcher.utils.llm.calculate_llm_cost",
            side_effect=[0.03, 0.02],
        ) as calculate_cost,
        patch("gpt_researcher.utils.llm.asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await create_chat_completion(
            messages=[{"role": "user", "content": "Summarize results"}],
            model="gpt-5.4",
            llm_provider="openai",
            max_tokens=8000,
            cost_callback=costs.append,
        )

    assert result == "research result"
    assert costs == [0.03, 0.02]
    assert calculate_cost.call_count == 2
    assert calculate_cost.call_args_list[0].kwargs["output_content"] == ""
