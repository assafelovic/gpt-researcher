# E2E Tests für GPT Researcher

End-to-End-Tests mit Playwright für das Vanilla-JS- und Next.js-Frontend sowie die REST-API.

## Voraussetzungen

- **Node.js 18+**
- **Backend läuft:** `http://localhost:8002` (via `python backend/run_server.py`)
- **Next.js (optional):** `http://localhost:3000` (via `cd frontend/nextjs && npm run dev`)
- **GH CLI (optional):** Für automatische Issue-Erstellung bei Fehlern (`gh auth login`)

## Installation

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

## Ausführung

### Alle Tests

```bash
npm test
```

### Nur Vanilla-Frontend

```bash
npm run test:vanilla
```

### Nur Next.js-Frontend

```bash
npm run test:nextjs
```

### Nur API-Tests

```bash
npm run test:api
```

### Mit Umgebungsvariablen

```bash
# GitHub-Repo für Issues (Default: assafelovic/gpt-researcher)
GITHUB_REPO=mein-user/gpt-researcher

# GH Token für API-basierte Issue-Erstellung (alternativ zu gh CLI)
GITHUB_TOKEN=ghp_xxx

# Abweichende URLs
VANILLA_URL=http://localhost:8002
NEXTJS_URL=http://localhost:3000

npm test
```

## Teststruktur

```
tests/e2e/
├── specs/
│   ├── vanilla/          # Tests gegen das Vanilla-JS-Frontend
│   │   ├── 01-homepage.spec.ts
│   │   ├── 02-research-flow.spec.ts
│   │   └── 03-chat.spec.ts
│   ├── nextjs/           # Tests gegen das Next.js-Frontend
│   │   ├── 01-homepage.spec.ts
│   │   ├── 02-research-flow.spec.ts
│   │   └── 03-chat.spec.ts
│   └── shared/           # API-Tests (frontend-unabhängig)
│       ├── 04-file-upload.spec.ts
│       └── 05-reports-crud.spec.ts
├── pages/                # Page Object Model
├── fixtures/             # Testdaten + Helfer
├── reporters/            # GitHub Issue Reporter
├── screenshots/          # Test-Screenshots
└── playwright-report/    # HTML-Report
```

## GitHub Issues bei Fehlern

Bei fehlgeschlagenen Tests erstellt der `GitHubIssueReporter` automatisch ein Issue:

1. **Via gh CLI** (Default): `gh issue create --repo "owner/repo" ...`
2. **Via GitHub API** (Fallback mit `GITHUB_TOKEN`): Direkter REST-Call

Das Issue enthält:
- Testname, Datei, Zeile
- Fehlermeldung + Stack Trace
- Screenshot-Pfade
- Dauer des fehlgeschlagenen Tests

## Screenshots

Screenshots werden in `screenshots/{project}/{testname}/{step}.png` gespeichert.
Jeder Test-Schritt erzeugt einen Screenshot für spätere Analyse.
