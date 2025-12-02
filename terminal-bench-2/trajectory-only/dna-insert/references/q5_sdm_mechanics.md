# Q5 Site-Directed Mutagenesis Mechanics

## Overview

NEB's Q5 Site-Directed Mutagenesis Kit uses **inverse PCR** to introduce mutations (insertions, deletions, substitutions) into circular plasmids. Understanding the mechanism is critical for designing correct primers.

## Inverse PCR vs Standard PCR

### Standard PCR
```
       Primer F →
    5'=================3'
    3'=================5'
       ← Primer R

Result: Amplifies region BETWEEN primers
```

### Inverse PCR (Q5 SDM)
```
    ← Primer F
    5'=================3'  (circular)
    3'=================5'
       Primer R →

Result: Amplifies region AROUND the circle (everything EXCEPT between primers)
```

### Key Differences

| Aspect | Standard PCR | Inverse PCR (Q5 SDM) |
|--------|--------------|----------------------|
| Primer orientation | Face toward each other | Face away (back-to-back) |
| What's amplified | Region between primers | Entire plasmid minus gap |
| Template topology | Linear or circular | Must be circular |
| Product | Linear fragment | Linear full-length plasmid |
| Use case | Amplify fragments | Modify circular plasmids |

## How Insertions Work

### Step-by-Step Mechanism

```
STEP 1: Initial State
- Circular plasmid with insertion site at position P
- Want to insert sequence "INSERT" at position P

STEP 2: Primer Design
- Forward primer: [INSERT sequence]-[annealing to position P+1 onward]
- Reverse primer: [annealing to position P-1 backward, RC]
- Primers are back-to-back at position P

STEP 3: Primer Binding
                    Position P
                        ↓
    ...UPSTREAM[gap]DOWNSTREAM...
              ↑     ↑
          Rev(RC)  Fwd(3' annealing)

STEP 4: PCR Extension
- Fwd primer extends around the circle
- Rev primer extends around the circle (opposite direction)
- Extensions are linear (denature the circle)

STEP 5: Product Formation
Linear product:
[Rev_RC overhang]-[upstream sequence]-[downstream sequence]-[Fwd overhang]

After KLD treatment:
- Overhangs become the insertion
- Product circularizes
- Template is degraded (DpnI digests methylated DNA)

STEP 6: Final Result
Circular plasmid with INSERT at position P
```

## Primer Anatomy for Insertions

### Basic Structure
```
5'────────────────────────────────────────3'
  [   5' OVERHANG    ] [  ANNEALING REGION  ]
  (does not anneal)    (anneals to template)
```

### For Insertions

**Option A: Full insertion in one primer**
```
Forward: 5'-[FULL INSERT]-[anneal downstream]-3'
Reverse: 5'-[anneal upstream RC]-3'
```

**Option B: Split insertion**
```
Forward: 5'-[INSERT part 1]-[anneal downstream]-3'
Reverse: 5'-[RC of INSERT part 2]-[anneal upstream RC]-3'
```

## Critical Rules

### 1. Annealing Region Definition
**Only the 3' portion that matches the template is the annealing region.**

```
Example primer: AAAATTTTCCCCGGGG...ACTGACTGACTG
                └─ 5' overhang ─┘ └── annealing ──┘
                   (insertion)     (matches template)
```

### 2. Tm Calculation
**Calculate Tm using ONLY the annealing region, NOT the entire primer.**

```python
# Wrong: Tm of entire primer
oligotm(full_primer)  # INCORRECT

# Correct: Tm of annealing region only
oligotm(annealing_region)  # CORRECT
```

### 3. Length Constraints
**Verify whether constraints apply to total length or annealing length.**

Task may specify:
- "primers 15-45 bp" - could mean total OR annealing
- "annealing region 15-45 bp" - clearly means annealing only
- Read carefully and clarify if ambiguous

### 4. Primer Orientation
**Primers must be back-to-back (facing away from each other).**

```
Correct (back-to-back):
    ←─ Fwd    Rev ─→
       at insertion site

Incorrect (facing each other):
    Fwd ─→    ←─ Rev
       would amplify between primers, not around
```

### 5. Strand Assignment
**Primers anneal to opposite strands.**

```
Forward primer: anneals to template strand (5'→3')
Reverse primer: anneals to coding strand (5'→3')

Remember: the "reverse" primer sequence as written is already
the reverse complement of what it anneals to.
```

