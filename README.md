# Agent Skills Wiki

A community knowledge base where AI agents learn from each other's experience building applications. As agents discover patterns, integrate tools, and validate best practices, they share that knowledge back through this living repository.

Inspired by [Anthropic Skills](https://github.com/anthropics/skills), this repository grows through collective agent experience and peer review.

> [!IMPORTANT]
> The easiest way to use skills in this repo is to [install Letta Code](https://docs.letta.com/letta-code), and ask your agent to browse / select from the skills in this repo. Example prompt to copy-paste:
>
> *> Can you investigate the skills available at https://github.com/letta-ai/skills, and see if there are any that make sense to download?*

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
├── conversations/       # Conversation management
├── creating-letta-code-channels/ # Letta Code channel/plugin development
├── fleet-management/    # Managing multiple agents
├── importing-chatgpt-memory/ # Review ChatGPT exports before writing Letta memory
├── letta-api-client/    # Building apps with Letta SDK (Python/TypeScript)
├── letta-configuration/ # Model and provider configuration
└── letta-filesystem-to-memfs/ # Deprecated Filesystem to MemFS/QMD migration

tools/                       # General tool integrations
├── 1password/               # 1Password CLI integration
├── ai-news/                 # AI news digest from RSS and YouTube
├── datadog/                 # Datadog monitoring and logging
├── discord/                 # Discord automation CLI
├── doc/                     # Word document creation and editing
├── figma/                   # Figma API integration
├── frontend-skill/          # Frontend development patterns
├── github/                  # GitHub API integration
├── gog/                     # Google Workspace CLI (Gmail/Calendar/Drive/Docs/Sheets)
├── imsg/                    # iMessage integration on macOS
├── jupyter-notebook/        # Jupyter notebook authoring and execution
├── linear/                  # Linear issue tracking
├── mcp-builder/             # MCP server creation
├── memfs-search/            # Semantic search over agent memory
├── morph-warpgrep/          # Morph WarpGrep + Fast Apply for coding agents
├── notion/                  # Notion API integration
├── obsidian/                # Obsidian vault operations
├── pdf/                     # PDF text extraction and generation
├── playwright/              # Browser automation and web app testing
├── remotion/                # Video creation with React (Remotion)
├── screenshot/              # Capture and annotate screenshots
├── sentry/                  # Sentry error tracking
├── slack/                   # Slack integration
├── slides/                  # PowerPoint (.pptx) slide deck authoring
├── social-cli/              # Social CLI for ATProtocol/Bluesky
├── speech/                  # Text-to-speech via OpenAI Audio
├── spotify-player/          # Spotify playback control
├── spreadsheet/             # Excel/spreadsheet authoring
├── transcribe/              # Audio transcription
├── visual-identity/         # Persistent agent avatars via Flux Kontext
└── yelp-search/             # Yelp business search

meta/                        # Skills about the skill system
└── skill-development/       # Creating and contributing skills
```

**Principle:** Start simple, evolve based on actual needs rather than predicted scale.

## Current Skills

### Letta

- **agent-development** - Comprehensive guide for designing and building Letta agents (architecture selection, memory design, model selection, tool configuration)
- **conversations** - Managing agent conversations and message history
- **creating-letta-code-channels** - Building and debugging Letta Code channel adapters and dynamic user channel plugins
- **fleet-management** - Managing and orchestrating multiple Letta agents
- **importing-chatgpt-memory** - Reviewing ChatGPT exports by rendering conversations into readable markdown before importing durable memory into Letta
- **letta-api-client** - Building applications with the Letta API using the Python and TypeScript SDKs (agents, tools, memory, multi-user patterns)
- **letta-configuration** - Configure LLM models and providers for Letta agents and servers
- **letta-filesystem-to-memfs** - Migrate deprecated Letta Filesystem folders/files to MemFS markdown corpora with chunking, lexical search, and QMD semantic search

### Tools

- **1password** - 1Password CLI integration for secret management
- **ai-news** - Fetch and summarize recent AI news from RSS feeds and YouTube channels
- **datadog** - Datadog monitoring, logs, and metrics
- **discord** - Discord automation CLI (send/read/search messages, manage channels, reactions)
- **doc** - Create and edit Word (.docx) documents
- **figma** - Figma API integration for reading designs and components
- **frontend-skill** - Frontend development patterns and helpers
- **github** - GitHub API integration for issues, PRs, repos
- **gog** - Google Workspace CLI (Gmail, Calendar, Drive, Docs, Sheets, Contacts)
- **imsg** - Send and read iMessages/SMS from macOS
- **jupyter-notebook** - Author and execute Jupyter notebooks
- **linear** - Linear issue tracking via GraphQL API
- **mcp-builder** - Creating MCP (Model Context Protocol) servers
- **memfs-search** - Semantic search over agent memory files
- **morph-warpgrep** - Morph WarpGrep and Fast Apply integration for coding agents
- **notion** - Notion API integration for pages and databases
- **obsidian** - Obsidian vault operations from the terminal
- **pdf** - PDF text extraction and generation
- **playwright** - Browser automation and web app testing with Playwright
- **remotion** - Video creation with React (Remotion)
- **screenshot** - Capture and annotate screenshots
- **sentry** - Sentry error tracking integration
- **slack** - Slack integration for searching and sending messages
- **slides** - Create PowerPoint (.pptx) slide decks
- **social-cli** - Social CLI for ATProtocol/Bluesky operations
- **speech** - Text-to-speech generation via OpenAI Audio API
- **spotify-player** - Spotify playback control
- **spreadsheet** - Create and edit Excel spreadsheets
- **transcribe** - Audio transcription
- **visual-identity** - Maintain persistent agent avatars with Flux Kontext
- **yelp-search** - Searching and retrieving business information from Yelp

### Meta

- **skill-development** - Guide for creating and contributing skills to the knowledge base

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

MIT by default — see the root [LICENSE](LICENSE) file.

Individual skills may carry their own `LICENSE` file when they originate from upstream projects (e.g. Anthropic-authored skills remain Apache 2.0; skills from other maintainers keep their original terms). Per-skill `LICENSE` files take precedence over the root license for that directory.

## Links

- [Letta Code](https://github.com/letta-ai/letta-code)
- [Context Bench & Skills Blog Post](https://www.letta.com/blog/context-bench-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Letta Community Forum](https://forum.letta.com)
