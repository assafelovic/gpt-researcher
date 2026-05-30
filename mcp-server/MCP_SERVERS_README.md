# MCP Servers - GPT Researcher Enhanced

This directory contains two powerful MCP (Model Context Protocol) servers built with FastMCP that extend GPT Researcher's capabilities with advanced document analysis and stakeholder management.

## 📦 Available Servers

### 1. GPT Researcher MCP Enhanced (`gpt_researcher_mcp_enhanced.py`)

An enhanced MCP server providing comprehensive research capabilities with AI-powered analysis.

**Tools Available:**
- `gpt_research` - Run GPT Researcher on topics and generate comprehensive reports
- `analyze_project_data` - Analyze JSON data with various analysis types (summary, trends, statistics, detailed)
- `analyze_documents` - Analyze files in directories with count, details, content, and metadata options
- `identify_stakeholders` - Identify and categorize project stakeholders using AI
- `generate_stakeholder_report` - Generate comprehensive stakeholder analysis reports with problems, solutions, and opportunities

**Features:**
- Multiple analysis types (summary, trends, statistics, detailed)
- AI-powered stakeholder identification
- Comprehensive report generation in multiple formats (JSON, Markdown, HTML)
- Safe file operations with path validation
- Pydantic models for input validation

### 2. Document Analysis MCP (`document_analysis_mcp.py`)

Specialized MCP server for comprehensive document processing, stakeholder analysis, funding matching, and reporting.

**Tools Available:**
- `read_file_content` - Safely read file content with encoding handling
- `search_in_files` - Search text within files with context
- `identify_stakeholders` - Identify and categorize all project stakeholders with AI
- `analyze_stakeholder_problems` - Deep analysis of stakeholder problems and challenges
- `identify_opportunities` - Identify opportunities, synergies, and benefits
- `find_matching_funding` - Match funding programs to projects using AI and web search
- `generate_comprehensive_report` - Generate full analysis reports with all components

**Features:**
- Advanced stakeholder analysis with AI
- Problem identification and solution recommendations
- Opportunity assessment (funding, partnership, market, innovation, social, economic)
- Funding program matching with Tavily web search
- Multiple report formats (Markdown, JSON, HTML, PDF)
- Safe file operations with path traversal prevention

## 🚀 Installation

### Prerequisites
- Python 3.11 or later
- API Keys:
  - `OPENAI_API_KEY` (required for AI analysis)
  - `TAVILY_API_KEY` (required for web research and funding matching)

### Setup

1. **Install Dependencies**
   ```bash
   cd mcp-server
   pip install -r mcp-requirements.txt
   ```

2. **Configure Environment Variables**
   
   Create a `.env` file in the `mcp-server` directory or set environment variables:
   
   ```bash
   # Required API Keys
   export OPENAI_API_KEY="your-openai-api-key"
   export TAVILY_API_KEY="your-tavily-api-key"
   
   # Optional Configuration
   export DOC_PATH="/path/to/your/documents"  # Default: C:/my_docs
   export OPENAI_BASE_URL="https://api.openai.com/v1"
   export STRATEGIC_LLM="gpt-4o"
   export SMART_LLM="gpt-4o"
   export FAST_LLM="gpt-3.5-turbo"
   ```

3. **Create Document Directory**
   ```bash
   mkdir -p ~/my_docs
   # Or use your custom path from DOC_PATH
   ```

## 🎯 Usage

### Running the Servers

#### GPT Researcher MCP Enhanced Server
```bash
cd mcp-server
python gpt_researcher_mcp_enhanced.py
```

#### Document Analysis MCP Server
```bash
cd mcp-server
python document_analysis_mcp.py
```

### Using with MCP Clients

Both servers implement the FastMCP protocol and can be used with any MCP-compatible client (Claude Desktop, custom clients, etc.).

