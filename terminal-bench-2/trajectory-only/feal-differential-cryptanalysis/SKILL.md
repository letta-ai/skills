---
name: feal-differential-cryptanalysis
description: Guidance for implementing differential cryptanalysis attacks on FEAL and similar Feistel ciphers. This skill should be used when asked to break FEAL encryption, recover cipher keys through differential attacks, or implement cryptanalysis techniques on block ciphers with weak round functions. Covers proper differential characteristic construction, not ad-hoc statistical methods.
---

# FEAL Differential Cryptanalysis

## Overview

This skill provides guidance for implementing differential cryptanalysis attacks on FEAL (Fast Data Encipherment Algorithm) and similar weak Feistel ciphers. Differential cryptanalysis exploits how specific input differences propagate through a cipher to produce predictable output differences with high probability.

## Critical Concept: What Differential Cryptanalysis Actually Is

Differential cryptanalysis is NOT about finding arbitrary statistical properties that distinguish correct keys. It requires:

1. **A specific input differential** - A chosen difference between plaintext pairs
2. **A differential characteristic** - A predicted path showing how the difference propagates through each round
3. **High probability transitions** - Each round transition must have non-negligible probability
4. **Key recovery condition** - The correct key makes the characteristic hold more often than random

### Common Misconception to Avoid

Do NOT try random statistical heuristics like:
- Entropy of intermediate values
- Hamming weight distributions
- Variance or collision counting
- Generic XOR sums

These approaches lack theoretical grounding and will fail. The attack must be based on the cipher's specific differential properties.

## FEAL Cipher Structure

FEAL is a 4-round Feistel network with the following components:

### The F-Function (Round Function)

The F-function is FEAL's weakness. It uses simple addition and rotation operations that create exploitable differential properties:

```
F(X, K) operates on 32-bit blocks
- Uses the G-function: G(a, b, mode) = ROT2((a + b + mode) mod 256)
- ROT2 rotates left by 2 bits
```

### Round Structure

For each round i:
- L[i+1] = R[i]
- R[i+1] = L[i] XOR F(R[i], K[i])

### Key Schedule

Understanding the key schedule is essential for mapping recovered subkey bits to the master key.

## Attack Methodology

### Step 1: Analyze the F-Function Differential Properties

Before implementing the attack, build a differential distribution table for the F-function:

1. For each possible input difference delta_in (focus on byte-level differences)
2. Compute output differences for all input values
3. Identify high-probability differentials (input diff -> output diff pairs)

For FEAL's G-function:
- Addition modulo 256 with rotation creates biased differentials
- Certain byte differences propagate with probability much higher than 2^-32

### Step 2: Construct a Differential Characteristic

Build a multi-round characteristic by chaining single-round differentials:

```
Round 0: (delta_L0, delta_R0) -> (delta_L1, delta_R1)
Round 1: (delta_L1, delta_R1) -> (delta_L2, delta_R2)
Round 2: (delta_L2, delta_R2) -> (delta_L3, delta_R3)
```

For FEAL-4, use a 3-round characteristic and recover the last round key:
- The characteristic probability is the product of individual round probabilities
- Higher probability = fewer plaintext pairs needed

### Step 3: Collect Plaintext-Ciphertext Pairs

Generate pairs with the chosen input difference:
- P' = P XOR delta_P (the chosen plaintext differential)
- Encrypt both P and P' to get C and C'

### Step 4: Partial Decryption and Key Recovery

For each candidate subkey value:
1. Partially decrypt the last round using the candidate key
2. Check if the resulting intermediate difference matches the characteristic
3. Count how often the characteristic holds for each candidate

The correct key will satisfy the characteristic significantly more often than incorrect keys.

### Step 5: Verification

CRITICAL: Before testing all candidate keys, verify the attack works with the known correct key:
- Compute what the intermediate difference should be for the correct key
- Confirm the characteristic holds at the expected rate
- If verification fails, the characteristic or implementation is wrong

## Verification Strategies

### Pre-Implementation Verification

1. **Trace through manually**: Work through 2-3 pairs by hand with the correct key to confirm the differential propagation

2. **Build the differential table**: Empirically verify F-function differential probabilities match theory

3. **Test characteristic probability**: With known key, confirm the characteristic holds at approximately the predicted rate

### During Implementation

1. **Oracle test**: If the correct key is known for testing, verify it scores highest before running the full attack

2. **Score distribution analysis**: The correct key should be a clear outlier, not just slightly higher

3. **Sanity checks**: Verify partial decryption formulas are correct by encrypting and decrypting test values

## Common Pitfalls

### Pitfall 1: Ad-Hoc Statistical Methods

**Wrong approach**: Trying entropy, hamming weight, variance, or other generic statistical measures

**Why it fails**: These don't exploit the cipher's specific structure and have no theoretical basis for distinguishing keys

**Correct approach**: Use the differential characteristic probability as the distinguisher

### Pitfall 2: Missing the Differential Characteristic

**Wrong approach**: Just XORing values and looking for "patterns"

**Why it fails**: Without a specific characteristic, there's no expected property to verify

**Correct approach**: Define exactly which input difference you're using and what output difference you expect at each round

### Pitfall 3: Incorrect Partial Decryption

**Wrong approach**: Implementing partial decryption without careful verification

**Why it fails**: A single bug means the correct key won't score highest

**Correct approach**: Verify partial decryption by checking encrypt(decrypt(x)) = x for test values

### Pitfall 4: Trial-and-Error Without Theory

**Wrong approach**: Trying different heuristics hoping one works

**Why it fails**: This is computationally expensive and unlikely to succeed

**Correct approach**: Understand WHY the attack works before implementing

### Pitfall 5: Not Verifying Against Known Key

**Wrong approach**: Running the full attack without first testing on known-key scenario

**Why it fails**: Can't diagnose whether the attack or implementation is wrong

**Correct approach**: Always verify the correct key scores highest on a test case first

## Resources

For detailed differential cryptanalysis theory and FEAL-specific attack parameters, see:
- `references/differential_cryptanalysis_guide.md` - Detailed theory and worked examples
