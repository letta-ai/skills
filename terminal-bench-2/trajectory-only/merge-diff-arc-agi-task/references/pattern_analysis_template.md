# Pattern Analysis Template

Use this template to systematically document pattern analysis for ARC-AGI tasks.

## Task Summary

- **Number of examples**:
- **Grid dimensions**: (input → output for each example)
- **Unique non-zero values across all examples**:

---

## Example Analysis

### Example 0

**Input Grid**:
```
[grid representation]
```
- Dimensions: rows × cols
- Unique non-zero values: [list]
- Value positions:
  - Value X: positions [(r1,c1), (r2,c2), ...]
  - Value Y: positions [(r1,c1), (r2,c2), ...]

**Output Grid**:
```
[grid representation]
```
- Dimensions: rows × cols
- Pattern observations:
  - [Observation 1]
  - [Observation 2]

**Input → Output Relationship**:
- [Describe what changed]
- [Describe what stayed the same]

---

### Example 1

[Repeat structure from Example 0]

---

### Example 2

[Repeat structure from Example 0]

---

## Hypothesis Formation

### Hypothesis 1

**Description**: [Clear statement of the proposed transformation rule]

**Formula/Algorithm**:
```
For each cell (i, j) in output:
  output[i][j] = [formula]
```

**Test Results**:
| Example | Expected Output | Hypothesis Output | Match? |
|---------|-----------------|-------------------|--------|
| 0       | [summary]       | [summary]         | Y/N    |
| 1       | [summary]       | [summary]         | Y/N    |
| 2       | [summary]       | [summary]         | Y/N    |

**Verdict**: [Accept/Reject]

**If rejected, reason**: [Why this hypothesis failed]

---

### Hypothesis 2

[Repeat structure if needed]

---

## Final Pattern

**Confirmed Pattern**:
[Clear description of the transformation rule]

**Mathematical Formulation**:
```
[Precise formula or algorithm]
```

**Logical Justification**:
[Explain WHY this pattern makes sense, not just that it works]

**Edge Cases Identified**:
1. [Edge case 1]: [How to handle]
2. [Edge case 2]: [How to handle]

**Generalization Confidence**: [High/Medium/Low]

**Reasoning for confidence level**:
[Explain why the pattern should or might not generalize]
