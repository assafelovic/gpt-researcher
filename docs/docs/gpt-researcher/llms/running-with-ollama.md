# Mit Ollama ausführen

Ollama erlaubt dir, ein lokales GGUF in ein benanntes Modell zu verwandeln und auf deiner eigenen Hardware bereitzustellen. Für dieses Repository ist das empfohlene lokale Modell `gemma4_obliterated`, das auf diesem GGUF basiert:

```text
/home/xxammaxx/Schreibtisch/gemma4/llama.cpp/models/gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf
```

## Das lokale Modell anlegen

Das Repo enthält eine fertige Modelfile:

```bash
ollama create gemma4_obliterated -f ollama/Modelfile.gemma4_obliterated
```

Für einen kurzen Smoke-Test nach dem Erstellen:

```bash
ollama run gemma4_obliterated "Antworte mit einem kurzen Satz und bestätige, dass das Modell bereit ist."
```

Wenn Ollama über zu wenig Arbeitsspeicher klagt, stoppe den großen `llama-server` auf Port `8081` und versuche es erneut. Auf dieser Maschine war das der Hauptkonkurrent während des Setups.

Mit diesem Befehl prüfst du, wie Ollama das Modell plant:

```bash
ollama ps
```

Unter Linux lassen sich Ollama-Server-Overrides mit `OLLAMA_CONTEXT_LENGTH=8192 ollama serve` setzen.
Auf der GTX-1070-/8-GB-VRAM-Maschine solltest du mit einem kleineren Kontextfenster starten:

```bash
OLLAMA_CONTEXT_LENGTH=2048 ollama serve
```

Wenn du den Modell-Cache an einem eigenen Ort ablegen möchtest, setze vor dem Start `OLLAMA_MODELS`:

```bash
OLLAMA_MODELS="$PWD/.ollama" ollama serve
```

## `gemma4_obliterated` mit GPT Researcher abfragen

GPT Researcher kann direkt mit dem lokalen Ollama-Server sprechen. Der Code verwendet standardmäßig `http://127.0.0.1:11434`, wenn `OLLAMA_BASE_URL` nicht gesetzt ist. Ein explizites Setzen hält das Setup jedoch verständlicher:

```bash
OLLAMA_BASE_URL="http://127.0.0.1:11434"
FAST_LLM="ollama:gemma4_obliterated"
SMART_LLM="ollama:gemma4_obliterated"
STRATEGIC_LLM="ollama:gemma4_obliterated"
EMBEDDING="ollama:nomic-embed-text"
```

Wenn du den gesamten Stack lokal halten möchtest, lasse `OLLAMA_BASE_URL` auf deine lokale Ollama-Instanz zeigen und nutze optional wie oben gezeigt auch Ollama-Embeddings.

## Historischer WebUI-Flow

Wenn du Ollama zusammen mit Open WebUI bereitstellst, kannst du Modelle weiterhin über die WebUI ziehen und sie über GPT Researcher abfragen. Dieser Flow bleibt unverändert; der Unterschied hier ist, dass das Repo jetzt einen direkten GGUF-Import für `gemma4_obliterated` mitbringt. Du musst dich für dieses Setup also nicht auf die öffentliche Ollama-Bibliothek verlassen.

## Ollama auf Elestio bereitstellen

Elestio ist eine Plattform zum Bereitstellen und Verwalten eigener Sprachmodelle. Diese Anleitung zeigt dir, wie du ein benutzerdefiniertes Modell auf Elestio deployen kannst.

Du kannst einen [Open WebUI](https://github.com/open-webui/open-webui/tree/main)-Server mit [Elestio](https://elest.io/open-source/ollama) bereitstellen.

## LLM-Testskript für GPTR ausführen

Du kannst die globale Funktion `test-your-llm` mit `tests/test-your-llm` verwenden. So geht's:

Schritt 1: Setze die folgenden Werte in deiner `.env`. Hinweis: Ersetze die Base-URLs durch die benutzerdefinierte Domain, unter der deine Web-App erreichbar ist. Wenn die App zum Beispiel unter `https://ollama-2d52b-u21899.vm.elestio.app/` erreichbar ist, verwende diese Adresse in deiner `.env`.

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

Hinweis: Um zu prüfen, ob du auf die richtige API-URL zeigst, kannst du im Terminal zum Beispiel Folgendes ausführen:

```bash
nslookup ollama-2d52b-u21899.vm.elestio.app
```

Schritt 2:

```bash
cd tests
python -m test-your-llm
```

Du solltest eine LLM-Antwort erhalten, zum Beispiel:
```
Hallo! Wie kann ich dir heute helfen? Wenn du Fragen hast oder Unterstützung brauchst, melde dich einfach.
```

#### Elestio-Authentifizierung deaktivieren oder Auth-Header hinzufügen

Um die Basic-Auth zu entfernen, gehe so vor:

Öffne in deinem Elestio-Admin-Panel deinen Service und gehe zu **Security**.

Schritt 1: Deaktiviere die Firewall.

Schritt 2: Bearbeite deine Nginx-Konfiguration. Kommentiere diese beiden Zeilen aus:

```bash
auth_basic           "Authentication"; 
auth_basic_user_file /etc/nginx/conf.d/.htpasswd;
```

Schritt 2: Klicke auf **Update & Restart**, um die Nginx-Änderungen zu übernehmen.
