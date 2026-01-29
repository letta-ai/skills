---
name: morph-warpgrep
description: Integration guide for Morph's WarpGrep (fast agentic code search) and Fast Apply (10,500 tok/s code editing). Use when building coding agents that need fast, accurate code search or need to apply AI-generated edits to code efficiently. Particularly useful for large codebases, deep logic queries, bug tracing, and code path analysis.
---

# Morph WarpGrep & Fast Apply

Morph provides two tools that significantly improve coding agent performance:

- **WarpGrep**: Agentic code search that's 5x faster than regular search, uses parallel tool calls, achieves 0.73 F1 in ~4 steps
- **Fast Apply**: Merges AI edits into code at 10,500 tok/s with 98% accuracy (2x faster than search-replace)

## Prerequisites

1. Get a Morph API key from https://www.morphllm.com/dashboard
2. Set environment variable:

```bash
export MORPH_API_KEY="your-api-key"
```

3. Ensure `ripgrep` is installed (required for local search):

```bash
# macOS
brew install ripgrep

# Ubuntu/Debian  
sudo apt install ripgrep

# Verify installation
rg --version
```

## When to Use

### Use WarpGrep When:
- Searching large codebases (1000+ files)
- Deep logic queries: bug tracing, code paths, control flow analysis
- Need to find relevant context without polluting the context window
- Regular grep returns too many irrelevant results

### Use Fast Apply When:
- Applying AI-generated code edits to existing files
- Need reliable edit merging (98% accuracy vs ~70% for search-replace)
- Working with large files where diff formats fail

### Don't Use When:
- Simple exact-match searches (regular `grep`/`rg` is free and fast enough)
- Surface-level queries where semantic search suffices
- Cost is a major concern (Morph API has usage costs)

---

## Quick Start: WarpGrep Client

This skill includes a **working WarpGrep client** (`scripts/warpgrep-client.ts`) that calls Morph's API directly.

### CLI Usage

```bash
# Basic search
bun scripts/warpgrep-client.ts "Find authentication logic" ./my-project

# With debug output (shows each turn)
bun scripts/warpgrep-client.ts "Find the main entry point" ./repo --debug
```

### Module Usage

```typescript
import { warpGrep } from './scripts/warpgrep-client';

const result = await warpGrep('Find authentication logic', '/path/to/repo');

if (result.success) {
  console.log(`Found ${result.contexts.length} code sections in ${result.turns} turns`);
  for (const ctx of result.contexts) {
    console.log(`File: ${ctx.file}`);
    console.log(ctx.content);
  }
} else {
  console.error('Search failed:', result.error);
}
```

### Response Format

```typescript
interface WarpGrepResult {
  success: boolean;
  contexts?: Array<{
    file: string;    // File path relative to repo root
    content: string; // Content with line numbers
    lines?: string;  // Line range if specified
  }>;
  summary?: string;  // Human-readable summary
  turns?: number;    // Number of API turns used (max 4)
  error?: string;    // Error message if failed
}
```

---

## Tested Results

The WarpGrep client has been tested on the [letta-code](https://github.com/letta-ai/letta-code) repository (~300 TypeScript files).

### Test Results

| Query | Result | Turns | Time | Files Found |
|-------|--------|-------|------|-------------|
| "Find authentication logic" | ✅ Pass | 3 | 6.6s | 5 files |
| "Find the main CLI entry point" | ✅ Pass | 3 | 5.1s | 1 file |
| "Find where models are configured" | ✅ Pass | 3 | 4.3s | 3 files |
| "Find how memory blocks work" | ✅ Pass | 2 | 4.3s | 2 files |
| "Find where API keys are stored" | ✅ Pass | 3 | 6.2s | 3 files |
| "Find the settings manager" | ✅ Pass | 3 | 6.2s | 3 files |

### Error Handling Tests

| Test Case | Expected | Actual |
|-----------|----------|--------|
| Invalid repository path | Error message | ✅ `Repository not found: /path` |
| Vague query ("Find something") | Fail after max turns | ✅ `Search did not complete within max turns` |
| Missing API key | Error message | ✅ `MORPH_API_KEY not set` |

### Performance Summary

- **Average turns**: 2-3 (out of max 4)
- **Average time**: 4-6 seconds
- **Success rate**: 100% for specific queries

---

## Quick Start: Fast Apply

Fast Apply works reliably via the direct API:

```typescript
const response = await fetch('https://api.morphllm.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.MORPH_API_KEY}`
  },
  body: JSON.stringify({
    model: 'morph-v3-fast',  // or 'morph-v3-large' for complex edits
    messages: [{
      role: 'user',
      content: `<instruction>Add error handling for division by zero</instruction>
<code>function divide(a, b) {
  return a / b;
}</code>
<update>function divide(a, b) {
  if (b === 0) throw new Error("Division by zero");
  return a / b;
}</update>`
    }],
    temperature: 0
  })
});

