# Running with Ollama

Ollama lets you turn a local GGUF into a named model and serve it on your own hardware.
For this repository, the recommended local model is `gemma4_obliterated`, backed by the
GGUF at:

```text
/home/xxammaxx/Schreibtisch/gemma4/llama.cpp/models/gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf
```

## Create the local model

The repo includes a ready-to-use Modelfile:

```bash
ollama create gemma4_obliterated -f ollama/Modelfile.gemma4_obliterated
```

If you want a quick smoke test after creation:

```bash
ollama run gemma4_obliterated "Reply with one short sentence confirming the model is ready."
```

If Ollama complains about insufficient system memory, stop the large
`llama-server` on port `8081` and retry. On this machine, that was the
main competing process during setup.

To verify how Ollama is scheduling the model:

```bash
ollama ps
```

On Linux, Ollama uses `OLLAMA_CONTEXT_LENGTH=8192 ollama serve` style overrides for the server.
For the GTX 1070 / 8 GB VRAM box, start conservatively with a smaller context window:

```bash
OLLAMA_CONTEXT_LENGTH=2048 ollama serve
```

If you want to keep Ollama's model cache in a custom location, set `OLLAMA_MODELS` before
starting the server:

```bash
OLLAMA_MODELS="$PWD/.ollama" ollama serve
```

## Querying `gemma4_obliterated` with GPT-Researcher

GPT-Researcher can talk to the local Ollama server directly. The code now defaults to
`http://127.0.0.1:11434` when `OLLAMA_BASE_URL` is not set, but setting it explicitly keeps
the setup obvious:

```bash
OLLAMA_BASE_URL="http://127.0.0.1:11434"
FAST_LLM="ollama:gemma4_obliterated"
SMART_LLM="ollama:gemma4_obliterated"
STRATEGIC_LLM="ollama:gemma4_obliterated"
EMBEDDING="ollama:nomic-embed-text"
```

If you want the whole stack local, keep `OLLAMA_BASE_URL` pointed at your local Ollama instance
and optionally use Ollama embeddings as shown above.

## Historical WebUI flow

If you deploy Ollama together with Open WebUI, you can still pull models from the WebUI and
query them through GPT-Researcher. That flow is unchanged; the difference here is that the
repo now ships a direct GGUF import for `gemma4_obliterated`, so you do not need to rely on
the public Ollama library for this setup.


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
