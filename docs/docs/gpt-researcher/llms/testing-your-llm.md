# Dein LLM testen

Hier ist ein kurzes Snippet, mit dem du prüfen kannst, ob deine LLM-bezogenen Umgebungsvariablen korrekt gesetzt sind.

```python
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
            messages = [{"role": "user", "content": "Hallo?"}],
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs
        )
    except Exception as e:
        print(f"Fehler beim Aufruf des LLM: {e}")

# Async-Funktion starten
asyncio.run(main())
```
