"""
Resilient HTTP Client for Scrapers

A standalone, generic HTTP client with retry, exponential backoff, rate limiting,
and source labeling — designed for web scrapers and data pipelines.

No project-specific imports. Requires only the Python standard library plus `urllib3`
(optional; falls back to urllib.request if unavailable).

Usage:
    from resilient_http import ResilientHTTP, HttpConfig

    client = ResilientHTTP(source="my-scraper")
    response = client.get("https://example.com/api/data")
    print(response.status, response.text)
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Status codes that are safe to retry
DEFAULT_RETRYABLE_STATUS_CODES: List[int] = [429, 500, 502, 503, 504]


@dataclass
class HttpConfig:
    """Configuration for the resilient HTTP client.

    Attributes:
        max_retries: Maximum retry attempts after initial request (default 3).
        initial_delay: Base delay in seconds before first retry (default 1.0).
        backoff_multiplier: Exponential multiplier per attempt (default 2.0).
        max_delay: Ceiling for computed delay in seconds (default 30.0).
        timeout: Per-request timeout in seconds (default 30).
        jitter: Add random jitter to prevent thundering herd (default True).
        retryable_status_codes: HTTP status codes that trigger a retry.
        default_headers: Headers sent with every request.
        rate_limit_delay: Minimum seconds between consecutive requests (default 0).
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 30.0
    timeout: int = 30
    jitter: bool = True
    retryable_status_codes: List[int] = field(
        default_factory=lambda: list(DEFAULT_RETRYABLE_STATUS_CODES)
    )
    default_headers: Dict[str, str] = field(default_factory=dict)
    rate_limit_delay: float = 0.0


@dataclass
class HttpResponse:
    """Simplified HTTP response wrapper.

    Attributes:
        status: HTTP status code.
        headers: Response headers as a dict.
        body: Raw response bytes.
        url: The final URL (after redirects).
    """

    status: int
    headers: Dict[str, str]
    body: bytes
    url: str

    @property
    def text(self) -> str:
        """Decode body as UTF-8 text."""
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        """Parse body as JSON."""
        return json.loads(self.body)


class ResilientHTTPError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        attempts: int = 0,
        last_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.status = status
        self.attempts = attempts
        self.last_error = last_error


class ResilientHTTP:
    """HTTP client with built-in retry, backoff, rate limiting, and source labeling.

    Args:
        source: Label for this client instance (appears in logs and User-Agent).
        config: Optional HttpConfig; uses defaults if not provided.
    """

    def __init__(
        self, source: str = "resilient-http", config: Optional[HttpConfig] = None
    ):
        self.source = source
        self.config = config or HttpConfig()
        self._last_request_time: float = 0.0

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """Send a GET request with retry and backoff."""
        if params:
            separator = "&" if "?" in url else "?"
            url = url + separator + urlencode(params)
        return self._request("GET", url, headers=headers)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        json_body: Optional[Any] = None,
    ) -> HttpResponse:
        """Send a POST request with retry and backoff."""
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers = dict(headers or {})
            headers.setdefault("Content-Type", "application/json")
        return self._request("POST", url, headers=headers, body=body)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> HttpResponse:
        """Execute an HTTP request with retry, backoff, and rate limiting."""
        merged_headers = dict(self.config.default_headers)
        if headers:
            merged_headers.update(headers)
        merged_headers.setdefault("User-Agent", f"ResilientHTTP/{self.source}")

        last_error: Optional[Exception] = None
        last_status: Optional[int] = None
        attempts = self.config.max_retries + 1  # initial + retries

        for attempt in range(attempts):
            # Rate limiting: enforce minimum delay between requests
            self._enforce_rate_limit()

            try:
                response = self._do_request(method, url, merged_headers, body)

                # Success
                if attempt > 0:
                    logger.info(
                        "[%s] %s %s succeeded after %d retries (status %d)",
                        self.source,
                        method,
                        url,
                        attempt,
                        response.status,
                    )
                return response

            except _RetryableHTTPError as exc:
                last_error = exc
                last_status = exc.status

                retry_after = self._parse_retry_after(exc)
                delay = self._calculate_delay(attempt, retry_after)

                logger.warning(
                    "[%s] %s %s attempt %d/%d failed (status %s). Retrying in %.2fs...",
                    self.source,
                    method,
                    url,
                    attempt + 1,
                    attempts,
                    exc.status,
                    delay,
                )
                time.sleep(delay)

            except _NonRetryableHTTPError as exc:
                logger.error(
                    "[%s] %s %s failed with non-retryable status %d",
                    self.source,
                    method,
                    url,
                    exc.status,
                )
                raise ResilientHTTPError(
                    f"HTTP {exc.status} for {method} {url}",
                    status=exc.status,
                    attempts=attempt + 1,
                    last_error=exc,
                ) from exc

            except (URLError, OSError, TimeoutError) as exc:
                last_error = exc
                last_status = None

                if attempt + 1 >= attempts:
                    break

                delay = self._calculate_delay(attempt)
                logger.warning(
                    "[%s] %s %s attempt %d/%d network error: %s. Retrying in %.2fs...",
                    self.source,
                    method,
                    url,
                    attempt + 1,
                    attempts,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise ResilientHTTPError(
            f"All {attempts} attempts failed for {method} {url}",
            status=last_status,
            attempts=attempts,
            last_error=last_error,
        )

    def _do_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[bytes],
    ) -> HttpResponse:
        """Execute a single HTTP request via urllib."""
        req = Request(url, data=body, headers=headers, method=method)
        try:
            resp = urlopen(req, timeout=self.config.timeout)  # noqa: S310
            resp_headers = {k.lower(): v for k, v in resp.getheaders()}
            return HttpResponse(
                status=resp.status,
                headers=resp_headers,
                body=resp.read(),
                url=resp.url,
            )
        except HTTPError as exc:
            if exc.code in self.config.retryable_status_codes:
                resp_headers = {k.lower(): v for k, v in exc.headers.items()}
                raise _RetryableHTTPError(exc.code, resp_headers) from exc
            raise _NonRetryableHTTPError(exc.code) from exc

    def _enforce_rate_limit(self) -> None:
        """Wait if needed to respect rate_limit_delay."""
        if self.config.rate_limit_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    def _calculate_delay(
        self, attempt: int, retry_after: Optional[float] = None
    ) -> float:
        """Compute delay with exponential backoff and optional jitter."""
        if retry_after is not None:
            base = min(retry_after, self.config.max_delay)
        else:
            base = min(
                self.config.initial_delay * (self.config.backoff_multiplier**attempt),
                self.config.max_delay,
            )
        if self.config.jitter:
            base *= 0.5 + random.random() * 0.5  # noqa: S311
        return base

    @staticmethod
    def _parse_retry_after(exc: _RetryableHTTPError) -> Optional[float]:
        """Extract Retry-After header value if present."""
        val = exc.headers.get("retry-after")
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None


# ------------------------------------------------------------------
# Internal exception helpers (not exported)
# ------------------------------------------------------------------


class _RetryableHTTPError(Exception):
    """HTTP error with a retryable status code."""

    def __init__(self, status: int, headers: Dict[str, str]):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.headers = headers


class _NonRetryableHTTPError(Exception):
    """HTTP error with a non-retryable status code."""

    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.status = status
