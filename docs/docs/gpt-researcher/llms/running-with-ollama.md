# Running with Ollama

Ollama is a platform that allows you to deploy and manage custom language models. This guide will walk you through deploying a custom language model on Ollama.

Read on to understand how to install a Custom LLM with the Ollama WebUI, and how to query it with GPT-Researcher.


## Fetching the Desired LLM Models

After deploying Ollama WebUI, you'll want to enter the [Open WebUI Admin App](https://github.com/open-webui/open-webui/tree/main) & download a custom LLM.

Choose a model from [Ollama's Library of LLM's](https://ollama.com/library?sort=popular)

Paste the model name & size into the Web UI:

<img width="1511" alt="Screen Shot 2024-08-27 at 23 26 28" src="https://github.com/user-attachments/assets/32abd048-745c-4232-9f1f-6af265cff250"></img>

For our example, let's choose to download the `qwen2:1.5b` model.

This model now automatically becomes available via your Server's out-of-the-box API - we'll leverage it within our GPT-Researcher .env file in the next step.


## Querying your Custom LLM with GPT-Researcher

If you deploy ollama locally, a .env like so, should enable powering GPT-Researcher with Ollama:

```bash
OPENAI_API_KEY="123"
OPENAI_API_BASE="http://127.0.0.1:11434/v1"
OLLAMA_BASE_URL="http://127.0.0.1:11434/"
FAST_LLM="ollama:qwen2:1.5b"
SMART_LLM="ollama:qwen2:1.5b"
EMBEDDING="ollama:all-minilm:22m"
```

Replace `FAST_LLM` & `SMART_LLM` with the model you downloaded from the Elestio Web UI in the previous step.


## Run LLM Test Script for GPTR

And here's a custom python script you can use to query your custom LLM:

```python

import os
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)
from gpt_researcher.llm_provider.generic import GenericLLMProvider
from gpt_researcher.utils.llm import get_llm

OLLAMA_BASE_URL = "https://ollama-ug3qr-u21899.vm.elestio.app:57987"
LLM_MODEL = "llama3.1"

# Create the GenericLLMProvider instance
llm_provider = get_llm(
    "ollama",
    base_url=OLLAMA_BASE_URL,
    model=LLM_MODEL,
    temperature=0.7,
    max_tokens=2000,
    verify_ssl=False  # Add this line
)

# Test the connection with a simple query
messages = [{"role": "user", "content": "sup?"}]

async def test_ollama():
    try:
        response = await llm_provider.get_chat_response(messages, stream=False)
        print("Ollama response:", response)
    except Exception as e:
        print(f"Error: {e}")

# Run the async function
asyncio.run(test_ollama())
    
```

Replace `OLLAMA_BASE_URL` with the URL of your Ollama instance, and `LLM_MODEL` with the model you downloaded from the Ollama Web UI.

Run the script to test the connection with your custom LLM.


## Deploy Ollama on Elestio

Elestio is a platform that allows you to deploy and manage custom language models. This guide will walk you through deploying a custom language model on Elestio.

You can deploy an [Open WebUI](https://github.com/open-webui/open-webui/tree/main) server with [Elestio](https://elest.io/open-source/ollama)

Here's an example .env file that will enable powering GPT-Researcher with Elestio:

```bash
OPENAI_API_KEY="123"
OPENAI_API_BASE="https://<your_custom_elestio_project>.vm.elestio.app:57987/v1"
OLLAMA_BASE_URL="https://<your_custom_elestio_project>.vm.elestio.app:57987/"
FAST_LLM="openai:qwen2:1.5b"
SMART_LLM="openai:qwen2:1.5b"
EMBEDDING="ollama:all-minilm:22m"
```

#### Disable Elestio Authentication or Add Auth Headers

To remove the basic auth you have to follow the below steps:
Go to your service -> Security -> at last Nginx -> in that find the below code:

```bash
auth_basic           "Authentication"; 
auth_basic_user_file /etc/nginx/conf.d/.htpasswd;
```

Comment these both these lines out and click the button "Update & Restart" to reflect the changes.
