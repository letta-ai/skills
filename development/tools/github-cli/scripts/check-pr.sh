#!/bin/bash
# Check PR CI status
# Usage: check-pr.sh [pr-number] [--watch]

set -e

PR="${1:-}"
WATCH=""

# Parse args
for arg in "$@"; do
    case $arg in
        --watch|-w)
            WATCH="--watch"
            ;;
        [0-9]*)
            if [ -z "$PR" ]; then
                PR="$arg"
            fi
            ;;
    esac
done

if [ -n "$PR" ]; then
    gh pr checks "$PR" "$WATCH"
else
    gh pr checks "$WATCH"
fi
