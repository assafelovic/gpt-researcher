# Configure LLM

As described in the [introduction](/docs/gpt-researcher/gptr/config), the default LLM and embedding is OpenAI due to its superior performance and speed. 
With that said, GPT Researcher supports various open/closed source LLMs and embeddings, and you can easily switch between them by updating the `SMART_LLM`, `FAST_LLM` and `EMBEDDING` env variables. You might also need to include the provider API key and corresponding configuration params.

Current supported LLMs are `openai`, `anthropic`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `groq`, `bedrock` and `litellm`.

Current supported embeddings are `openai`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `nomic` ,`voyageai` and `bedrock`.

To learn more about support customization options see [here](/gpt-researcher/config).

**Please note**: GPT Researcher is optimized and heavily tested on GPT models. Some other models might run into context limit errors, and unexpected responses.
Please provide any feedback in our [Discord community](https://discord.gg/DUmbTebB) channel, so we can better improve the experience and performance.

Below you can find examples for how to configure the various supported LLMs.

## OpenAI

```bash
# set the custom OpenAI API key
OPENAI_API_KEY=[Your Key]

# specify llms
FAST_LLM="openai:gpt-4o-mini"
SMART_LLM="openai:gpt-4o"
STRATEGIC_LLM="openai:o1-preview"

# specify embedding
EMBEDDING="openai:text-embedding-3-small"
```


## Custom LLM

Create a local OpenAI API using [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md#quick-start).

For custom LLM, specify "openai:{your-llm}"
```bash
# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="dummy_key"

# specify custom llms  
FAST_LLM="openai:your_fast_llm"
SMART_LLM="openai:your_smart_llm"
STRATEGIC_LLM="openai:your_strategic_llm"
```

For custom embedding, set "custom:{your-embedding}"
```bash
# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="dummy_key"

# specify the custom embedding model   
EMBEDDING="custom:your_embedding"
```


## Azure OpenAI

See also the documentation in the Langchain [Azure OpenAI](https://api.python.langchain.com/en/latest/chat_models/langchain_openai.chat_models.azure.AzureChatOpenAI.html) page.

On Azure OpenAI you will need to create deployments for each model you want to use. Please also specify the model names/deployment names in your `.env` file:

Required Embedding Model:
To ensure optimal performance, GPT Researcher requires the text-embedding-3-large model. Please deploy this specific model to your Azure Endpoint.

```bash
AZURE_OPENAI_API_KEY=[Your Key]
AZURE_OPENAI_ENDPOINT=https://{your-endpoint}.openai.azure.com/
OPENAI_API_VERSION=2024-05-01-preview

# note that the deployment name must be the same as the model name
FAST_LLM=azure_openai:gpt-4o-mini 
SMART_LLM=azure_openai:gpt-4o
STRATEGIC_LLM=azure_openai:o1-preview


```


## Ollama

GPT Researcher supports both Ollama LLMs and embeddings. You can choose each or both.
To use [Ollama](http://www.ollama.com) you can set the following environment variables

```bash
OLLAMA_BASE_URL=http://localhost:11434
FAST_LLM="ollama:llama3"
SMART_LLM="ollama:llama3"
STRATEGIC_LLM="ollama:llama3"

EMBEDDING="ollama:nomic-embed-text"
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
GROQ_API_KEY=[Your Key]

# Set one of the LLM models supported by Groq
FAST_LLM="groq:Mixtral-8x7b-32768"
SMART_LLM="groq:Mixtral-8x7b-32768"
STRATEGIC_LLM="groq:Mixtral-8x7b-32768"
```

__NOTE:__ As of the writing of this Doc (May 2024), the available Language Models from Groq are:

* Llama3-70b-8192
* Llama3-8b-8192
* Mixtral-8x7b-32768
* Gemma-7b-it


## Anthropic

Refer to Anthropic [Getting started page](https://docs.anthropic.com/en/api/getting-started) to obtain Anthropic API key. Update the corresponding env vars, for example:
```bash
ANTHROPIC_API_KEY=[Your key]
FAST_LLM="anthropic:claude-2.1"
SMART_LLM="anthropic:claude-3-opus-20240229"
STRATEGIC_LLM="anthropic:claude-3-opus-20240229"
```

Anthropic does not offer its own embedding model. 


## Mistral AI

Sign up for a [Mistral API key](https://console.mistral.ai/users/api-keys/). 
Then update the corresponding env vars, for example:
```bash
MISTRAL_API_KEY=[Your key]
FAST_LLM="mistralai:open-mistral-7b"
SMART_LLM="mistralai:mistral-large-latest"
STRATEGIC_LLM="mistralai:mistral-large-latest"

EMBEDDING="mistralai:mistral-embed"
```


## Together AI
[Together AI](https://www.together.ai/) offers an API to query [50+ leading open-source models](https://docs.together.ai/docs/inference-models) in a couple lines of code.
Then update corresponding env vars, for example:
```bash
TOGETHER_API_KEY=[Your key]
FAST_LLM="together:meta-llama/Llama-3-8b-chat-hf"
SMART_LLM="together:meta-llama/Llama-3-70b-chat-hf"
STRATEGIC_LLM="together:meta-llama/Llama-3-70b-chat-hf"

EMBEDDING="mistralai:nomic-ai/nomic-embed-text-v1.5"
```


## HuggingFace

This integration requires a bit of extra work. Follow [this guide](https://python.langchain.com/v0.1/docs/integrations/chat/huggingface/) to learn more.
After you've followed the tutorial above, update the env vars:
```bash
HUGGINGFACE_API_KEY=[Your key]
FAST_LLM="huggingface:HuggingFaceH4/zephyr-7b-beta"
SMART_LLM="huggingface:HuggingFaceH4/zephyr-7b-beta"
STRATEGIC_LLM="huggingface:HuggingFaceH4/zephyr-7b-beta"

EMBEDDING="sentence-transformers/all-MiniLM-L6-v2"
```


## Google Gemini

Sign up [here](https://ai.google.dev/gemini-api/docs/api-key) for obtaining a Google Gemini API Key and update the following env vars:
```bash
GOOGLE_API_KEY=[Your key]
FAST_LLM="google_genai:gemini-1.5-flash"
SMART_LLM="google_genai:gemini-1.5-pro"
STRATEGIC_LLM="google_genai:gemini-1.5-pro"

EMBEDDING="google_genai:models/text-embedding-004"
```


## Google VertexAI

```bash
FAST_LLM="google_vertexai:gemini-1.5-flash-001"
SMART_LLM="google_vertexai:gemini-1.5-pro-001"
STRATEGIC_LLM="google_vertexai:gemini-1.5-pro-001"

EMBEDDING="google_vertexai:text-embedding-004"
```


## Cohere

```bash
COHERE_API_KEY=[Your key]
FAST_LLM="cohere:command"
SMART_LLM="cohere:command-nightly"
STRATEGIC_LLM="cohere:command-nightly"

EMBEDDING="cohere:embed-english-v3.0"
```


## Fireworks

```bash
FIREWORKS_API_KEY=[Your key]
base_url="https://api.fireworks.ai/inference/v1/completions"
FAST_LLM="fireworks:accounts/fireworks/models/mixtral-8x7b-instruct"
SMART_LLM="fireworks:accounts/fireworks/models/mixtral-8x7b-instruct"
STRATEGIC_LLM="fireworks:accounts/fireworks/models/mixtral-8x7b-instruct"

EMBEDDING="fireworks:nomic-ai/nomic-embed-text-v1.5"
```


## Bedrock

```bash
FAST_LLM="bedrock:anthropic.claude-3-sonnet-20240229-v1:0"
SMART_LLM="bedrock:anthropic.claude-3-sonnet-20240229-v1:0"
STRATEGIC_LLM="bedrock:anthropic.claude-3-sonnet-20240229-v1:0"

EMBEDDING="bedrock:amazon.titan-embed-text-v2:0"
```


## LiteLLM

```bash
FAST_LLM="litellm:perplexity/pplx-7b-chat"
SMART_LLM="litellm:perplexity/pplx-70b-chat"
STRATEGIC_LLM="litellm:perplexity/pplx-70b-chat"
```


## xAI

```bash
FAST_LLM="xai:grok-beta"
SMART_LLM="xai:grok-beta"
STRATEGIC_LLM="xai:grok-beta"
```


## DeepSeek
```bash
DEEPSEEK_API_KEY=[Your key]
FAST_LLM="deepseek:deepseek-chat"
SMART_LLM="deepseek:deepseek-chat"
STRATEGIC_LLM="deepseek:deepseek-chat"
```


## Other Embedding Models

### Nomic

```bash
EMBEDDING="nomic:nomic-embed-text-v1.5"
```

### VoyageAI

```bash
VOYAGE_API_KEY=[Your Key]
EMBEDDING="voyageai:voyage-law-2"
```
