# Docker: Schnellstart

> **Schritt 1** - Docker Desktop installieren und öffnen

Folge den Anweisungen unter https://www.docker.com/products/docker-desktop/


> **Schritt 2** - [Diesem Ablauf folgen](https://www.youtube.com/watch?v=x1gKFt_6Us4)

Dabei geht es vor allem darum, die Datei `.env.example` zu kopieren, deine API-Keys in die Kopie einzutragen und die Datei anschließend als `.env` zu speichern.

In `requirements.txt` musst du die passenden LangChain-Pakete für das von dir gewählte LLM ergänzen, zum Beispiel `langchain-google-genai`, `langchain-deepseek` oder `langchain_mistralai`.

> **Schritt 3** - Im Projektstamm mit Docker starten.

```bash
docker-compose up --build
```

Wenn das nicht funktioniert, versuche es ohne Bindestrich:
```bash
docker compose up --build
```

> **Schritt 4** - Wenn du in deiner `docker-compose`-Datei nichts auskommentiert hast, startet dieser Ablauf standardmäßig zwei Prozesse:
 - der Python-Server auf `localhost:8000`
 - die React-App auf `localhost:3000`

Öffne `localhost:3000` in deinem Browser und leg direkt mit der Recherche los!


## Running with the Docker CLI

Wenn du den Docker-Container ohne `docker-compose` starten möchtest, kannst du folgenden Befehl verwenden:

```bash
docker run -it --name gpt-researcher -p 8000:8000 --env-file .env  -v /absolute/path/to/gptr_docs:/my-docs  gpt-researcher
```

Dadurch wird der Docker-Container gestartet und das Verzeichnis `/gptr_docs` auf das Verzeichnis `/my-docs` im Container gemountet, damit der GPTR-API-Server es analysieren kann.
