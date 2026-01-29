---
sidebar_label: AI-Assisted Development
sidebar_position: 6
---

# 🤖 AI-Assisted Development with Claude

GPT Researcher includes a comprehensive skill file that enables AI assistants like Claude to understand, use, and extend the codebase effectively. This guide explains how to leverage Claude Code for contributing to GPT Researcher.

## Overview

We maintain a `.claude/skills/` directory containing detailed documentation that Claude automatically discovers and uses when working with this repository. This enables:

- **Faster onboarding** - Claude understands the architecture instantly
- **Consistent contributions** - Follows established patterns
- **Fewer errors** - Knows common gotchas and best practices
- **End-to-end features** - Can implement complete features following the 8-step pattern

## The Skills Directory

```
.claude/
└── skills/
    ├── SKILL.md      # Comprehensive development guide (~1,500 lines)
    └── REFERENCE.md  # Quick lookup for config, API, WebSocket events
```

### What's in SKILL.md

| Section | Description |
|---------|-------------|
| Architecture Deep Dive | Full system diagram with all layers and components |
| Core Components | Method signatures for `GPTResearcher`, `ResearchConductor`, etc. |
| End-to-End Flow | Complete code paths from request to report |
| Data Flow | What gets passed between components |
| Prompt System | Real prompt examples from `prompts.py` |
| Retriever System | All 14 retrievers, how to add new ones |
| MCP Integration | Strategy options, configuration, processing logic |
| Deep Research | Recursive exploration configuration |
| Multi-Agent System | LangGraph-based 8-agent workflow |
| Image Generation Case Study | Complete real implementation as reference |
| 8-Step Feature Pattern | How to add new features |
| Advanced Usage | Callbacks, LangChain, vector stores |
| Error Handling | Graceful degradation patterns |
| Testing Guide | pytest setup and examples |
| Critical Gotchas | Common mistakes to avoid |

### What's in REFERENCE.md

- All environment variables
- REST API endpoints
- WebSocket message types
- Python client parameters

## Using Claude Code

### Installation

1. Install [Claude Code](https://claude.ai/code) (VS Code extension or CLI)
2. Open the GPT Researcher repository
3. Claude automatically discovers the skills in `.claude/skills/`

### Example Prompts

**Understanding the codebase:**
```
How does the research flow work from query to report?
```

**Adding a feature:**
```
I want to add a feature that generates audio summaries of reports. 
Follow the 8-step pattern from the skills file.
```

**Debugging:**
```
Why might images not be appearing in the report? Check the image generation flow.
```

**Extending functionality:**
```
Add a new retriever for Wikipedia. Follow the retriever pattern in the skills.
```

### What Claude Can Do

With the skills loaded, Claude can:

1. **Explain any part of the codebase** - Architecture, data flow, component interactions
2. **Implement features end-to-end** - Config → Provider → Skill → Agent → Prompts → Frontend
3. **Debug issues** - Understands common gotchas and error patterns
4. **Write tests** - Knows the testing patterns and pytest setup
5. **Add retrievers** - Follows the exact pattern for new search engines
6. **Modify prompts** - Understands the PromptFamily system
7. **Extend the API** - Knows FastAPI patterns and WebSocket events

## Contributing with Claude

### Before You Start

1. Fork and clone the repository
2. Install in editable mode: `pip install -e .`
3. Set up your `.env` file with required API keys
4. Open in an editor with Claude Code

### Contribution Workflow

1. **Describe your feature/fix** to Claude with context
2. **Let Claude implement** following the established patterns
3. **Review the changes** - Claude will explain what it did
4. **Test thoroughly** - `python -m pytest tests/`
5. **Submit PR** with clear description

### Example: Adding a New Feature

```
I want to add a feature that allows users to specify a custom 
writing style for reports (e.g., "academic", "blog post", "executive summary").

This should:
1. Be configurable via environment variable
2. Affect the report generation prompt
3. Be optional with a sensible default

Please implement following the 8-step pattern.
```

Claude will:
1. Add `REPORT_STYLE` to config defaults
2. Add type to `BaseConfig`
3. Update the prompt in `prompts.py`
4. Show you exactly what changed
5. Explain any gotchas (like lowercase config access)

## Updating the Skills

If you add significant features or change the architecture:

1. Update `.claude/skills/SKILL.md` with the new patterns
2. Add any new config vars to `.claude/skills/REFERENCE.md`
3. Include your feature as a case study if it's a good example

### Skills File Best Practices

- Keep code examples real (from actual implementation)
- Include both "what" and "why"
- Document gotchas prominently
- Update data flow diagrams when adding components
- Add new features to the "Supported Options" sections

## Why This Matters

AI-assisted development is becoming standard practice. By maintaining high-quality skills files:

- **New contributors** can onboard in minutes instead of hours
- **Experienced contributors** can work faster with AI assistance
- **Code quality** stays consistent across contributions
- **Documentation** stays up-to-date as a side effect

The skills file is essentially a "brain dump" of everything an expert developer knows about GPT Researcher, made available to AI assistants.

## Learn More

- [Claude Code Documentation](https://claude.ai/code/docs)
- [Anthropic Agent Skills](https://github.com/anthropics/skills)
- [Contributing Guidelines](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md)
