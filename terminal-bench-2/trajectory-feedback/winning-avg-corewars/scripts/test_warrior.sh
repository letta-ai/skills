#!/bin/bash
# CoreWars Warrior Test Script
# Runs a warrior against all opponents and reports win rates
#
# Usage: ./test_warrior.sh <warrior.red> [rounds] [opponents_dir]
#
# Arguments:
#   warrior.red   - Path to the warrior file to test
#   rounds        - Number of rounds per opponent (default: 100)
#   opponents_dir - Directory containing opponent .red files (default: current dir)
#
# Output: Win percentages against each opponent with pass/fail indicators

set -e

WARRIOR="${1:?Error: Provide warrior file as first argument}"
ROUNDS="${2:-100}"
OPPONENTS_DIR="${3:-.}"

if [ ! -f "$WARRIOR" ]; then
    echo "Error: Warrior file not found: $WARRIOR"
    exit 1
fi

echo "=================================================="
echo "Testing: $WARRIOR"
echo "Rounds per opponent: $ROUNDS"
echo "Opponents directory: $OPPONENTS_DIR"
echo "=================================================="
echo ""

# Find all .red files except the warrior itself
OPPONENTS=$(find "$OPPONENTS_DIR" -maxdepth 1 -name "*.red" ! -name "$(basename "$WARRIOR")" -type f 2>/dev/null | sort)

if [ -z "$OPPONENTS" ]; then
    echo "No opponent .red files found in $OPPONENTS_DIR"
    exit 1
fi

# Track overall results
TOTAL_OPPONENTS=0
TESTS_PASSED=0

echo "| Opponent | Wins | Losses | Ties | Win% |"
echo "|----------|------|--------|------|------|"

for OPPONENT in $OPPONENTS; do
    OPPONENT_NAME=$(basename "$OPPONENT")

    # Run pmars and capture output
    # Output format varies but typically shows W1 L1 T1 W2 L2 T2
    RESULT=$(pmars -r "$ROUNDS" "$WARRIOR" "$OPPONENT" 2>&1 | tail -1)

    # Parse results - pmars output: "warrior1 W L T  warrior2 W L T"
    # The first warrior's stats are wins/losses/ties from its perspective
    WINS=$(echo "$RESULT" | awk '{print $2}')
    LOSSES=$(echo "$RESULT" | awk '{print $3}')
    TIES=$(echo "$RESULT" | awk '{print $4}')

    # Calculate win percentage
    if [ "$ROUNDS" -gt 0 ]; then
        WIN_PCT=$(echo "scale=1; $WINS * 100 / $ROUNDS" | bc)
    else
        WIN_PCT=0
    fi

    printf "| %-20s | %4d | %6d | %4d | %5.1f%% |\n" "$OPPONENT_NAME" "$WINS" "$LOSSES" "$TIES" "$WIN_PCT"

    TOTAL_OPPONENTS=$((TOTAL_OPPONENTS + 1))
done

echo ""
echo "=================================================="
echo "Summary: Tested against $TOTAL_OPPONENTS opponents"
echo "=================================================="
