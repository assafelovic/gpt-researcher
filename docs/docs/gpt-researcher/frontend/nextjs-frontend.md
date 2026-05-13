# NextJS-Frontend

Dieses Frontend soll die Nutzererfahrung von GPT Researcher verbessern und bietet eine intuitive, effiziente Oberfläche für automatisierte Recherche. Es gibt zwei Bereitstellungsoptionen für unterschiedliche Bedürfnisse und Umgebungen.

#### Demo
<iframe height="400" width="700" src="https://github.com/user-attachments/assets/092e9e71-7e27-475d-8c4f-9dddd28934a3" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

Ein ausführliches Produkt-Tutorial findest du hier: [GPT-Researcher Frontend Tutorial](https://www.youtube.com/watch?v=hIZqA6lPusk)

## NextJS-Frontend-App

Die React-App im Verzeichnis `frontend` ist unsere Frontend-2.0-Version. Damit wollen wir die Stärke des Backends auch im Frontend sichtbar machen.

Sie bringt viele zusätzliche Funktionen mit, zum Beispiel:
- Drag-and-Drop-Oberfläche zum Hochladen und Löschen von Dateien, die GPT Researcher als lokale Dokumente nutzen kann
- GUI zum Setzen deiner GPTR-Umgebungsvariablen
- Möglichkeit, den Multi-Agents-Flow über das Backend-Modul oder den LangGraph-Cloud-Host auszulösen
- Stabilitätsverbesserungen
- und weitere Funktionen folgen

### NextJS-React-App mit Docker starten

> **Schritt 1** - [Docker installieren](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Schritt 2** - Die `.env.example` kopieren, die API-Keys eintragen und die Datei als `.env` speichern

> **Schritt 3** - In der `docker-compose`-Datei die Services auskommentieren, die du nicht mit Docker laufen lassen möchtest

```bash
docker compose up --build
```

Wenn das nicht funktioniert, probiere es ohne Bindestrich:
```bash
docker compose up --build
```

> **Schritt 4** - Wenn du in der `docker-compose`-Datei nichts aktiviert hast, starten standardmäßig zwei Prozesse:
 - der Python-Server auf `localhost:8000`
 - die React-App auf `localhost:3000`

Öffne `localhost:3000` im Browser und lege los.

Wenn du den GPTR-API-Server nicht auf `localhost:8000` laufen lassen möchtest, kannst du die Umgebungsvariable `NEXT_PUBLIC_GPTR_API_URL` in deiner `.env`-Datei setzen.

Beispiele:
```
NEXT_PUBLIC_GPTR_API_URL=https://app.gptr.dev
```

Oder:
```
NEXT_PUBLIC_GPTR_API_URL=http://localhost:7000
```

## NextJS-Frontend per CLI starten

Eine robustere Lösung mit erweiterten Funktionen und besserer Performance.

#### Voraussetzungen
- Node.js (empfohlen: v18.17.0)
- npm

#### Einrichtung und Start

1. In das NextJS-Verzeichnis wechseln:
   ```
   cd nextjs
   ```

2. Node.js einrichten:
   ```
   nvm install 18.17.0
   nvm use v18.17.0
   ```

3. Abhängigkeiten installieren:
   ```
   npm install --legacy-peer-deps
   ```

4. Entwicklungsserver starten:
   ```
   npm run dev
   ```

5. Unter `http://localhost:3000` öffnen

Hinweis: Dafür muss der Backend-Server wie in Option 1 auf `localhost:8000` laufen.

### Google Analytics hinzufügen

Wenn du Google Analytics in dein NextJS-Frontend einbinden möchtest, füge einfach Folgendes in deine `.env`-Datei ein:

```
NEXT_PUBLIC_GA_MEASUREMENT_ID="G-G2YVXKHJNZ"
```
