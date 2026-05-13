# Fork-spezifischer lokaler Stack

Dieser Fork wurde Ende-zu-Ende mit einem lokalen Gemma/llama.cpp-Server und einem angepassten GPT-Researcher-Backend validiert.

Das validierte Laufzeit-Setup ist:

- LLM server: `http://127.0.0.1:8081`
- Backend API: `http://127.0.0.1:8002`
- Next.js frontend: `http://127.0.0.1:3000`
- Research artifacts: `outputs/`

## Was funktioniert

Der aktuelle Stack unterstützt:

- Greeting shortcuts in chat
- Summary questions answered directly from the report
- Live search using DuckDuckGo
- Report-specific Q&A with a short LLM attempt and deterministic fallback
- Report generation to Markdown, PDF, DOCX, and JSON
- Streaming research logs and cleanup-friendly artifact files
- Verification reviews and a reasoning critic appended to generated reports
- A bounded deep-crawler that improves source discovery without uncontrolled fan-out

## Warum sich dieser Fork vom Upstream unterscheidet

Das lokale Modell ist OpenAI-kompatibel, aber für lange freie Synthesen langsamer und weniger zuverlässig als das Cloud-Setup des Upstreams. Damit das System brauchbar bleibt, wendet der Fork einige gezielte Änderungen an:

- Kürzere Timeouts und weniger Wiederholungen für lokale LLMs
- Deterministische Fallbacks für Zusammenfassungs- und Report-Fragen
- Live-Suchantworten, die nicht von Tool-Calling-Roundtrips abhängen
- Kollisionssichere Artefaktnamen für parallele Läufe
- Ein einziges kanonisches Artefaktverzeichnis: `outputs/`

## Relevante Code-Pfade

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

## So startest du es

Start the local model server first, then the backend, then the frontend:

```bash
/home/xxammaxx/Schreibtisch/gemma4/serve_gemma4_obliterated.sh
PORT=8002 PYTHONPATH=. .venv/bin/python backend/run_server.py
env NEXT_PUBLIC_GPTR_API_URL=http://127.0.0.1:8002 NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8002 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Wenn du Upstream-Beispiele verwendest, ersetze für diesen Fork `8000` durch `8002`.

## Ollama-Variante

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

Wenn du auf eingeschränkter Hardware ein kleineres Kontextfenster brauchst, starte Ollama mit
`OLLAMA_CONTEXT_LENGTH=2048 ollama serve`.

## Validierung

Die folgenden Prüfungen wurden gegen den laufenden lokalen Stack ausgeführt:

- `pytest tests/test_chat_regressions.py`
- `pytest tests/test_logs.py`
- `pytest tests/test_logging.py`
- `pytest tests/test_logging_output.py`
- `pytest tests/test_researcher_logging.py`

## Artefakthinweise

- `outputs/` ist das kanonische Artefaktverzeichnis dieses Forks.
- Research-JSON-Logs, Markdown-Reports, PDFs, DOCX-Dateien und Screenshots werden alle unter `outputs/` geschrieben.
- Der alte Pfad `logs/` ist Legacy und sollte für neue Research-Artefakte nicht mehr verwendet werden.
- Das Screenshot-Debugging schreibt jetzt nach `outputs/screenshots`.
