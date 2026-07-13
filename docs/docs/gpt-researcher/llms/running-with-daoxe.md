# Running with DaoXE

[DaoXE](https://daoxe.com) is a multi-model multi-protocol API gateway. It exposes:

- OpenAI-compatible Chat Completions (`https://daoxe.com/v1`)
- OpenAI Responses (where available)
- Anthropic Messages / Claude protocol (`/v1/messages` and related Anthropic-shaped paths)
- Image-compatible endpoints where enabled for your account

GPT Researcher talks to LLMs through LangChain-style providers. The simplest path is the **OpenAI-compatible** provider with DaoXE as `OPENAI_BASE_URL`. Other clients (Claude Code, Anthropic SDK, etc.) can use DaoXE’s Anthropic Messages path separately; this guide focuses on GPTR.

DaoXE is **not available in mainland China**. Model IDs, pricing, and capability flags are account-scoped—always resolve them from your live catalog, not from a static blog list.

## 1. Get credentials and model IDs

1. Create an account at [daoxe.com](https://daoxe.com) and issue an API key.
2. List models available to your key:

```bash
curl -sS https://daoxe.com/v1/models \
  -H "Authorization: Bearer $DAOXE_API_KEY" | head
```

3. Pick three IDs that fit GPTR roles (fast / smart / strategic). Prefer long-context, tool-capable models for `SMART_LLM` and `STRATEGIC_LLM`.

## 2. Configure environment

```env
OPENAI_API_KEY=[Your DaoXE API key]
OPENAI_BASE_URL=https://daoxe.com/v1

# Exact IDs from GET /v1/models for your account
FAST_LLM=openai:YOUR_FAST_MODEL_ID
SMART_LLM=openai:YOUR_SMART_MODEL_ID
STRATEGIC_LLM=openai:YOUR_STRATEGIC_MODEL_ID
```

Notes:

- The `openai:` prefix tells GPTR to use the OpenAI-compatible stack; traffic still goes to DaoXE via `OPENAI_BASE_URL`.
- If embeddings are not on your DaoXE plan, keep a separate embedding provider (for example OpenAI, Voyage, or Ollama) and set `EMBEDDING=...` accordingly.
- Raise token limits for modern long-output models when reports truncate—see [config documentation](../gptr/config).

## 3. Optional: Python OpenAI client smoke test

Before a full research run, verify the gateway:

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://daoxe.com/v1"),
)

model = os.environ["FAST_LLM"].split(":", 1)[-1]  # strip openai: prefix if present

resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Reply with the single word: pong"}],
    max_tokens=16,
)
print(resp.choices[0].message.content)
```

You can also use GPTR’s `tests/test-your-llm` helper after the env is set—see [Testing your LLM](/docs/gpt-researcher/llms/testing-your-llm).

## 4. Run a small research query

Start with a short topic and a single retriever to keep cost low, then scale concurrency and depth once the path is stable.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `401` / auth errors | API key value and `Authorization: Bearer` shape; no extra whitespace |
| `404` model not found | ID must match your account catalog exactly (including vendor prefixes) |
| Context / truncate errors | Smaller model for `FAST_LLM`; raise `SMART_TOKEN_LIMIT` / related limits |
| Slow or rate-limited runs | Lower concurrency; pick a faster model for `FAST_LLM` |
| Region / access denied | DaoXE is not available in mainland China; use a supported region |

## Multi-protocol note

This GPTR path uses **Chat Completions** only. DaoXE’s Anthropic Messages and OpenAI Responses surfaces are useful for other stacks (Claude clients, Responses-native apps). Keep protocol and model choices explicit—DaoXE is not an OpenAI-only or Claude-only gateway.

## Disclosure

This guide was contributed by a DaoXE maintainer. Sample clients: [DaoXE-AI](https://github.com/seven7763/DaoXE-AI).
