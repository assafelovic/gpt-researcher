# Supported LLMs

The following LLMs are supported by GPTR (though you'll need to install the relevant langchain package separately if you're not using OpenAI).

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
- vllm

If you'd like to know the name of the langchain package for each LLM, you can check the [Langchain documentation](https://python.langchain.com/v0.2/docs/integrations/platforms/), or run GPTR as is and inspect the error message.

The GPTR LLM Module is built on top of the [Langchain LLM Module](https://python.langchain.com/v0.2/docs/integrations/llms/).

If you'd like to add a new LLM into GPTR, you can start with the [langchain documentation](https://python.langchain.com/v0.2/docs/integrations/platforms/) and then look into integrating it into the [GPTR LLM Module](https://github.com/assafelovic/gpt-researcher/blob/master/gpt_researcher/llm_provider/generic/base.py).