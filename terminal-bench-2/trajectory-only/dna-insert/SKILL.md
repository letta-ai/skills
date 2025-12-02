---
name: dna-insert
description: Specialized skill for designing primers to insert DNA sequences into circular plasmids using Q5 site-directed mutagenesis (SDM). This skill should be used when tasks involve inserting sequences into plasmids, designing primers for Q5 SDM insertions, or converting an input plasmid to an output plasmid with additional sequence. The skill provides workflows for understanding Q5 SDM mechanics, proper primer design with annealing regions, Tm calculation, and critical verification strategies.
---

# DNA Insert Primer Design

Design primers for inserting DNA sequences into circular plasmids using Q5 site-directed mutagenesis.

## When to Use This Skill

Apply this skill when tasks involve:
- Inserting DNA sequences into circular plasmids
- Designing primers for Q5 site-directed mutagenesis insertions
- Converting input plasmid to output plasmid with additional sequence
- Tasks mentioning NEB Q5 SDM kit for insertions
- Comparing input/output sequences where output is longer (insertion detected)

## Critical Conceptual Understanding

### Q5 SDM Uses Inverse PCR - Not Standard PCR

**This is the most important concept to understand correctly.**

Q5 site-directed mutagenesis uses **inverse PCR** which is fundamentally different from standard PCR:

| Standard PCR | Inverse PCR (Q5 SDM) |
|--------------|----------------------|
| Primers face toward each other | Primers face away from each other (back-to-back) |
| Amplifies region BETWEEN primers | Amplifies EVERYTHING EXCEPT between primers |
| For amplifying fragments | For modifying circular plasmids |

### How Insertions Work in Q5 SDM

For insertions, the mechanism is:

```
1. Primers bind back-to-back at the insertion site
2. The 5' end of one or both primers contains the insertion sequence
3. PCR extends around the entire circular plasmid
4. The product is linear, containing the full plasmid plus insertion
5. KLD enzyme mix circularizes and removes template
```

### Primer Annealing Regions - Critical Distinction

**Only the 3' portion of the primer that matches the template is the "annealing region".**

```
Primer anatomy:
5'-[5' OVERHANG (insertion)]-[ANNEALING REGION]->3'
    └── Does NOT anneal ───┘ └── Anneals to template ─┘

For Tm calculation: Use ONLY the annealing region
For length constraints: Verify which applies (total vs annealing)
```

## Core Workflow

### Step 1: Identify the Insertion

Compare input and output sequences to identify:
- The exact insertion position in the input
- The sequence being inserted
- The length of the insertion

```python
# Example: Finding insertion by sequence comparison
# If input is shorter than output, an insertion exists
# Align sequences to find where they diverge
```

### Step 2: Understand Constraint Requirements

Parse task constraints carefully:
- **Length constraints**: Do they apply to total primer length or annealing region?
- **Tm constraints**: Always calculated on annealing region only
- **ΔTm constraint**: Maximum difference between primer pair Tms
- **Tm calculation tool**: Use specified tool (e.g., oligotm with exact flags)

### Step 3: Install Required Tools

```bash
# Install primer3 for oligotm
which oligotm || apt-get update && apt-get install -y primer3

# Verify installation
oligotm --help
```

### Step 4: Design Primer Strategy

For Q5 SDM insertions, two valid approaches exist:

**Approach A: Insertion in Forward Primer Only**
```
Forward: 5'-[entire insertion]-[annealing downstream]->3'
Reverse: 5'-[annealing upstream (RC)]->3'

Primers are back-to-back at insertion site
Forward primer contains full insertion as 5' overhang
```

**Approach B: Split Insertion Between Primers**
```
Forward: 5'-[part of insertion]-[annealing downstream]->3'
Reverse: 5'-[RC of rest of insertion]-[annealing upstream (RC)]->3'

Both primers have 5' overhangs that together form the insertion
```

### Step 5: Calculate Annealing Region Length

Target annealing region characteristics:
- Length: 15-45 bp (or per task specification)
- Tm: 58-72°C (or per task specification)
- GC content: 40-60%
- End with G or C at 3' end (GC clamp)

### Step 6: Calculate Tm Using Specified Tool

**Use oligotm with exact flags from task specification:**

```bash
# Example with common Q5 SDM flags
echo "ANNEALING_REGION_SEQUENCE" | oligotm -tp 1 -sc 1 -mv 50 -dv 2 -n 0.8 -d 500
```

**Verify the command works before relying on it:**
```bash
# Test with known sequence
echo "ATCGATCGATCGATCG" | oligotm -tp 1 -sc 1 -mv 50 -dv 2 -n 0.8 -d 500
```

### Step 7: Validate Primer Design

#### A. Constraint Validation
- Annealing region length within bounds
- Tm within specified range
- ΔTm between primers within tolerance

#### B. Quality Validation
- GC content 40-60%
- No poly-runs (>4 consecutive identical bases)
- 3' GC clamp present
- No strong secondary structures

#### C. Biological Validation
- Primers anneal to INPUT template (not output)
- Primers are on opposite strands
- Primers are back-to-back (not facing toward each other)
- Annealing regions are sufficient length on EACH side

### Step 8: Simulate PCR Product (Critical)

**This step catches errors that constraint checking misses.**

