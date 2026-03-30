---
name: cross-validated-search
description: Source-backed web search, page reading, and evidence-aware claim checking for AI agents. Use when you need live search results, current facts, citations, or a support/conflict read on a factual claim before answering.
---

# Cross-Validated Search

Use this skill when a task depends on current information, explicit sources, or a compact evidence report instead of a raw search result list.

## Install

```bash
pip install cross-validated-search
```

## Core Commands

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to Use

- factual questions about releases, dates, versions, companies, or statistics
- recent events that may have changed since model training
- claims that should be checked before being stated confidently
- workflows where conflicting evidence should be surfaced instead of hidden
- cases where one citation-ready report is more useful than raw search output

## Guidance

- Start with `search-web` for current or factual questions.
- Use `browse-page` when snippets are too thin to justify an answer.
- Use `verify-claim` for support/conflict classification.
- Use `evidence-report` when you want one artifact with verdict, citations, and next steps.
- Prefer the free `ddgs + self-hosted searxng` path for stronger provider diversity.

## Compatibility

- Repository: `cross-validated-search`
- Package: `cross-validated-search`
- Module: `cross_validated_search`
- CLI: `search-web`, `browse-page`, `verify-claim`, `evidence-report`
- MCP: `cross-validated-search-mcp`

## Limits

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default provider path starts with `ddgs`.
- Deep verification is stronger than snippets alone, but still not full-document reasoning.
