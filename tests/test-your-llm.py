from __future__ import annotations

import asyncio

from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

load_dotenv()


async def main():
    cfg = Config()

    try:
        report: str = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[{"role": "user", "content": "sup?"}],
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            max_tokens=cfg.smart_token_limit,  # pyright: ignore[reportAttributeAccessIssue]
            llm_kwargs=cfg.llm_kwargs,
            cfg=cfg,
        )

        print(report)
    except Exception as e:
        print(f"Error in calling LLM: {e.__class__.__name__}: {e}")


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
