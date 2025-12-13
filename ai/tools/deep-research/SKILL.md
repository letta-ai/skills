---
name: deep-research
description: Guide for conducting comprehensive research using the deep-researcher-sdk. Use when you need to perform deep research on a topic with web search grounding, generate research plans, and synthesize findings into detailed reports.
license: MIT
---

# Deep Research Tool Guide

## Overview

The `deep-researcher-sdk` is a Python SDK for conducting deep research using Google's Gemini models with built-in search grounding. It orchestrates a multi-step research flow that generates comprehensive, well-sourced reports.

Use this skill when you need to:
- Research a topic thoroughly before making recommendations
- Generate comprehensive reports with real-time web data
- Synthesize information from multiple search queries into coherent findings

---

## Installation

### For Standalone Use

```bash
pip install deep-researcher-sdk
```

### For Letta Agents

Add to your Letta Dockerfile:

```dockerfile
FROM letta/letta:latest

RUN /app/.venv/bin/python3 -m pip install deep-researcher-sdk
```

Ensure `GEMINI_API_KEY` is set in your environment.

---

## Quick Start

```python
from deep_research import research

result = research("What are the top trends in B2B SaaS marketing in 2025?")
print(result.report)
```

---

## How It Works

The SDK orchestrates a four-step research flow:

### 1. Plan Generation
Uses the thinking model (gemini-2.5-pro) to create a structured research plan based on your query.

### 2. Query Generation
Generates 3-5 targeted search queries from the plan, each with a specific research goal.

### 3. Search & Learn
Executes each query using Gemini's built-in search grounding, extracting key learnings from real-time web results.

### 4. Report Synthesis
Combines all learnings into a comprehensive final report with proper structure and citations.

---

## Usage Patterns

### Simple Research

```python
from deep_research import research

result = research("Your research query here")

# Access results
print(result.plan)       # Research plan
print(result.learnings)  # List of learnings from searches
print(result.report)     # Final synthesized report
```

### Save Output to Files

```python
result = research(
    "Your research query here",
    output_dir="./research_output"
)
# Saves: plan.md, learning_1.md, ..., learnings.md, report.md
```

### Custom Models

```python
result = research(
    "Your research query here",
    thinking_model="gemini-2.5-pro",  # For planning and synthesis
    task_model="gemini-2.5-flash",     # For search tasks
)
```

### Class-Based Usage

```python
from deep_research import DeepResearcher

researcher = DeepResearcher(
    thinking_model="gemini-2.5-pro",
    task_model="gemini-2.5-flash",
    api_key="your-api-key",  # Optional
)

# Run full research
result = researcher.research("Your query", output_dir="./output")

# Or run individual steps
plan = researcher.write_plan("Your query")
queries = researcher.generate_search_queries(plan)
learnings = [researcher.search_and_learn(q.query, q.research_goal) for q in queries]
report = researcher.write_report(plan, learnings)
```

---

## Creating a Letta Tool

To use deep-research as a Letta agent tool, create a tool file:

```python
def deep_research(query: str) -> str:
    """
    Conduct deep research on a topic and return a comprehensive report.

    Use this tool when you need to research a topic thoroughly before
    making recommendations or answering complex questions. The query
    should be specific and well-defined.

    Args:
        query (str): The research topic or question to investigate

    Returns:
        str: A comprehensive markdown report with findings and sources
    """
    from deep_research import research
    result = research(query)
    return result.report
```

Register and attach to your agent:

```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283")

tool = client.tools.create_from_file(filepath="deep_research_tool.py")
client.tools.attach_to_agent(agent_id="your-agent-id", tool_id=tool.id)
```

---

## Dual Model Architecture

The SDK uses two models optimized for different tasks:

| Model | Default | Purpose |
|-------|---------|---------|
| Thinking Model | `gemini-2.5-pro` | Planning, query generation, report synthesis |
| Task Model | `gemini-2.5-flash` | Search tasks with grounding enabled |

---

## Output Structure

When using `output_dir`, the SDK saves:

```
output_dir/
├── plan.md           # Research plan
├── learning_1.md     # First search result
├── learning_2.md     # Second search result
├── ...
├── learnings.md      # All learnings combined
└── report.md         # Final synthesized report
```

---

## Best Practices

### Query Design
- Be specific and well-defined in your research queries
- If the topic is vague, break it into multiple specific queries
- Include context about what aspects you want to explore

### Performance
- Research typically takes 3-5 minutes depending on query complexity
- The SDK generates 3-5 search queries, each taking 15-30 seconds
- Use `output_dir` to save intermediate results for long research tasks

### Integration
- For Letta agents, add clarifying question logic in your agent's system prompt
- The tool returns markdown - format appropriately for your use case
- Consider caching results for repeated queries on the same topic

---

## Requirements

- Python 3.12+
- Google Gemini API key (`GEMINI_API_KEY` environment variable)

## Links

- [PyPI Package](https://pypi.org/project/deep-researcher-sdk/)
- [GitHub Repository](https://github.com/nouamanecodes/deep-research-sdk)
