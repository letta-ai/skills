/**
 * Tests for resilient_http.ts
 *
 * Covers acceptance criteria:
 * - Retry on 503
 * - Backoff on 429
 * - Succeed on 200
 *
 * Run with: npx tsx test_resilient_http.ts
 * Or: bun test_resilient_http.ts
 * Or: deno run --allow-net test_resilient_http.ts
 */

import { ResilientHTTP, ResilientHTTPError } from "./resilient_http";
import * as http from "node:http";

// ----- Minimal test framework (no external deps) -----

let passed = 0;
let failed = 0;
const errors: string[] = [];

async function test(name: string, fn: () => Promise<void>): Promise<void> {
  try {
    await fn();
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (err) {
    failed++;
    const msg = err instanceof Error ? err.message : String(err);
    errors.push(`${name}: ${msg}`);
    console.log(`  ✗ ${name} — ${msg}`);
  }
}

function assert(condition: boolean, msg: string): void {
  if (!condition) throw new Error(`Assertion failed: ${msg}`);
}

function assertEqual<T>(actual: T, expected: T, msg?: string): void {
  if (actual !== expected) {
    throw new Error(
      `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}${msg ? ` — ${msg}` : ""}`,
    );
  }
}

function assertGreaterOrEqual(actual: number, expected: number, msg?: string): void {
  if (actual < expected) {
    throw new Error(
      `Expected ${actual} >= ${expected}${msg ? ` — ${msg}` : ""}`,
    );
  }
}

// ----- Mock server -----

type Scenario = Array<{
  status: number;
  headers?: Record<string, string>;
  body?: string;
}>;

function createMockServer(scenario: Scenario): Promise<{ server: http.Server; url: string }> {
  return new Promise((resolve) => {
    let idx = 0;
    const server = http.createServer((req, res) => {
      const step = idx < scenario.length ? scenario[idx++] : { status: 200, body: '{"ok":true}' };
      const hdrs = step.headers ?? {};
      res.writeHead(step.status, hdrs);
      res.end(step.body ?? "");
    });
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address();
      if (addr && typeof addr === "object") {
        resolve({ server, url: `http://127.0.0.1:${addr.port}` });
      }
    });
  });
}

// ----- Tests -----

