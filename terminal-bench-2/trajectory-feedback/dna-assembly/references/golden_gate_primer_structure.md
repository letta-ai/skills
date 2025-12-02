# Golden Gate Assembly Primer Structure Reference

## Type IIS Restriction Enzymes

Type IIS restriction enzymes cut DNA outside their recognition sequence, enabling scarless assembly of multiple DNA fragments. The most common enzymes for Golden Gate assembly are:

| Enzyme | Recognition Site | Cut Pattern | Overhang |
|--------|-----------------|-------------|----------|
| BsaI | GGTCTC | N(1/5) | 4bp 5' overhang |
| BsmBI | CGTCTC | N(1/5) | 4bp 5' overhang |
| BbsI | GAAGAC | N(2/6) | 4bp 5' overhang |
| SapI | GCTCTTC | N(1/4) | 3bp 5' overhang |

## Complete Primer Structure for BsaI

### Forward Primer (5' to 3')

```
[Clamp]-[GGTCTC]-[N]-[Overhang]-[Binding Region]
  |        |      |      |           |
  |        |      |      |           └── 15-45bp complementary to template
  |        |      |      └── 4bp sticky end for assembly
  |        |      └── 1nt spacer (any nucleotide)
  |        └── BsaI recognition site (6bp)
  └── 1-6bp for enzyme binding efficiency
```

### Reverse Primer (5' to 3')

```
[Clamp]-[GAGACC]-[N]-[Overhang RC]-[Binding Region RC]
  |        |      |       |              |
  |        |      |       |              └── 15-45bp reverse complement of template
  |        |      |       └── 4bp reverse complement of desired overhang
  |        |      └── 1nt spacer
  |        └── Reverse complement of BsaI site
  └── 1-6bp clamp
```

## Clamp Sequence Requirements

The clamp sequence is essential for enzyme efficiency. Requirements vary by enzyme and manufacturer:

### NEB Recommendations for BsaI-HFv2

- Minimum: 1 nucleotide
- Recommended: 2-6 nucleotides
- Common sequences: `GC`, `CG`, `GCG`, `GCGC`

### Why Clamps Are Required

Type IIS enzymes need flanking sequences to:
1. Stabilize binding to DNA
2. Allow proper positioning of the catalytic domain
3. Achieve optimal cutting efficiency (>90%)

Without clamps, cutting efficiency can drop to 10-50%.

## Overhang Design Guidelines

### Characteristics of Good Overhangs

1. **Non-palindromic**: Avoid sequences like `AATT` or `GCGC`
2. **Unique**: Each overhang should appear only once per assembly
3. **Non-complementary**: Overhangs should not base-pair with each other
4. **Balanced GC content**: 25-75% GC preferred
5. **No homopolymers**: Avoid `AAAA`, `TTTT`, `GGGG`, `CCCC`

### Standard Overhang Sets

For common applications, use validated overhang sets:

**MoClo Standard (for 4-part assembly):**
- Position 1: `GGAG`
- Position 2: `TACT`
- Position 3: `AATG`
- Position 4: `GCTT`

**Fusion Protein Overhangs:**
- Start codon junction: `AATG` (contains ATG)
- Internal junctions: Choose from validated sets
- Stop codon junction: Handle stop codon removal

## Fusion Protein Considerations

### Removing Stop Codons

When creating fusion proteins, stop codons between fragments must be removed:

1. **TAA**: Remove from forward primer binding region
2. **TAG**: Remove from forward primer binding region
3. **TGA**: Remove from forward primer binding region

### Maintaining Reading Frame

For in-frame fusions:
- Total length of insert (excluding primer additions) must be divisible by 3
- Overhangs (4bp) are NOT divisible by 3
- Careful design of junction points required

## Melting Temperature Calculations

### Binding Region Tm

Target: 50-65°C (varies by protocol)

**Simple estimation (for primers 14-24bp):**
```
Tm = 4(G+C) + 2(A+T) °C
```

**Nearest-neighbor method (more accurate):**
```
Tm = ΔH / (ΔS + R × ln(C/4)) - 273.15
```
Where:
- ΔH = enthalpy sum
- ΔS = entropy sum
- R = 1.987 cal/mol·K
- C = primer concentration

### Important Notes

- Calculate Tm for binding region ONLY (not full primer)
- Use consistent method throughout design
- Account for salt concentration in buffer

## Verification Protocol

### Structural Verification

For each designed primer, verify:

```python
def verify_primer_structure(primer, enzyme='BsaI'):
    """Verify primer has correct structure for Golden Gate."""

    recognition_sites = {
        'BsaI': 'GGTCTC',
        'BsmBI': 'CGTCTC'
    }

    site = recognition_sites[enzyme]
    site_pos = primer.find(site)

    # Check 1: Recognition site exists
    assert site_pos != -1, "Recognition site not found"

    # Check 2: Clamp sequence present (site not at position 0)
    assert site_pos >= 1, "Missing clamp sequence before recognition site"

    # Check 3: Spacer after recognition site
    spacer_pos = site_pos + len(site)
    assert spacer_pos < len(primer), "Missing spacer nucleotide"

    # Check 4: Overhang length (4bp after spacer)
    overhang_start = spacer_pos + 1
    overhang_end = overhang_start + 4
    assert overhang_end <= len(primer), "Overhang too short"

    # Check 5: Binding region exists
    binding_start = overhang_end
    binding_region = primer[binding_start:]
    assert len(binding_region) >= 15, "Binding region too short"
    assert len(binding_region) <= 45, "Binding region too long"

    return True
```

### Assembly Verification

Before synthesis, verify:

1. All overhangs are unique
2. No overhang pairs are complementary
3. Assembly order is correct
4. No internal restriction sites in inserts
5. Reading frame maintained for fusions

## Common Enzymes Quick Reference

### BsaI-HFv2 (NEB #R3733)

- Recognition: 5'-GGTCTC(N)₁↓-3'
- Temperature: 37°C
- Buffer: CutSmart or rCutSmart
- Inactivation: 65°C for 20 min
- Clamp requirement: ≥1bp

### BsmBI-v2 (NEB #R0739)

- Recognition: 5'-CGTCTC(N)₁↓-3'
- Temperature: 55°C
- Buffer: NEBuffer 3.1
- Inactivation: 80°C for 20 min
- Clamp requirement: ≥1bp
