# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file with these keys)
export OPENAI_API_KEY={Your OpenAI API Key}
export TAVILY_API_KEY={Your Tavily API Key}
export LANGCHAIN_API_KEY={Your LangChain API Key}  # Optional
export DOC_PATH="./my-docs"  # For local document research

# Start the FastAPI backend server
python -m uvicorn main:app --reload  # Development with auto-reload
python main.py  # Alternative: Direct startup

# Start the Next.js frontend (optional)
cd frontend/nextjs
npm install
npm run dev
```

### Docker Commands
```bash
# Build and run all services
docker-compose up --build

# Run only backend
docker-compose up gpt-researcher

# Run tests in Docker
docker-compose run gpt-researcher-tests
```

### Testing
```bash
# Run Python tests
python -m pytest tests/

# Run specific test files
python -m pytest tests/report-types.py
python -m pytest tests/vector-store.py

# Test your retriever configuration
python tests/test-your-retriever.py

# Test your LLM configuration
python tests/test-your-llm.py
```

### Frontend Development
```bash
# Static FastAPI version (lightweight)
# Serves automatically at http://localhost:8000 when backend starts

# Next.js version (production-ready)
cd frontend/nextjs
npm run dev      # Development
npm run build    # Production build
npm run lint     # Run linter
```

## High-Level Architecture

### Core Research System (`/gpt_researcher`)
The main research agent that orchestrates the research process:

1. **Agent Initialization** (`agent.py`): 
   - `GPTResearcher` class manages the entire research lifecycle
   - Supports web research, local documents, and MCP (Model Context Protocol) sources
   - Configurable report types, tones, and output formats

2. **Research Workflow**:
   - **Query Processing**: Generates research questions and sub-queries
   - **Information Gathering**: Uses retrievers (Tavily, Google, DuckDuckGo, etc.) to find sources
   - **Web Scraping**: JavaScript-enabled scraping with browser automation
   - **Context Management**: Filters and aggregates information from multiple sources
   - **Report Generation**: Creates comprehensive reports with citations

3. **Skills Architecture** (`/skills`):
   - `ResearchConductor`: Orchestrates the research process
   - `BrowserManager`: Handles web scraping and content extraction
   - `ContextManager`: Manages research context and source validation
   - `SourceCurator`: Validates and ranks sources
   - `ReportGenerator`: Creates final reports in various formats
   - `DeepResearchSkill`: Recursive research for in-depth exploration

### Multi-Agent System (`/multi_agents`)
LangGraph-based multi-agent system for complex research tasks:

1. **Agent Roles**:
   - **ChiefEditor**: Orchestrates the entire research workflow
   - **Researcher**: Conducts deep research on topics
   - **Writer**: Drafts initial content
   - **Editor**: Reviews and improves content structure
   - **Reviewer**: Ensures quality and accuracy
   - **Reviser**: Makes final improvements
   - **Publisher**: Formats and exports final report

2. **Workflow**: Agents work together using LangGraph state management to produce publication-quality research reports (5-6 pages) in PDF, DOCX, or Markdown formats.

### Backend API (`/backend`)
FastAPI server providing REST and WebSocket endpoints:

1. **Server Structure**:
   - `server.py`: Main FastAPI application
   - `websocket_manager.py`: Handles real-time communication
   - Research endpoints: `/report`, `/research`
   - Multi-agent endpoint: `/langgraph`
   - File management: Upload/delete documents for local research

2. **Report Processing**:
   - Generates reports in multiple formats (PDF, DOCX, Markdown)
   - Streams research progress via WebSocket
   - Maintains research memory and context

### Frontend Applications (`/frontend`)

1. **Static Version** (served by FastAPI):
   - Lightweight HTML/CSS/JS interface
   - Real-time WebSocket updates
   - Basic research configuration

2. **Next.js Version** (production-ready):
   - Full-featured React application with TypeScript
   - Advanced UI with research history
   - File upload for local document research
   - Real-time progress tracking
   - Export functionality

### Key Integration Points

1. **LLM Configuration**:
   - Default: GPT-4 Turbo
   - Supports multiple providers via `litellm`
   - Configurable via environment variables
   - Custom prompts per research type

2. **Retriever System**:
   - Web search: Tavily (default), Google, DuckDuckGo, etc.
   - Local documents: PDF, DOCX, CSV, PowerPoint, etc.
   - MCP integration for specialized data sources
   - Vector store support for semantic search

3. **Output Formats**:
   - Markdown (default)
   - PDF (via md2pdf and weasyprint)
   - DOCX (via python-docx)
   - JSON for programmatic access

## Important Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for GPT models
- `TAVILY_API_KEY`: Required for web search (recommended)
- `DOC_PATH`: Path to local documents folder
- `RETRIEVER`: Comma-separated list (e.g., "tavily,mcp")
- `STRATEGIC_LLM`: Override model for multi-agent system
- `LOGGING_LEVEL`: Set to DEBUG for detailed logs

### Report Types
- `research_report`: Comprehensive research report
- `detailed_report`: In-depth analysis with more sources
- `quick_summary`: Brief overview
- `multi_agents`: Multi-agent collaborative report

### MCP Integration
GPT Researcher supports Model Context Protocol for connecting to specialized data sources:
```python
mcp_configs = [{
    "name": "github",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
}]
```

## Development Notes

1. **Code Style**: 
   - Follow existing patterns in the codebase
   - Python: PEP 8 compliance
   - TypeScript: Strict mode enabled
   - Use type hints and proper error handling

2. **Testing**:
   - Write tests for new features
   - Test with multiple LLM providers
   - Verify retriever functionality
   - Check report generation in all formats

3. **Performance**:
   - Research tasks use async/await for concurrency
   - WebSocket for real-time updates
   - Caching for repeated searches
   - Parallel source processing

4. **Error Handling**:
   - Graceful degradation for failed sources
   - Retry logic for API calls
   - User-friendly error messages
   - Comprehensive logging

End all your comments with a :-)