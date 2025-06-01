from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    cfg = Config()

    try:
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages = [{"role": "user", "content": "sup?"}],
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs
        )
    except Exception as e:
        print(f"Error in calling LLM: {e}")

# Run the async function
asyncio.run(main())