# Configure LLM
As described in the [introduction](/docs/gpt-researcher/config), the default LLM is OpenAI due to its superior performance and speed. 
However, GPT Researcher supports various open/closed source LLMs, and you can easily switch between them by adding the `LLM_PROVIDER` env variable and corresponding configuration params.

Below you can find how to configure the various supported LLMs.

## OpenAI

## Ollama

## Groq

GroqCloud provides advanced AI hardware and software solutions designed to deliver amazingly fast AI inference performance.
To leverage Groq in GPT-Researcher, you will need a GroqCloud account and an API Key. (__NOTE:__ Groq has a very _generous free tier_.)

- You can signup here: [https://console.groq.com/login](https://console.groq.com/login)
- Once you are logged in, you can get an API Key here: [https://console.groq.com/keys](https://console.groq.com/keys)

- Once you have an API key, you will need to add it to your `systems environment` using the variable name:
`GROQ_API_KEY="*********************"`


And finally, you will need to configure the GPT-Researcher Provider and Model variables:

```bash
# To use Groq set the llm provider to groq
LLM_PROVIDER=groq

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

...
