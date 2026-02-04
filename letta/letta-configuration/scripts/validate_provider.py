#!/usr/bin/env python3
"""
Validate provider credentials and list available models.

Usage:
    python validate_provider.py --provider-id provider-abc123
    python validate_provider.py --provider-id provider-abc123 --server http://localhost:8283
"""

import argparse
import json
import sys

import requests


def validate_provider(provider_id: str, server: str = "http://localhost:8283") -> dict:
    """
    Validate provider credentials via REST API.

    Args:
        provider_id: Provider ID to validate
        server: Letta server URL

    Returns:
        Provider validation result
    """
    # First, get the provider details
    get_endpoint = f"{server}/v1/providers/{provider_id}"

    try:
        print(f"Fetching provider {provider_id}...")
        response = requests.get(get_endpoint, timeout=30)
        response.raise_for_status()
        provider = response.json()

        print(f"✓ Provider found")
        print(f"  Name: {provider['name']}")
        print(f"  Type: {provider['provider_type']}")
        if "base_url" in provider and provider["base_url"]:
            print(f"  Base URL: {provider['base_url']}")

    except requests.exceptions.HTTPError as e:
        print(f"✗ Provider not found: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Now validate the credentials
    check_endpoint = f"{server}/v1/providers/{provider_id}/check"

    try:
        print(f"\nValidating credentials...")
        response = requests.post(check_endpoint, timeout=30)
        response.raise_for_status()

        print(f"✓ Credentials are valid")

    except requests.exceptions.HTTPError as e:
        print(f"✗ Credential validation failed: {e}", file=sys.stderr)
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Detail: {json.dumps(error_detail, indent=2)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"  Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    # List available models
    models_endpoint = f"{server}/v1/models"

    try:
        print(f"\nFetching available models...")
        response = requests.get(
            models_endpoint, params={"provider_category": "byok", "limit": 100}, timeout=30
        )
        response.raise_for_status()
        all_models = response.json()

        # Filter models for this provider
        provider_models = [m for m in all_models if m.get("provider_name") == provider["name"]]

        if provider_models:
            print(f"✓ Found {len(provider_models)} models:")
            for model in provider_models[:10]:  # Show first 10
                print(f"  - {model['model']}")
            if len(provider_models) > 10:
                print(f"  ... and {len(provider_models) - 10} more")
        else:
            print(f"⚠ No models found for this provider")
            print(f"  Try refreshing: curl -X PATCH {server}/v1/providers/{provider_id}/refresh")

        return {"provider": provider, "models": provider_models}

    except requests.exceptions.RequestException as e:
        print(f"⚠ Could not fetch models: {e}", file=sys.stderr)
        return {"provider": provider, "models": []}


def main():
    parser = argparse.ArgumentParser(description="Validate provider credentials")

    parser.add_argument("--provider-id", required=True, help="Provider ID to validate")
    parser.add_argument("--server", default="http://localhost:8283", help="Letta server URL")

    args = parser.parse_args()

    validate_provider(provider_id=args.provider_id, server=args.server)


if __name__ == "__main__":
    main()
