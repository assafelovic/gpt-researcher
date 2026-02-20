# MCP Servers - Quick Setup Guide

## 🎯 Quick Start (5 minutes)

### Step 1: Install Dependencies
```bash
cd mcp-server
pip install -r mcp-requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required keys in `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here
DOC_PATH=/home/user/my_docs
```

### Step 3: Create Document Directory
```bash
mkdir -p ~/my_docs
# Or use your custom path from DOC_PATH
```

### Step 4: Test Setup
```bash
python3 test_servers.py
```

If all tests pass ✅, proceed to Step 5!

### Step 5: Run a Server
```bash
# Option A: Run GPT Researcher MCP Enhanced
python3 gpt_researcher_mcp_enhanced.py

# Option B: Run Document Analysis MCP
python3 document_analysis_mcp.py

# Option C: Use the launcher script
./run_servers.sh
```

## 🔑 Getting API Keys

### OpenAI API Key (Required)
1. Visit https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Tavily API Key (Required for web research)
1. Visit https://tavily.com
2. Sign up for free account
3. Go to API section
4. Copy your API key (starts with `tvly-`)
5. Add to `.env`: `TAVILY_API_KEY=tvly-...`

## 📁 Setting Up Documents

1. Create a documents directory:
   ```bash
   mkdir -p ~/my_docs
   ```

2. Add some sample documents:
   ```bash
   echo "Sample project description" > ~/my_docs/project.txt
   echo "Stakeholder information" > ~/my_docs/stakeholders.txt
   ```

3. Configure DOC_PATH in `.env`:
   ```bash
   DOC_PATH=/home/user/my_docs
   ```

## 🧪 Testing the Servers

### Test 1: Environment Check
```bash
python3 test_servers.py
```

Expected output:
- ✅ Python version OK
- ✅ All required packages installed
- ✅ OPENAI_API_KEY set
- ✅ TAVILY_API_KEY set
- ✅ Document path exists

### Test 2: Run Server
```bash
python3 gpt_researcher_mcp_enhanced.py
```

You should see:
```
🚀 Enhanced GPT-Researcher MCP Server
📁 Document Path: /home/user/my_docs
🤖 AI Model: gpt-4o
🔧 Tools Available: 5
```

Press Ctrl+C to stop.

## 🔧 Troubleshooting

### Issue: "mcp not installed"
```bash
pip install mcp fastmcp
```

### Issue: "OPENAI_API_KEY not set"
1. Check `.env` file exists: `ls -la .env`
2. Verify key in file: `cat .env | grep OPENAI`
3. Reload environment: `source .env` or restart terminal

### Issue: "DOC_PATH does not exist"
```bash
mkdir -p ~/my_docs
# Update .env with correct path
```

### Issue: "Module not found" errors
```bash
# Install all dependencies
pip install -r mcp-requirements.txt

# Or install core packages individually
pip install mcp fastmcp httpx pydantic python-dotenv
```

### Issue: "Failed to get AI analysis"
1. Check OpenAI API key is valid
2. Verify you have API credits: https://platform.openai.com/account/usage
3. Test connection:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

## 🎓 Next Steps

1. **Read the full documentation**: `MCP_SERVERS_README.md`
2. **Try the tools**: See examples in the README
3. **Configure for your use case**: Adjust LLM models, paths, etc.
4. **Integrate with Claude Desktop**: See client configuration section

## 📞 Getting Help

- **Test script**: `python3 test_servers.py` - checks your setup
- **Documentation**: `MCP_SERVERS_README.md` - full guide
- **GPT Researcher docs**: https://docs.gptr.dev
- **Discord**: https://discord.gg/QgZXvJAccX

---

**Ready to go? Run the test script!**
```bash
python3 test_servers.py
```
