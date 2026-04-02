/**
 * Resilient HTTP Client for Scrapers (TypeScript)
 *
 * A standalone HTTP client with retry, exponential backoff, rate limiting,
 * and source labeling — designed for web scrapers and data pipelines.
 *
 * Uses native `fetch()` (Node 18+ / Bun / Deno / browsers).
 * Zero external dependencies.
 *
 * @example
 * ```ts
 * import { ResilientHTTP } from "./resilient_http";
 *
 * const client = new ResilientHTTP("my-scraper");
 * const response = await client.get("https://example.com/api/data");
 * console.log(response.status, await response.text());
 * ```
 */

// ----- Configuration -----

/** Status codes that are safe to retry by default. */
const DEFAULT_RETRYABLE_STATUS_CODES: ReadonlySet<number> = new Set([
  429, 500, 502, 503, 504,
]);

export interface HttpConfig {
  /** Maximum retry attempts after initial request (default 3). */
  maxRetries?: number;
  /** Base delay in seconds before first retry (default 1). */
  initialDelay?: number;
  /** Exponential multiplier per attempt (default 2). */
  backoffMultiplier?: number;
  /** Ceiling for computed delay in seconds (default 30). */
  maxDelay?: number;
  /** Per-request timeout in milliseconds (default 30_000). */
  timeoutMs?: number;
  /** Add random jitter to prevent thundering herd (default true). */
  jitter?: boolean;
  /** HTTP status codes that trigger a retry. */
  retryableStatusCodes?: number[];
  /** Headers sent with every request. */
  defaultHeaders?: Record<string, string>;
  /** Minimum milliseconds between consecutive requests (default 0). */
  rateLimitDelayMs?: number;
}

interface ResolvedConfig {
  maxRetries: number;
  initialDelay: number;
  backoffMultiplier: number;
  maxDelay: number;
  timeoutMs: number;
  jitter: boolean;
  retryableStatusCodes: Set<number>;
  defaultHeaders: Record<string, string>;
  rateLimitDelayMs: number;
}

// ----- Response wrapper -----

export interface HttpResponse {
  status: number;
  headers: Headers;
  url: string;
  /** Read body as text. */
  text(): Promise<string>;
  /** Parse body as JSON. */
  json(): Promise<unknown>;
  /** Read body as raw bytes. */
  bytes(): Promise<Uint8Array>;
}

// ----- Error -----

export class ResilientHTTPError extends Error {
  status: number | null;
  attempts: number;
  lastError: Error | null;

  constructor(
    message: string,
    status: number | null = null,
    attempts: number = 0,
    lastError: Error | null = null,
  ) {
    super(message);
    this.name = "ResilientHTTPError";
    this.status = status;
    this.attempts = attempts;
    this.lastError = lastError;
  }
}

// ----- Client -----

export class ResilientHTTP {
  readonly source: string;
  private readonly config: ResolvedConfig;
  private lastRequestTime = 0;

  constructor(source = "resilient-http", config: HttpConfig = {}) {
    this.source = source;
    this.config = {
      maxRetries: config.maxRetries ?? 3,
      initialDelay: config.initialDelay ?? 1,
      backoffMultiplier: config.backoffMultiplier ?? 2,
      maxDelay: config.maxDelay ?? 30,
      timeoutMs: config.timeoutMs ?? 30_000,
      jitter: config.jitter ?? true,
      retryableStatusCodes: new Set(
        config.retryableStatusCodes ?? DEFAULT_RETRYABLE_STATUS_CODES,
      ),
      defaultHeaders: { ...config.defaultHeaders },
      rateLimitDelayMs: config.rateLimitDelayMs ?? 0,
    };
  }

  /** Send a GET request with retry and backoff. */
  async get(
    url: string,
    opts?: { headers?: Record<string, string>; params?: Record<string, string> },
  ): Promise<HttpResponse> {
    let finalUrl = url;
    if (opts?.params) {
      const sep = url.includes("?") ? "&" : "?";
      finalUrl = url + sep + new URLSearchParams(opts.params).toString();
    }
    return this.request("GET", finalUrl, { headers: opts?.headers });
  }

  /** Send a POST request with retry and backoff. */
  async post(
    url: string,
    opts?: {
      headers?: Record<string, string>;
      body?: string;
      jsonBody?: unknown;
    },
  ): Promise<HttpResponse> {
    const headers = { ...opts?.headers };
    let body: string | undefined = opts?.body;
    if (opts?.jsonBody !== undefined) {
      body = JSON.stringify(opts.jsonBody);
      headers["Content-Type"] ??= "application/json";
    }
    return this.request("POST", url, { headers, body });
  }

