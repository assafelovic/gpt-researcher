# Deploy LLM on Elestio

Elestio is a platform that allows you to deploy and manage custom language models. This guide will walk you through deploying a custom language model on Elestio.

You can deploy an [Open WebUI](https://github.com/open-webui/open-webui/tree/main) server with [Elestio](https://elest.io/open-source/ollama)

After deploying the Elestio server, you'll want to enter the [Open WebUI Admin App](https://github.com/open-webui/open-webui/tree/main) & download a custom LLM.

For our example, let's choose to download the `gemma2:2b` model.

This model now automatically becomes available via your Server's out-of-the-box API.


### Querying your Custom LLM with GPT-Researcher

Here's the .env file you'll need to query your custom LLM with GPT-Researcher:

```bash
OPENAI_API_KEY="123"
OPENAI_API_BASE="https://<your_custom_elestio_project>.vm.elestio.app:57987/v1"
OLLAMA_BASE_URL="https://<your_custom_elestio_project>.vm.elestio.app:57987/"
FAST_LLM_MODEL=gemma2:2b
SMART_LLM_MODEL=gemma2:2b
OLLAMA_EMBEDDING_MODEL=all-minilm
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=ollama
```

#### Disable Elestio Authentication or Added Auth Headers

To remove the basic auth you have to follow the below steps:
Go to your service -> Security -> at last Nginx -> in that find the below code:

```bash
auth_basic           "Authentication"; 

auth_basic_user_file /etc/nginx/conf.d/.htpasswd;
```

Comment these both these lines out and click the button "Update & Restart" to reflect the changes.


#### Run LLM Test Script for GPTR

And here's a custom python script you can use to query your custom LLM:

```python

import os
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)
from gpt_researcher.llm_provider.generic import GenericLLMProvider
from gpt_researcher.utils.llm import get_llm

# Set up environment variables
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_BASE_URL"] = "https://ollama-ug3qr-u21899.vm.elestio.app:57987"
os.environ["FAST_LLM_MODEL"] = "llama3.1"

# Create the GenericLLMProvider instance
llm_provider = get_llm(
    "ollama",
    base_url=os.environ["OLLAMA_BASE_URL"],
    model=os.environ["FAST_LLM_MODEL"],
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

