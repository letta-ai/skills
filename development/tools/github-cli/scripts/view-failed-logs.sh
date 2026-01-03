#!/bin/bash
# View failed test logs for a GitHub Actions run or job
# Usage: view-failed-logs.sh <run-id|job-id> [--job]

set -e

ID="${1:?Usage: view-failed-logs.sh <run-id|job-id> [--job]}"
IS_JOB=""

# Check if --job flag is passed
if [ "$2" = "--job" ] || [ "$2" = "-j" ]; then
    IS_JOB="true"
fi

if [ -n "$IS_JOB" ]; then
    # View logs for specific job
    gh run view --job "$ID" --log-failed
else
    # View logs for entire run
    gh run view "$ID" --log-failed
fi
