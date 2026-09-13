---
name: resilient-http
description: Add retry, exponential backoff, and rate limiting to HTTP requests in scrapers and data pipelines
triggers:
  - "resilient http"
  - "http retry"
  - "retry backoff"
  - "rate limit http"
  - "exponential backoff"
  - "resilient scraper"
  - "http client with retry"
tools_required:
  - Read
  - Write
  - Edit
---

# Resilient HTTP

Adds retry with exponential backoff, rate limiting, and source labeling to HTTP requests.
Drop-in module for scrapers and data pipelines that currently do ad-hoc retry logic.

Available in both Python (stdlib only) and TypeScript (native `fetch()`).

## When to use

- Scraper hitting transient 429/5xx errors
- Data pipeline making unreliable API calls
- Any HTTP client that needs automatic retry with backoff
- Replacing ad-hoc `time.sleep` + retry loops

## What it provides

- `python/resilient_http.py` — Python module using only `urllib` (no external deps)
- `typescript/resilient_http.ts` — TypeScript module using native `fetch()` (Node 18+/Bun/Deno)
- Both have matching APIs: `ResilientHTTP` client with `get()` and `post()` methods
- Configurable: max retries, backoff multiplier, max delay, timeout, rate limit, jitter
- Respects `Retry-After` header from 429 responses
- Source labeling in logs and User-Agent for debugging

## Quick start

Copy the relevant file into your project and import:

```python
from resilient_http import ResilientHTTP
client = ResilientHTTP(source="my-scraper")
response = client.get("https://api.example.com/data")
```

```typescript
import { ResilientHTTP } from "./resilient_http";
const client = new ResilientHTTP("my-scraper");
const response = await client.get("https://api.example.com/data");
```

See `README.md` for full configuration reference.
