# LLM konfigurieren

Mit GPT Researcher kannst du verschiedene LLM-Provider verwenden. Die Standardkonfiguration ist auf OpenAI und DuckDuckGo ausgerichtet, aber du kannst lokale Modelle, Azure, Ollama und viele weitere Provider einsetzen.

## OpenAI

```bash
# OpenAI API-Key setzen
OPENAI_API_KEY=dein-openai-api-key

# Modelle auswählen
FAST_LLM=openai:gpt-4o-mini
SMART_LLM=openai:gpt-4o

# Embeddings wählen
EMBEDDING=openai:text-embedding-3-small
```

## Eigene OpenAI-kompatible API

Wenn du einen lokalen Server oder einen anderen OpenAI-kompatiblen Anbieter verwendest:

```bash
# Eigene API-URL setzen
OPENAI_BASE_URL=http://127.0.0.1:8081/v1

# API-Key setzen
OPENAI_API_KEY=sk-local

# Eigene Modelle eintragen
FAST_LLM=custom:gpt-4o-mini
SMART_LLM=custom:gpt-4o
EMBEDDING=custom:text-embedding-3-small
```

## Azure OpenAI

```bash
OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_ENDPOINT=https://DEIN-DEPLOYMENT.openai.azure.com/
AZURE_OPENAI_API_KEY=dein-azure-key

FAST_LLM=azure_openai:gpt-4o-mini
SMART_LLM=azure_openai:gpt-4o
EMBEDDING=azure_openai:text-embedding-ada-002
RETRIEVER=bing
BING_API_KEY=dein-bing-key
```

## Ollama

Für lokale Modelle wie `gemma4_obliterated`:

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434
FAST_LLM=ollama:gemma4_obliterated
SMART_LLM=ollama:gemma4_obliterated
STRATEGIC_LLM=ollama:gemma4_obliterated
EMBEDDING=ollama:nomic-embed-text
```

Weitere Ollama-Hinweise findest du in der Seite [Mit Ollama ausführen](/docs/gpt-researcher/llms/running-with-ollama).

## Weitere Anbieter

GPT Researcher unterstützt außerdem unter anderem:

- anthropic
- cohere
- google_vertexai
- google_genai
- fireworks
- gigachat
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

Wenn du einen Provider nutzt, der zusätzliche Bibliotheken benötigt, installiere das passende LangChain-Paket. Eine Übersicht findest du in der [Dokumentation zu unterstützten LLMs](/docs/gpt-researcher/llms/supported-llms).

## Tipps

- `LANGUAGE=german` setzt die Ausgabesprache des Reports.
- `TEMPERATURE` steuert die Zufälligkeit der Antworten.
- `LLM_KWARGS` ist nützlich für provider-spezifische Parameter wie `num_ctx` bei Ollama.
- `REASONING_EFFORT` beeinflusst strategische Modelle.

## Validierung

Wenn du deine Konfiguration testen möchtest, nutze die Seite [Dein LLM testen](/docs/gpt-researcher/llms/testing-your-llm).
