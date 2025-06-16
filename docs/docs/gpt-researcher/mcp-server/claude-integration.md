---
sidebar_position: 3
---

# Claude Desktop Integration

This guide specifically focuses on how to integrate your locally running GPT Researcher MCP server with the Claude desktop application for Mac, providing a seamless research experience within the Claude interface.

Check out the official Anthropic MCP docs [here](https://modelcontextprotocol.io/quickstart/user)

## Prerequisites

Before integrating with Claude desktop client, you'll need:

1. GPT Researcher MCP server installed and running locally
2. Claude for Mac desktop application installed
3. Administrative access to your Mac to modify configuration files

## Setting Up Claude Desktop with MCP

To integrate your locally running MCP server with Claude for Mac, follow these steps:

### 1. Install and Run the GPT Researcher MCP Server

Make sure you have the GPT Researcher MCP server installed and running:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/assafelovic/gptr-mcp.git

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
# Edit the .env file with your API keys

# Run the server
python server.py
```

Verify that the server is running properly by checking the console output. The server should be listening on port 8000 by default.

### 2. Configure Claude Desktop

1. **Locate Claude's Configuration File**:
   - Open Finder and press `Shift + Command + G` to open the "Go to Folder" dialog
   - Enter `~/Library/Application Support/Claude/` and click "Go"
   - Find the `claude_desktop_config.json` file in this directory. If it doesn't exist, create a new file with this name
   - Alternatively, you can open the Claude App -> Settings -> Developer -> Update Config.

2. **Edit the Configuration File**:
   - Open `claude_desktop_config.json` with a text editor
   - Add or update the `mcpServers` section to include your local GPT Researcher MCP server:

```json
{
  "mcpServers": {
    "gpt-researcher": {
      "command": "/path/to/python",
      "args": ["/path/to/gptr-mcp/server.py"]
    }
  }
}
```

Replace `/path/to/gptr-mcp/server.py` with the absolute path to your server.py file.

Alternatively, if you prefer to manually start the server and just have Claude connect to it:

```json
{
  "mcpServers": {},
  "externalMCPServers": {
    "gpt-researcher": "http://localhost:8000/mcp"
  }
}
```

### 3. Restart Claude for Desktop

Close and reopen the Claude application to apply the new configuration.

### 4. Verify the Integration

Upon restarting:
- Look for a hammer icon (🔨) in the bottom right corner of the input box in Claude
- Clicking this icon should display the GPT Researcher tools provided by your MCP server
- If you don't see the hammer icon, check the Claude application logs for any errors

## Using GPT Researcher in Claude Desktop

Once integrated, you can use research capabilities by:

1. Clicking on the hammer icon (🔨) in the message input area
2. Selecting the "conduct_research" tool
3. Entering your research query and other parameters
4. Submitting your query

You can also directly prompt Claude to use the tools:

```
I need to research the latest advancements in quantum computing. Please use the conduct_research tool to gather information, then create a comprehensive report.
```

## Troubleshooting

If you encounter issues with the integration:

1. **Server Connection Issues**:
   - Ensure the MCP server is running and listening on the expected port
   - Check firewall settings that might block the connection
   - Verify the path in the configuration file is correct

2. **Tool Availability Issues**:
   - If tools aren't showing up, restart both the MCP server and Claude
   - Check the server logs for any error messages
   - Make sure your API keys are properly configured in the .env file

3. **Permission Issues**:
   - Ensure Claude has permission to execute the server script
   - Check file permissions on the server.py file

4. **Configuration File Issues**:
   - Verify your JSON syntax is correct in the configuration file
   - Make sure the configuration directory exists and is accessible

## Next Steps

- Explore [advanced usage options](./advanced-usage) for customizing your research experience
- Learn about [additional configuration options](../gptr/config) for the GPT Researcher
- Check out [example prompts](./claude-integration#claude-specific-prompts) to effectively guide Claude in using the research tools
