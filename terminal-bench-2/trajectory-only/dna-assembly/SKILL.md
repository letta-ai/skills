---
name: dna-assembly
description: Guidance for Golden Gate assembly primer design and DNA assembly tasks. This skill should be used when designing primers for Golden Gate cloning, Type IIS restriction enzyme assembly, or multi-fragment DNA assembly workflows. It covers overhang selection, primer structure, assembly simulation, and verification strategies.
---

# DNA Assembly

## Overview

This skill provides procedural knowledge for Golden Gate assembly primer design, a molecular cloning technique that uses Type IIS restriction enzymes (like BsaI) to create scarless multi-fragment assemblies. The skill emphasizes rigorous verification and simulation to ensure designed primers produce the expected assembled product.

## Workflow

### Phase 1: Understand the Assembly Requirements

Before designing primers, thoroughly analyze:

1. **Input sequences**: Read and parse all input FASTA files to understand the fragments to be assembled
2. **Output sequence**: Understand the expected final assembled product
3. **Assembly topology**: Determine if the assembly is linear or circular (circular plasmids require the last overhang to match the first)
4. **Fragment order**: Identify the correct order of fragments in the final assembly
5. **Reading frame considerations**: Note which fragments require start codons, stop codons, or neither

### Phase 2: Overhang Design

Overhang selection is critical for efficient Golden Gate assembly. Follow these principles:

**Use established overhang sets**: Rather than designing arbitrary overhangs, use validated overhang sets from NEB or published literature. See `references/overhang_design.md` for recommended sets.

**Overhang requirements**:
- 4-nucleotide overhangs for BsaI-based assembly
- Overhangs must be sufficiently different (Hamming distance >= 2 recommended)
- Avoid palindromic overhangs that could self-ligate
- Avoid overhangs with high GC content at ligation junction
- For N fragments in circular assembly, exactly N unique overhangs are needed

**Common mistake**: Selecting overhangs that differ by only one nucleotide (e.g., AACC, AACG, AACT). These similar overhangs can cause mis-ligation and reduce assembly efficiency.

### Phase 3: Primer Structure Design

Golden Gate primers have a specific structure. Understanding orientation is crucial:

**Forward primer structure** (5' to 3'):
```
[5' extension (optional)] - [BsaI recognition site: GGTCTC] - [N spacer] - [4nt overhang] - [gene-specific binding region]
```

**Reverse primer structure** (5' to 3'):
```
[5' extension (optional)] - [BsaI recognition site: GAGACC] - [N spacer] - [4nt overhang (reverse complement)] - [gene-specific binding region (reverse complement)]
```

**Critical orientation check**: The BsaI site must always be at the 5' end of the primer as written. A common mistake is placing the recognition site at the 3' end, which will not produce the intended cut.

**Gene-specific binding region requirements**:
- Typically 18-25 nucleotides
- Melting temperature (Tm) between 55-65 degrees C
- GC content of 40-60% preferred
- Avoid runs of >4 identical nucleotides
- Check for secondary structure (hairpins) that could affect PCR

### Phase 4: Pre-Assembly Verification

Before finalizing primers, perform these checks:

1. **Internal restriction site check**: Verify that insert sequences do not contain BsaI recognition sites (GGTCTC or GAGACC). If present, consider silent mutations or alternative enzymes.

2. **Backbone check**: Also verify the plasmid backbone being amplified does not contain internal BsaI sites.

3. **Overhang uniqueness verification**: Confirm all overhangs are unique and sufficiently different from each other.

4. **Primer quality checks**:
   - Self-complementarity analysis (avoid hairpins)
   - Primer-dimer formation potential
   - 3' end GC content (1-2 G/C in last 5 bases ideal for specificity)
   - Overall GC content (40-60%)

### Phase 5: Assembly Simulation

**This is the most critical verification step.** Before declaring success:

1. **Simulate PCR products**: For each primer pair, determine the exact PCR product sequence including the BsaI sites and overhangs.

2. **Simulate BsaI digestion**: Apply the enzyme cut to each PCR product to determine the digested fragment with overhangs.

3. **Simulate ligation**: Assemble all digested fragments in silico based on overhang complementarity.

4. **Compare to expected output**: Perform a nucleotide-by-nucleotide comparison of the simulated assembled product against the expected output sequence.

**Common mistake**: Claiming assembly will work without actually simulating the complete product and comparing it to the expected output.

### Phase 6: Output Generation

Generate primer output in a clear format:
- Primer name (indicating fragment and direction)
- Primer sequence (5' to 3')
- Calculated Tm for binding region
- Overhang produced after digestion

## Verification Checklist

Before finalizing any primer design, confirm:

- [ ] All input sequences parsed correctly
- [ ] Expected output sequence understood
- [ ] Overhang set uses established/validated sequences
- [ ] All overhangs differ by Hamming distance >= 2
- [ ] No internal BsaI sites in inserts or backbone
- [ ] BsaI sites positioned at 5' end of all primers
- [ ] Primer Tm values within acceptable range (55-65 degrees C)
- [ ] No significant primer secondary structures
- [ ] Full assembly simulated in silico
- [ ] Simulated product matches expected output exactly
- [ ] Circular topology handled correctly (if applicable)
- [ ] Start/stop codons correctly included/excluded per fragment

## Common Pitfalls

1. **Inconsistent overhang reporting**: Track overhangs carefully throughout the design process. If reported overhangs change between steps, this indicates a bug.

2. **Primer orientation confusion**: Remember that reverse primers are written 5' to 3' but bind to the opposite strand. The overhang sequence in a reverse primer should be the reverse complement of the desired overhang.

3. **Circular assembly errors**: For circular plasmids, the overhang connecting the last fragment back to the first must be correctly designed. Verify the plasmid closes in the correct orientation.

4. **Incomplete verification**: Checking that "the fusion matches at position X" is insufficient. Verify the entire assembled sequence matches the expected output.

5. **Tm calculation inconsistencies**: If Tm values differ between reports, investigate the calculation method. Use a consistent, reliable Tm calculation approach.

6. **Script development approach**: Test primer design logic incrementally on simple cases before applying to complex multi-fragment assemblies. Avoid writing large scripts that fail with cryptic errors.

## Resources

### references/

- `overhang_design.md`: Validated overhang sets and selection criteria for Golden Gate assembly
