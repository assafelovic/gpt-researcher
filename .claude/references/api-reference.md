# API Reference

## Table of Contents
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [Python Client](#python-client)
- [Output Files](#output-files)

---

## REST API

Base URL: `http://localhost:8000`

### Generate Report

**POST `/report/`**

```json
{
    "task": "What are the latest AI developments?",
    "report_type": "research_report",
    "report_source": "web",
    "tone": "Objective",
    "source_urls": [],
    "query_domains": [],
    "generate_in_background": false
}
```

**Response:**

```json
{
    "report": "# Research Report\n\n...",
    "research_id": "task_1234567890_query",
    "costs": 0.05,
    "pdf_path": "outputs/task_123.pdf",
    "docx_path": "outputs/task_123.docx"
}
```

### Chat with Report

**POST `/api/chat`**

```json
{
    "report": "The full report text...",
    "messages": [
        {"role": "user", "content": "What are the key findings?"}
    ]
}
```

### Report Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports` | List all reports |
| GET | `/api/reports/{id}` | Get single report |
| POST | `/api/reports` | Create/update report |
| PUT | `/api/reports/{id}` | Update report |
| DELETE | `/api/reports/{id}` | Delete report |

### File Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/` | Upload document |
| DELETE | `/delete/{filename}` | Delete file |
| GET | `/outputs/{filename}` | Get output file |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/getConfig` | Get current config |
| POST | `/setConfig` | Update config |

---

## WebSocket API

**Endpoint:** `ws://localhost:8000/ws`

### Send Research Request

```json
{
    "task": "Research query",
    "report_type": "research_report",
    "report_source": "web",
    "tone": "Objective",
    "source_urls": [],
    "mcp_enabled": false,
    "mcp_strategy": "fast",
    "mcp_configs": []
}
```

### Message Types (Server → Client)

| Type | Content | Description |
|------|---------|-------------|
| `logs` | `starting_research` | Research initiated |
| `logs` | `planning_research` | Generating sub-queries |
| `logs` | `running_subquery_research` | Researching sub-query |
| `logs` | `research_step_finalized` | Research complete |
| `logs` | `agent_generated` | Agent role selected |
| `logs` | `scraping_urls` | Scraping web pages |
| `logs` | `mcp_optimization` | MCP processing |
| `logs` | `image_planning` | Planning images |
| `logs` | `images_ready` | Images generated |
| `report` | - | Streaming report chunks |
| `report_complete` | - | Final complete report |
| `path` | `pdf`, `docx`, `md` | Output file paths |
| `error` | - | Error messages |
| `human_feedback` | `request` | Request user input |

### Message Format

```json
{
    "type": "logs",
    "content": "starting_research",
    "output": "🔍 Starting the research task...",
    "metadata": null
}
```

### Frontend Handler Example

```typescript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'logs':
            setLogs(prev => [...prev, data]);
            break;
        case 'report':
            setAnswer(prev => prev + data.output);
            break;
        case 'report_complete':
            setAnswer(data.output);
            break;
        case 'path':
            setPaths(prev => ({...prev, [data.content]: data.output}));
            break;
        case 'error':
            setError(data.output);
            break;
    }
};
```

---

## Python Client

### Basic Usage

```python
from gpt_researcher import GPTResearcher
import asyncio

async def main():
    researcher = GPTResearcher(
        query="What are the latest AI developments?",
        report_type="research_report",
    )
    
    await researcher.conduct_research()
    report = await researcher.write_report()
    
    print(f"Report: {report}")
    print(f"Costs: ${researcher.get_costs()}")

asyncio.run(main())
```

### With MCP

```python
researcher = GPTResearcher(
    query="Research topic",
    mcp_configs=[{
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
    }],
    mcp_strategy="deep",
)
```

### With WebSocket Streaming

```python
class MockWebSocket:
    async def send_json(self, data):
        print(f"[{data['type']}] {data.get('output', '')}")

researcher = GPTResearcher(
    query="Research topic",
    websocket=MockWebSocket(),
)
```

### GPTResearcher Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Research question |
| `report_type` | str | `research_report` | Type of report |
| `report_source` | str | `web` | Data source |
| `tone` | Tone | `Objective` | Writing tone |
| `source_urls` | list | `[]` | Specific URLs to research |
| `document_urls` | list | `[]` | Document URLs |
| `query_domains` | list | `[]` | Restrict to domains |
| `config_path` | str | None | Path to JSON config |
| `websocket` | WebSocket | None | For streaming |
| `mcp_configs` | list | `[]` | MCP server configs |
| `mcp_strategy` | str | `fast` | MCP strategy |
| `verbose` | bool | `True` | Verbose output |

---

## Output Files

```
outputs/
├── task_{timestamp}_{query}.md
├── task_{timestamp}_{query}.pdf
├── task_{timestamp}_{query}.docx
└── images/
    └── {research_id}/
        └── img_{hash}_{index}.png
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Report not found |
| 429 | Rate Limited - API quota exceeded |
| 500 | Internal Server Error |
