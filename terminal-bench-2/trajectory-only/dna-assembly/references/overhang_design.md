# Golden Gate Overhang Design Reference

## Overhang Selection Principles

Golden Gate assembly efficiency depends critically on overhang design. Poorly designed overhangs lead to mis-ligation, reduced colony counts, and incorrect assemblies.

## Validated Overhang Sets

### NEB High-Fidelity 4-Fragment Assembly Set

For assemblies with 4 fragments (plus backbone), these overhangs have been validated for high-fidelity assembly:

| Junction | Overhang (5' to 3') | Notes |
|----------|---------------------|-------|
| J1       | GGAG               | Backbone to Fragment 1 |
| J2       | TACT               | Fragment 1 to Fragment 2 |
| J3       | AATG               | Fragment 2 to Fragment 3 |
| J4       | AGGT               | Fragment 3 to Fragment 4 |
| J5       | GCTT               | Fragment 4 to Backbone (circular) |

### Alternative High-Fidelity Sets

**Set A (4 fragments)**:
- GGAG, TACT, AATG, GCTT

**Set B (6 fragments)**:
- GGAG, TACT, AATG, AGGT, GCTT, CGAA

**Set C (8 fragments)**:
- GGAG, TACT, AATG, AGGT, GCTT, CGAA, TTCG, ATCC

## Overhang Compatibility Rules

### Minimum Hamming Distance

Overhangs should differ by at least 2 nucleotides (Hamming distance >= 2):

**Good examples**:
- GGAG vs TACT (differ by 4 positions)
- AATG vs GCTT (differ by 4 positions)

**Bad examples**:
- AACC vs AACG (differ by only 1 position)
- AACT vs AAGT (differ by only 1 position)

### Avoid Palindromic Overhangs

Palindromic sequences can self-ligate, reducing assembly efficiency:

**Avoid**: AATT, GCGC, CGCG, TATA, ACGT

### Avoid High GC Content

Overhangs with 3-4 G/C nucleotides ligate more slowly:

**Suboptimal**: GCGC, CCGG, GGGC
**Preferred**: TACT, AATG (mixed GC content)

## Calculating Hamming Distance

To verify overhang compatibility, calculate pairwise Hamming distances:

```python
def hamming_distance(s1, s2):
    """Calculate Hamming distance between two equal-length strings."""
    if len(s1) != len(s2):
        raise ValueError("Sequences must be same length")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def verify_overhang_set(overhangs, min_distance=2):
    """Verify all overhangs in a set have sufficient Hamming distance."""
    for i, oh1 in enumerate(overhangs):
        for oh2 in overhangs[i+1:]:
            dist = hamming_distance(oh1, oh2)
            if dist < min_distance:
                print(f"WARNING: {oh1} and {oh2} differ by only {dist} positions")
                return False
    return True
```

## Reverse Complement Reference

When designing reverse primers, the overhang must be reverse-complemented:

| Overhang | Reverse Complement |
|----------|-------------------|
| GGAG     | CTCC              |
| TACT     | AGTA              |
| AATG     | CATT              |
| AGGT     | ACCT              |
| GCTT     | AAGC              |

## Assembly-Specific Considerations

### Circular Plasmid Assembly

For circular assemblies, the number of unique overhangs equals the number of fragments:
- 4 fragments = 4 unique overhangs
- The last overhang connects back to the first fragment

### Linear Assembly

For linear assemblies, the number of overhangs equals (fragments - 1):
- 4 fragments = 3 internal junctions
- End overhangs depend on downstream cloning strategy

### Maintaining Reading Frame

When fusing coding sequences:
- Junction overhangs should maintain the reading frame
- Plan overhangs at codon boundaries when possible
- Verify the resulting amino acid sequence at junctions

## BsaI Recognition and Cut Sites

BsaI is a Type IIS restriction enzyme:

```
Recognition: GGTCTC(N)1
Cut:         GGTCTC(N)1 | (N)4
                       ^--- Cut here (leaves 4nt 5' overhang)
```

**Forward strand**: 5'-GGTCTC-N-[NNNN]-...-3'
**Reverse strand**: 3'-CCAGAG-N-[NNNN]-...-5'

After digestion:
- 4-nucleotide 5' overhang remains
- Recognition site is removed from final assembly (scarless)

## Troubleshooting Overhang Issues

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Low colony count | Similar overhangs | Use validated overhang set |
| Wrong assemblies | Overhang mis-ligation | Increase Hamming distance |
| No colonies | Palindromic overhangs | Avoid self-complementary sequences |
| Variable results | GC-rich overhangs | Use balanced GC content |
