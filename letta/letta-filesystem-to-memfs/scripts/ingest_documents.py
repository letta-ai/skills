#!/usr/bin/env python3
"""Compatibility wrapper for letta_fs_to_memfs.py ingest."""

from __future__ import annotations

import sys

from letta_fs_to_memfs import main


if __name__ == "__main__":
    raise SystemExit(main(["ingest", *sys.argv[1:]]))
