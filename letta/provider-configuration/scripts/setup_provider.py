#!/usr/bin/env python3
"""
Add a provider to Letta via REST API.

Usage:
    python setup_provider.py --type openai --api-key sk-...
    python setup_provider.py --type azure --api-key xxx --base-url https://resource.openai.azure.com --api-version 2024-09-01-preview
    python setup_provider.py --type ollama --api-key ollama --base-url http://localhost:11434
"""

import argparse
import json
import sys

import requests


def setup_provider(
    provider_type: str,
    api_key: str,
    name: str | None = None,
    base_url: str | None = None,
    api_version: str | None = None,
    region: str | None = None,
    access_key: str | None = None,
    server: str = "http://localhost:8283",
) -> dict:
    """
    Add a provider via REST API.

    Args:
        provider_type: Provider type (openai, anthropic, azure, etc.)
        api_key: API key for authentication
        name: Display name (defaults to provider_type)
        base_url: Custom endpoint URL
        api_version: API version (for Azure)
        region: Region (for Bedrock)
        access_key: Access key (for AWS)
        server: Letta server URL

    Returns:
        Provider object from API response
    """
    endpoint = f"{server}/v1/providers"

    payload = {
        "name": name or provider_type.title(),
        "provider_type": provider_type,
        "api_key": api_key,
    }

    # Add optional fields
    if base_url:
        payload["base_url"] = base_url
    if api_version:
        payload["api_version"] = api_version
    if region:
        payload["region"] = region
    if access_key:
        payload["access_key"] = access_key

    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        provider = response.json()

        print(f"✓ Provider created successfully")
        print(f"  ID: {provider['id']}")
        print(f"  Name: {provider['name']}")
        print(f"  Type: {provider['provider_type']}")
        if "base_url" in provider and provider["base_url"]:
            print(f"  Base URL: {provider['base_url']}")

        return provider

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}", file=sys.stderr)
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


def main():
    parser = argparse.ArgumentParser(description="Add a provider to Letta via REST API")

    # Required arguments
    parser.add_argument("--type", required=True, help="Provider type (openai, anthropic, azure, ollama, etc.)")
    parser.add_argument("--api-key", required=True, help="API key for the provider")

    # Optional arguments
    parser.add_argument("--name", help="Display name for the provider (defaults to provider type)")
    parser.add_argument("--base-url", help="Custom endpoint URL (for Azure, Ollama, etc.)")
    parser.add_argument("--api-version", help="API version (for Azure)")
    parser.add_argument("--region", help="Region (for AWS Bedrock)")
    parser.add_argument("--access-key", help="Access key (for AWS)")
    parser.add_argument("--server", default="http://localhost:8283", help="Letta server URL")

    args = parser.parse_args()

    setup_provider(
        provider_type=args.type,
        api_key=args.api_key,
        name=args.name,
        base_url=args.base_url,
        api_version=args.api_version,
        region=args.region,
        access_key=args.access_key,
        server=args.server,
    )


if __name__ == "__main__":
    main()
