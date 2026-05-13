# GPT-Researcher MCP-Integration

Dieses Verzeichnis enthält die vollständige Model Context Protocol-(MCP)-Integration für GPT Researcher. MCP ermöglicht es GPT Researcher, sich über ein standardisiertes Protokoll nahtlos mit externen Tools und Datenquellen zu verbinden und diese zu nutzen.

## 🔧 Was ist MCP?

Model Context Protocol (MCP) ist ein offener Standard, der sichere Verbindungen zwischen KI-Anwendungen und externen Datenquellen sowie Tools ermöglicht. Mit MCP kann GPT Researcher:

- **Auf lokale Daten zugreifen**: Datenbanken, Dateisysteme und lokale APIs anbinden
- **Externe Tools verwenden**: Webdienste, APIs und Tools von Drittanbietern integrieren
- **Fähigkeiten erweitern**: Eigene Funktionen über MCP-Server hinzufügen
- **Sicherheit erhalten**: Kontrollierter Zugriff mit sauberer Authentifizierung und Berechtigungskonzepten

## 📁 Modulstruktur

```text
gpt_researcher/mcp/
├── __init__.py           # Modulinitialisierung und Importe
├── client.py             # MCP-Client-Verwaltung und Konfiguration
├── tool_selector.py      # Intelligente Tool-Auswahl mithilfe eines LLM
├── research.py           # Rechercheausführung mit ausgewählten Tools
├── streaming.py          # WebSocket-Streaming und Logging-Hilfsfunktionen
└── README.md             # Diese Dokumentation
```

### Kernkomponenten

#### 🤖 `client.py` - MCPClientManager
Verwaltet MCP-Serververbindungen und den Lebenszyklus der Clients:
- Wandelt GPT-Researcher-Konfigurationen in MCP-Format um
- Verwaltet `MultiServerMCPClient`-Instanzen
- Behandelt Verbindungstypen (`stdio`, `websocket`, `HTTP`)
- Sorgt für automatisches Cleanup und Ressourcenverwaltung

#### 🧠 `tool_selector.py` - MCPToolSelector
Intelligente Tool-Auswahl mithilfe von LLM-Analyse:
- Analysiert verfügbare Tools gegen Forschungsanfragen
- Nutzt ein strategisches LLM für optimale Tool-Auswahl
- Bietet eine Fallback-Auswahl per Mustererkennung
- Begrenzt die Anzahl der ausgewählten Tools, um Overhead zu vermeiden

#### 🔍 `research.py` - MCPResearchSkill
Führt Recherche mit ausgewählten MCP-Tools aus:
- Bindet Tools an das LLM für eine intelligente Nutzung
- Verwaltet Tool-Ausführung und Fehlerbehandlung
- Bereitet Ergebnisse in ein Standardformat auf
- Inklusive LLM-Analyse neben den Tool-Ergebnissen

#### 📡 `streaming.py` - MCPStreamer
Echtzeit-Streaming und Logging:
- WebSocket-Streaming für Live-Updates
- Strukturierte Logs für Debugging
- Fortschrittsanzeige und Status-Updates
- Fehler- und Warnungsverwaltung

## 🚀 Erste Schritte

### Voraussetzungen

1. **MCP-Abhängigkeiten installieren**:
   ```bash
   pip install langchain-mcp-adapters
   ```

2. **MCP-Server einrichten**: Du benötigst mindestens einen MCP-Server, mit dem du dich verbinden kannst. Das kann sein:
   - ein lokal entwickelter Server
   - ein MCP-Server eines Drittanbieters
   - ein cloudbasierter MCP-Dienst

### Grundverwendung

#### 1. MCP in GPT Researcher konfigurieren

```python
from gpt_researcher import GPTResearcher

# MCP-Konfiguration für einen lokalen Server
mcp_configs = [{
    "command": "python",
    "args": ["my_mcp_server.py"],
    "name": "local_server",
    "tool_name": "search"  # Optional: ein bestimmtes Tool angeben
}]

# Researcher mit MCP initialisieren
researcher = GPTResearcher(
    query="What are the latest developments in AI?",
    mcp_configs=mcp_configs
)

# Recherche mit MCP-Tools durchführen
context = await researcher.conduct_research()
report = await researcher.write_report()
```

#### 2. WebSocket-/HTTP-Serverkonfiguration

```python
# WebSocket-MCP-Server
mcp_configs = [{
    "connection_url": "ws://localhost:8080/mcp",
    "connection_type": "websocket",
    "name": "websocket_server"
}]

# HTTP-MCP-Server
mcp_configs = [{
    "connection_url": "https://api.example.com/mcp",
    "connection_type": "http",
    "connection_token": "your-auth-token",
    "name": "http_server"
}]
```

#### 3. Mehrere Server

```python
mcp_configs = [
    {
        "command": "python",
        "args": ["database_server.py"],
        "name": "database",
        "env": {"DB_HOST": "localhost"}
    },
    {
        "connection_url": "ws://localhost:8080/search",
        "name": "search_service"
    },
    {
        "connection_url": "https://api.knowledge.com/mcp",
        "connection_token": "token123",
        "name": "knowledge_base"
    }
]
```

