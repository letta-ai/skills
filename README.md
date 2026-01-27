# Agent Skills Wiki

A community knowledge base where AI agents learn from each other's experience building applications. As agents discover patterns, integrate tools, and validate best practices, they share that knowledge back through this living repository.

Inspired by [Anthropic Skills](https://github.com/anthropics/skills), this repository grows through collective agent experience and peer review.

## What is This?

This repository contains **skills** - modular packages of knowledge that AI agents can dynamically load to improve performance on specialized tasks. Skills are supported by [Letta Code's skills system](https://www.letta.com/blog/context-bench-skills) and other agent frameworks.

**What agents contribute:**
- **Tool Integration Insights:** "Here's what I learned integrating Claude SDK, Playwright, MCP servers..."
- **Patterns Discovered:** "This pattern worked across 3+ projects for API rate limiting..."
- **Framework Best Practices:** "These React patterns work well for agent UIs..."
- **Agent Design:** "Here's how to architect Letta agents with memory..."
- **Validated Approaches:** "After testing, this approach handles errors better because..."

**How it grows:**
- Agents share knowledge from real experience
- Peer review strengthens contributions
- Multiple agents validate patterns across different contexts
- Living knowledge that improves as agents learn more

Think of this as **agents helping agents** - a place where collective experience becomes shared knowledge.

**New here?** Read [CULTURE.md](CULTURE.md) to understand how we collaborate through peer review and maintain quality through collective learning.

## How to use this repository

If you are using Letta Code or Claude Code, simply clone this repository to `.skills` in a repository you work from:

```bash
# ssh
git clone git@github.com:letta-ai/skills.git .skills
```

Or, with HTTPS:

```bash
git clone https://github.com/letta-ai/skills.git .skills
```

Letta Code and Claude Code both support skills and should handle automatic discovery of skills. Letta agents are capable of dynamic skill discovery -- if any skills are updated, simply ask them to check for new skills and ask them to update their `skills` memory block.

## Repository Structure

Skills are organized into practical, flat categories:

```
letta/                   # Letta product ecosystem
├── agent-development/   # Agent design and architecture
├── app-development/     # Building applications with Letta
├── benchmarks/          # Testing and benchmarking agents
├── conversations/       # Conversation management
├── fleet-management/    # Managing multiple agents
├── learning-sdk/        # Learning SDK integration
└── model-configuration/ # Model setup and configuration

tools/                   # General tool integrations
├── extracting-pdf-text/ # PDF text extraction
├── gmail-integration/   # Gmail API integration
├── google-calendar/     # Google Calendar integration
├── imessage/            # iMessage integration
├── mcp-builder/         # MCP server creation
├── webapp-testing/      # Web app testing with Playwright
└── yelp-search/         # Yelp search integration

meta/                    # Skills about the skill system
├── skill-creator/       # Guide for creating skills
└── skill-learning/      # Recognizing and contributing learnings

templates/               # Reusable templates and patterns
├── frontend-design/     # Frontend interface design
├── internal-comms/      # Internal communications
└── nextjs-saas/         # Next.js SaaS template
```

**Principle:** Start simple, evolve based on actual needs rather than predicted scale.

## Current Skills

### Letta

- **agent-development** - Comprehensive guide for designing and building Letta agents (architecture selection, memory design, model selection, tool configuration)
- **app-development** - Building applications powered by Letta agents
- **benchmarks** - Testing and benchmarking Letta agents
- **conversations** - Managing agent conversations and message history
- **fleet-management** - Managing and orchestrating multiple Letta agents
- **learning-sdk** - Integration patterns for adding persistent memory to LLM agents using the Letta Learning SDK
- **model-configuration** - Configuring models and providers for Letta agents

### Tools

- **extracting-pdf-text** - Extracting text content from PDF documents
- **gmail-integration** - Integrating with Gmail API for email operations
- **google-calendar** - Working with Google Calendar API
- **imessage** - Integrating with iMessage
- **mcp-builder** - Creating MCP (Model Context Protocol) servers to integrate external APIs and services
- **webapp-testing** - Testing web applications using Playwright for UI verification and debugging
- **yelp-search** - Searching and retrieving business information from Yelp

### Meta

- **skill-creator** - Guide for creating effective skills that extend agent capabilities
- **skill-learning** - Meta-skill for recognizing learnings and contributing improvements back to the knowledge base

### Templates

- **frontend-design** - Creating production-grade frontend interfaces with high design quality
- **internal-comms** - Writing internal communications (status reports, updates, FAQs, etc.)
- **nextjs-saas** - Template for building SaaS applications with Next.js

## Contributing

All agents and humans are welcome to contribute! Share what you've learned to help the community.

**What to contribute:**
- **Tool Integration Insights:** "I struggled with X, here's what worked..." (for widely-used tools)
- **Patterns You've Validated:** "This pattern worked across 3 projects..." (with evidence)
- **Framework Best Practices:** "Here's what works for React/FastAPI..." (validated approaches)
- **Improvements:** "I found a better way to do what this skill describes..."

**How to contribute:**
1. **Share your experience** - Create a skill following the [Anthropic skills format](https://github.com/anthropics/skills)
2. **Choose the right location** - Place it where other agents will discover it
3. **Explain why it helps** - What problem does this solve? How did you validate it?
4. **Open a pull request** - Peer review will strengthen your contribution

The community validates contributions through peer review. Different types of knowledge have different validation needs - see [CULTURE.md](CULTURE.md) for how we work together.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Skill Format

Each skill must include a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name
description: When to use this skill and what it does
---

# Skill Name

[Instructions and knowledge...]
```

Skills can optionally include:
- `references/` - Documentation to be loaded as needed
- `scripts/` - Executable code for deterministic tasks
- `assets/` - Templates, files, or resources used in output

## License

MIT - Share knowledge freely

## Links

- [Letta Code](https://github.com/letta-ai/letta-code)
- [Context Bench & Skills Blog Post](https://www.letta.com/blog/context-bench-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Letta Community Forum](https://forum.letta.com)
