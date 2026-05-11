# Frontend-Anwendung

Dieses Frontend-Projekt soll die Benutzererfahrung von GPT Researcher verbessern und eine intuitive, effiziente Oberfläche für automatisierte Recherche bieten. Es gibt zwei Bereitstellungsoptionen, damit unterschiedliche Anforderungen und Umgebungen abgedeckt sind.

## Option 1: Statisches Frontend (FastAPI)

Eine leichte Lösung, bei der FastAPI statische Dateien ausliefert.

#### Voraussetzungen
- Python 3.11+
- pip

#### Einrichtung und Start

1. Erforderliche Pakete installieren:
   ```
   pip install -r requirements.txt
   ```

2. Server starten:
   ```
   python -m uvicorn main:app
   ```

3. Auf `http://localhost:8000` zugreifen

#### Demo
https://github.com/assafelovic/gpt-researcher/assets/13554167/dd6cf08f-b31e-40c6-9907-1915f52a7110

## Option 2: NextJS-Frontend

Eine robustere Lösung mit erweiterten Funktionen und besserer Performance.

#### Voraussetzungen
- Node.js (empfohlen: v18.17.0)
- npm

#### Einrichtung und Start

1. Ins NextJS-Verzeichnis wechseln:
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

5. Auf `http://localhost:3000` zugreifen

Hinweis: Dafür wird ein Backend-Server auf `localhost:8002` benötigt, wie in Option 1 beschrieben.

#### Demo
https://github.com/user-attachments/assets/092e9e71-7e27-475d-8c4f-9dddd28934a3

## Wie wähle ich die Option?

- Statisches Frontend: Schnelle Einrichtung, leichtgewichtiges Deployment.
- NextJS-Frontend: Funktionsreicher, skalierbarer, bessere Performance und SEO.

Für die Produktion wird NextJS empfohlen.

## Frontend-Funktionen

Unser Frontend verbessert GPT Researcher durch:

1. Eine intuitive Forschungsoberfläche: Straffes Eingabefeld für Suchanfragen.
2. Fortschrittsanzeige in Echtzeit: Visuelles Feedback für laufende Aufgaben.
3. Interaktive Ergebnisdarstellung: Leicht navigierbare Präsentation der Ergebnisse.
4. Anpassbare Einstellungen: Passe Rechercheparameter an deine Anforderungen an.
5. Responsives Design: Optimales Erlebnis auf verschiedenen Geräten.

Diese Funktionen sollen den Forschungsprozess effizienter und benutzerfreundlicher machen und die leistungsstarken Agentenfähigkeiten von GPT Researcher ergänzen.
