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
2. Install the SDK:

```bash
bun add @morphllm/morphsdk
```

3. Set environment variable:

```bash
export MORPH_API_KEY="your-api-key"
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

## Quick Start: WarpGrep

### Basic Usage

```typescript
import { MorphClient } from '@morphllm/morphsdk';

const morph = new MorphClient({
  apiKey: process.env.MORPH_API_KEY
});

const result = await morph.warpGrep.execute({
  query: 'Find where user authentication is handled',
  repoRoot: '.'
});

if (result.success) {
  for (const ctx of result.contexts) {
    console.log(`File: ${ctx.file}`);
    console.log(ctx.content);
  }
  console.log(`Summary: ${result.summary}`);
} else {
  console.error(`Search failed: ${result.error}`);
}
```

### As an Agent Tool (Vercel AI SDK)

```typescript
import { generateText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';
import { MorphClient } from '@morphllm/morphsdk';

const morph = new MorphClient({ apiKey: process.env.MORPH_API_KEY });
const grepTool = morph.vercel.createWarpGrepTool({ repoRoot: '.' });

const result = await generateText({
  model: anthropic('claude-sonnet-4-5-20250929'),
  tools: { grep: grepTool },
  prompt: 'Find where user authentication is handled',
  maxSteps: 5
});
```

### As an Agent Tool (OpenAI SDK)

```typescript
import OpenAI from 'openai';
import { MorphClient } from '@morphllm/morphsdk';

const morph = new MorphClient({ apiKey: process.env.MORPH_API_KEY });
const grepTool = morph.openai.createWarpGrepTool({ repoRoot: '.' });

// Use grepTool.definition for tool registration
// Use grepTool.execute(args) when tool is called
```

### Custom Tool Name/Description

```typescript
const grepTool = morph.openai.createWarpGrepTool({
  repoRoot: '.',
  name: 'search_codebase',
  description: 'Search the codebase for specific functionality or patterns'
});
```

## Quick Start: Fast Apply

```typescript
import { MorphClient } from '@morphllm/morphsdk';

const morph = new MorphClient({ apiKey: process.env.MORPH_API_KEY });

const result = await morph.fastApply.apply({
  originalCode: '... existing file contents ...',
  updateSnippet: '... AI-generated edit with context ...',
  language: 'typescript'
});

if (result.success) {
  console.log(result.mergedCode);
}
```

## Response Types

### WarpGrep Success Response

```typescript
interface WarpGrepResult {
  success: true;
  contexts: Array<{
    file: string;    // File path relative to repo root
    content: string; // Content of the relevant code section
  }>;
  summary: string;   // Summary of what was found
}
```

### WarpGrep Error Response

```typescript
interface WarpGrepError {
  success: false;
  error: string;
}
```

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
// 1. Search for relevant code
const searchResult = await morph.warpGrep.execute({
  query: 'Where is the payment processing logic?',
  repoRoot: '.'
});

// 2. Use found contexts to inform next steps
if (searchResult.success) {
  const relevantFiles = searchResult.contexts.map(c => c.file);
  // Now read/edit these specific files
}
```

### Combining WarpGrep + Fast Apply

```typescript
// 1. Find the code to modify
const search = await morph.warpGrep.execute({
  query: 'Find the user validation function',
  repoRoot: '.'
});

// 2. Generate edit with your LLM (not shown)
const aiGeneratedEdit = '...';

// 3. Apply the edit reliably
const applied = await morph.fastApply.apply({
  originalCode: originalFileContents,
  updateSnippet: aiGeneratedEdit,
  language: 'typescript'
});
```

## Cost Considerations

- WarpGrep and Fast Apply are paid APIs
- Use regular grep/ripgrep for simple exact-match searches
- Reserve WarpGrep for complex queries where it provides clear value
- Monitor usage via the Morph dashboard

## Troubleshooting

### "Search did not complete" Error

If the SDK returns this error, the SDK may be using a deprecated model name. Solutions:

1. **Update the SDK**: `bun add @morphllm/morphsdk@latest`
2. **Check Morph status**: The API and SDK may have version mismatches - check [Morph Discord](https://discord.gg/AdXta4yxEK) for updates
3. **Use Fast Apply directly**: Fast Apply (`morph-v3-fast`) works reliably while WarpGrep SDK issues are resolved

### Verify Your API Key Works

Test your API key with Fast Apply (more stable):

```typescript
const response = await fetch('https://api.morphllm.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.MORPH_API_KEY}`
  },
  body: JSON.stringify({
    model: 'morph-v3-fast',
    messages: [{
      role: 'user',
      content: '<instruction>Add logging</instruction>\n<code>function test() {}</code>\n<update>function test() { console.log("called"); }</update>'
    }],
    temperature: 0
  })
});
// Should return 200 OK
```

### Direct API Usage

```typescript
// Fast Apply - Direct API
const response = await fetch('https://api.morphllm.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.MORPH_API_KEY}`
  },
  body: JSON.stringify({
    model: 'morph-v3-fast',  // For Fast Apply
    messages: [{
      role: 'user',
      content: `<instruction>Description of change</instruction>
<code>${originalCode}</code>
<update>${updatedCode}</update>`
    }],
    temperature: 0
  })
});
```

For WarpGrep direct API usage, see [Morph's Direct API Guide](https://docs.morphllm.com/sdk/components/warp-grep/direct).

## Resources

- [Morph Documentation](https://docs.morphllm.com)
- [WarpGrep Benchmarks](https://www.morphllm.com/benchmarks/warp-grep)
- [Fast Apply Benchmarks](https://www.morphllm.com/benchmarks/fast-apply)
- [Morph Dashboard](https://www.morphllm.com/dashboard)
- [SDK on npm](https://www.npmjs.com/package/@morphllm/morphsdk)
