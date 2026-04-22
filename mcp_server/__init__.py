"""HLT-hosted MCP server for GPT Researcher.

Separate Python package (note: underscore, not hyphen) living alongside the
upstream `mcp-server/` directory so upstream merges don't touch our code.
Exposes the library via streamable HTTP so any MCP client can point at the
hosted URL and get research tools.
"""
