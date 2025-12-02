#!/bin/bash
# CoreWars Warrior Testing Script
#
# This script provides systematic testing of a warrior against multiple opponents.
# Modify the OPPONENTS array and paths for your specific environment.
#
# Usage: ./test_warrior.sh <warrior.red> [rounds_per_opponent]

set -e

# Configuration - MODIFY THESE FOR YOUR ENVIRONMENT
PMARS="${PMARS:-pmars}"  # Path to pmars executable
CORE_SIZE=8000
ROUNDS=${2:-100}  # Default 100 rounds per opponent

# Opponent files - MODIFY THIS LIST
OPPONENTS=(
    "opponents/stone.red"
    "opponents/paper.red"
    "opponents/vampire.red"
    "opponents/snake.red"
    "opponents/scanner.red"
)

# Win rate thresholds - MODIFY BASED ON REQUIREMENTS
declare -A THRESHOLDS
THRESHOLDS["stone"]=75
THRESHOLDS["paper"]=75
THRESHOLDS["vampire"]=75
THRESHOLDS["snake"]=33
THRESHOLDS["scanner"]=33

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <warrior.red> [rounds_per_opponent]"
    echo ""
    echo "Example: $0 my_warrior.red 100"
    exit 1
fi

WARRIOR="$1"

if [ ! -f "$WARRIOR" ]; then
    echo "Error: Warrior file not found: $WARRIOR"
    exit 1
fi

# Verify warrior assembles correctly
echo "Verifying warrior assembly..."
if ! $PMARS -b "$WARRIOR" 2>/dev/null; then
    echo -e "${RED}Error: Warrior failed to assemble${NC}"
    exit 1
fi
echo -e "${GREEN}Warrior assembles correctly${NC}"
echo ""

# Results storage
declare -A WINS
declare -A LOSSES
declare -A TIES

# Test against each opponent
echo "Testing $WARRIOR against opponents ($ROUNDS rounds each)"
echo "=========================================="

for opponent in "${OPPONENTS[@]}"; do
    if [ ! -f "$opponent" ]; then
        echo -e "${YELLOW}Warning: Opponent not found: $opponent (skipping)${NC}"
        continue
    fi

    # Extract opponent name from path
    opp_name=$(basename "$opponent" .red)

    # Run pmars and capture output
    result=$($PMARS -r "$ROUNDS" -s "$CORE_SIZE" "$WARRIOR" "$opponent" 2>&1 | tail -1)

    # Parse results (format: "Results: W1 L1 T / W2 L2 T")
    # Warrior 1 (ours) results are first
    wins=$(echo "$result" | awk '{print $2}')
    losses=$(echo "$result" | awk '{print $3}')
    ties=$(echo "$result" | awk '{print $4}')

    WINS[$opp_name]=$wins
    LOSSES[$opp_name]=$losses
    TIES[$opp_name]=$ties

    # Calculate win rate
    win_rate=$(echo "scale=1; $wins * 100 / $ROUNDS" | bc)
    threshold=${THRESHOLDS[$opp_name]:-50}

    # Color based on threshold
    if (( wins >= threshold )); then
        status="${GREEN}PASS${NC}"
    else
        status="${RED}FAIL${NC}"
    fi

    printf "%-15s: %3d wins, %3d losses, %3d ties (%5.1f%%) [need %d] %b\n" \
        "$opp_name" "$wins" "$losses" "$ties" "$win_rate" "$threshold" "$status"
done

echo ""
echo "=========================================="

# Summary
passing=0
failing=0
for opponent in "${OPPONENTS[@]}"; do
    opp_name=$(basename "$opponent" .red)
    threshold=${THRESHOLDS[$opp_name]:-50}
    wins=${WINS[$opp_name]:-0}
    if (( wins >= threshold )); then
        ((passing++))
    else
        ((failing++))
    fi
done

echo "Summary: $passing passing, $failing failing"

if [ $failing -eq 0 ]; then
    echo -e "${GREEN}All thresholds met!${NC}"
    exit 0
else
    echo -e "${RED}Some thresholds not met${NC}"
    exit 1
fi