  // ---- internal -----------------------------------------------------------

  private async request(
    method: string,
    url: string,
    opts: { headers?: Record<string, string>; body?: string },
  ): Promise<HttpResponse> {
    const mergedHeaders: Record<string, string> = {
      ...this.config.defaultHeaders,
      ...opts.headers,
    };
    mergedHeaders["User-Agent"] ??= `ResilientHTTP/${this.source}`;

    let lastError: Error | null = null;
    let lastStatus: number | null = null;
    const totalAttempts = this.config.maxRetries + 1;

    for (let attempt = 0; attempt < totalAttempts; attempt++) {
      await this.enforceRateLimit();

      try {
        const resp = await this.doRequest(method, url, mergedHeaders, opts.body);

        if (attempt > 0) {
          console.log(
            `[${this.source}] ${method} ${url} succeeded after ${attempt} retries (status ${resp.status})`,
          );
        }
        return resp;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));

        if (error instanceof RetryableHTTPError) {
          lastError = error;
          lastStatus = error.status;

          const retryAfter = this.parseRetryAfter(error.headers);
          const delay = this.calculateDelay(attempt, retryAfter);

          console.warn(
            `[${this.source}] ${method} ${url} attempt ${attempt + 1}/${totalAttempts} ` +
              `failed (status ${error.status}). Retrying in ${delay.toFixed(2)}s...`,
          );
          await sleep(delay);
          continue;
        }

        if (error instanceof NonRetryableHTTPError) {
          throw new ResilientHTTPError(
            `HTTP ${error.status} for ${method} ${url}`,
            error.status,
            attempt + 1,
            error,
          );
        }

        // Network / timeout errors
        lastError = error;
        lastStatus = null;

        if (attempt + 1 >= totalAttempts) break;

        const delay = this.calculateDelay(attempt);
        console.warn(
          `[${this.source}] ${method} ${url} attempt ${attempt + 1}/${totalAttempts} ` +
            `network error: ${error.message}. Retrying in ${delay.toFixed(2)}s...`,
        );
        await sleep(delay);
      }
    }

    throw new ResilientHTTPError(
      `All ${totalAttempts} attempts failed for ${method} ${url}`,
      lastStatus,
      totalAttempts,
      lastError,
    );
  }

  private async doRequest(
    method: string,
    url: string,
    headers: Record<string, string>,
    body?: string,
  ): Promise<HttpResponse> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.config.timeoutMs);

    let resp: Response;
    try {
      resp = await fetch(url, {
        method,
        headers,
        body,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if (!resp.ok) {
      if (this.config.retryableStatusCodes.has(resp.status)) {
        throw new RetryableHTTPError(resp.status, resp.headers);
      }
      throw new NonRetryableHTTPError(resp.status);
    }

    // Buffer the body once so consumers can call text()/json()/bytes() freely.
    const buffer = await resp.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    return {
      status: resp.status,
      headers: resp.headers,
      url: resp.url,
      text: () => Promise.resolve(new TextDecoder().decode(bytes)),
      json: () => Promise.resolve(JSON.parse(new TextDecoder().decode(bytes))),
      bytes: () => Promise.resolve(bytes),
    };
  }

  private async enforceRateLimit(): Promise<void> {
    if (this.config.rateLimitDelayMs <= 0) return;
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < this.config.rateLimitDelayMs) {
      await sleep((this.config.rateLimitDelayMs - elapsed) / 1000);
    }
    this.lastRequestTime = Date.now();
  }

  private calculateDelay(attempt: number, retryAfter?: number): number {
    let base: number;
    if (retryAfter !== undefined) {
      base = Math.min(retryAfter, this.config.maxDelay);
    } else {
      base = Math.min(
        this.config.initialDelay * this.config.backoffMultiplier ** attempt,
        this.config.maxDelay,
      );
    }
    if (this.config.jitter) {
      base *= 0.5 + Math.random() * 0.5;
    }
    return base;
  }

  private parseRetryAfter(headers: Headers): number | undefined {
    const val = headers.get("retry-after");
    if (val === null) return undefined;
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : undefined;
  }
}

// ----- Internal helpers (not exported) -----

class RetryableHTTPError extends Error {
  constructor(
    public readonly status: number,
    public readonly headers: Headers,
  ) {
    super(`HTTP ${status}`);
    this.name = "RetryableHTTPError";
  }
}

class NonRetryableHTTPError extends Error {
  constructor(public readonly status: number) {
    super(`HTTP ${status}`);
    this.name = "NonRetryableHTTPError";
  }
}

function sleep(seconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}