const data = await response.json();
const mergedCode = data.choices[0].message.content;
```

---

## How WarpGrep Works

WarpGrep is an agentic search that runs up to 4 turns:

```
┌─────────────────────────────────────────────────────────────┐
│  Turn 1: Analyze query, map repo structure, initial search  │
├─────────────────────────────────────────────────────────────┤
│  Turn 2-3: Refine search, read specific files               │
├─────────────────────────────────────────────────────────────┤
│  Turn 4: Must call finish with all relevant code locations  │
└─────────────────────────────────────────────────────────────┘
```

The client handles the multi-turn conversation automatically, executing local tools:

| Tool | Description | Implementation |
|------|-------------|----------------|
| `grep` | Regex search across files | Uses ripgrep (`rg`) |
| `read` | Read file contents | Node.js `fs` module |
| `list_directory` | Show directory structure | Node.js `fs` module |
| `finish` | Return final results | Parses file paths |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Your Code / Agent                         │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│              warpgrep-client.ts                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. Build repo structure                                 │ │
│  │ 2. Send query to Morph API                              │ │
│  │ 3. Parse tool calls from response                       │ │
│  │ 4. Execute local tools (grep, read, list_directory)     │ │
│  │ 5. Send results back to API                             │ │
│  │ 6. Repeat until finish or max turns                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
┌───────────────────────┐    ┌───────────────────────┐
│    Morph API          │    │   Local Filesystem    │
│  (morph-warp-grep-v1) │    │   (ripgrep, fs)       │
└───────────────────────┘    └───────────────────────┘
```

---

## Morph's Benchmarks

From Morph's SWE-bench evaluation with Claude 4.5 Opus:

| Metric | Without WarpGrep | With WarpGrep | Improvement |
|--------|------------------|---------------|-------------|
| Input Tokens | 14K | 9K | **39% fewer** |
| Agent Turns | 35.0 | 26.0 | **26% fewer** |
| Tasks Solved | 74.4% | 81.9% | **10% more** |

Source: [Morph WarpGrep Benchmarks](https://www.morphllm.com/benchmarks/warp-grep)

---

## Query Guidelines

### Good Queries (Specific)

```bash
# ✅ Specific functionality
"Find where user authentication is handled"
"Find the main entry point"
"Find where API keys are stored"

# ✅ Conceptual questions
"Find how memory blocks are initialized"
"Find the settings management logic"

# ✅ Code patterns
"Find all React hooks usage"
"Find database connection handling"
```

### Bad Queries (Too Vague)

```bash
# ❌ Too vague - model doesn't know what to search for
"Find something"
"Find code"
"Search"
```

---

## Troubleshooting

### "Search did not complete" with Official SDK

The official Morph SDK (`@morphllm/morphsdk`) may have version issues. Use the included `warpgrep-client.ts` script instead, which calls the API directly with the correct model name (`morph-warp-grep-v1`).

### ripgrep Not Found

```bash
# Install ripgrep
brew install ripgrep  # macOS
sudo apt install ripgrep  # Ubuntu/Debian

# Verify
rg --version
```

### API Key Issues

```bash
# Verify API key works
curl -X POST https://api.morphllm.com/v1/chat/completions \
  -H "Authorization: Bearer $MORPH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"morph-v3-fast","messages":[{"role":"user","content":"test"}]}'
```

### Query Takes Too Long / Fails

- Make query more specific
- Ensure repo isn't too large (>10K files may timeout)
- Check API key has sufficient credits

---

## Cost Considerations

- WarpGrep uses **1-4 API calls** per search (typically 2-3)
- Fast Apply uses **1 API call** per edit
- Monitor usage via [Morph Dashboard](https://www.morphllm.com/dashboard)
- Use regular grep/ripgrep for simple exact-match searches (free)

---

## Resources

- [Morph Documentation](https://docs.morphllm.com)
- [WarpGrep Benchmarks](https://www.morphllm.com/benchmarks/warp-grep)
- [Fast Apply Benchmarks](https://www.morphllm.com/benchmarks/fast-apply)
- [Morph Dashboard](https://www.morphllm.com/dashboard)
- [Morph Discord](https://discord.gg/AdXta4yxEK)
- [Direct API Guide](https://docs.morphllm.com/sdk/components/warp-grep/direct)
