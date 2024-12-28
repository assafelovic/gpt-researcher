# Adding a toga frontend

## Integration Overview

### Phase 1: Initial Toga Setup and Basic Window

1. Create a new directory `toga_frontend/` parallel to the existing frontend
2. Create a basic Toga application structure:

```python:toga_frontend/app.py
from toga import App, MainWindow, Box, Button, TextInput, ScrollContainer
import httpx

class GPTResearcherApp(App):
    def __init__(self):
        super().__init__('GPT Researcher', 'org.gptresearcher')
        
    def startup(self):
        self.main_window = MainWindow(title=self.name)
        self.main_box = Box(style=Pack(direction=COLUMN, padding=10))
        
        # Basic query input
        self.query_input = TextInput(placeholder='Enter your research query')
        self.submit_button = Button('Research', on_press=self.handle_research)
        
        self.main_box.add(self.query_input)
        self.main_box.add(self.submit_button)
        
        self.main_window.content = self.main_box
        self.main_window.show()

    async def handle_research(self, widget):
        # Will implement in Phase 2
        pass

def main():
    return GPTResearcherApp()

if __name__ == '__main__':
    app = main()
    app.main_loop()
```

### Phase 2: API Integration Layer

Create an API client class to handle backend communication:

```python
import httpx
import asyncio

class GPTResearcherClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    async def submit_research(self, query, report_type="research_report"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/research",
                json={
                    "task": query,
                    "report_type": report_type,
                    "agent": "researcher"
                }
            )
            return response.json()
```

### Phase 3: Research Results Display

Add a results view component:

```python:toga_frontend/components/results_view.py
from toga import Box, ScrollContainer, Label, MultilineTextInput
from toga.style import Pack

class ResultsView(Box):
    def __init__(self):
        super().__init__(style=Pack(direction='column', padding=5))
        self.results_display = MultilineTextInput(
            readonly=True,
            style=Pack(flex=1)
        )
        self.add(self.results_display)
    
    def update_results(self, content):
        self.results_display.value = content
```

### Phase 4: Integration with Existing Backend

The existing FastAPI backend can remain largely unchanged([1](https://toga.readthedocs.io/en/stable/how-to/contribute/code.html)). We'll reference the existing server code:

```1:50:backend/server/server.py
import json
import os
from typing import Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.server.websocket_manager import WebSocketManager
from backend.server.server_utils import (
    get_config_dict,
    update_environment_variables, handle_file_upload, handle_file_deletion,
    execute_multi_agents, handle_websocket_communication
)


# Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SEARCHAPI_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''
    XAI_API_KEY: str


# App initialization
app = FastAPI()

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
```

### Phase 5: Configuration and Settings

Create a settings interface that matches the existing configuration:

```python:toga_frontend/components/settings.py
from toga import Box, TextInput, Button, Label
from toga.style import Pack

class SettingsView(Box):
    def __init__(self, on_save):
        super().__init__(style=Pack(direction='column', padding=5))
        self.api_key_input = TextInput(placeholder='OpenAI API Key')
        self.tavily_key_input = TextInput(placeholder='Tavily API Key')
        self.save_button = Button('Save Settings', on_press=on_save)
        
        self.add(self.api_key_input)
        self.add(self.tavily_key_input)
        self.add(self.save_button)
```

### Implementation Strategy

1. **Modular Approach**:

    - Keep the existing frontend and backend intact
    - Create the Toga UI as an alternative frontend
    - Use feature flags or command line arguments to choose which frontend to launch

2. **Minimal Changes**:

    - The FastAPI backend remains unchanged
    - Add a small bridge layer for Toga-FastAPI communication
    - Implement only core features initially

3. **Progressive Enhancement**:

    - Start with basic research functionality
    - Add advanced features (file upload, detailed reports) incrementally
    - Keep the existing web frontend as a fallback option

### Running Both Frontends

Add a launcher script:

```python:run.py
import argparse
import uvicorn
from backend.server.server import app as fastapi_app
from toga_frontend.app import main as toga_main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frontend', choices=['web', 'toga'], default='web')
    args = parser.parse_args()
    
    if args.frontend == 'toga':
        toga_main()
    else:
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()
```

This approach allows for:

1. Gradual migration to Toga UI
2. Testing both frontends in parallel
3. Minimal disruption to existing functionality
4. Easy rollback if needed

The modular structure means you can continue developing both frontends independently while sharing the same backend logic([2](https://toga.readthedocs.io/en/stable/background/project/philosophy.html)).
