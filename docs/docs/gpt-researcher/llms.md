# Configure LLM
As described in the [introduction](/docs/gpt-researcher/config), the default LLM is OpenAI due to its superior performance and speed. 
With that said, GPT Researcher supports various open/closed source LLMs, and you can easily switch between them by adding the `LLM_PROVIDER` env variable and corresponding configuration params.
Current supported LLMs are `openai`, `google` (gemini), `azureopenai`, `ollama`, `anthropic`, `mistral`, `huggingface` and `groq`.

Using any model will require at least updating the `LLM_PROVIDER` param and passing the LLM provider API Key. You might also need to update the `SMART_LLM_MODEL` and `FAST_LLM_MODEL` env vars.
To learn more about support customization options see [here](/gpt-researcher/config).

**Please note**: GPT Researcher is optimized and heavily tested on GPT models. Some other models might run intro context limit errors, and unexpected responses.
Please provide any feedback in our [Discord community](https://discord.gg/DUmbTebB) channel, so we can better improve the experience and performance.

Below you can find examples for how to configure the various supported LLMs.

## Custom OpenAI
Create a local OpenAI API using [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md#quick-start).

### Custom OpenAI API LLM
```bash
# use a custom OpenAI API LLM provider
LLM_PROVIDER="openai"

# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="Your Key"

# specify the custom OpenAI API llm model  
FAST_LLM_MODEL="gpt-3.5-turbo-16k"
# specify the custom OpenAI API llm model  
SMART_LLM_MODEL="gpt-4o"

```
### Custom OpenAI API Embedding
```bash
# use a custom OpenAI API EMBEDDING provider
EMBEDDING_PROVIDER="custom"

# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="Your Key"

# specify the custom OpenAI API embedding model   
OPENAI_EMBEDDING_MODEL="custom_model"
```

### Azure OpenAI

```bash
EMBEDDING_PROVIDER="azureopenai"
AZURE_OPENAI_API_KEY="Your key"
```


## Ollama

GPT Researcher supports both Ollama LLMs and embeddings. You can choose each or both.
To use [Ollama](http://www.ollama.com) you can set the following environment variables

```bash
# Use ollama for both, LLM and EMBEDDING provider
LLM_PROVIDER=ollama

# Ollama endpoint to use
OLLAMA_BASE_URL=http://localhost:11434

# Specify one of the LLM models supported by Ollama
FAST_LLM_MODEL=llama3
# Specify one of the LLM models supported by Ollama 
SMART_LLM_MODEL=llama3 
# The temperature to use, defaults to 0.55
TEMPERATURE=0.55
```

**Optional** - You can also use ollama for embeddings
```bash
EMBEDDING_PROVIDER=ollama
# Specify one of the embedding models supported by Ollama 
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Groq

GroqCloud provides advanced AI hardware and software solutions designed to deliver amazingly fast AI inference performance.
To leverage Groq in GPT-Researcher, you will need a GroqCloud account and an API Key. (__NOTE:__ Groq has a very _generous free tier_.)

### Sign up
- You can signup here: [https://console.groq.com/login](https://console.groq.com/login)
- Once you are logged in, you can get an API Key here: [https://console.groq.com/keys](https://console.groq.com/keys)

- Once you have an API key, you will need to add it to your `systems environment` using the variable name:
`GROQ_API_KEY="*********************"`

### Update env vars
And finally, you will need to configure the GPT-Researcher Provider and Model variables:

```bash
# To use Groq set the llm provider to groq
LLM_PROVIDER=groq
GROQ_API_KEY=[Your Key]

# Set one of the LLM models supported by Groq
FAST_LLM_MODEL=Mixtral-8x7b-32768

# Set one of the LLM models supported by Groq
SMART_LLM_MODEL=Mixtral-8x7b-32768 

# The temperature to use defaults to 0.55
TEMPERATURE=0.55
```

__NOTE:__ As of the writing of this Doc (May 2024), the available Language Models from Groq are:

* Llama3-70b-8192
* Llama3-8b-8192
* Mixtral-8x7b-32768
* Gemma-7b-it

## Anthropic
[Anthropic](https://www.anthropic.com/) is an AI safety and research company, and is the creator of Claude. This page covers all integrations between Anthropic models and LangChain.

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=[Your key]
```

You can then define the fast and smart LLM models for example:
```bash
FAST_LLM_MODEL=claude-2.1
SMART_LLM_MODEL=claude-3-opus-20240229
```

You can then define the fast and smart LLM models for example:
```bash
FAST_LLM_MODEL=claude-2.1
SMART_LLM_MODEL=claude-3-opus-20240229
```

## Mistral
Sign up for a [Mistral API key](https://console.mistral.ai/users/api-keys/). 
Then update the corresponding env vars, for example:
```bash
LLM_PROVIDER=mistral
ANTHROPIC_API_KEY=[Your key]
FAST_LLM_MODEL=open-mistral-7b
SMART_LLM_MODEL=mistral-large-latest
```

## Together AI
[Together AI](https://www.together.ai/) offers an API to query [50+ leading open-source models](https://docs.together.ai/docs/inference-models) in a couple lines of code.
Then update corresponding env vars, for example:
```bash
LLM_PROVIDER=together
TOGETHER_API_KEY=[Your key]
FAST_LLM_MODEL=meta-llama/Llama-3-8b-chat-hf
SMART_LLM_MODEL=meta-llama/Llama-3-70b-chat-hf
```

## HuggingFace
This integration requires a bit of extra work. Follow [this guide](https://python.langchain.com/v0.1/docs/integrations/chat/huggingface/) to learn more.
After you've followed the tutorial above, update the env vars:

```bash
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=[Your key]
FAST_LLM_MODEL=HuggingFaceH4/zephyr-7b-beta
SMART_LLM_MODEL=HuggingFaceH4/zephyr-7b-beta
```

## Google Gemini
Sign up [here](https://ai.google.dev/gemini-api/docs/api-key) for obtaining a Google Gemini API Key and update the following env vars:

Please make sure to update fast and smart models to corresponding valid Gemini models.
```bash
LLM_PROVIDER=google
GEMINI_API_KEY=[Your key]
```
