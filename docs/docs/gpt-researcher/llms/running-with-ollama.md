# Running with Ollama

Ollama is a platform that allows you to deploy and manage custom language models. This guide will walk you through deploying a custom language model on Ollama.

Read on to understand how to install a Custom LLM with the Ollama WebUI, and how to query it with GPT-Researcher.


## Fetching the Desired LLM Models

After deploying Ollama WebUI, you'll want to enter the [Open WebUI Admin App](https://github.com/open-webui/open-webui/tree/main) & download a custom LLM.

Choose a model from [Ollama's Library of LLM's](https://ollama.com/library?sort=popular)

Paste the model name & size into the Web UI:

<img width="1511" alt="Screen Shot 2024-08-27 at 23 26 28" src="https://github.com/user-attachments/assets/32abd048-745c-4232-9f1f-6af265cff250"></img>

For our example, let's choose to download the `qwen2:1.5b` from the chat completion model & `nomic-embed-text` for the embeddings model.

This model now automatically becomes available via your Server's out-of-the-box API - we'll leverage it within our GPT-Researcher .env file in the next step.


## Querying your Custom LLM with GPT-Researcher

If you deploy ollama locally, a .env like so, should enable powering GPT-Researcher with Ollama:

```bash
OPENAI_API_KEY="123"
OPENAI_API_BASE="http://127.0.0.1:11434/v1"
OLLAMA_BASE_URL="http://127.0.0.1:11434/"
FAST_LLM="ollama:qwen2:1.5b"
SMART_LLM="ollama:qwen2:1.5b"
STRATEGIC_LLM="ollama:qwen2:1.5b"
EMBEDDING_PROVIDER="ollama"
OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

Replace `FAST_LLM` & `SMART_LLM` with the model you downloaded from the Elestio Web UI in the previous step.


## Deploy Ollama on Elestio

Elestio is a platform that allows you to deploy and manage custom language models. This guide will walk you through deploying a custom language model on Elestio.

You can deploy an [Open WebUI](https://github.com/open-webui/open-webui/tree/main) server with [Elestio](https://elest.io/open-source/ollama)


## Run LLM Test Script for GPTR

You can leverage the global `test-your-llm` function with `tests/test-your-llm`.
Here are the steps to do so:

Step 1: Set the following values in your `.env`. Note: replace the base urls with the custom domain that your web app is available on - for example: if the web app is available on `https://ollama-2d52b-u21899.vm.elestio.app/` within the browser, that becomes the value to use in your .env file.

```bash
OPENAI_API_KEY="123"
OPENAI_API_BASE="https://ollama-2d52b-u21899.vm.elestio.app:57987/v1"
OLLAMA_BASE_URL="https://ollama-2d52b-u21899.vm.elestio.app:57987/"
FAST_LLM="openai:qwen2.5"
SMART_LLM="openai:qwen2.5"
STRATEGIC_LLM="openai:qwen2.5"
EMBEDDING_PROVIDER="ollama"
OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

Note: to verify you're pointing at the correct API URL, you can run something like this in your terminal:

```bash
nslookup ollama-2d52b-u21899.vm.elestio.app
```

Step 2:

```bash
cd tests
python -m test-your-llm
```

You should get an LLM response, such as:
```
Sup! How can I assist you today? Feel free to ask me any questions or let me know if you need help with anything.
```

#### Disable Elestio Authentication or Add Auth Headers

To remove the basic auth you have to follow the below steps:

Go to your service -> Security in your Elestio admin panel.

Step 1: Disable the Firewall.

Step 2: Edit your Nginx Configuration. You'll want to comment both these both these lines out:

```bash
auth_basic           "Authentication"; 
auth_basic_user_file /etc/nginx/conf.d/.htpasswd;
```

Step 2: Click the button "Update & Restart" to apply your nginx changes.
