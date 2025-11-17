# MCP Servers Directory - File Index

## 📂 Directory Structure

```
mcp-server/
├── README.md                           # Original GPT Researcher MCP documentation
├── MCP_SERVERS_README.md               # Comprehensive guide for both servers
├── SETUP_GUIDE.md                      # Quick setup instructions
├── INDEX.md                            # This file - directory overview
├── .env.example                        # Environment configuration template
├── mcp-requirements.txt                # Python dependencies
├── gpt_researcher_mcp_enhanced.py      # GPT Researcher MCP Enhanced Server
├── document_analysis_mcp.py            # Document Analysis MCP Server
├── run_servers.sh                      # Server launcher script
└── test_servers.py                     # Environment and setup test script
```

## 📄 File Descriptions

### Documentation Files

**README.md**
- Original GPT Researcher MCP Server documentation
- Links to official gptr-mcp repository
- Basic installation and usage instructions

**MCP_SERVERS_README.md** ⭐ Main Documentation
- Comprehensive guide for both MCP servers
- Tool descriptions and examples
- Configuration options
- Security features
- Troubleshooting guide
- Best practices

**SETUP_GUIDE.md** 🚀 Quick Start
- 5-minute setup instructions
- API key acquisition guide
- Step-by-step configuration
- Common troubleshooting
- Testing procedures

**INDEX.md** (This file)
- Directory structure overview
- File descriptions
- Quick reference guide

### Configuration Files

**.env.example**
- Environment variable template
- API key placeholders
- Configuration options with descriptions
- Copy to `.env` and customize

**mcp-requirements.txt**
- Python package dependencies
- Core requirements (mcp, fastmcp, httpx, pydantic)
- Optional packages (gpt-researcher, document processing, web crawling)
- Install with: `pip install -r mcp-requirements.txt`

### Server Files

**gpt_researcher_mcp_enhanced.py** (32KB)
- Enhanced GPT Researcher MCP server
- 5 specialized tools:
  - `gpt_research` - Comprehensive research reports
  - `analyze_project_data` - JSON data analysis
  - `analyze_documents` - File analysis in directories
  - `identify_stakeholders` - AI-powered stakeholder identification
  - `generate_stakeholder_report` - Comprehensive reporting
- Built with FastMCP
- Pydantic validation
- Multiple output formats

**document_analysis_mcp.py** (49KB)
- Specialized document processing server
- 7 advanced tools:
  - `read_file_content` - Safe file reading
  - `search_in_files` - Text search with context
  - `identify_stakeholders` - Stakeholder mapping
  - `analyze_stakeholder_problems` - Problem identification
  - `identify_opportunities` - Opportunity assessment
  - `find_matching_funding` - AI-powered funding matching
  - `generate_comprehensive_report` - Full analysis reports
- Tavily integration for web research
- Advanced security features
- Multiple report formats (Markdown, JSON, HTML)

### Utility Scripts

**run_servers.sh** (Executable)
- Interactive server launcher
- Menu-driven interface
- Dependency checking
- Environment validation
- Usage: `./run_servers.sh`

**test_servers.py** (Executable)
- Comprehensive environment testing
- Python version check
- Package dependency verification
- API key validation
- Document path checking
- Server file structure validation
- Usage: `python3 test_servers.py`

## 🎯 Quick Reference

### First Time Setup
1. Read: `SETUP_GUIDE.md`
2. Configure: Copy `.env.example` to `.env` and add API keys
3. Install: `pip install -r mcp-requirements.txt`
4. Test: `python3 test_servers.py`
5. Run: `./run_servers.sh` or `python3 <server_file>.py`

### Daily Usage
- **Start server**: `python3 gpt_researcher_mcp_enhanced.py`
- **Run tests**: `python3 test_servers.py`
- **Check setup**: Review `SETUP_GUIDE.md`

### Learning
- **Overview**: `MCP_SERVERS_README.md` - sections 1-3
- **Tool examples**: `MCP_SERVERS_README.md` - section "Tool Examples"
- **Configuration**: `MCP_SERVERS_README.md` - section "Configuration Options"

### Troubleshooting
- **Quick fixes**: `SETUP_GUIDE.md` - "Troubleshooting" section
- **Detailed guide**: `MCP_SERVERS_README.md` - "Troubleshooting" section
- **Test environment**: `python3 test_servers.py`

## 📊 Server Comparison

| Feature | GPT Researcher Enhanced | Document Analysis |
|---------|------------------------|-------------------|
| **Tools** | 5 | 7 |
| **Primary Focus** | Research & Analysis | Document Processing & Stakeholders |
| **File Size** | 32KB | 49KB |
| **Web Research** | Via gpt-researcher | Via Tavily API |
| **AI Analysis** | OpenAI GPT-4 | OpenAI GPT-4 |
| **Best For** | Research reports, data analysis | Stakeholder analysis, funding matching |

## 🔗 Related Resources

### Internal Links
- Main Project: `/home/user/webapp/README.md`
- GPT Researcher: `/home/user/webapp/gpt_researcher/`
- Documentation: `/home/user/webapp/docs/`

### External Links
- **GPT Researcher**: https://gptr.dev
- **MCP Protocol**: https://modelcontextprotocol.io
- **FastMCP**: https://github.com/jlowin/fastmcp
- **Tavily API**: https://tavily.com
- **OpenAI API**: https://platform.openai.com

## 📝 Version Information

**Created**: November 17, 2025
**Last Updated**: November 17, 2025
**Server Version**: 1.0.0
**MCP Protocol**: Latest
**Python**: 3.11+ required

## 🔄 Update Notes

When updating this directory:
1. Update version numbers in server files
2. Regenerate test results if dependencies change
3. Update documentation for new features
4. Test all scripts after changes
5. Update this INDEX.md with new files

## 🤝 Contributing

To contribute improvements:
1. Test changes with `test_servers.py`
2. Update relevant documentation
3. Follow existing code style
4. Submit to main GPT Researcher repository

---

**Need help? Start with `SETUP_GUIDE.md` or run `python3 test_servers.py`**