## 🔧 Konfigurationsoptionen

### MCP-Serverkonfiguration

Jede MCP-Serverkonfiguration unterstützt die folgenden Optionen:

| Feld              | Typ | Beschreibung | Beispiel |
|--------------------|------|-------------|---------|
| `name`             | `str` | Eindeutiger Name des Servers | `"my_server"` |
| `command`          | `str` | Befehl zum Starten des `stdio`-Servers | `"python"` |
| `args`             | `list[str]` | Argumente für den Befehl | `["server.py", "--port", "8080"]` |
| `connection_url`   | `str` | URL für WebSocket-/HTTP-Verbindung | `"ws://localhost:8080/mcp"` |
| `connection_type`  | `str` | Verbindungstyp | `"stdio"`, `"websocket"`, `"http"` |
| `connection_token` | `str` | Authentifizierungs-Token | `"your-token"` |
| `tool_name`        | `str` | Optional: spezifisches Tool | `"search"` |
| `env`              | `dict` | Umgebungsvariablen | `{"API_KEY": "secret"}` |

### Auto-Erkennung

Der MCP-Client erkennt Verbindungstypen automatisch:
- URLs mit `ws://` oder `wss://` → WebSocket
- URLs mit `http://` oder `https://` → HTTP
- Keine URL angegeben → `stdio` (Standard)

## 🏗️ Entwicklung

### Neue Komponenten hinzufügen

1. **Komponente erstellen** in der passenden Datei
2. **Zu `__init__.py` hinzufügen**, damit sie leicht importierbar ist
3. **Diese README aktualisieren**
4. **Tests hinzufügen** im Testverzeichnis

### Tool-Auswahl erweitern

Um die Logik der Tool-Auswahl anzupassen, erweitere `MCPToolSelector`:

```python
from gpt_researcher.mcp import MCPToolSelector

class CustomToolSelector(MCPToolSelector):
    def _fallback_tool_selection(self, all_tools, max_tools):
        # Eigene Fallback-Logik
        return super()._fallback_tool_selection(all_tools, max_tools)
```

### Eigene Ergebnisverarbeitung

Erweitere `MCPResearchSkill` für eigene Ergebnisverarbeitung:

```python
from gpt_researcher.mcp import MCPResearchSkill

class CustomResearchSkill(MCPResearchSkill):
    def _process_tool_result(self, tool_name, result):
        # Eigene Ergebnisverarbeitung
        return super()._process_tool_result(tool_name, result)
```

## 🔒 Sicherheitsaspekte

- **Token-Verwaltung**: Authentifizierungs-Token sicher speichern
- **Serverprüfung**: Nur mit vertrauenswürdigen MCP-Servern verbinden
- **Umgebungsvariablen**: Für sensible Konfiguration env-Variablen verwenden
- **Netzwerksicherheit**: Für entfernte Verbindungen HTTPS/WSS verwenden
- **Zugriffskontrolle**: Saubere Berechtigungen implementieren

## 🐛 Fehlerbehebung

### Häufige Probleme

1. **Importfehler**: `langchain-mcp-adapters not installed`
   ```bash
   pip install langchain-mcp-adapters
   ```

2. **Verbindung fehlgeschlagen**: Server-URL und Authentifizierung prüfen
   - Prüfen, ob der Server läuft
   - URL-Format prüfen
   - Authentifizierungs-Token validieren

3. **Keine Tools verfügbar**: Der Server stellt möglicherweise keine Tools bereit
   - Serverimplementierung prüfen
   - Tool-Registrierung validieren
   - Server-Logs prüfen

4. **Probleme bei der Tool-Auswahl**: Das LLM wählt möglicherweise nicht die passenden Tools
   - Tool-Beschreibungen prüfen
   - Relevanz der Anfrage prüfen
   - Eigene Auswahllogik in Betracht ziehen

### Debug-Logging

Aktiviere Debug-Logging für detaillierte Informationen:

```python
import logging
logging.getLogger('gpt_researcher.mcp').setLevel(logging.DEBUG)
```

## 📚 Ressourcen

- **MCP-Spezifikation**: [Model Context Protocol Docs](https://spec.modelcontextprotocol.io/)
- **langchain-mcp-adapters**: [GitHub Repository](https://github.com/modelcontextprotocol/langchain-mcp-adapters)
- **GPT-Researcher-Dokumentation**: [Dokumentation](https://docs.gptr.dev/)
- **Beispiel-MCP-Server**: [MCP Examples](https://github.com/modelcontextprotocol/servers)

## 🤝 Mitwirken

Beiträge zur MCP-Integration sind willkommen! Bitte:

1. **Die oben beschriebene Projektstruktur einhalten**
2. **Umfassende Tests für neue Funktionen ergänzen**
3. **Die Dokumentation einschließlich dieser README aktualisieren**
4. **Den Coding-Standards des Projekts folgen**
5. **Abwärtskompatibilität berücksichtigen**

---

*Diese MCP-Integration bringt mächtige Erweiterbarkeit zu GPT Researcher und ermöglicht Verbindungen zu nahezu jeder Datenquelle oder jedem Tool über das standardisierte MCP-Protokoll.* 🙂
