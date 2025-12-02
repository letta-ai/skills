---
name: merge-diff-arc-agi-task
description: This skill provides guidance for tasks involving merging git branches that contain different implementations of ARC-AGI pattern recognition algorithms, and then implementing a working solution that generalizes across examples. Use this skill when the task involves (1) merging git branches with conflicting code, (2) analyzing ARC-AGI style input/output grid transformations, or (3) implementing pattern recognition algorithms that must generalize to unseen test cases.
---

# Merge Diff ARC-AGI Task

## Overview

This skill addresses tasks that combine git branch merging with ARC-AGI pattern recognition challenges. These tasks typically involve:
1. Extracting and merging multiple git branches from bundles
2. Resolving merge conflicts between different algorithm implementations
3. Analyzing input/output grid examples to discover transformation patterns
4. Implementing a `map` function that generalizes to hidden test cases

## Pre-flight Checklist

Before starting any git operations, complete these setup steps to avoid interruptions:

1. **Configure git identity** (prevents merge commit failures):
   ```bash
   git config user.email "agent@example.com"
   git config user.name "Agent"
   ```

2. **Verify working directory** is clean or stash changes
3. **Identify the base branch** to work from

## Phase 1: Git Operations

### Branch Extraction and Setup

1. Extract branches from bundle files:
   ```bash
   git bundle unbundle <bundle-file>
   ```

2. Create local branches from the extracted refs:
   ```bash
   git checkout -b <branch-name> <ref>
   ```

3. Before merging, examine each branch's implementation:
   - Read the algorithm files on each branch
   - Understand what approach each implementation takes
   - Note dependencies (numpy, etc.) and coding styles

### Merge Conflict Resolution

When merge conflicts occur:

1. **Do not blindly choose one side** - both implementations may contain insights
2. **Understand both approaches** before resolving:
   - What pattern does each implementation detect?
   - What edge cases does each handle?
   - Can elements from both be combined?
3. **Document the resolution rationale** - explain why the final implementation was chosen

## Phase 2: Pattern Analysis Framework

### Systematic Analysis Process

Apply this structured approach to avoid jumping between hypotheses:

1. **Inventory the data**:
   - Grid dimensions for each example
   - Unique values present (zero vs non-zero)
   - Positions of each unique value

2. **Compare input to output**:
   - What values appear in output that weren't in input?
   - What spatial relationships change?
   - What remains constant?

3. **Formulate a single hypothesis** and test against ALL examples before moving on

4. **Document findings** in a structured format:
   ```
   Example N:
   - Input: [dimensions, unique values, positions]
   - Output: [dimensions, patterns observed]
   - Hypothesis test: [pass/fail with explanation]
   ```

### Common ARC-AGI Patterns to Consider

- **Tiling patterns**: Values repeated across grid based on position formulas
- **Diagonal patterns**: Relationships based on `i+j`, `i-j`, or similar
- **First occurrence mapping**: Order determined by where values first appear
- **Modular arithmetic**: `(i+j) % n` or similar cyclic patterns
- **Spatial transformations**: Rotations, reflections, translations

### Pattern Verification Checklist

Before finalizing an algorithm:

- [ ] Does the pattern explain ALL provided examples?
- [ ] Is the formula derivation logically justified (not just empirically fitted)?
- [ ] What happens with edge cases:
  - Empty grids or all-zero grids?
  - Single unique non-zero value?
  - Collision scenarios (e.g., two values with same modular position)?
- [ ] Would the pattern generalize to different grid sizes?

## Phase 3: Implementation

### Algorithm Development

1. **Start with clear documentation**:
   ```python
   def map(grid: list[list[int]]) -> list[list[int]]:
       """
       Transform input grid to output grid.

       Algorithm:
       1. [Step 1 explanation]
       2. [Step 2 explanation]

       Edge cases handled:
       - [Case 1]
       - [Case 2]
       """
   ```

2. **Handle edge cases explicitly**:
   ```python
   if not grid or not grid[0]:
       return grid
   unique_values = [v for v in set(flatten(grid)) if v != 0]
   if len(unique_values) == 0:
       return [[0] * len(grid[0]) for _ in range(len(grid))]
   ```

3. **Avoid collision bugs**: When mapping values to positions based on formulas, verify that no two values map to the same position, or handle the collision explicitly

### Testing Strategy

Create a reusable test function early:

```python
def test_map_function(examples_path: str) -> bool:
    """Test map function against all examples."""
    import json
    with open(examples_path) as f:
        examples = json.load(f)

    all_passed = True
    for i, ex in enumerate(examples):
        result = map(ex['input'])
        expected = ex['output']
        if result != expected:
            print(f"Example {i} FAILED")
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")
            all_passed = False
        else:
            print(f"Example {i} PASSED")
    return all_passed
```

Run this after every algorithm change rather than writing ad-hoc test scripts.

## Phase 4: Verification

### Final Verification Checklist

Before declaring the task complete:

1. **All examples pass**: Run test function against examples.json
2. **Algorithm is documented**: Comments explain the "why" not just the "what"
3. **Edge cases are handled**: Empty inputs, single values, boundary conditions
4. **Generalization is justified**: The algorithm logic follows from the pattern, not from fitting to specific examples
5. **Git state is clean**: Merge is complete, no uncommitted changes

### Generalization Confidence Assessment

Rate confidence that the solution will pass hidden tests:

- **High confidence**: Pattern logic is clearly derived from first principles; edge cases explicitly handled; formula is mathematically justified
- **Medium confidence**: Pattern works on all examples but some aspects were discovered empirically
- **Low confidence**: Solution was fitted to examples without clear logical derivation

If confidence is medium or low, revisit the pattern analysis phase.

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Git config not set before merge | Run git config commands at start |
| Jumping between hypotheses | Test each hypothesis against ALL examples before abandoning |
| Ignoring one branch's implementation | Read and understand both implementations first |
| No edge case handling | Explicitly list and handle edge cases in code |
| Empirical fitting without justification | Document why the formula works, not just that it works |
| Testing with ad-hoc scripts | Create reusable test function early |
| Missing collision handling | Verify no two values map to same position |

## Resources

### references/

The `references/` directory contains detailed guidance:

- `pattern_analysis_template.md` - Structured template for documenting pattern analysis
- `git_merge_checklist.md` - Step-by-step git operations checklist
