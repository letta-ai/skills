# Chess Image Analysis Guide

This reference provides detailed techniques for extracting chess positions from images.

## Image Processing Fundamentals

### Board Detection

Before detecting pieces, locate the chess board within the image:

```python
import cv2
import numpy as np

def find_board_boundaries(image):
    """
    Locate chess board boundaries in an image.
    Returns (x, y, width, height) of board region.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Look for rectangular grid pattern
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100,
                            minLineLength=100, maxLineGap=10)

    # Find bounding rectangle of detected lines
    if lines is not None:
        all_points = lines.reshape(-1, 2)
        x, y, w, h = cv2.boundingRect(all_points)
        return x, y, w, h

    # Fallback: assume board fills image
    return 0, 0, image.shape[1], image.shape[0]
```

### Color Calibration

Critical step - extract actual colors from the image:

```python
def calibrate_colors(image, board_region):
    """
    Extract calibration colors from known squares.

    Args:
        image: Full image
        board_region: (x, y, w, h) of board

    Returns:
        Dictionary of color signatures
    """
    x, y, w, h = board_region
    square_w = w // 8
    square_h = h // 8

    def get_square_color(file_idx, rank_idx):
        """Get average color of a square (0-7 indices)."""
        sx = x + file_idx * square_w
        sy = y + (7 - rank_idx) * square_h  # Flip for standard orientation
        square = image[sy:sy+square_h, sx:sx+square_w]
        return np.mean(square, axis=(0, 1))

    calibration = {
        # Sample known empty squares
        'light_square': get_square_color(0, 0),  # a1 is light
        'dark_square': get_square_color(1, 0),   # b1 is dark

        # Note: Piece colors require finding actual pieces
        # This is position-dependent
    }

    return calibration
```

### Piece Detection Strategies

#### Strategy 1: Color Variance

Empty squares have uniform color; squares with pieces have higher variance:

```python
def detect_occupied_by_variance(square_image, threshold=500):
    """
    Detect if square is occupied using color variance.

    Args:
        square_image: Image of single square
        threshold: Variance threshold (calibrate per image)

    Returns:
        True if likely occupied
    """
    variance = np.var(square_image)
    return variance > threshold
```

#### Strategy 2: Template Matching

If you can identify one clear piece, use it as template:

```python
def find_similar_pieces(image, template, threshold=0.8):
    """
    Find all locations matching a piece template.

    Args:
        image: Full board image
        template: Image of known piece
        threshold: Match confidence threshold

    Returns:
        List of (x, y) locations
    """
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    return list(zip(*locations[::-1]))
```

#### Strategy 3: Contour Analysis

Pieces have distinct contours different from empty squares:

```python
def analyze_square_contours(square_image):
    """
    Analyze contours to detect piece presence and type.

    Returns:
        Dictionary with detection results
    """
    gray = cv2.cvtColor(square_image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return {'occupied': False}

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    perimeter = cv2.arcLength(largest, True)

    # Circularity helps distinguish piece types
    circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

    return {
        'occupied': area > 100,  # Calibrate threshold
        'area': area,
        'circularity': circularity
    }
```

## Piece Color Determination

Distinguishing white vs black pieces:

```python
def determine_piece_color(square_image, square_color, piece_mask):
    """
    Determine if piece is white or black.

    Args:
        square_image: Image of square with piece
        square_color: 'light' or 'dark' (the square's color)
        piece_mask: Binary mask of detected piece

    Returns:
        'white', 'black', or 'unknown'
    """
    # Extract piece pixels only
    piece_pixels = square_image[piece_mask > 0]

    if len(piece_pixels) == 0:
        return 'unknown'

    avg_brightness = np.mean(piece_pixels)

    # Threshold depends on board style
    # Most boards: white pieces are brighter
    if avg_brightness > 180:
        return 'white'
    elif avg_brightness < 80:
        return 'black'
    else:
        return 'unknown'  # Uncertain - need better calibration
```

## Common Board Styles

Different chess websites use different color schemes:

### Chess.com Style
- Light squares: RGB ~(238, 238, 210)
- Dark squares: RGB ~(118, 150, 86)
- White pieces: Bright with shadows
- Black pieces: Dark gray/black

### Lichess Style
- Light squares: RGB ~(240, 217, 181)
- Dark squares: RGB ~(181, 136, 99)
- Piece styles vary by theme

### Generic Detection Approach

When board style is unknown:

