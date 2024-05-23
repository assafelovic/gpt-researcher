# Configure LLM
As described in the [introduction](/docs/gpt-researcher/config), the default LLM is OpenAI due to its superior performance and speed. 
However, GPT Researcher supports various open/closed source LLMs, and you can easily switch between them by adding the `LLM_PROVIDER` env variable and corresponding configuration params.

Below you can find how to configure the various supported LLMs.

## OpenAI

## Ollama

To use [Ollama](http://www.ollama.com) you have to set the following environment variables

```bash
# use ollama for both, LLM and EMBEDDING provider
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

# the Ollama endpoint to use
OLLAMA_BASE_URL=http://localhost:11434

# specify one of the LLM models supported by Ollama
FAST_LLM_MODEL=llama3
# specify one of the LLM models supported by Ollama 
SMART_LLM_MODEL=llama3 
# the temperature to use, defaults to 0.55
TEMPERATURE=0.55

# specify one of the embedding models supported by Ollama 
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Groq

## Anthropic

...