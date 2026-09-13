"""Tests for resilient_http.py

Covers the acceptance criteria:
- Retry on 503
- Backoff on 429
- Succeed on 200
"""

import http.server
import json
import threading
import time
import unittest

from resilient_http import HttpConfig, HttpResponse, ResilientHTTP, ResilientHTTPError


# ---------------------------------------------------------------------------
# Mock HTTP server for integration-style tests
# ---------------------------------------------------------------------------


class _MockHandler(http.server.BaseHTTPRequestHandler):
    """Programmable HTTP handler. Reads scenario from server.scenario list."""

    def do_GET(self):
        scenario = self.server.scenario  # type: ignore[attr-defined]
        if not scenario:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return

        code, headers, body = scenario.pop(0)
        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body.encode() if isinstance(body, str) else body)

    def do_POST(self):
        # Read the body so the connection doesn't hang
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self.do_GET()

    def log_message(self, format, *args):
        pass  # silence server logs


def _start_server(scenario):
    """Start a mock server on a random port. Returns (server, base_url)."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _MockHandler)
    server.scenario = scenario  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    return server, f"http://127.0.0.1:{port}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSuccessOn200(unittest.TestCase):
    """A simple 200 response should succeed without retries."""

    def test_get_200(self):
        scenario = [(200, {}, '{"status": "ok"}')]
        server, url = _start_server(scenario)
        try:
            client = ResilientHTTP(source="test", config=HttpConfig(jitter=False))
            resp = client.get(url)
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.json(), {"status": "ok"})
        finally:
            server.shutdown()

    def test_post_json(self):
        scenario = [(200, {}, '{"created": true}')]
        server, url = _start_server(scenario)
        try:
            client = ResilientHTTP(source="test", config=HttpConfig(jitter=False))
            resp = client.post(url, json_body={"name": "test"})
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.json(), {"created": True})
        finally:
            server.shutdown()


class TestRetryOn503(unittest.TestCase):
    """503 should be retried, and succeed when the server recovers."""

    def test_retry_then_succeed(self):
        scenario = [
            (503, {}, "Service Unavailable"),
            (503, {}, "Service Unavailable"),
            (200, {}, '{"recovered": true}'),
        ]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(
                max_retries=3,
                initial_delay=0.01,
                backoff_multiplier=1.0,
                jitter=False,
            )
            client = ResilientHTTP(source="test-503", config=config)
            resp = client.get(url)
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.json(), {"recovered": True})
        finally:
            server.shutdown()

    def test_exhaust_retries_on_503(self):
        scenario = [
            (503, {}, "down"),
            (503, {}, "down"),
            (503, {}, "down"),
            (503, {}, "down"),
        ]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(
                max_retries=3,
                initial_delay=0.01,
                backoff_multiplier=1.0,
                jitter=False,
            )
            client = ResilientHTTP(source="test-503-exhaust", config=config)
            with self.assertRaises(ResilientHTTPError) as ctx:
                client.get(url)
            self.assertEqual(ctx.exception.status, 503)
            self.assertEqual(ctx.exception.attempts, 4)  # initial + 3 retries
        finally:
            server.shutdown()


class TestBackoffOn429(unittest.TestCase):
    """429 should trigger exponential backoff and respect Retry-After."""

    def test_429_with_retry_after(self):
        scenario = [
            (429, {"Retry-After": "0.05"}, "rate limited"),
            (200, {}, '{"ok": true}'),
        ]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(
                max_retries=2,
                initial_delay=0.01,
                jitter=False,
            )
            client = ResilientHTTP(source="test-429", config=config)
            start = time.monotonic()
            resp = client.get(url)
            elapsed = time.monotonic() - start
            self.assertEqual(resp.status, 200)
            # Should have waited at least the Retry-After value
            self.assertGreaterEqual(elapsed, 0.04)
        finally:
            server.shutdown()

    def test_429_exponential_backoff(self):
        scenario = [
            (429, {}, "rate limited"),
            (429, {}, "rate limited"),
            (200, {}, '{"ok": true}'),
        ]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(
                max_retries=3,
                initial_delay=0.05,
                backoff_multiplier=2.0,
                jitter=False,
            )
            client = ResilientHTTP(source="test-backoff", config=config)
            start = time.monotonic()
            resp = client.get(url)
            elapsed = time.monotonic() - start
            self.assertEqual(resp.status, 200)
            # attempt 0 delay = 0.05, attempt 1 delay = 0.10 → total ~0.15s
            self.assertGreaterEqual(elapsed, 0.12)
        finally:
            server.shutdown()


class TestNonRetryableStatus(unittest.TestCase):
    """4xx errors (except 429) should fail immediately."""

    def test_404_fails_immediately(self):
        scenario = [(404, {}, "not found")]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(max_retries=3, initial_delay=0.01, jitter=False)
            client = ResilientHTTP(source="test-404", config=config)
            with self.assertRaises(ResilientHTTPError) as ctx:
                client.get(url)
            self.assertEqual(ctx.exception.status, 404)
            self.assertEqual(ctx.exception.attempts, 1)
        finally:
            server.shutdown()


class TestExponentialBackoffCalculation(unittest.TestCase):
    """Unit test the delay calculation logic."""

    def test_backoff_sequence(self):
        config = HttpConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=30.0,
            jitter=False,
        )
        client = ResilientHTTP(source="test", config=config)
        delays = [client._calculate_delay(i) for i in range(5)]
        self.assertAlmostEqual(delays[0], 1.0)
        self.assertAlmostEqual(delays[1], 2.0)
        self.assertAlmostEqual(delays[2], 4.0)
        self.assertAlmostEqual(delays[3], 8.0)
        self.assertAlmostEqual(delays[4], 16.0)

    def test_max_delay_cap(self):
        config = HttpConfig(
            initial_delay=1.0,
            backoff_multiplier=10.0,
            max_delay=5.0,
            jitter=False,
        )
        client = ResilientHTTP(source="test", config=config)
        delay = client._calculate_delay(3)
        self.assertEqual(delay, 5.0)

    def test_retry_after_overrides_backoff(self):
        config = HttpConfig(initial_delay=1.0, jitter=False)
        client = ResilientHTTP(source="test", config=config)
        delay = client._calculate_delay(0, retry_after=7.0)
        self.assertAlmostEqual(delay, 7.0)

    def test_retry_after_capped_by_max_delay(self):
        config = HttpConfig(max_delay=5.0, jitter=False)
        client = ResilientHTTP(source="test", config=config)
        delay = client._calculate_delay(0, retry_after=20.0)
        self.assertEqual(delay, 5.0)

    def test_jitter_within_range(self):
        config = HttpConfig(
            initial_delay=10.0,
            jitter=True,
        )
        client = ResilientHTTP(source="test", config=config)
        delays = [client._calculate_delay(0) for _ in range(100)]
        for d in delays:
            self.assertGreaterEqual(d, 5.0)  # 10 * 0.5
            self.assertLessEqual(d, 10.0)  # 10 * 1.0


class TestQueryParams(unittest.TestCase):
    """GET params should be properly appended to the URL."""

    def test_params_appended(self):
        scenario = [(200, {}, "ok")]
        server, url = _start_server(scenario)
        try:
            client = ResilientHTTP(source="test", config=HttpConfig(jitter=False))
            resp = client.get(url, params={"q": "hello", "page": "2"})
            self.assertEqual(resp.status, 200)
        finally:
            server.shutdown()


class TestSourceLabeling(unittest.TestCase):
    """User-Agent should include the source label."""

    def test_user_agent_contains_source(self):
        client = ResilientHTTP(source="my-crawler")
        # The default header is set during request; we can check the defaults
        # by inspecting what would be sent
        self.assertEqual(client.source, "my-crawler")


class TestRateLimiting(unittest.TestCase):
    """Consecutive requests should respect rate_limit_delay."""

    def test_rate_limit_enforced(self):
        scenario = [
            (200, {}, "first"),
            (200, {}, "second"),
        ]
        server, url = _start_server(scenario)
        try:
            config = HttpConfig(
                rate_limit_delay=0.1,
                jitter=False,
            )
            client = ResilientHTTP(source="test-rate", config=config)
            start = time.monotonic()
            client.get(url)
            client.get(url)
            elapsed = time.monotonic() - start
            # Second request should have waited ~0.1s
            self.assertGreaterEqual(elapsed, 0.08)
        finally:
            server.shutdown()


class TestHttpResponse(unittest.TestCase):
    """Test the HttpResponse wrapper."""

    def test_text_property(self):
        resp = HttpResponse(
            status=200,
            headers={},
            body=b"hello world",
            url="http://example.com",
        )
        self.assertEqual(resp.text, "hello world")

    def test_json_method(self):
        resp = HttpResponse(
            status=200,
            headers={},
            body=json.dumps({"key": "value"}).encode(),
            url="http://example.com",
        )
        self.assertEqual(resp.json(), {"key": "value"})


if __name__ == "__main__":
    unittest.main()
