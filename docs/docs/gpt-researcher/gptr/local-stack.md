# Fork-Specific Local Stack

This fork has been validated end-to-end with a local Gemma/llama.cpp server and a patched GPT Researcher backend.

The validated runtime layout is:

- LLM server: `http://127.0.0.1:8081`
- Backend API: `http://127.0.0.1:8002`
- Next.js frontend: `http://127.0.0.1:3000`
- Research artifacts: `outputs/`

## What Works

The current stack supports:

- Greeting shortcuts in chat
- Summary questions answered directly from the report
- Live search using DuckDuckGo
- Report-specific Q&A with a short LLM attempt and deterministic fallback
- Report generation to Markdown, PDF, DOCX, and JSON
- Streaming research logs and cleanup-friendly artifact files
- Verification reviews and a reasoning critic appended to generated reports
- A bounded deep-crawler that improves source discovery without uncontrolled fan-out

## Why This Fork Differs From Upstream

The local model is OpenAI-compatible, but it is slower and less reliable for long free-form synthesis than the upstream cloud setup. To keep the system usable, the fork applies a few targeted changes:

- Shorter local LLM timeouts and fewer retries
- Deterministic fallbacks for summary and report-style questions
- Live search answers that do not depend on tool-calling round trips
- Collision-resistant artifact names for concurrent runs
- A single canonical artifact directory: `outputs/`

## Relevant Code Paths

- `backend/chat/chat.py`
- `backend/server/server_utils.py`
- `backend/server/app.py`
- `gpt_researcher/utils/artifacts.py`
- `gpt_researcher/utils/logging_config.py`
- `gpt_researcher/actions/deep_crawler.py`
- `gpt_researcher/actions/reasoning_critic.py`
- `gpt_researcher/actions/verification.py`
- `gpt_researcher/scraper/browser/nodriver_scraper.py`
- `tests/test_chat_regressions.py`
- `tests/test_logs.py`
- `tests/test_deep_crawler.py`
- `tests/test_reasoning_critic.py`
- `tests/test_verification.py`

## How To Run It

Start the local model server first, then the backend, then the frontend:

```bash
/home/xxammaxx/Schreibtisch/gemma4/serve_gemma4_obliterated.sh
PORT=8002 PYTHONPATH=. .venv/bin/python backend/run_server.py
env NEXT_PUBLIC_GPTR_API_URL=http://127.0.0.1:8002 NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8002 npm run dev -- --hostname 127.0.0.1 --port 3000
```

If you are following upstream examples, replace `8000` with `8002` for this fork.

## Ollama Variant

This fork also ships an Ollama setup for the same local GGUF checkpoint.
The model name is `gemma4_obliterated`, and the repo includes the Modelfile
needed to create it:

```bash
ollama create gemma4_obliterated -f ollama/Modelfile.gemma4_obliterated
ollama run gemma4_obliterated "Reply with one short sentence confirming the model is ready."
```

For GPT Researcher, point the LLM env vars at that local model:

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434
FAST_LLM=ollama:gemma4_obliterated
SMART_LLM=ollama:gemma4_obliterated
STRATEGIC_LLM=ollama:gemma4_obliterated
EMBEDDING=ollama:nomic-embed-text
```

If you need a smaller context window on constrained hardware, start Ollama with
`OLLAMA_CONTEXT_LENGTH=2048 ollama serve`.

## Validation

The following checks were run against the live local stack:

- `pytest tests/test_chat_regressions.py`
- `pytest tests/test_logs.py`
- `pytest tests/test_logging.py`
- `pytest tests/test_logging_output.py`
- `pytest tests/test_researcher_logging.py`

## Artifact Notes

- `outputs/` is the canonical artifact directory for this fork.
- Research JSON logs, Markdown reports, PDFs, DOCX files, and screenshots are all written under `outputs/`.
- The old `logs/` path is legacy and should not be used for new research artifacts.
- Screenshot debugging now writes to `outputs/screenshots`.
