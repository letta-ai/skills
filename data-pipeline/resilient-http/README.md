# Resilient HTTP Client

A standalone HTTP client with retry, exponential backoff, rate limiting, and source labeling for web scrapers and data pipelines.

Available in **Python** and **TypeScript** with matching APIs.

## Features

- **Configurable retries** — set max attempts, or use the default of 3
- **Exponential backoff** — delays double each attempt (1s → 2s → 4s → …)
- **Jitter** — randomized delay to prevent thundering herd
- **Retryable status codes** — 429, 500, 502, 503, 504 by default
- **Retry-After header** — respected when servers include it on 429 responses
- **Rate limiting** — enforce minimum delay between consecutive requests
- **Timeout** — per-request timeout (30s default)
- **Source labeling** — every log line and User-Agent tagged with your source name
- **Zero external dependencies** — Python uses `urllib`; TypeScript uses native `fetch()`

## Python Usage

```python
from resilient_http import ResilientHTTP, HttpConfig

# Basic usage with defaults
client = ResilientHTTP(source="my-scraper")
response = client.get("https://example.com/api/data")
print(response.status, response.text)

# With query parameters
response = client.get(
    "https://api.example.com/search",
    params={"q": "python", "page": "1"},
)

# POST with JSON body
response = client.post(
    "https://api.example.com/items",
    json_body={"name": "New Item", "value": 42},
)
data = response.json()

# Custom configuration
config = HttpConfig(
    max_retries=5,
    initial_delay=0.5,
    backoff_multiplier=3.0,
    max_delay=60.0,
    timeout=15,
    rate_limit_delay=1.0,  # 1 request per second
)
client = ResilientHTTP(source="polite-scraper", config=config)

# Error handling
from resilient_http import ResilientHTTPError

try:
    response = client.get("https://example.com/missing")
except ResilientHTTPError as e:
    print(f"Failed after {e.attempts} attempts, status={e.status}")
```

## TypeScript Usage

```typescript
import { ResilientHTTP, ResilientHTTPError } from "./resilient_http";

// Basic usage with defaults
const client = new ResilientHTTP("my-scraper");
const response = await client.get("https://example.com/api/data");
console.log(response.status, await response.text());

// With query parameters
const response = await client.get("https://api.example.com/search", {
  params: { q: "typescript", page: "1" },
});

// POST with JSON body
const response = await client.post("https://api.example.com/items", {
  jsonBody: { name: "New Item", value: 42 },
});
const data = await response.json();

// Custom configuration
const client = new ResilientHTTP("polite-scraper", {
  maxRetries: 5,
  initialDelay: 0.5,
  backoffMultiplier: 3.0,
  maxDelay: 60,
  timeoutMs: 15_000,
  rateLimitDelayMs: 1000, // 1 request per second
});

// Error handling
try {
  const response = await client.get("https://example.com/missing");
} catch (err) {
  if (err instanceof ResilientHTTPError) {
    console.error(`Failed after ${err.attempts} attempts, status=${err.status}`);
  }
}
```

## Configuration Reference

| Python field | TypeScript field | Default | Description |
|---|---|---|---|
| `max_retries` | `maxRetries` | 3 | Retry attempts after initial request |
| `initial_delay` | `initialDelay` | 1.0 | Base delay (seconds) before first retry |
| `backoff_multiplier` | `backoffMultiplier` | 2.0 | Exponential multiplier per attempt |
| `max_delay` | `maxDelay` | 30.0 | Ceiling for delay (seconds) |
| `timeout` | `timeoutMs` | 30 / 30000 | Per-request timeout (sec / ms) |
| `jitter` | `jitter` | true | Randomize delay to prevent thundering herd |
| `retryable_status_codes` | `retryableStatusCodes` | [429,500,502,503,504] | Status codes that trigger retry |
| `default_headers` | `defaultHeaders` | {} | Headers sent with every request |
| `rate_limit_delay` | `rateLimitDelayMs` | 0 | Min delay between requests (sec / ms) |

## Retry Behavior

1. Initial request fires immediately
2. On retryable failure (429, 5xx, network error), wait `initial_delay * backoff_multiplier^attempt` seconds
3. If server sends `Retry-After` header, use that value instead
4. Jitter adds ±25% randomness to prevent synchronized retries
5. After `max_retries` failures, raises `ResilientHTTPError` with context

## File Structure

```
skills/data-pipeline/resilient-http/
  SKILL.md                            # Skill metadata and triggers
  README.md                           # This file
  python/resilient_http.py            # Python implementation (stdlib only)
  python/test_resilient_http.py       # Python tests
  typescript/resilient_http.ts        # TypeScript implementation (native fetch)
  typescript/test_resilient_http.ts   # TypeScript tests
```