async function run(): Promise<void> {
  console.log("\nResilient HTTP — TypeScript Tests\n");

  // --- 200 Success ---
  await test("GET 200 succeeds without retries", async () => {
    const { server, url } = await createMockServer([
      { status: 200, body: '{"status":"ok"}' },
    ]);
    try {
      const client = new ResilientHTTP("test", { jitter: false });
      const resp = await client.get(url);
      assertEqual(resp.status, 200);
      const data = (await resp.json()) as { status: string };
      assertEqual(data.status, "ok");
    } finally {
      server.close();
    }
  });

  await test("POST with JSON body succeeds", async () => {
    const { server, url } = await createMockServer([
      { status: 200, body: '{"created":true}' },
    ]);
    try {
      const client = new ResilientHTTP("test", { jitter: false });
      const resp = await client.post(url, { jsonBody: { name: "test" } });
      assertEqual(resp.status, 200);
      const data = (await resp.json()) as { created: boolean };
      assertEqual(data.created, true);
    } finally {
      server.close();
    }
  });

  // --- 503 Retry ---
  await test("retries on 503 then succeeds", async () => {
    const { server, url } = await createMockServer([
      { status: 503, body: "down" },
      { status: 503, body: "down" },
      { status: 200, body: '{"recovered":true}' },
    ]);
    try {
      const client = new ResilientHTTP("test-503", {
        maxRetries: 3,
        initialDelay: 0.01,
        backoffMultiplier: 1.0,
        jitter: false,
      });
      const resp = await client.get(url);
      assertEqual(resp.status, 200);
      const data = (await resp.json()) as { recovered: boolean };
      assertEqual(data.recovered, true);
    } finally {
      server.close();
    }
  });

  await test("exhausts retries on persistent 503", async () => {
    const { server, url } = await createMockServer([
      { status: 503, body: "down" },
      { status: 503, body: "down" },
      { status: 503, body: "down" },
      { status: 503, body: "down" },
    ]);
    try {
      const client = new ResilientHTTP("test-503-exhaust", {
        maxRetries: 3,
        initialDelay: 0.01,
        backoffMultiplier: 1.0,
        jitter: false,
      });
      let caught = false;
      try {
        await client.get(url);
      } catch (err) {
        caught = true;
        assert(err instanceof ResilientHTTPError, "should be ResilientHTTPError");
        assertEqual(err.status, 503);
        assertEqual(err.attempts, 4);
      }
      assert(caught, "should have thrown");
    } finally {
      server.close();
    }
  });

  // --- 429 Backoff ---
  await test("429 with Retry-After header waits", async () => {
    const { server, url } = await createMockServer([
      { status: 429, headers: { "Retry-After": "0.05" }, body: "rate limited" },
      { status: 200, body: '{"ok":true}' },
    ]);
    try {
      const client = new ResilientHTTP("test-429", {
        maxRetries: 2,
        initialDelay: 0.01,
        jitter: false,
      });
      const start = Date.now();
      const resp = await client.get(url);
      const elapsed = (Date.now() - start) / 1000;
      assertEqual(resp.status, 200);
      assertGreaterOrEqual(elapsed, 0.04, "should wait for Retry-After");
    } finally {
      server.close();
    }
  });

  await test("429 uses exponential backoff", async () => {
    const { server, url } = await createMockServer([
      { status: 429, body: "rate limited" },
      { status: 429, body: "rate limited" },
      { status: 200, body: '{"ok":true}' },
    ]);
    try {
      const client = new ResilientHTTP("test-backoff", {
        maxRetries: 3,
        initialDelay: 0.05,
        backoffMultiplier: 2.0,
        jitter: false,
      });
      const start = Date.now();
      const resp = await client.get(url);
      const elapsed = (Date.now() - start) / 1000;
      assertEqual(resp.status, 200);
      // attempt 0 = 0.05s, attempt 1 = 0.10s → total ~0.15s
      assertGreaterOrEqual(elapsed, 0.12, "should have exponential backoff");
    } finally {
      server.close();
    }
  });

  // --- Non-retryable errors ---
  await test("404 fails immediately", async () => {
    const { server, url } = await createMockServer([
      { status: 404, body: "not found" },
    ]);
    try {
      const client = new ResilientHTTP("test-404", {
        maxRetries: 3,
        initialDelay: 0.01,
        jitter: false,
      });
      let caught = false;
      try {
        await client.get(url);
      } catch (err) {
        caught = true;
        assert(err instanceof ResilientHTTPError, "should be ResilientHTTPError");
        assertEqual(err.status, 404);
        assertEqual(err.attempts, 1);
      }
      assert(caught, "should have thrown");
    } finally {
      server.close();
    }
  });

  // --- Query params ---
  await test("GET with params appends to URL", async () => {
    const { server, url } = await createMockServer([
      { status: 200, body: "ok" },
    ]);
    try {
      const client = new ResilientHTTP("test", { jitter: false });
      const resp = await client.get(url, { params: { q: "hello", page: "2" } });
      assertEqual(resp.status, 200);
    } finally {
      server.close();
    }
  });

  // --- Source labeling ---
  await test("source is preserved on client", async () => {
    const client = new ResilientHTTP("my-crawler");
    assertEqual(client.source, "my-crawler");
  });

  // --- Summary ---
  console.log(`\n${passed} passed, ${failed} failed\n`);
  if (errors.length > 0) {
    console.log("Failures:");
    for (const e of errors) console.log(`  - ${e}`);
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("Test runner error:", err);
  process.exit(1);
});
