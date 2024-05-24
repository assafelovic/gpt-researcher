# Configure LLM
As described in the [introduction](/docs/gpt-researcher/config), the default LLM is OpenAI due to its superior performance and speed. 
However, GPT Researcher supports various open/closed source LLMs, and you can easily switch between them by adding the `LLM_PROVIDER` env variable and corresponding configuration params.

Below you can find how to configure the various supported LLMs.

## OpenAI
Create a local OpenAI API using [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md#quick-start).

### custom OpenAI API LLM
```bash
# use a custom OpenAI API LLM provider
LLM_PROVIDER="openai"

# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="custom_key"

# specify the custom OpenAI API llm model  
FAST_LLM_MODEL="gpt-3.5-turbo-16k"
# specify the custom OpenAI API llm model  
SMART_LLM_MODEL="gpt-4o"

```
### custom OpenAI API EMBEDDING
```bash
# use a custom OpenAI API EMBEDDING provider
EMBEDDING_PROVIDER="custom"

# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="custom_key"

# specify the custom OpenAI API embedding model   
OPENAI_EMBEDDING_MODEL="custom_model"
```


## Ollama

## Groq

## Anthropic

...