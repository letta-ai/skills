#!/usr/bin/env python3
"""Generate images and manage visual identities.

Supports two providers:
  - OpenAI (gpt-image-1 via /v1/images/generations and /v1/images/edits)
  - Flux (BFL Kontext Pro via api.bfl.ai)

Provider is auto-detected from environment variables:
  OPENAI_API_KEY -> OpenAI (preferred)
  BFL_API_KEY    -> Flux (fallback)

Override with --provider openai|flux.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ──────────────────────────────────────────────────────

FLUX_API_BASE = "https://api.bfl.ai/v1"
OPENAI_API_BASE = "https://api.openai.com/v1"

DEFAULT_ASPECT_RATIO = "3:4"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_POLL_TIMEOUT = 300.0
DEFAULT_SAFETY_TOLERANCE = 2

ALLOWED_ASPECT_RATIOS = {"1:1", "3:4", "4:3", "16:9", "9:16"}
ALLOWED_OUTPUT_FORMATS = {"jpeg", "png", "webp"}
FORMAT_EXTENSIONS = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}

# Map aspect ratios to OpenAI size strings.
ASPECT_TO_OPENAI_SIZE = {
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
}


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


# ── Provider detection ─────────────────────────────────────────────


def _detect_provider(explicit: Optional[str], dry_run: bool) -> str:
    """Return 'openai' or 'flux' based on explicit choice or env vars."""
    if explicit:
        if explicit not in ("openai", "flux"):
            _die(f"--provider must be 'openai' or 'flux', got '{explicit}'")
        return explicit
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("BFL_API_KEY", "").strip():
        return "flux"
    if dry_run:
        return "openai"
    _die(
        "No image generation API key found.\n"
        "  Set OPENAI_API_KEY (recommended) or BFL_API_KEY.\n"
        "  Or use --provider to choose explicitly."
    )
    return ""


def _get_api_key(provider: str, dry_run: bool) -> str:
    env_var = "OPENAI_API_KEY" if provider == "openai" else "BFL_API_KEY"
    key = os.getenv(env_var, "").strip()
    if key:
        return key
    if dry_run:
        print(f"{env_var} is not set; dry-run only.", file=sys.stderr)
        return ""
    _die(f"{env_var} is not set.")
    return ""


# ── Shared helpers ─────────────────────────────────────────────────


def _encode_image(path: str) -> str:
    """Read an image file and return its base64-encoded contents."""
    p = Path(path)
    if not p.exists():
        _die(f"Image not found: {p}")
    data = p.read_bytes()
    if len(data) > 10 * 1024 * 1024:
        _die(f"Image too large ({len(data) // (1024*1024)}MB). Resize to under 10MB.")
    return base64.b64encode(data).decode()


def _normalize_out_path(out: Optional[str], fmt: str) -> Path:
    if not out:
        ext = FORMAT_EXTENSIONS.get(fmt, ".png")
        return Path(f"output{ext}")
    path = Path(out)
    if path.suffix == "":
        ext = FORMAT_EXTENSIONS.get(fmt, ".png")
        return path.with_suffix(ext)
    return path


def _save_image(data: bytes, out_path: Path, *, force: bool) -> None:
    if out_path.exists() and not force:
        _die(f"Output exists: {out_path} (use --force to overwrite)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"Wrote {out_path} ({len(data) // 1024}KB)")


# ── OpenAI backend ─────────────────────────────────────────────────


def _openai_generate(
    api_key: str,
    prompt: str,
    *,
    aspect_ratio: str,
    output_format: str,
    quality: str = "medium",
) -> bytes:
    """Text-to-image via OpenAI /v1/images/generations."""
    import requests

    size = ASPECT_TO_OPENAI_SIZE.get(aspect_ratio, "1024x1024")
    payload: Dict[str, Any] = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
    }
    if output_format in ("png", "jpeg", "webp"):
        payload["output_format"] = output_format

    print("Generating image via OpenAI...", file=sys.stderr)
    resp = requests.post(
        f"{OPENAI_API_BASE}/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        _die(f"OpenAI API returned {resp.status_code}: {detail}")

    result = resp.json()
    b64 = result.get("data", [{}])[0].get("b64_json")
    if not b64:
        _die(f"No image data in response: {json.dumps(result, indent=2)}")
    return base64.b64decode(b64)


def _openai_edit(
    api_key: str,
    prompt: str,
    reference_path: str,
    *,
    aspect_ratio: str,
    output_format: str,
    quality: str = "medium",
) -> bytes:
    """Reference-based editing via OpenAI /v1/images/edits (multipart)."""
    import requests

    size = ASPECT_TO_OPENAI_SIZE.get(aspect_ratio, "1024x1024")
    ref = Path(reference_path)
    if not ref.exists():
        _die(f"Reference image not found: {ref}")

    print(f"Editing image via OpenAI (reference: {ref})...", file=sys.stderr)
    with open(ref, "rb") as f:
        resp = requests.post(
            f"{OPENAI_API_BASE}/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            files=[("image[]", (ref.name, f, "image/png"))],
            data={
                "model": "gpt-image-1",
                "prompt": prompt,
                "n": "1",
                "size": size,
                "quality": quality,
            },
            timeout=120,
        )

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        _die(f"OpenAI API returned {resp.status_code}: {detail}")

    result = resp.json()
    b64 = result.get("data", [{}])[0].get("b64_json")
    if not b64:
        _die(f"No image data in response: {json.dumps(result, indent=2)}")
    return base64.b64decode(b64)


# ── Flux backend ───────────────────────────────────────────────────


def _flux_submit(api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit an image generation request to the Flux Kontext Pro API."""
    import requests

    headers = {
        "accept": "application/json",
        "x-key": api_key,
        "Content-Type": "application/json",
    }
    resp = requests.post(
        f"{FLUX_API_BASE}/flux-kontext-pro",
        headers=headers,
        json=payload,
        timeout=30,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        _die(f"Flux API returned {resp.status_code}: {detail}")
    return resp.json()


def _flux_poll(
    api_key: str,
    polling_url: str,
    request_id: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_POLL_TIMEOUT,
) -> Dict[str, Any]:
    """Poll the Flux status endpoint until Ready or timeout."""
    import requests

    headers = {"accept": "application/json", "x-key": api_key}
    start = time.time()
    last_status = None

    while True:
        result = requests.get(
            polling_url,
            headers=headers,
            params={"id": request_id},
            timeout=15,
        ).json()

        status = result.get("status", "unknown")
        if status != last_status:
            print(f"Status: {status}", file=sys.stderr)
            last_status = status

        if status == "Ready":
            return result
        if status in ("Error", "Failed"):
            _die(f"Generation failed: {json.dumps(result, indent=2)}")

        elapsed = time.time() - start
        if elapsed > timeout:
            _die(f"Timed out after {timeout:.0f}s waiting for request {request_id}")

        time.sleep(poll_interval)


def _flux_download(result: Dict[str, Any]) -> bytes:
    """Download the generated image from a Flux result URL."""
    import requests

    sample_url = result.get("result", {}).get("sample")
    if not sample_url:
        _die("No sample URL in Flux result")
    return requests.get(sample_url, timeout=60).content


def _flux_generate(
    api_key: str,
    prompt: str,
    *,
    aspect_ratio: str,
    output_format: str,
    seed: Optional[int] = None,
    safety_tolerance: int = DEFAULT_SAFETY_TOLERANCE,
    guidance: Optional[float] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_POLL_TIMEOUT,
) -> bytes:
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "safety_tolerance": safety_tolerance,
    }
    if seed is not None:
        payload["seed"] = seed
    if guidance is not None:
        payload["guidance"] = guidance

    print("Generating image via Flux...", file=sys.stderr)
    resp = _flux_submit(api_key, payload)
    request_id = resp.get("id")
    polling_url = resp.get("polling_url")
    if not polling_url:
        _die(f"No polling_url in response: {json.dumps(resp, indent=2)}")

    result = _flux_poll(
        api_key, polling_url, request_id,
        poll_interval=poll_interval, timeout=timeout,
    )
    return _flux_download(result)


