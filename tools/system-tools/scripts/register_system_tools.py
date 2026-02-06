#!/usr/bin/env python3
"""
Register system tools with Letta server.

Usage:
    python register_system_tools.py
    python register_system_tools.py --server http://localhost:8283
    python register_system_tools.py --list
    python register_system_tools.py --delete
"""

import argparse
import logging
import sys

try:
    import requests
except ImportError:
    print("Error: requests package required. Install with: pip install requests")
    sys.exit(1)

from system_tools import TOOLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_source_code(func) -> str:
    """Get source code from a function."""
    import inspect
    return inspect.getsource(func)


def list_tools(server_url: str) -> bool:
    """List all registered tools."""
    try:
        response = requests.get(f"{server_url}/v1/tools", timeout=30)
        response.raise_for_status()
        tools = response.json()

        logger.info(f"\nRegistered Tools ({len(tools)}):")
        logger.info("-" * 60)

        for tool in sorted(tools, key=lambda t: t.get("name", "")):
            name = tool.get("name", "unknown")
            tags = ", ".join(tool.get("tags", [])) or "none"
            logger.info(f"  {name}")
            logger.info(f"    Tags: {tags}")

        return True

    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Letta server at {server_url}")
        return False
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return False


def register_tools(server_url: str, tools: list = None) -> bool:
    """Register tools via REST API."""
    tools_to_register = tools or list(TOOLS.keys())

    # Get existing tools
    try:
        response = requests.get(f"{server_url}/v1/tools", timeout=30)
        response.raise_for_status()
        existing_tools = {t.get("name") for t in response.json()}
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Letta server at {server_url}")
        return False
    except Exception as e:
        logger.warning(f"Could not list existing tools: {e}")
        existing_tools = set()

    registered = 0
    skipped = 0
    failed = 0

    for tool_name in tools_to_register:
        if tool_name not in TOOLS:
            logger.warning(f"Unknown tool: {tool_name}")
            continue

        if tool_name in existing_tools:
            logger.info(f"  Tool '{tool_name}' already exists (skipping)")
            skipped += 1
            continue

        tool_def = TOOLS[tool_name]

        try:
            # Get source code from the function
            source_code = get_source_code(tool_def["func"])

            payload = {
                "source_code": source_code,
                "tags": tool_def.get("tags", []),
            }

            if "json_schema" in tool_def:
                payload["json_schema"] = tool_def["json_schema"]

            response = requests.post(
                f"{server_url}/v1/tools",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"  Registered: {tool_name} (ID: {result.get('id', 'unknown')})")
            registered += 1

        except Exception as e:
            logger.error(f"  Failed to register {tool_name}: {e}")
            failed += 1

    logger.info(f"\nSummary: {registered} registered, {skipped} skipped, {failed} failed")
    return failed == 0


def delete_tools(server_url: str, tools: list = None) -> bool:
    """Delete tools via REST API."""
    tools_to_delete = tools or list(TOOLS.keys())

    try:
        response = requests.get(f"{server_url}/v1/tools", timeout=30)
        response.raise_for_status()
        existing_tools = {t.get("name"): t.get("id") for t in response.json()}
    except Exception as e:
        logger.error(f"Failed to list existing tools: {e}")
        return False

    deleted = 0
    for tool_name in tools_to_delete:
        if tool_name not in existing_tools:
            continue

        tool_id = existing_tools[tool_name]
        try:
            response = requests.delete(f"{server_url}/v1/tools/{tool_id}", timeout=30)
            response.raise_for_status()
            logger.info(f"  Deleted: {tool_name}")
            deleted += 1
        except Exception as e:
            logger.error(f"  Failed to delete {tool_name}: {e}")

    logger.info(f"\nDeleted {deleted} tools")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Register system tools with Letta server"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8283",
        help="Letta server URL (default: http://localhost:8283)"
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=list(TOOLS.keys()),
        help="Specific tools to register"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing tools"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete tools"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Letta System Tools Registration")
    logger.info("=" * 60)
    logger.info(f"Server: {args.server}")
    logger.info(f"Tools: {list(TOOLS.keys())}")
    logger.info("")

    if args.list:
        success = list_tools(args.server)
    elif args.delete:
        success = delete_tools(args.server, args.tools)
    else:
        success = register_tools(args.server, args.tools)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