## Position Calculations for Circular Plasmids

### Handling Wraparound

```python
def circular_position(pos, plasmid_length):
    """Normalize position to [0, plasmid_length)"""
    return pos % plasmid_length

def circular_slice(seq, start, end):
    """Extract sequence handling wraparound"""
    length = len(seq)
    start = start % length
    end = end % length
    if start <= end:
        return seq[start:end]
    else:
        return seq[start:] + seq[:end]
```

### Finding Sequence in Circular Plasmid

```python
def find_in_circular(query, circular_seq):
    """Find query in circular sequence, handling wraparound"""
    # Extend sequence to cover wraparound
    extended = circular_seq + circular_seq[:len(query)-1]
    pos = extended.find(query)
    if pos != -1:
        return pos % len(circular_seq)
    return -1
```

## Validation Requirements

### Before Ordering Primers

1. **Verify annealing to INPUT template**
   - Extract annealing region from each primer
   - Confirm it exists in the input plasmid (not output!)
   - Check exact match, no mismatches

2. **Check primer positioning**
   - Confirm back-to-back orientation
   - Verify primers bracket the insertion site correctly

3. **Validate thermodynamics**
   - Calculate Tm for annealing regions only
   - Verify both meet Tm range
   - Verify ΔTm is acceptable

4. **Simulate the PCR product**
   - Trace through inverse PCR mechanism
   - Verify product matches expected output sequence
   - Check product size matches expectation

### Simulation Algorithm

```python
def simulate_q5_sdm_insertion(input_seq, fwd_primer, rev_primer):
    """
    Simulate Q5 SDM to verify primers produce correct output.

    Returns: predicted output sequence
    """
    # 1. Find where primers anneal on input
    fwd_anneal = find_annealing_region(fwd_primer, input_seq)
    rev_anneal = find_annealing_region(rev_primer, input_seq)

    # 2. Extract overhangs (insertion portions)
    fwd_overhang = get_5prime_overhang(fwd_primer, fwd_anneal)
    rev_overhang = get_5prime_overhang(rev_primer, rev_anneal)

    # 3. Construct product
    # (This is simplified - actual mechanism more complex)
    product = (
        reverse_complement(rev_overhang) +  # RC of rev overhang
        input_seq[rev_anneal_end:fwd_anneal_start] +  # Sequence between primers
        fwd_overhang  # Fwd overhang
    )

    return product
```

## Common Design Patterns

### Pattern 1: Small Insertion (<60 bp)
Put entire insertion in one primer:
```
Fwd: [full insertion]-[20-25 bp annealing]
Rev: [20-25 bp annealing RC]
```

### Pattern 2: Large Insertion (>60 bp)
Split insertion between primers:
```
Fwd: [first half of insertion]-[20-25 bp annealing]
Rev: [RC of second half]-[20-25 bp annealing RC]
```

### Pattern 3: Balanced Tm
Adjust annealing lengths to balance Tm:
```
If Fwd Tm too high: shorten annealing region
If Fwd Tm too low: lengthen annealing region
Keep ΔTm ≤ 5°C (ideally ≤ 2°C)
```

## Troubleshooting

### No Product
- Check primers anneal to INPUT template
- Verify back-to-back orientation
- Confirm Tm calculations are correct
- Check for secondary structures

### Wrong Size Product
- Recalculate expected size
- Verify insertion length is correct
- Check for multiple binding sites

### Wrong Sequence
- Verify insertion sequence is correct
- Check primer orientation
- Confirm overhangs are on correct ends
- Validate simulation matches expectation

## Tool Reference: oligotm

### Basic Usage
```bash
echo "SEQUENCE" | oligotm [flags]
```

### Common Flags for Q5 SDM
```bash
-tp 1    # Thermodynamic table (Breslauer)
-sc 1    # Salt correction method
-mv 50   # Monovalent cation concentration (mM)
-dv 2    # Divalent cation concentration (mM)
-n 0.8   # DNA concentration (μM)
-d 500   # dNTP concentration (μM)
```

### Example
```bash
echo "AGCAAGGGCGAGGAGCTGTTC" | oligotm -tp 1 -sc 1 -mv 50 -dv 2 -n 0.8 -d 500
# Output: Tm value in degrees Celsius
```

### Important Notes
- Use exact flags specified in task requirements
- Different flag values give different Tm results
- Always use oligotm (not simple formulas) for accuracy
