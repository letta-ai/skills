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

## Quick Start: WarpGrep Client

This skill includes a working WarpGrep client (`scripts/warpgrep-client.ts`) that calls Morph's API directly.

### CLI Usage

```bash
# Basic usage
bun scripts/warpgrep-client.ts "Find authentication logic" ./my-project

# With debug output (shows each turn)
bun scripts/warpgrep-client.ts "Find where models are configured" ./repo --debug
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

## How WarpGrep Works

WarpGrep is an agentic search that runs up to 4 turns:

1. **Turn 1**: Analyzes query, maps repository structure, runs initial searches
2. **Turns 2-3**: Refines search based on findings, reads specific files
3. **Turn 4**: Must call `finish` with all relevant code locations

The client handles the multi-turn conversation automatically, executing local tools:
- `grep` - Regex search across files (uses ripgrep)
- `read` - Read file contents with optional line ranges
- `list_directory` - Show directory structure
- `finish` - Return final results

## Performance Benchmarks

From Morph's SWE-bench evaluation with Claude 4.5 Opus:

| Metric | Without WarpGrep | With WarpGrep | Improvement |
|--------|------------------|---------------|-------------|
| Input Tokens | 14K | 9K | 39% fewer |
| Agent Turns | 35.0 | 26.0 | 26% fewer |
| Tasks Solved | 74.4% | 81.9% | 10% more |

## Common Patterns

### Reconnaissance-Then-Action

```typescript
import { warpGrep } from './scripts/warpgrep-client';

// 1. Search for relevant code
const result = await warpGrep('Where is the payment processing logic?', '.');

// 2. Use found contexts to inform next steps
if (result.success) {
  const relevantFiles = result.contexts.map(c => c.file);
  console.log('Found relevant files:', relevantFiles);
  // Now read/edit these specific files
}
```

### Combining WarpGrep + Fast Apply

```typescript
import { warpGrep } from './scripts/warpgrep-client';

// 1. Find the code to modify
const search = await warpGrep('Find the user validation function', '.');

if (search.success && search.contexts.length > 0) {
  const targetFile = search.contexts[0];
  
  // 2. Generate edit with your LLM
  const aiGeneratedEdit = await generateEdit(targetFile.content);
  
  // 3. Apply the edit reliably with Fast Apply
  const applied = await applyEdit(targetFile.content, aiGeneratedEdit);
}
```

## Troubleshooting

### "Search did not complete" with Official SDK

The official Morph SDK (`@morphllm/morphsdk`) may have version issues. Use the included `warpgrep-client.ts` script instead, which calls the API directly with the correct model name (`morph-warp-grep-v1`).

### ripgrep Not Found

The WarpGrep client requires ripgrep (`rg`) for local file searching:

```bash
# macOS
brew install ripgrep

# Check installation
rg --version
```

### API Key Issues

Verify your API key works:

```bash
curl -X POST https://api.morphllm.com/v1/chat/completions \
  -H "Authorization: Bearer $MORPH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"morph-v3-fast","messages":[{"role":"user","content":"test"}]}'
```

## Cost Considerations

- WarpGrep and Fast Apply are paid APIs
- WarpGrep uses 1-4 API calls per search (usually 2-3)
- Use regular grep/ripgrep for simple exact-match searches
- Reserve WarpGrep for complex queries where it provides clear value
- Monitor usage via the [Morph Dashboard](https://www.morphllm.com/dashboard)

## Resources

- [Morph Documentation](https://docs.morphllm.com)
- [WarpGrep Benchmarks](https://www.morphllm.com/benchmarks/warp-grep)
- [Fast Apply Benchmarks](https://www.morphllm.com/benchmarks/fast-apply)
- [Morph Dashboard](https://www.morphllm.com/dashboard)
- [Morph Discord](https://discord.gg/AdXta4yxEK)