Example MCP client configuration for Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gpt-researcher-enhanced": {
      "command": "python",
      "args": ["/path/to/webapp/mcp-server/gpt_researcher_mcp_enhanced.py"],
      "env": {
        "OPENAI_API_KEY": "your-key",
        "TAVILY_API_KEY": "your-key",
        "DOC_PATH": "/path/to/documents"
      }
    },
    "document-analysis": {
      "command": "python",
      "args": ["/path/to/webapp/mcp-server/document_analysis_mcp.py"],
      "env": {
        "OPENAI_API_KEY": "your-key",
        "TAVILY_API_KEY": "your-key",
        "DOC_PATH": "/path/to/documents"
      }
    }
  }
}
```

## 📚 Tool Examples

### GPT Researcher MCP Enhanced

#### 1. Conduct Research
```python
# Tool: gpt_research
params = {
    "topic": "AI in healthcare 2024",
    "pages": 5
}
# Returns comprehensive research report
```

#### 2. Analyze Data
```python
# Tool: analyze_project_data
params = {
    "data": '{"revenue": [100, 120, 150], "costs": [80, 90, 100]}',
    "analysis_type": "statistics",
    "response_format": "markdown"
}
```

#### 3. Identify Stakeholders
```python
# Tool: identify_stakeholders
params = {
    "file_pattern": "*.txt",
    "max_files": 20,
    "use_ai_analysis": true,
    "categories": ["primary", "secondary", "indirect"]
}
```

### Document Analysis MCP

#### 1. Search in Files
```python
# Tool: search_in_files
params = {
    "search_text": "funding opportunities",
    "file_pattern": "*.txt",
    "case_sensitive": false,
    "max_results": 10
}
```

#### 2. Analyze Stakeholder Problems
```python
# Tool: analyze_stakeholder_problems
params = {
    "file_pattern": "*.txt",
    "stakeholders": ["Community", "Government", "NGOs"],
    "use_ai_analysis": true
}
```

#### 3. Find Matching Funding
```python
# Tool: find_matching_funding
params = {
    "funding_websites": [
        "https://grants.gov",
        "https://ec.europa.eu/funding"
    ],
    "project_files_pattern": "*.txt",
    "top_matches": 5
}
```

#### 4. Generate Comprehensive Report
```python
# Tool: generate_comprehensive_report
params = {
    "title": "Project Stakeholder Analysis",
    "file_pattern": "*.txt",
    "include_problems": true,
    "include_solutions": true,
    "include_opportunities": true,
    "format": "markdown",
    "report_type": "detailed"
}
```

## 🔧 Configuration Options

### Analysis Types
- **Summary**: Quick overview and key metrics
- **Trends**: Pattern identification with AI
- **Statistics**: Statistical analysis of numeric data
- **Detailed**: Comprehensive deep analysis

### File Analysis Types
- **Count**: Basic file count and statistics
- **Details**: Detailed file information (size, modified date, etc.)
- **Content**: Extract and preview file content
- **Metadata**: File metadata analysis

### Response Formats
- **JSON**: Structured data format
- **Markdown**: Formatted markdown text
- **HTML**: Styled HTML reports
- **Text**: Plain text output

### Opportunity Types
- **Funding**: Grants, investments, revenue streams
- **Partnership**: Collaborations and alliances
- **Market**: New markets and customer segments
- **Innovation**: New solutions and improvements
- **Social**: Community benefits and impact
- **Economic**: Cost savings and efficiency

### Report Types
- **Summary**: Concise key points
- **Detailed**: Comprehensive analysis
- **Executive**: Strategic insights for leadership
- **Technical**: Implementation details

## 🛡️ Security Features

Both servers implement robust security measures:
- Path traversal prevention
- Input validation with Pydantic models
- Binary file detection
- Safe file size limits
- Encoding error handling
- API key protection
- Rate limiting consideration

## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set" Error**
   - Ensure your `.env` file contains `OPENAI_API_KEY=your-key`
   - Or export the environment variable before running the server

2. **"DOC_PATH does not exist" Warning**
   - Create the directory: `mkdir -p ~/my_docs`
   - Or set `DOC_PATH` to an existing directory

3. **"TAVILY_API_KEY required" Error**
   - Required for web research and funding matching
   - Get a free API key at https://tavily.com

4. **"Failed to get AI analysis" Error**
   - Check your OpenAI API key is valid
   - Verify you have sufficient API credits
   - Check network connectivity

5. **Import Errors**
   - Install all requirements: `pip install -r mcp-requirements.txt`
   - Verify Python version: `python --version` (must be 3.11+)

### Debug Mode

Run servers with verbose output:
```bash
python gpt_researcher_mcp_enhanced.py --debug
```

## 📊 Performance Considerations

- **File Operations**: Limited to configured max files (default: 20)
- **Content Size**: File content limited to prevent memory issues
- **API Calls**: Async operations for better performance
- **Timeout**: Default 30-60 seconds for API calls
- **Caching**: Consider implementing caching for repeated queries

## 🔄 Updates and Maintenance

Keep your servers up to date:
```bash
# Update dependencies
pip install --upgrade -r mcp-requirements.txt

# Update GPT Researcher
pip install --upgrade gpt-researcher
```

## 📝 Best Practices

1. **API Key Management**: Use environment variables, never hardcode keys
2. **File Organization**: Keep project documents organized in DOC_PATH
3. **Resource Limits**: Adjust max_files and max_chars based on your needs
4. **Error Handling**: Always check response status field
5. **Format Selection**: Choose appropriate response format for your use case
6. **Backup**: Regularly backup analysis results

## 🤝 Contributing

To contribute improvements to these MCP servers:
1. Test your changes thoroughly
2. Update documentation
3. Follow existing code style (Pydantic models, type hints)
4. Add appropriate error handling
5. Submit pull request to main repository

## 📄 License

These MCP servers are part of the GPT Researcher project and follow the same license terms.

## 🌐 Resources

- **GPT Researcher**: https://gptr.dev
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **MCP Protocol**: https://modelcontextprotocol.io
- **Tavily API**: https://tavily.com
- **OpenAI API**: https://platform.openai.com

## 💬 Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/assafelovic/gpt-researcher/issues
- Discord: https://discord.gg/QgZXvJAccX
- Email: assaf.elovic@gmail.com

---

**Built with ❤️ using FastMCP and GPT Researcher**