Mentally or computationally trace through inverse PCR:

```
1. Forward primer binds at position X on input template
2. Reverse primer binds at position Y on input template (opposite strand)
3. Extension goes AROUND the plasmid
4. Product = [insertion] + [downstream of fwd] + [wrap around] + [upstream of rev]
5. After circularization: Does this match expected output?
```

If simulation doesn't produce expected output:
- Check primer orientation (must be back-to-back)
- Verify strand assignments
- Check position calculations for off-by-one errors
- Handle circular topology correctly (positions wrap)

### Step 9: Output Results

Format primers as specified (typically FASTA):
```
>forward_primer Tm=XX.X annealing_length=YY
SEQUENCE...
>reverse_primer Tm=XX.X annealing_length=YY
SEQUENCE...
```

## Common Pitfalls and Mitigations

### Pitfall 1: Misunderstanding Annealing vs Total Length

**Error**: Calculating Tm or checking length constraints using total primer length instead of annealing region.

**Mitigation**:
- Always separate primer into [5' overhang] and [annealing region]
- Calculate Tm using only annealing region
- Verify which length the constraints apply to

### Pitfall 2: Counting Both Sides of Insertion as "Annealing"

**Error**: For insertions with flanking annealing regions, incorrectly summing both sides as total annealing.

**Mitigation**: In Q5 SDM, a primer anneals from one direction only. The insertion sits at the 5' end and does not contribute to annealing. If designing with flanking sequences, understand that these are typically split across two primers.

### Pitfall 3: Not Verifying oligotm Tool Availability

**Error**: Writing scripts that call oligotm without first confirming it's installed.

**Mitigation**:
```bash
# Always verify tool exists before using
which oligotm || (apt-get update && apt-get install -y primer3)
# Test tool works
echo "ATCG" | oligotm -tp 1 -sc 1
```

### Pitfall 4: Running oligotm with Wrong Invocation

**Error**: Using `oligotm SEQUENCE` instead of piping.

**Mitigation**: oligotm reads from stdin:
```bash
# Correct
echo "SEQUENCE" | oligotm -tp 1 -sc 1 -mv 50 -dv 2 -n 0.8 -d 500

# Wrong
oligotm "SEQUENCE" -tp 1 -sc 1  # May not work as expected
```

### Pitfall 5: Ignoring Circular Plasmid Topology

**Error**: Using linear sequence operations on circular plasmids.

**Mitigation**:
- Extend sequence for wraparound searches: `seq + seq[:overlap]`
- Handle positions that wrap: `position % plasmid_length`
- Consider if mutation site spans origin

### Pitfall 6: Not Simulating the Final Product

**Error**: Assuming primers that meet constraints will work.

**Mitigation**: Always trace through PCR mentally or computationally:
- Where does each primer bind?
- What orientation are they?
- What product results from amplification?
- Does product match expected output?

### Pitfall 7: Wrong Primer Orientation

**Error**: Designing primers facing toward each other (standard PCR) instead of back-to-back (inverse PCR).

**Mitigation**: For Q5 SDM:
- Primers must face AWAY from each other
- Think of it as amplifying "around the circle"
- Draw out the circular plasmid to visualize

### Pitfall 8: Very Short Annealing on One Side

**Error**: Having 4 bp or less annealing on one side of insertion.

**Mitigation**:
- Aim for at least 10-15 bp annealing on each side
- Very short annealing regions may be unstable
- Reposition primers if needed to balance annealing

### Pitfall 9: Truncated or Incomplete Scripts

**Error**: Writing complex scripts that get truncated or have incomplete logic.

**Mitigation**:
- Write simpler, modular code
- Test each function independently
- Verify full script contents before execution

## Verification Checklist

Before declaring task complete, verify:

- [ ] oligotm tool is installed and working
- [ ] Tm calculated using ONLY annealing regions
- [ ] Tm values verified by running actual oligotm commands
- [ ] Annealing length constraints satisfied (check which length applies)
- [ ] ΔTm between primers within tolerance
- [ ] Primers bind to INPUT template (not output)
- [ ] Primers are back-to-back orientation
- [ ] Primers are on opposite strands
- [ ] Simulated PCR product matches expected output
- [ ] Output format matches specification

## Reference Materials

See `references/q5_sdm_mechanics.md` for detailed explanation of:
- Inverse PCR mechanism
- How different mutation types are achieved
- Primer anatomy for insertions
- Common design patterns

## Example: 39 bp Insertion Design

Given:
- Input plasmid with sequence at position 215
- Need to insert 39 bp at that position
- Constraints: 15-45 bp annealing, Tm 58-72°C, ΔTm ≤ 5°C

Strategy:
```
1. Forward primer:
   5'-[39 bp insertion]-[~20 bp annealing to downstream]->3'
   Total length: ~59 bp
   Annealing length: ~20 bp (this is what Tm is calculated on)

2. Reverse primer:
   5'-[~20 bp annealing to upstream (reverse complement)]->3'
   Total length: ~20 bp
   Annealing length: ~20 bp

3. Verify:
   - Both annealing regions: 15-45 bp ✓
   - Calculate Tm of each annealing region
   - Verify ΔTm ≤ 5°C
   - Simulate PCR to confirm output matches expected
```
