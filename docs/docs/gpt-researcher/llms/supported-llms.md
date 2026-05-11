# Unterstützte LLMs

Folgende LLMs werden von GPTR unterstützt. Wenn du nicht OpenAI verwendest, musst du das passende LangChain-Paket separat installieren.

- openai
- anthropic
- azure_openai
- cohere
- google_vertexai
- google_genai
- fireworks
- gigachat
- ollama
- together
- mistralai
- huggingface
- groq
- bedrock
- dashscope
- xai
- deepseek
- litellm
- openrouter
- forge
- avian
- vllm

Wenn du wissen möchtest, wie das jeweilige LangChain-Paket heißt, schau in die [LangChain-Dokumentation](https://python.langchain.com/v0.2/docs/integrations/platforms/) oder starte GPTR direkt und lies die Fehlermeldung.

Das GPTR-LLM-Modul basiert auf dem [LangChain-LLM-Modul](https://python.langchain.com/v0.2/docs/integrations/llms/).

Wenn du ein neues LLM zu GPTR hinzufügen möchtest, beginne mit der [LangChain-Dokumentation](https://python.langchain.com/v0.2/docs/integrations/platforms/) und schaue dir anschließend die Integration in das [GPTR-LLM-Modul](https://github.com/assafelovic/gpt-researcher/blob/master/gpt_researcher/llm_provider/generic/base.py) an.