def _flux_edit(
    api_key: str,
    prompt: str,
    reference_path: str,
    *,
    aspect_ratio: str,
    output_format: str,
    seed: Optional[int] = None,
    safety_tolerance: int = DEFAULT_SAFETY_TOLERANCE,
    guidance: Optional[float] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_POLL_TIMEOUT,
) -> bytes:
    img_b64 = _encode_image(reference_path)
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "input_image": img_b64,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "safety_tolerance": safety_tolerance,
    }
    if seed is not None:
        payload["seed"] = seed
    if guidance is not None:
        payload["guidance"] = guidance

    print(f"Generating image via Flux (reference: {reference_path})...", file=sys.stderr)
    resp = _flux_submit(api_key, payload)
    request_id = resp.get("id")
    polling_url = resp.get("polling_url")
    if not polling_url:
        _die(f"No polling_url in response: {json.dumps(resp, indent=2)}")

    result = _flux_poll(
        api_key, polling_url, request_id,
        poll_interval=poll_interval, timeout=timeout,
    )
    return _flux_download(result)


# ── Commands ───────────────────────────────────────────────────────


def _cmd_generate(args: argparse.Namespace) -> int:
    """Text-to-image generation."""
    provider = _detect_provider(args.provider, args.dry_run)
    api_key = _get_api_key(provider, args.dry_run)
    prompt = args.prompt.strip()
    if not prompt:
        _die("--prompt is required")

    aspect_ratio = args.aspect_ratio
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        _die(f"--aspect-ratio must be one of: {', '.join(sorted(ALLOWED_ASPECT_RATIOS))}")

    output_format = args.output_format
    out_path = _normalize_out_path(args.out, output_format)

    if args.dry_run:
        print(json.dumps({"provider": provider, "mode": "generate", "prompt": prompt,
                           "aspect_ratio": aspect_ratio, "output_format": output_format}, indent=2))
        return 0

    if provider == "openai":
        img_data = _openai_generate(
            api_key, prompt,
            aspect_ratio=aspect_ratio,
            output_format=output_format,
            quality=args.quality,
        )
    else:
        img_data = _flux_generate(
            api_key, prompt,
            aspect_ratio=aspect_ratio,
            output_format=output_format,
            seed=args.seed,
            safety_tolerance=args.safety_tolerance,
            guidance=args.guidance,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

    _save_image(img_data, out_path, force=args.force)
    return 0


def _cmd_edit(args: argparse.Namespace) -> int:
    """Reference-based generation for visual identity."""
    provider = _detect_provider(args.provider, args.dry_run)
    api_key = _get_api_key(provider, args.dry_run)
    prompt = args.prompt.strip()
    if not prompt:
        _die("--prompt is required")
    if not args.reference:
        _die("--reference is required for edit mode")

    aspect_ratio = args.aspect_ratio
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        _die(f"--aspect-ratio must be one of: {', '.join(sorted(ALLOWED_ASPECT_RATIOS))}")

    output_format = args.output_format
    out_path = _normalize_out_path(args.out, output_format)

    if args.dry_run:
        print(json.dumps({"provider": provider, "mode": "edit", "prompt": prompt,
                           "reference": args.reference, "aspect_ratio": aspect_ratio,
                           "output_format": output_format}, indent=2))
        return 0

    if provider == "openai":
        img_data = _openai_edit(
            api_key, prompt, args.reference,
            aspect_ratio=aspect_ratio,
            output_format=output_format,
            quality=args.quality,
        )
    else:
        img_data = _flux_edit(
            api_key, prompt, args.reference,
            aspect_ratio=aspect_ratio,
            output_format=output_format,
            seed=args.seed,
            safety_tolerance=args.safety_tolerance,
            guidance=args.guidance,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

    _save_image(img_data, out_path, force=args.force)
    return 0


# ── CLI ────────────────────────────────────────────────────────────


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", required=True, help="Image description")
    parser.add_argument("--out", help="Output file path")
    parser.add_argument("--provider", choices=["openai", "flux"], default=None,
                        help="Image provider (auto-detected from env vars if omitted)")
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO,
                        help=f"Aspect ratio ({', '.join(sorted(ALLOWED_ASPECT_RATIOS))})")
    parser.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT,
                        help="Output format (png, jpeg, webp)")
    parser.add_argument("--quality", default="medium",
                        help="Image quality: low, medium, high (OpenAI only)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility (Flux only)")
    parser.add_argument("--safety-tolerance", type=int, default=DEFAULT_SAFETY_TOLERANCE,
                        help="Safety filter tolerance 0-6 (Flux only)")
    parser.add_argument("--guidance", type=float, default=None,
                        help="Prompt adherence strength 1.5-100 (Flux only)")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL,
                        help="Seconds between status polls (Flux only)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_POLL_TIMEOUT,
                        help="Max seconds to wait for generation (Flux only)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing output file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print request payload without sending")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate images for visual identity workflows"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate", help="Text-to-image generation"
    )
    _add_common_args(gen_parser)
    gen_parser.set_defaults(func=_cmd_generate)

    edit_parser = subparsers.add_parser(
        "edit", help="Reference-based generation (visual identity)"
    )
    _add_common_args(edit_parser)
    edit_parser.add_argument(
        "--reference", required=True,
        help="Path to reference image for character consistency"
    )
    edit_parser.set_defaults(func=_cmd_edit)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
