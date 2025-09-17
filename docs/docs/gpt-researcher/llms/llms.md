# Configure LLM

As described in the [introduction](/docs/gpt-researcher/gptr/config), the default LLM and embedding is OpenAI due to its superior performance and speed. 
With that said, GPT Researcher supports various open/closed source LLMs and embeddings, and you can easily switch between them by updating the `SMART_LLM`, `FAST_LLM` and `EMBEDDING` env variables. You might also need to include the provider API key and corresponding configuration params.

Current supported LLMs are `openai`, `anthropic`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `groq`, `bedrock` and `litellm`.

Current supported embeddings are `openai`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `nomic` ,`voyageai` and `bedrock`.

To learn more about support customization options see [here](/docs/gpt-researcher/gptr/config).

**Please note**: GPT Researcher is optimized and heavily tested on GPT models. Some other models might run into context limit errors, and unexpected responses.
Please provide any feedback in our [Discord community](https://discord.gg/DUmbTebB) channel, so we can better improve the experience and performance.

Below you can find examples for how to configure the various supported LLMs.

## OpenAI

```env
# set the custom OpenAI API key
OPENAI_API_KEY=[Your Key]

# specify llms
FAST_LLM=openai:gpt-5-mini
SMART_LLM=openai:gpt-5
STRATEGIC_LLM=openai:o4-mini

# specify embedding
EMBEDDING=openai:text-embedding-3-small
```


## Custom LLM

Create a local OpenAI API using [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md#quick-start).

For custom LLM, specify "openai:&#123;your-llm&#125;"
```env
# set the custom OpenAI API url
OPENAI_BASE_URL=http://localhost:1234/v1
# set the custom OpenAI API key
OPENAI_API_KEY=dummy_key

# specify custom llms  
FAST_LLM=openai:your_fast_llm
SMART_LLM=openai:your_smart_llm
STRATEGIC_LLM=openai:your_strategic_llm
```

For custom embedding, set "custom:&#123;your-embedding&#125;"
```env
# set the custom OpenAI API url
OPENAI_BASE_URL=http://localhost:1234/v1
# set the custom OpenAI API key
OPENAI_API_KEY=dummy_key

# specify the custom embedding model   
EMBEDDING=custom:your_embedding
```


## Azure OpenAI

In Azure OpenAI you have to chose which models you want to use and make deployments for each model. You do this on the [Azure OpenAI Portal](https://portal.azure.com/). 

In January 2025 the models that are recommended to use are: 

- gpt-4o-mini
- gpt-4o
- o1-preview or o1-mini (You might need to request access to these models before you can deploy them).

Please then specify the model names/deployment names in your `.env` file.

**Required Precondition** 

- Your endpoint can have any valid name.
- A model's deployment name *must be the same* as the model name.
- You need to deploy an *Embedding Model*: To ensure optimal performance, GPT Researcher requires the 'text-embedding-3-large' model. Please deploy this specific model to your Azure Endpoint.

**Recommended**:

- Quota increase: You should also request a quota increase especially for the embedding model, as the default quota is not sufficient. 

```env
# set the azure api key and deployment as you have configured it in Azure Portal. There is no default access point unless you configure it yourself!
AZURE_OPENAI_API_KEY=[Your Key]
AZURE_OPENAI_ENDPOINT=https://&#123;your-endpoint&#125;.openai.azure.com/
OPENAI_API_VERSION=2024-05-01-preview

# each string is "azure_openai:deployment_name". ensure that your deployment have the same name as the model you use!
FAST_LLM=azure_openai:gpt-4o-mini
SMART_LLM=azure_openai:gpt-4o
STRATEGIC_LLM=azure_openai:o1-preview

# specify embedding
EMBEDDING=azure_openai:text-embedding-3-large
```

Add `langchain-azure-dynamic-sessions` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Ollama

GPT Researcher supports both Ollama LLMs and embeddings. You can choose each or both.
To use [Ollama](http://www.ollama.com) you can set the following environment variables

```env
OLLAMA_BASE_URL=http://localhost:11434
FAST_LLM=ollama:llama3
SMART_LLM=ollama:llama3
STRATEGIC_LLM=ollama:llama3

EMBEDDING=ollama:nomic-embed-text
```

Add `langchain-ollama` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

### Granite with Ollama

GPT Researcher has custom prompt formatting for the [Granite family of models](https://ollama.com/search?q=granite). To use
the right formatting, you can set the following environment variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
FAST_LLM=ollama:granite3.3:2b
SMART_LLM=ollama:granite3.3:8b
STRATEGIC_LLM=ollama:granite3.3:8b
PROMPT_FAMILY=granite
```

## Groq

GroqCloud provides advanced AI hardware and software solutions designed to deliver amazingly fast AI inference performance.
To leverage Groq in GPT-Researcher, you will need a GroqCloud account and an API Key. (__NOTE:__ Groq has a very _generous free tier_.)

### Sign up
- You can signup here: [https://console.groq.com/login](https://console.groq.com/login)
- Once you are logged in, you can get an API Key here: [https://console.groq.com/keys](https://console.groq.com/keys)

- Once you have an API key, you will need to add it to your `systems environment` using the variable name:
`GROQ_API_KEY=*********************`

### Update env vars
And finally, you will need to configure the GPT-Researcher Provider and Model variables:

```env
GROQ_API_KEY=[Your Key]

# Set one of the LLM models supported by Groq
FAST_LLM=groq:Mixtral-8x7b-32768
SMART_LLM=groq:Mixtral-8x7b-32768
STRATEGIC_LLM=groq:Mixtral-8x7b-32768
```

Add `langchain-groq` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

__NOTE:__ As of the writing of this Doc (May 2024), the available Language Models from Groq are:

* Llama3-70b-8192
* Llama3-8b-8192
* Mixtral-8x7b-32768
* Gemma-7b-it


## Anthropic

Refer to Anthropic [Getting started page](https://docs.anthropic.com/en/api/getting-started) to obtain Anthropic API key. Update the corresponding env vars, for example:
```env
ANTHROPIC_API_KEY=[Your Key]
FAST_LLM=anthropic:claude-2.1
SMART_LLM=anthropic:claude-3-opus-20240229
STRATEGIC_LLM=anthropic:claude-3-opus-20240229
```

Add `langchain-anthropic` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

Anthropic does not offer its own embedding model, therefore, you'll want to either default to the OpenAI embedding model, or find another.


## Mistral AI

Sign up for a [Mistral API key](https://console.mistral.ai/users/api-keys/). 
Then update the corresponding env vars, for example:
```env
MISTRAL_API_KEY=[Your Key]
FAST_LLM=mistralai:open-mistral-7b
SMART_LLM=mistralai:mistral-large-latest
STRATEGIC_LLM=mistralai:mistral-large-latest

EMBEDDING=mistralai:mistral-embed
```

Add `langchain-mistralai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Together AI
[Together AI](https://www.together.ai/) offers an API to query [50+ leading open-source models](https://docs.together.ai/docs/inference-models) in a couple lines of code.
Then update corresponding env vars, for example:
```env
TOGETHER_API_KEY=[Your Key]
FAST_LLM=together:meta-llama/Llama-3-8b-chat-hf
SMART_LLM=together:meta-llama/Llama-3-70b-chat-hf
STRATEGIC_LLM=together:meta-llama/Llama-3-70b-chat-hf

EMBEDDING=mistralai:nomic-ai/nomic-embed-text-v1.5
```

Add `langchain-together` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## NetMind
[NetMind](https://netmind.ai/) provide a variety of [model API](https://www.netmind.ai/modelsLibrary) services—including LLM, image, text, audio, and video—that add limitless possibilities for scaling your application.
```env
NETMIND_API_KEY=[Your Key]

FAST_LLM=netmind:deepseek-ai/DeepSeek-V3-0324
SMART_LLM=netmind:deepseek-ai/DeepSeek-R1-0528
STRATEGIC_LLM=netmind:deepseek-ai/DeepSeek-V3-0324

EMBEDDING=netmind:nvidia/NV-Embed-v2
```
Add langchain-netmind to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or pip install it

## HuggingFace

This integration requires a bit of extra work. Follow [this guide](https://python.langchain.com/v0.1/docs/integrations/chat/huggingface/) to learn more.
After you've followed the tutorial above, update the env vars:
```env
HUGGINGFACE_API_KEY=[Your Key]
FAST_LLM=huggingface:HuggingFaceH4/zephyr-7b-beta
SMART_LLM=huggingface:HuggingFaceH4/zephyr-7b-beta
STRATEGIC_LLM=huggingface:HuggingFaceH4/zephyr-7b-beta

EMBEDDING=huggingface:sentence-transformers/all-MiniLM-L6-v2
```

Add `langchain-huggingface` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Google Gemini

Sign up [here](https://ai.google.dev/gemini-api/docs/api-key) for obtaining a Google Gemini API Key and update the following env vars:
```env
GOOGLE_API_KEY=[Your Key]
FAST_LLM=google_genai:gemini-1.5-flash
SMART_LLM=google_genai:gemini-1.5-pro
STRATEGIC_LLM=google_genai:gemini-1.5-pro

EMBEDDING=google_genai:models/text-embedding-004
```

Add `langchain-google-genai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Google VertexAI

```env
FAST_LLM=google_vertexai:gemini-1.5-flash-001
SMART_LLM=google_vertexai:gemini-1.5-pro-001
STRATEGIC_LLM=google_vertexai:gemini-1.5-pro-001

EMBEDDING=google_vertexai:text-embedding-004
```

Add `langchain-google-vertexai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Cohere

```env
COHERE_API_KEY=[Your Key]
FAST_LLM=cohere:command
SMART_LLM=cohere:command-nightly
STRATEGIC_LLM=cohere:command-nightly

EMBEDDING=cohere:embed-english-v3.0
```

Add `langchain-cohere` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Fireworks

```env
FIREWORKS_API_KEY=[Your Key]
base_url=https://api.fireworks.ai/inference/v1/completions
FAST_LLM=fireworks:accounts/fireworks/models/mixtral-8x7b-instruct
SMART_LLM=fireworks:accounts/fireworks/models/mixtral-8x7b-instruct
STRATEGIC_LLM=fireworks:accounts/fireworks/models/mixtral-8x7b-instruct

EMBEDDING=fireworks:nomic-ai/nomic-embed-text-v1.5
```

Add `langchain-fireworks` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Bedrock

```env
FAST_LLM=bedrock:anthropic.claude-3-sonnet-20240229-v1:0
SMART_LLM=bedrock:anthropic.claude-3-sonnet-20240229-v1:0
STRATEGIC_LLM=bedrock:anthropic.claude-3-sonnet-20240229-v1:0

EMBEDDING=bedrock:amazon.titan-embed-text-v2:0
```

Add `langchain_aws` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## LiteLLM

```env
FAST_LLM=litellm:perplexity/pplx-7b-chat
SMART_LLM=litellm:perplexity/pplx-70b-chat
STRATEGIC_LLM=litellm:perplexity/pplx-70b-chat
```

Add `langchain_community` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## xAI

```env
FAST_LLM=xai:grok-beta
SMART_LLM=xai:grok-beta
STRATEGIC_LLM=xai:grok-beta
```

Add `langchain_xai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## DeepSeek
```env
DEEPSEEK_API_KEY=[Your Key]
FAST_LLM=deepseek:deepseek-chat
SMART_LLM=deepseek:deepseek-chat
STRATEGIC_LLM=deepseek:deepseek-chat
```

## Dashscope

```envs
DASHSCOPE_API_KEY=[Your Key]
export FAST_LLM=dashscope:qwen3-32b
export SMART_LLM=dashscope:qwen-turbo-2025-04-28
export STRATEGIC_LLM=dashscope:qwen-plus-latest

export EMBEDDING=dashscope:text-embedding-v3
```

Add `dashscope` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it

## Openrouter.ai

```env
OPENROUTER_API_KEY=[Your openrouter.ai key]
OPENAI_BASE_URL=https://openrouter.ai/api/v1
FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
SMART_LLM=openrouter:google/gemini-2.0-flash-001
STRATEGIC_LLM=openrouter:google/gemini-2.5-pro-exp-03-25
OPENROUTER_LIMIT_RPS=1  # Ratelimit request per secound
EMBEDDING=google_genai:models/text-embedding-004 # openrouter doesn't support embedding models, use google instead its free
GOOGLE_API_KEY=[Your *google gemini* key]
```
## AI/ML API
#### AI/ML API provides 300+ AI models including Deepseek, Gemini, ChatGPT. The models run at enterprise-grade rate limits and uptimes.
You can check provider docs [_here_](https://docs.aimlapi.com/?utm_source=gptr&utm_medium=github&utm_campaign=integration)

And models overview is [_here_](https://aimlapi.com/models/?utm_source=gptr&utm_medium=github&utm_campaign=integration)

```env
AIMLAPI_API_KEY=[Your aimlapi.com key]
AIMLAPI_BASE_URL="https://api.aimlapi.com/v1"
FAST_LLM="aimlapi:claude-3-5-sonnet-20241022"
SMART_LLM="aimlapi:openai/o4-mini-2025-04-16"
STRATEGIC_LLM="aimlapi:x-ai/grok-3-mini-beta"
EMBEDDING="aimlapi:text-embedding-3-small"
```

## vLLM
```env
VLLM_OPENAI_API_KEY=[Your Key] # you can set this to 'EMPTY' or anything
VLLM_OPENAI_API_BASE=[Your base url] # for example http://localhost:8000/v1/
FAST_LLM=vllm_openai:Qwen/Qwen3-8B-AWQ
SMART_LLM=vllm_openai:Qwen/Qwen3-8B-AWQ
STRATEGIC_LLM=vllm_openai:Qwen/Qwen3-8B-AWQ
```

## Other Embedding Models

### Nomic

```env
EMBEDDING=nomic:nomic-embed-text-v1.5
```

### VoyageAI

```env
VOYAGE_API_KEY=[Your Key]
EMBEDDING=voyageai:voyage-law-2
```

Add `langchain-voyageai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it
