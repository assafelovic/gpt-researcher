# GPT-Researcher Leitfaden für die lokale Serverbereitstellung

## Inhaltsverzeichnis

1. [Architekturübersicht](#architekturübersicht)
2. [Hardware-Anforderungen](#hardware-anforderungen)
3. [Bereitstellungsoptionen](#bereitstellungsoptionen)
4. [Umgebungsdetails](#umgebungsdetails)
5. [API-Keys und Kosten](#api-keys-und-kosten)
6. [Sicherheit](#sicherheit)
7. [Monitoring und Betrieb](#monitoring-und-betrieb)
8. [Skalierung und Optimierung](#skalierung-und-optimierung)
9. [Fehlerbehebung](#fehlerbehebung)

---

## Architekturübersicht

### Systemkomponenten

```text
┌─────────────────────────────────────────────────────────────┐
│                    Nutzerebene                               │
│                  (Browser / API)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                       │
│                (Port 3000 - einheitlicher Einstieg)         │
│   ┌─────────────────┬──────────────────┬─────────────────┐  │
│   │  /ws, /outputs   │  /reports        │  andere Pfade   │  │
│   │  → Backend       │  → Backend       │  → Frontend     │  │
│   └─────────────────┴──────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│    FastAPI-Backend      │     │    Next.js-Frontend    │
│    (Port 8000)          │     │    (intern Port 3001)  │
│                         │     │                         │
│  • WebSocket-Kommunikation │   │  • Benutzeroberfläche  │
│  • Bearbeitung von Tasks   │   │  • Berichtsanzeige     │
│  • Berichtserzeugung       │   │  • Interaktive Steuerung│
└─────────────────────────┘     └─────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Externe Abhängigkeiten                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  LLM API     │  │  Such-API    │  │  Scraper     │       │
│  │  (OpenAI/    │  │  (Tavily/    │  │  (Selenium/  │       │
│  │   Ollama)    │  │   DuckDuckGo)│  │   Playwright)│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Vom Projekt bereitgestellte Docker-Images

| Image | Zweck | Port |
|------|------|------|
| `gptresearcher/gpt-researcher` | Backend-API | 8000 |
| `gptresearcher/gptr-nextjs` | Frontend-Weboberfläche | 3000 |
| `Dockerfile.fullstack` | Vollständiger Stack in einem Container | 3000, 8000 |

---

## Hardware-Anforderungen

### Mindestkonfiguration

| Komponente | Empfehlung | Hinweis |
|------|------|------|
| CPU | 2 Kerne | Basisverarbeitung |
| RAM | 4 GB | Python + Node.js |
| Speicher | 20 GB SSD | System, Images, Logs |
| Netzwerk | 10 Mbps | Zugriff auf externe APIs |

### Empfehlung für Produktion

| Komponente | Empfehlung | Hinweis |
|------|------|------|
| CPU | 4-8 Kerne | Parallele Rechercheaufgaben |
| RAM | 8-16 GB | Größere Dokumente und Scraping |
| Speicher | 100 GB SSD | Berichte, Logs, lokale Dokumente |
| Netzwerk | 100 Mbps+ | Schneller Webzugriff |

### Für lokale LLMs

Wenn Ollama oder andere lokale Modelle genutzt werden:

| Komponente | Empfehlung | Hinweis |
|------|------|------|
| CPU | 8+ Kerne | Schnellere Inferenz |
| RAM | 32 GB+ | Große Modelle laden |
| GPU | NVIDIA RTX 3090/4090 oder A100 | 24 GB+ VRAM |
| Speicher | 500 GB NVMe SSD | Modelle und Daten |

### Grobe Speicherabschätzung

```text
Basisdienste:
├── Python FastAPI Backend:  ~500 MB - 1 GB
├── Node.js Frontend:        ~200 MB - 500 MB
├── Nginx:                   ~50 MB
├── Chromium (Scraping):     ~200 MB - 1 GB pro Instanz
└── System-Overhead:         ~500 MB

Einzelne Research-Tasks:
├── Normale Recherche:       ~500 MB zusätzlich
├── Detaillierte Recherche:   ~1 GB zusätzlich
└── Deep Research:            ~2-4 GB zusätzlich

Lokales LLM (optional):
├── Llama 3 8B:              ~8 GB VRAM
├── Llama 3 70B:             ~40 GB VRAM (mit Quantisierung)
└── Qwen 7B:                 ~7 GB VRAM
```

---

## Bereitstellungsoptionen

### Option A: Docker Compose (empfohlen)

Die einfachste Bereitstellungsform für die meisten Szenarien.

#### Schritt 1: Umgebung vorbereiten

```bash
# Docker installieren
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose installieren
sudo apt-get install docker-compose-plugin
```

#### Schritt 2: Projekt klonen

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

#### Schritt 3: Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
nano .env
```

Beispiel für `.env`:

```bash
# Erforderliche API-Keys
OPENAI_API_KEY=sk-your-openai-key
TAVILY_API_KEY=tvly-your-tavily-key

# Optional: anderer LLM-Anbieter
# OPENAI_BASE_URL=https://api.openai.com/v1

# Lokaler Dokumentpfad
DOC_PATH=./my-docs

# Frontend-API-URL (je nach Server-IP anpassen)
NEXT_PUBLIC_GPTR_API_URL=http://your-server-ip:8000
```

#### Schritt 4: Dienste starten

```bash
# Alle Dienste bauen und starten
docker compose up -d

# Logs ansehen
docker compose logs -f
```

#### Schritt 5: Deployment prüfen

```bash
# Status prüfen
docker compose ps

# Backend testen
curl http://localhost:8000/

# Frontend im Browser öffnen
# http://your-server-ip:3000
```

---

### Option B: Fullstack-Ein-Container-Deployment

Mit `Dockerfile.fullstack` laufen alle Dienste in einem Container.

```bash
# Image bauen
docker build -f Dockerfile.fullstack -t gpt-researcher-fullstack .

# Container starten
docker run -d \
  --name gpt-researcher \
  -p 3000:3000 \
  -p 8000:8000 \
  -v $(pwd)/my-docs:/usr/src/app/my-docs \
  -v $(pwd)/outputs:/usr/src/app/outputs \
  -e OPENAI_API_KEY=sk-your-key \
  -e TAVILY_API_KEY=tvly-your-key \
  gpt-researcher-fullstack
```

Vorteile:
- Einfache Verwaltung mit einem Container
- Nginx Reverse Proxy inklusive
- Gut für einfache Deployments

Nachteile:
- Komponenten lassen sich nicht separat skalieren
- Debugging ist etwas schwieriger

---

### Option C: Natives Deployment ohne Docker

Geeignet für stark angepasste Umgebungen oder spezielle Setups.

#### Systemabhängigkeiten

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  python3.12 python3.12-venv python3-pip \
  nodejs npm \
  chromium-browser chromium-chromedriver \
  firefox-esr
```

---

## Umgebungsdetails

- `DOC_PATH` verweist auf lokale Dokumente
- `OPENAI_BASE_URL` kann für OpenAI-kompatible lokale Modelle gesetzt werden
- `RETRIEVER=duckduckgo,mcp` aktiviert hybride Web- und MCP-Recherche
- `NEXT_PUBLIC_GPTR_API_URL` muss auf den verwendeten Backend-Port zeigen

---

## API-Keys und Kosten

- OpenAI oder ein kompatibler LLM-Anbieter wird für die Berichtserzeugung benötigt
- Tavily ist optional; der Standard für Websuche kann auch DuckDuckGo sein
- Kosten hängen stark von Suchvolumen, Modell und Deep-Research-Tiefe ab

---

## Sicherheit

- API-Keys nur in sicheren `.env`-Dateien oder Secret-Systemen speichern
- Backend und Frontend nur über vertrauenswürdige Netzwerke exponieren
- Bei MCP- und lokalen Quellen nur vertrauenswürdige Server verbinden

---

## Monitoring und Betrieb

- Container-Logs regelmäßig prüfen
- `outputs/` für Berichte und Artefakte beobachten
- WebSocket- und Backend-Fehler getrennt loggen
- Für lokale LLMs Speicher- und GPU-Auslastung überwachen

---

## Skalierung und Optimierung

- Mehr Worker nur dann aktivieren, wenn CPU/RAM es zulassen
- Deep Research und Browser-Scraping sind die teuersten Pfade
- Für hohe Last sind getrennte Services für Backend, Frontend und Scraper sinnvoll

---

## Fehlerbehebung

- Backend antwortet nicht: Port, Container-Status und Logs prüfen
- Frontend lädt nicht: `NEXT_PUBLIC_GPTR_API_URL` prüfen
- LLM-Fehler: API-Key, `OPENAI_BASE_URL` und Modellverfügbarkeit prüfen
- Scraper-Probleme: Browser-Abhängigkeiten und Netzwerkzugriff prüfen

---

## Weiteres Vorgehen

1. Kleine Umgebung zuerst mit Docker Compose testen
2. Lokale Dokumente und MCP-Quellen schrittweise hinzufügen
3. Danach Last, Logs und Kosten optimieren
