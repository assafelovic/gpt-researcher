#!/bin/bash
# MCP Servers Launcher Script

set -e

echo "=================================="
echo "MCP Servers Launcher"
echo "=================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and configure your API keys"
    echo "   cp .env.example .env"
    echo ""
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import fastmcp" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip install -r mcp-requirements.txt
else
    echo "✓ Dependencies installed"
fi

echo ""
echo "Available servers:"
echo "  1) GPT Researcher MCP Enhanced"
echo "  2) Document Analysis MCP"
echo "  3) Run both servers (separate terminals)"
echo ""
read -p "Select server to run (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Starting GPT Researcher MCP Enhanced..."
        python3 gpt_researcher_mcp_enhanced.py
        ;;
    2)
        echo ""
        echo "Starting Document Analysis MCP..."
        python3 document_analysis_mcp.py
        ;;
    3)
        echo ""
        echo "Starting both servers..."
        echo "Note: You'll need to open separate terminals for each"
        echo ""
        echo "Terminal 1: python3 gpt_researcher_mcp_enhanced.py"
        echo "Terminal 2: python3 document_analysis_mcp.py"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
