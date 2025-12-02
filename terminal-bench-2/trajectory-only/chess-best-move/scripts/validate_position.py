#!/usr/bin/env python3
"""
Chess Position Validator

Validates detected chess positions for correctness.
Run this after any position detection to catch obvious errors.

Usage:
    python validate_position.py <fen_string>
    python validate_position.py "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

Or import as module:
    from validate_position import validate_fen, validate_piece_counts
"""

import sys
from typing import Tuple, List


def count_pieces_in_fen(fen: str) -> dict:
    """
    Count all pieces in a FEN string.

    Args:
        fen: FEN position string

    Returns:
        Dictionary with piece counts
    """
    position_part = fen.split()[0]

    counts = {
        'K': 0, 'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'P': 0,  # White
        'k': 0, 'q': 0, 'r': 0, 'b': 0, 'n': 0, 'p': 0,  # Black
    }

    for char in position_part:
        if char in counts:
            counts[char] += 1

    return counts


def validate_piece_counts(counts: dict) -> Tuple[bool, List[str]]:
    """
    Validate piece counts are legal.

    Args:
        counts: Dictionary of piece counts

    Returns:
        (is_valid, list of error messages)
    """
    errors = []

    # Exactly one king per side
    if counts['K'] != 1:
        errors.append(f"White must have exactly 1 king, found {counts['K']}")
    if counts['k'] != 1:
        errors.append(f"Black must have exactly 1 king, found {counts['k']}")

    # Maximum pawns
    if counts['P'] > 8:
        errors.append(f"White cannot have more than 8 pawns, found {counts['P']}")
    if counts['p'] > 8:
        errors.append(f"Black cannot have more than 8 pawns, found {counts['p']}")

    # Total pieces per side (accounting for promotions)
    white_total = sum(counts[p] for p in 'KQRBNP')
    black_total = sum(counts[p] for p in 'kqrbnp')

    if white_total > 16:
        errors.append(f"White cannot have more than 16 pieces, found {white_total}")
    if black_total > 16:
        errors.append(f"Black cannot have more than 16 pieces, found {black_total}")

    # Total pieces
    total = white_total + black_total
    if total > 32:
        errors.append(f"Total pieces cannot exceed 32, found {total}")

    # Check promotion limits (extra pieces beyond starting count)
    # White starts with 1Q, 2R, 2B, 2N - extras must come from pawn promotion
    white_extras = max(0, counts['Q'] - 1) + max(0, counts['R'] - 2) + \
                   max(0, counts['B'] - 2) + max(0, counts['N'] - 2)
    white_missing_pawns = 8 - counts['P']
    if white_extras > white_missing_pawns:
        errors.append(f"White has {white_extras} extra pieces but only {white_missing_pawns} "
                      f"pawns could have promoted (impossible position)")

    black_extras = max(0, counts['q'] - 1) + max(0, counts['r'] - 2) + \
                   max(0, counts['b'] - 2) + max(0, counts['n'] - 2)
    black_missing_pawns = 8 - counts['p']
    if black_extras > black_missing_pawns:
        errors.append(f"Black has {black_extras} extra pieces but only {black_missing_pawns} "
                      f"pawns could have promoted (impossible position)")

    return len(errors) == 0, errors


def validate_fen(fen: str) -> Tuple[bool, List[str]]:
    """
    Validate a FEN string for basic correctness.

    Args:
        fen: FEN position string

    Returns:
        (is_valid, list of error messages)
    """
    errors = []

    # Split FEN into components
    parts = fen.split()
    if len(parts) < 1:
        return False, ["Empty FEN string"]

    position = parts[0]
    ranks = position.split('/')

    # Must have 8 ranks
    if len(ranks) != 8:
        errors.append(f"FEN must have 8 ranks, found {len(ranks)}")

    # Each rank must sum to 8 squares
    for i, rank in enumerate(ranks):
        square_count = 0
        for char in rank:
            if char.isdigit():
                square_count += int(char)
            elif char in 'KQRBNPkqrbnp':
                square_count += 1
            else:
                errors.append(f"Invalid character '{char}' in rank {8-i}")
        if square_count != 8:
            errors.append(f"Rank {8-i} has {square_count} squares, must be 8")

    # Validate piece counts
    counts = count_pieces_in_fen(fen)
    count_valid, count_errors = validate_piece_counts(counts)
    errors.extend(count_errors)

    # Check for pawns on first/last rank (illegal)
    if 'P' in ranks[0] or 'p' in ranks[0]:
        errors.append("Pawns cannot be on the 8th rank")
    if 'P' in ranks[7] or 'p' in ranks[7]:
        errors.append("Pawns cannot be on the 1st rank")

    return len(errors) == 0, errors


def print_validation_report(fen: str):
    """
    Print a detailed validation report for a FEN string.
    """
    print("=" * 60)
    print("CHESS POSITION VALIDATION REPORT")
    print("=" * 60)
    print(f"\nFEN: {fen}\n")

    # Basic FEN validation
    is_valid, errors = validate_fen(fen)

    # Piece counts
    counts = count_pieces_in_fen(fen)
    white_total = sum(counts[p] for p in 'KQRBNP')
    black_total = sum(counts[p] for p in 'kqrbnp')

    print("PIECE COUNTS:")
    print(f"  White: K={counts['K']} Q={counts['Q']} R={counts['R']} "
          f"B={counts['B']} N={counts['N']} P={counts['P']} (Total: {white_total})")
    print(f"  Black: K={counts['k']} Q={counts['q']} R={counts['r']} "
          f"B={counts['b']} N={counts['n']} P={counts['p']} (Total: {black_total})")
    print(f"  Grand Total: {white_total + black_total}")

    print("\nVALIDATION CHECKS:")
    checks = [
        ("Exactly 1 white king", counts['K'] == 1),
        ("Exactly 1 black king", counts['k'] == 1),
        ("White pieces <= 16", white_total <= 16),
        ("Black pieces <= 16", black_total <= 16),
        ("Total pieces <= 32", white_total + black_total <= 32),
        ("White pawns <= 8", counts['P'] <= 8),
        ("Black pawns <= 8", counts['p'] <= 8),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check_name}")
        if not passed:
            all_passed = False

    if errors:
        print("\nERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)
    if is_valid:
        print("RESULT: Position appears VALID")
    else:
        print("RESULT: Position is INVALID")
        print("\nThis likely indicates a detection error. Do NOT proceed with")
        print("move analysis until the position is correctly detected.")
    print("=" * 60)

    return is_valid


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_position.py <fen_string>")
        print("\nExample:")
        print('  python validate_position.py "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"')
        sys.exit(1)

    # Join all arguments in case FEN has spaces
    fen = " ".join(sys.argv[1:])
    is_valid = print_validation_report(fen)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
