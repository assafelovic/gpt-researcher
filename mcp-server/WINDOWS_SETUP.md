# Windows Setup Guide for MCP Servers

## 🪟 Windows-Specific Instructions

This guide addresses common issues when running MCP servers on Windows.

## ✅ Your Test Results Look Great!

Based on your test output, your environment is **perfectly configured**:
- ✅ Python 3.11.0 installed
- ✅ All required packages installed (mcp, fastmcp, httpx, pydantic, dotenv)
- ✅ OPENAI_API_KEY configured
- ✅ TAVILY_API_KEY configured
- ✅ DOC_PATH exists with 13 files
- ✅ All optional packages installed
- ✅ Server files are valid

## 🎯 You're Ready to Run!

### Quick Start
```cmd
# Navigate to the directory
cd C:\Users\sofia\gpt-researcher\mcp-server

# Run GPT Researcher Enhanced
python gpt_researcher_mcp_enhanced.py

# Or run Document Analysis
python document_analysis_mcp.py
```

## 🐛 Common Windows Issues & Solutions

### Issue 1: Encoding Errors
**Symptom**: `'charmap' codec can't decode byte...`

**Solution**: This has been fixed! The files now explicitly declare UTF-8 encoding with:
```python
# -*- coding: utf-8 -*-
```

If you still see encoding issues:
```cmd
# Set console to UTF-8
chcp 65001

# Then run the server
python gpt_researcher_mcp_enhanced.py
```

### Issue 2: Path Issues
**Symptom**: File not found or path errors

**Solution**: Use Windows paths with forward slashes or double backslashes:
```python
# Good options:
DOC_PATH=C:/my_docs
DOC_PATH=C:\\my_docs
```

### Issue 3: PowerShell Execution Policy
**Symptom**: Cannot run scripts

**Solution**:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 4: Virtual Environment
**Recommended**: Use a virtual environment

```cmd
# Create virtual environment
python -m venv venv

# Activate (Command Prompt)
venv\Scripts\activate.bat

# Activate (PowerShell)
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r mcp-requirements.txt
```

## 📂 Windows File Paths

### Your Current Setup (Perfect!)
```
DOC_PATH: C:/my_docs
Files found: 13
```

### Path Format Options
```python
# Option 1: Forward slashes (recommended)
DOC_PATH=C:/my_docs

# Option 2: Raw string with backslashes
DOC_PATH=C:\\my_docs

# Option 3: Use pathlib (in Python)
from pathlib import Path
doc_path = Path("C:/my_docs")
```

## 🚀 Running the Servers on Windows

### Option 1: Command Prompt
```cmd
cd C:\Users\sofia\gpt-researcher\mcp-server
python gpt_researcher_mcp_enhanced.py
```

### Option 2: PowerShell
```powershell
cd C:\Users\sofia\gpt-researcher\mcp-server
python gpt_researcher_mcp_enhanced.py
```

### Option 3: Run Both Servers
Open two separate command prompts:

**Terminal 1:**
```cmd
cd C:\Users\sofia\gpt-researcher\mcp-server
python gpt_researcher_mcp_enhanced.py
```

**Terminal 2:**
```cmd
cd C:\Users\sofia\gpt-researcher\mcp-server
python document_analysis_mcp.py
```

## 🔧 Windows-Specific Configuration

### Environment Variables (.env file)
Your `.env` should look like:
```ini
# API Keys
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here

# Document Path (use forward slashes)
DOC_PATH=C:/my_docs

# Optional: LLM Configuration
STRATEGIC_LLM=gpt-4o
SMART_LLM=gpt-4o
FAST_LLM=gpt-3.5-turbo
```

### Creating the .env File on Windows
```cmd
# Copy example
copy .env.example .env

# Edit with Notepad
notepad .env

# Or use your preferred editor
code .env
```

## 📊 Testing on Windows

### Run the Test Script
```cmd
python test_servers.py
```

Expected output (like yours):
```
✅ Python version OK
✅ All required packages
✅ API keys configured
✅ Document path exists
✅ Server files valid
```

## 🎓 Windows Tips & Tricks

### 1. Use Windows Terminal (Recommended)
- Better Unicode support
- Multiple tabs
- Copy/paste works better
- Download: Microsoft Store → "Windows Terminal"

### 2. Enable UTF-8 in Console
```cmd
# Temporary (current session)
chcp 65001

# Permanent (registry edit)
# Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Command Processor
# Add: AutoRun = chcp 65001
```

### 3. File Associations
Make Python files executable:
```cmd
assoc .py=Python.File
ftype Python.File="C:\Python311\python.exe" "%1" %*
```

### 4. Add to PATH
Ensure Python is in your PATH:
```cmd
# Check current PATH
echo %PATH%

# Add Python (run as Administrator)
setx PATH "%PATH%;C:\Python311;C:\Python311\Scripts"
```

## 🌐 Using with Claude Desktop (Windows)

Configuration file location:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Full path typically:
```
C:\Users\sofia\AppData\Roaming\Claude\claude_desktop_config.json
```

Configuration example:
```json
{
  "mcpServers": {
    "gpt-researcher-enhanced": {
      "command": "python",
      "args": ["C:/Users/sofia/gpt-researcher/mcp-server/gpt_researcher_mcp_enhanced.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "TAVILY_API_KEY": "tvly-your-key",
        "DOC_PATH": "C:/my_docs"
      }
    }
  }
}
```

## 🔍 Debugging on Windows

### Check Python Installation
```cmd
python --version
where python
python -c "import sys; print(sys.executable)"
```

### Check Package Installation
```cmd
pip list | findstr mcp
pip show fastmcp
```

### Check File Encoding
```cmd
file gpt_researcher_mcp_enhanced.py
# Or use PowerShell
Get-Content gpt_researcher_mcp_enhanced.py -Encoding UTF8
```

### Test API Connection
```cmd
# Test OpenAI
python -c "import openai; print('OpenAI OK')"

# Test Tavily
python -c "import httpx; print('httpx OK')"
```

## 📝 Quick Reference

### Your Setup (Working!)
- ✅ Python: 3.11.0
- ✅ Location: `C:\Users\sofia\gpt-researcher\mcp-server`
- ✅ Documents: `C:/my_docs` (13 files)
- ✅ All packages installed
- ✅ API keys configured

### Next Steps
1. **Run a server**: `python gpt_researcher_mcp_enhanced.py`
2. **Test a tool**: Try the `gpt_research` tool
3. **Explore**: Read `MCP_SERVERS_README.md` for tool examples

## 🎉 Success Checklist

Based on your test results, you have:
- [x] Python 3.11+ installed
- [x] All required packages
- [x] All optional packages
- [x] OpenAI API key configured
- [x] Tavily API key configured
- [x] Document directory with files
- [x] Server files validated
- [x] Environment configured

**You're ready to go! Just run the servers!**

## 📞 Windows-Specific Help

### Resources
- **Python Windows FAQ**: https://docs.python.org/3/faq/windows.html
- **pip on Windows**: https://pip.pypa.io/en/stable/installation/
- **VS Code on Windows**: https://code.visualstudio.com/docs/python/python-tutorial

### Common Commands
```cmd
# List installed packages
pip list

# Update pip
python -m pip install --upgrade pip

# Reinstall package
pip uninstall fastmcp
pip install fastmcp

# Check Python version
python --version

# Run in verbose mode
python -v gpt_researcher_mcp_enhanced.py
```

---

**🪟 Windows Setup Complete!**

Your environment is perfectly configured. Just run:
```cmd
python gpt_researcher_mcp_enhanced.py
```
