# Supported LLMs

The following LLMs are supported by GPTR. Please note that you'll need to install the relevant langchain package for each LLM.

- openai
- anthropic
- azure_openai
- cohere
- google_vertexai
- google_genai
- fireworks
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

The GPTR LLM Module is built on top of the [Langchain LLM Module](https://python.langchain.com/v0.2/docs/integrations/llms/).

If you'd like to add a new LLM into GPTR, you can start with the [langchain documentation](https://python.langchain.com/v0.2/docs/integrations/platforms/) and then look into integrating it into the GPTR LLM Module.