```python
def adaptive_detection(image):
    """
    Detect position without prior knowledge of board style.
    """
    # Step 1: Find the board
    board_region = find_board_boundaries(image)

    # Step 2: Sample corner squares to determine colors
    calibration = calibrate_colors(image, board_region)

    # Step 3: Calculate adaptive thresholds
    light_brightness = np.mean(calibration['light_square'])
    dark_brightness = np.mean(calibration['dark_square'])
    board_contrast = abs(light_brightness - dark_brightness)

    # Step 4: Detect square by square with validation
    position = []
    for rank in range(8):
        rank_pieces = []
        for file in range(8):
            square = extract_square(image, board_region, file, rank)
            result = analyze_square(square, calibration)
            rank_pieces.append(result)
        position.append(rank_pieces)

    # Step 5: Validate before returning
    is_valid, errors = validate_position(position)
    if not is_valid:
        raise ValueError(f"Invalid position detected: {errors}")

    return position
```

## Debugging Techniques

### Visual Verification

Always output intermediate results:

```python
def debug_detection(image, board_region):
    """
    Output visual representation of detection for debugging.
    """
    x, y, w, h = board_region
    square_w = w // 8
    square_h = h // 8

    print("Detection results (view from White's perspective):")
    print("  a b c d e f g h")
    print("  ---------------")

    for rank in range(7, -1, -1):  # 8 down to 1
        row_str = f"{rank+1}|"
        for file in range(8):
            square = extract_square(image, board_region, file, rank)
            result = detect_piece(square)
            if result['piece']:
                symbol = result['piece']
            else:
                symbol = '.' if (file + rank) % 2 == 0 else ','
            row_str += f"{symbol} "
        print(row_str)
```

### Sanity Checks

Run these after every detection:

```python
def sanity_check(detected_position):
    """
    Quick sanity checks that should never fail.
    """
    checks = []

    # Count all pieces
    total = count_all_pieces(detected_position)
    checks.append(('Total pieces <= 32', total <= 32, total))

    # Count kings
    white_kings = count_specific(detected_position, 'K')
    black_kings = count_specific(detected_position, 'k')
    checks.append(('Exactly 1 white king', white_kings == 1, white_kings))
    checks.append(('Exactly 1 black king', black_kings == 1, black_kings))

    # Check for impossible situations
    white_total = count_white_pieces(detected_position)
    black_total = count_black_pieces(detected_position)
    checks.append(('White pieces <= 16', white_total <= 16, white_total))
    checks.append(('Black pieces <= 16', black_total <= 16, black_total))

    # Report results
    all_passed = True
    for name, passed, value in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {value}")
        if not passed:
            all_passed = False

    return all_passed
```

## FEN Generation

Convert detected position to FEN notation:

```python
def position_to_fen(position, to_move='w'):
    """
    Convert detected position to FEN string.

    Args:
        position: 8x8 array of piece symbols (or None/empty)
        to_move: 'w' or 'b'

    Returns:
        FEN string (position only, no castling/en passant)
    """
    fen_rows = []
    for rank in range(7, -1, -1):  # 8 down to 1
        empty_count = 0
        row_fen = ""
        for file in range(8):
            piece = position[rank][file]
            if piece:
                if empty_count > 0:
                    row_fen += str(empty_count)
                    empty_count = 0
                row_fen += piece
            else:
                empty_count += 1
        if empty_count > 0:
            row_fen += str(empty_count)
        fen_rows.append(row_fen)

    return "/".join(fen_rows) + f" {to_move} - - 0 1"
```

## Using Chess Engines

Once FEN is generated, use an engine for analysis:

```python
import chess
import chess.engine

def find_best_move(fen, engine_path="/usr/bin/stockfish", depth=20):
    """
    Find best move using Stockfish.

    Args:
        fen: Position in FEN notation
        engine_path: Path to Stockfish executable
        depth: Analysis depth

    Returns:
        Best move in UCI notation (e.g., 'e2e4')
    """
    board = chess.Board(fen)

    # Validate position is legal
    if not board.is_valid():
        raise ValueError("Invalid chess position")

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        result = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = result['pv'][0]
        return best_move.uci()
```

## Error Recovery

When detection fails, try these recovery strategies:

1. **Adjust thresholds**: Try ±20% on brightness/variance thresholds
2. **Change color space**: Try HSV instead of RGB
3. **Apply preprocessing**: Blur, sharpen, or adjust contrast
4. **Try different approach**: Switch from variance to template matching
5. **Request clarification**: Ask user for FEN or position description

Never present an unreliable detection as a confident answer.
