# Hierarchical Structure Patterns for Data Resharding

This reference provides detailed patterns for implementing hierarchical directory structures when simple flat organization violates constraints.

## When Hierarchical Structure is Required

Given:
- N = total number of items to organize
- K = maximum items per directory

**Flat structure works when:** `ceil(N/K) <= K`
**Hierarchical structure required when:** `ceil(N/K) > K`

### Example Calculation

With N=9,898 files and K=30 max per directory:
- Shards needed: ceil(9898/30) = 330
- Can 330 shards fit in root? 330 > 30, NO
- Need hierarchical organization

Required depth = ceil(log_K(N)) = ceil(log_30(9898)) = ceil(2.7) = 3 levels

## Hierarchical Index Generation

Convert linear indices to hierarchical paths:

```python
def linear_to_hierarchical_path(index: int, branching_factor: int = 30) -> str:
    """
    Convert a linear index to a hierarchical directory path.

    Examples with branching_factor=30:
        0 -> "shard_0000"
        29 -> "shard_0029"
        30 -> "level_01/shard_0000"
        59 -> "level_01/shard_0029"
        900 -> "level_02/level_00/shard_0000"

    Args:
        index: Linear index (0, 1, 2, ...)
        branching_factor: Max items per directory level

    Returns:
        Hierarchical path string
    """
    if index < branching_factor:
        return f"shard_{index:04d}"

    parts = []
    remaining = index

    # Build path from leaf to root
    while remaining >= 0:
        level_index = remaining % branching_factor
        parts.append(level_index)
        remaining = remaining // branching_factor - 1
        if remaining < 0:
            break

    # Convert to path components
    path_parts = []
    for i, level_idx in enumerate(reversed(parts)):
        if i == len(parts) - 1:
            path_parts.append(f"shard_{level_idx:04d}")
        else:
            path_parts.append(f"level_{level_idx:02d}")

    return "/".join(path_parts)


def hierarchical_path_to_linear(path: str, branching_factor: int = 30) -> int:
    """
    Convert a hierarchical path back to linear index.

    Inverse of linear_to_hierarchical_path().
    """
    parts = path.split("/")
    index = 0
    multiplier = 1

    for part in reversed(parts):
        if part.startswith("shard_"):
            idx = int(part.split("_")[1])
        else:  # level_XX
            idx = int(part.split("_")[1])
        index += idx * multiplier
        multiplier *= branching_factor

    return index
```

## Alternative: Group-Based Organization

Simpler approach using fixed grouping:

```python
def get_group_path(shard_index: int, items_per_group: int = 30) -> str:
    """
    Organize shards into groups.

    shard_index=0  -> "group_00/shard_0000"
    shard_index=29 -> "group_00/shard_0029"
    shard_index=30 -> "group_01/shard_0030"
    """
    group_index = shard_index // items_per_group
    return f"group_{group_index:02d}/shard_{shard_index:04d}"
```

For very large datasets, add another level:

```python
def get_deep_group_path(shard_index: int, items_per_level: int = 30) -> str:
    """
    Two-level grouping for large datasets.

    shard_index=0    -> "super_00/group_00/shard_0000"
    shard_index=899  -> "super_00/group_29/shard_0899"
    shard_index=900  -> "super_01/group_00/shard_0900"
    """
    group_index = shard_index // items_per_level
    super_index = group_index // items_per_level
    return f"super_{super_index:02d}/group_{group_index:02d}/shard_{shard_index:04d}"
```

## Validation Pattern

Always validate the entire output structure:

```python
def validate_hierarchical_structure(
    root_dir: str,
    max_items: int = 30,
    max_file_size: int = 15 * 1024 * 1024
) -> list[str]:
    """
    Validate ALL directories in the output tree meet constraints.

    Returns list of violations (empty if compliant).
    """
    violations = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Count ALL items (both files AND directories)
        total_items = len(dirnames) + len(filenames)

        if total_items > max_items:
            violations.append(
                f"ITEM COUNT: {dirpath} has {total_items} items "
                f"(max {max_items})"
            )

        # Check file sizes
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
                if size > max_file_size:
                    violations.append(
                        f"FILE SIZE: {filepath} is {size:,} bytes "
                        f"(max {max_file_size:,})"
                    )
            except OSError:
                violations.append(f"UNREADABLE: {filepath}")

    return violations
```

## Metadata Placement Consideration

The metadata file counts toward the root directory item limit:

```
output/
├── .reshard_metadata.json  <- Counts as 1 item!
├── group_00/
├── group_01/
└── ... (if 30 groups + metadata = 31 items = VIOLATION)
```

**Solutions:**

1. **Reduce groups by 1** to leave room for metadata:
   ```python
   max_groups = max_items - 1  # Reserve slot for metadata
   ```

2. **Place metadata inside a group:**
   ```
   output/
   ├── group_00/
   │   └── .reshard_metadata.json
   ├── group_01/
   └── ...
   ```

3. **Place metadata outside constrained structure:**
   ```
   /tmp/reshard_metadata.json  # Reference by absolute path
   ```

## Reconstruction from Hierarchical Structure

When decompressing, the metadata must support mapping back:

```python
def decompress_hierarchical(resharded_dir: str) -> None:
    """Reconstruct original structure from hierarchical shards."""
    metadata_path = Path(resharded_dir) / ".reshard_metadata.json"
    metadata = json.loads(metadata_path.read_text())

    # Create temporary directory for reconstruction
    temp_dir = Path(resharded_dir).parent / f".temp_{uuid.uuid4()}"
    temp_dir.mkdir()

    try:
        # Restore each file to its original location
        for shard_path, original_path in metadata["shard_mapping"].items():
            src = Path(resharded_dir) / shard_path
            dst = temp_dir / original_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Handle split files
        for original_name, chunks in metadata.get("split_files", {}).items():
            dst = temp_dir / original_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst, 'wb') as out_file:
                for chunk_path in chunks:
                    chunk_full = Path(resharded_dir) / chunk_path
                    out_file.write(chunk_full.read_bytes())

        # Clear resharded directory and move reconstructed content
        for item in Path(resharded_dir).iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        for item in temp_dir.iterdir():
            shutil.move(str(item), resharded_dir)

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
```

## Testing Hierarchical Structures

Test at scales that exercise different hierarchy depths:

```python
TEST_CASES = [
    # (file_count, expected_depth, description)
    (1, 1, "Single file - no sharding"),
    (30, 1, "Exactly at limit - single level"),
    (31, 2, "Just over - needs 2 shards"),
    (900, 2, "30 groups of 30 - two levels"),
    (901, 3, "Just over 900 - needs third level"),
    (27000, 3, "30^3 - three full levels"),
]

def test_hierarchy_depth(file_count, expected_depth, description):
    """Verify correct hierarchy depth is created."""
    # Create test files
    # Run compression
    # Measure actual depth
    actual_depth = max_directory_depth(output_dir)
    assert actual_depth <= expected_depth, \
        f"{description}: expected depth {expected_depth}, got {actual_depth}"
```

## Summary

1. **Always calculate** whether hierarchical structure is needed before implementing
2. **Use consistent indexing** that maps bidirectionally (linear <-> hierarchical)
3. **Account for metadata** in item counts
4. **Validate entire tree** after creation, not just leaf directories
5. **Test at boundary scales** where hierarchy depth changes
