# Erste Schritte

> **Schritt 0** - Installiere Python 3.11 oder neuer. Eine Schritt-für-Schritt-Anleitung findest du [hier](https://www.tutorialsteacher.com/python/install-python).

> **Schritt 1** - Lade das Projekt herunter und wechsle in das Verzeichnis

```bash
$ git clone https://github.com/assafelovic/gpt-researcher.git
$ cd gpt-researcher
```

> **Schritt 3** - Richte die API-Keys auf zwei Arten ein: direkt als Umgebungsvariablen oder über eine `.env`-Datei.

Für Linux oder eine temporäre Windows-Einrichtung nutze die Export-Variante:

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
# Optional: Web-Retriever konfigurieren, wenn du den DuckDuckGo-Standard überschreiben möchtest.
# export TAVILY_API_KEY={Your Tavily API Key here}
```

Für eigene OpenAI-kompatible APIs, zum Beispiel lokale Modelle oder andere Provider, kannst du außerdem setzen:

```bash
export OPENAI_BASE_URL={Your custom API base URL here}
```

Für eine dauerhafte Einrichtung lege im aktuellen `gpt-researcher`-Verzeichnis eine `.env`-Datei an und trage die Variablen dort ohne `export` ein.

- Als LLM-Provider empfehlen wir **[OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**, du kannst aber jedes andere LLM-Modell verwenden, auch Open Source. Wie du das LLM wechselst, erfährst du auf der [Dokumentationsseite](https://docs.gptr.dev/docs/gpt-researcher/llms).
- Für die Websuche ist DuckDuckGo der Standard, wenn kein Retriever-API-Key gesetzt ist. Wenn du Tavily oder einen anderen Provider nutzen möchtest, ändere den Suchanbieter in `config/config.py` und setze den passenden API-Key.

## Schnellstart

> **Schritt 1** - Abhängigkeiten installieren

```bash
$ pip install -r requirements.txt
```

> **Schritt 2** - Den Agenten mit FastAPI starten

```bash
$ uvicorn main:app --reload
```

> **Schritt 3** - Öffne http://localhost:8000 in deinem Browser und leg los!

## Using Virtual Environment or Poetry
Wähle je nach Vorliebe entweder Virtual Environment oder Poetry:

### Virtual Environment

#### *Virtuelle Umgebung mit Aktivieren/Deaktivieren einrichten*

Erstelle mit dem `venv`-Paket eine virtuelle Umgebung mit dem Namen `<your_name>`, zum Beispiel `env`. Führe dazu im PowerShell- oder CMD-Terminal folgenden Befehl aus:

```bash
python -m venv env
```

Zum Aktivieren der virtuellen Umgebung nutze im PowerShell- oder CMD-Terminal das folgende Skript:

```bash
.\env\Scripts\activate
```

Zum Deaktivieren der virtuellen Umgebung führe das folgende Skript aus:

```bash
deactivate
```

#### *Abhängigkeiten für eine virtuelle Umgebung installieren*

Nachdem du die `env`-Umgebung aktiviert hast, installiere die Abhängigkeiten mit folgendem Befehl:

```bash
python -m pip install -r requirements.txt
```

<br />

### Poetry

#### *Poetry-Abhängigkeiten und virtuelle Umgebung mit Poetry-Version `~1.7.1` einrichten*

Installiere die Projektabhängigkeiten und erstelle gleichzeitig eine virtuelle Umgebung für das Projekt. Poetry liest dabei die `pyproject.toml`, bestimmt die benötigten Abhängigkeiten und deren Versionen und sorgt so für eine konsistente, isolierte Entwicklungsumgebung. Die virtuelle Umgebung trennt projektspezifische Pakete sauber von systemweiten Paketen und erleichtert das Abhängigkeitsmanagement über den gesamten Projektlebenszyklus.

```bash
poetry install
```

#### *Die mit dem Poetry-Projekt verknüpfte virtuelle Umgebung aktivieren*

Mit diesem Befehl öffnest du eine Shell-Sitzung innerhalb der isolierten Projektumgebung. Dadurch erhältst du einen eigenen Arbeitsbereich für Entwicklung und Ausführung. Die virtuelle Umgebung kapselt die Projektabhängigkeiten ab und verhindert Konflikte mit systemweiten Paketen. Das Aktivieren der Poetry-Shell ist wichtig, damit die richtigen Abhängigkeitsversionen verwendet werden und du in einer kontrollierten Umgebung entwickeln und testen kannst.

```bash
poetry shell
```

### *Die Anwendung starten*
> Starte die FastAPI-Anwendung in einer *Virtual-Environment- oder Poetry*-Einrichtung mit folgendem Befehl:
```bash
python -m uvicorn main:app --reload
```
> Öffne http://localhost:8000 in deinem Browser und erkunde deine Recherchen!

<br />
