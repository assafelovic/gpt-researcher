---
sidebar_position: 3
---

# Integrating with Claude

This guide focuses specifically on how to integrate the GPT Researcher MCP Server with Claude, allowing you to leverage Claude's powerful conversational abilities with GPT Researcher's web research capabilities.

## Prerequisites

Before integrating with Claude, you'll need:

1. A Claude API key with MCP access enabled
2. GPT Researcher MCP server running and accessible
3. Basic familiarity with the Claude API

## Setting Up Claude with MCP

To use Claude with the GPT Researcher MCP server:

1. Configure your Claude API client to point to your MCP server endpoint
2. Ensure Claude can access the necessary tools via MCP

Here's an example configuration:

```python
import anthropic

client = anthropic.Anthropic(
    api_key="your_anthropic_api_key",
)

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0.0,
    system="You are a helpful research assistant that has access to research tools via MCP.",
    messages=[
        {"role": "user", "content": "Research the impact of quantum computing on cryptography."}
    ],
    tools=[
        {
            "name": "gpt_researcher",
            "description": "GPT Researcher tools for conducting web research",
            "schemas": {
                "conduct_research": {
                    "type": "function",
                    "function": {
                        "name": "conduct_research",
                        "description": "Conduct web research on a topic",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The research query to investigate"
                                },
                                "depth": {
                                    "type": "string",
                                    "enum": ["basic", "deep"],
                                    "description": "The depth of research to conduct"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                "write_report": {
                    "type": "function",
                    "function": {
                        "name": "write_report",
                        "description": "Generate a report based on research results",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "format": {
                                    "type": "string",
                                    "enum": ["markdown", "text"],
                                    "description": "The format of the report"
                                },
                                "style": {
                                    "type": "string",
                                    "enum": ["academic", "blog", "summary"],
                                    "description": "The writing style of the report"
                                }
                            }
                        }
                    }
                }
            }
        }
    ],
    tool_choice="auto",
    tool_endpoints={
        "gpt_researcher": {
            "url": "http://localhost:8000/mcp"
        }
    }
)
```

## Claude-Specific Prompts

To effectively guide Claude in using the GPT Researcher tools, use prompts like:

```
I need you to research [TOPIC]. Please use the conduct_research tool to gather information, then generate a comprehensive report using the write_report tool. Make sure to cite your sources properly.
```

For a more structured approach:

```
Please help me with a research task following these steps:
1. Use the conduct_research tool to investigate [TOPIC]
2. When the research is complete, use the write_report tool to create a comprehensive report
3. Make sure to include key findings, trends, and cite your sources
```

## Example Conversation Flow

Here's an example of a typical conversation flow when using Claude with the GPT Researcher MCP server:

```
User: I need to understand the current state of fusion energy research. Please conduct thorough research on this topic and provide a comprehensive report.

Claude: I'll help you research the current state of fusion energy research. Let me use the GPT Researcher tools to gather information and then create a comprehensive report for you.

[Claude calls conduct_research tool with query="current state of fusion energy research" and depth="deep"]

Claude: I've completed my research on fusion energy. Here are the key findings:

1. Recent breakthroughs at NIF and JET laboratories
2. Progress with ITER and other tokamak designs  
3. Private fusion companies like Commonwealth Fusion Systems making significant advances
4. Remaining challenges in plasma containment and net energy gain
5. Projected timelines for commercial fusion energy

Let me generate a complete report for you.

[Claude calls write_report tool with format="markdown" and style="academic"]

Claude: # Current State of Fusion Energy Research

## Executive Summary
Fusion energy research has seen significant advancements in recent years, with both public and private efforts accelerating progress toward viable fusion power...

[Full report continues]

## References
1. ITER Organization. (2023). "Status of the ITER Project." https://www.iter.org/proj/status
2. Lawrence Livermore National Laboratory. (2023). "National Ignition Facility achieves fusion ignition." https://www.llnl.gov/...
...

Would you like me to focus on any particular aspect of fusion energy research in more detail?
```

## Best Practices

When integrating Claude with the GPT Researcher MCP server:

1. **Provide clear instructions**: Be specific about what you want Claude to research and how you want the information presented.

2. **Use system prompts effectively**: Configure Claude's system prompt to establish its role as a research assistant.

3. **Balance depth vs. time**: For quick overviews, specify a "basic" depth. For comprehensive research, use "deep" but be aware it will take longer.

4. **Request specific formats**: If you need a particular report format or style, specify it in your prompt or in the write_report tool parameters.

5. **Verify sources**: Always review the sources Claude provides to ensure they're reliable and relevant.

## Troubleshooting

If you encounter issues with Claude and the MCP server:

1. **Connection problems**: Ensure the MCP server is running and accessible from Claude's environment.

2. **Authorization errors**: Check that your API keys are correctly configured and have the necessary permissions.

3. **Tool schema errors**: Verify that your tool schemas match the expected format for the MCP server.

4. **Rate limiting**: If you hit rate limits, implement exponential backoff or reduce the frequency of requests.

## Advanced Claude Integration

For advanced use cases, you can:

1. **Chain multiple research queries**: Break complex topics into multiple focused research queries.

2. **Implement custom tools**: Extend the MCP server with additional tools tailored to your needs.

3. **Use Claude's memory**: Leverage Claude's context window to maintain research state across multiple interactions.

4. **Combine with other tools**: Integrate GPT Researcher with other Claude tools for a more comprehensive workflow.

## Next Steps

- Explore [Claude's MCP documentation](https://docs.anthropic.com/claude/docs/model-context-protocol) for more details
- Learn about [Claude's tool use capabilities](https://docs.anthropic.com/claude/docs/tools-use)
- Check out the [GPT Researcher API documentation](../gptr/querying-the-backend) for additional features

:-) 