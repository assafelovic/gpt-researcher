# Claude Skill

GPT Researcher is available as a [Claude Skill](https://skills.sh), allowing you to extend Claude's research capabilities directly within Claude Code and other Claude-powered applications.

## What are Claude Skills?

Skills are modular packages that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. When you install GPT Researcher as a skill, Claude gains access to deep research procedures, helping it conduct comprehensive research with citations.

## Installation

Install GPT Researcher as a Claude Skill using the skills CLI:

```bash
npx skills add assafelovic/gpt-researcher
```

This installs the skill from the [GPT Researcher GitHub repository](https://github.com/assafelovic/gpt-researcher).

## What's Included

The GPT Researcher skill provides Claude with:

- **Architecture Knowledge** - Understanding of the planner-executor-publisher pattern
- **Component Signatures** - Method signatures for `GPTResearcher`, `ResearchConductor`, `ReportGenerator`
- **Integration Patterns** - How to add features, retrievers, and customize workflows
- **Configuration Reference** - All environment variables and config options
- **API Reference** - REST and WebSocket API documentation

## Usage

Once installed, Claude can help you with:

- Understanding GPT Researcher's architecture
- Adding new features following the 8-step pattern
- Debugging research pipelines
- Integrating MCP data sources
- Customizing report generation
- Adding new retrievers

## Skill Structure

The skill is located in the `.claude/` directory of the repository:

```
.claude/
├── SKILL.md              # Main skill file (lean, <500 lines)
└── references/           # Detailed documentation
    ├── architecture.md
    ├── components.md
    ├── flows.md
    ├── prompts.md
    ├── retrievers.md
    ├── mcp.md
    ├── deep-research.md
    ├── multi-agents.md
    ├── adding-features.md
    ├── advanced-patterns.md
    ├── api-reference.md
    └── config-reference.md
```

## Learn More

- [Skills.sh Registry](https://skills.sh) - Discover more Claude skills
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/skills) - Official skills documentation
- [GPT Researcher Documentation](https://docs.gptr.dev) - Full project documentation
