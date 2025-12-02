---
name: feal-linear-cryptanalysis
description: This skill provides guidance for FEAL cipher linear cryptanalysis tasks. It should be used when recovering encryption keys from FEAL-encrypted data using known plaintext-ciphertext pairs, implementing linear approximation attacks on block ciphers, or solving cryptanalysis challenges involving the FEAL cipher family. The skill emphasizes mathematical analysis over brute-force approaches.
---

# FEAL Linear Cryptanalysis

## Overview

This skill provides procedural guidance for attacking the FEAL (Fast Data Encipherment Algorithm) cipher using linear cryptanalysis. FEAL is a well-studied cipher with known vulnerabilities that make it susceptible to linear cryptanalysis attacks, which exploit linear approximations of non-linear components to recover key bits statistically.

## Critical Decision Point: Brute Force vs. Linear Cryptanalysis

**Before writing any code, determine the attack approach:**

| Approach | Key Size | Feasibility | Time Complexity |
|----------|----------|-------------|-----------------|
| Brute Force | 32-bit | Feasible | ~2^32 operations |
| Brute Force | 64-bit | Marginal | ~2^64 operations |
| Brute Force | 80+ bit | Infeasible | Days to years |
| Linear Cryptanalysis | Any | Feasible | Polynomial with sufficient pairs |

**Rule of thumb:** If the problem mentions "linear attack" or provides many known plaintext-ciphertext pairs (typically 32+), linear cryptanalysis is the intended approach. Brute force is almost never the answer for academic cryptanalysis challenges.

## Linear Cryptanalysis Approach

### Phase 1: Cipher Analysis

Before implementing any attack:

1. **Study the cipher structure**
   - Identify the G-function (basic operation)
   - Understand the F-function (round function)
   - Map the key schedule and subkey derivation
   - Count the number of rounds

2. **Identify linear approximations**
   - Analyze the G-function for linear biases
   - The G-function typically uses rotation and XOR
   - Find input/output bit masks with bias > 0.5
   - Document approximations with their probabilities

3. **Chain approximations through rounds**
   - Connect single-round approximations
   - Calculate cumulative bias using piling-up lemma: bias = 2^(n-1) * Π(bias_i)
   - Identify which key bits are exposed by each approximation

### Phase 2: Statistical Attack Implementation

1. **Collect statistics from known pairs**
   - For each plaintext-ciphertext pair, evaluate the linear approximation
   - Count how often the approximation holds (equals 0 or 1)
   - The bias indicates the correct key guess

2. **Key recovery strategy**
   - Attack round keys one at a time, typically starting from the last round
   - For each candidate partial key, count approximation matches
   - The correct key produces the strongest bias deviation from 0.5
   - Use maximum likelihood or chi-squared test for key ranking

3. **Recover full key from subkeys**
   - Once round keys are known, reverse the key schedule
   - Verify by encrypting a known plaintext

### Phase 3: Verification

Before running the full attack:

1. **Test with known keys**
   - Generate your own key and encrypt test plaintexts
   - Verify your attack recovers the known key
   - This catches implementation bugs early

2. **Verify cipher implementation**
   - Compare encrypt/decrypt outputs with reference implementations
   - Check that your FEAL implementation matches the provided one exactly

3. **Validate approximation bias**
   - With random keys, verify your approximations show expected bias
   - If bias is ~0.5, the approximation is wrong

## Common Pitfalls

### Pitfall 1: Attempting Brute Force Despite Hints

**Problem:** Ignoring explicit hints about "linear attack" and attempting brute force variations.

**Signs of this mistake:**
- Writing meet-in-the-middle code
- Creating hash tables for partial key enumeration
- Running out of memory with 2^40+ entries
- Optimizing brute force with "prioritized" key values

**Solution:** If a problem mentions linear cryptanalysis, implement linear cryptanalysis. No amount of brute force optimization will work for 80-bit keys.

### Pitfall 2: Insufficient Cipher Analysis

**Problem:** Starting to code without understanding the cipher's mathematical properties.

**Signs of this mistake:**
- Copy-pasting encrypt/decrypt without understanding internals
- Unable to explain what makes FEAL vulnerable
- No identification of specific linear approximations

**Solution:** Read the reference material on FEAL structure. Understand G(a,b) = ROL2((a+b) mod 256) and how this creates linear biases.

### Pitfall 3: Not Verifying Implementation

**Problem:** Running attacks against unknown keys without first testing on known keys.

**Signs of this mistake:**
- Attack produces random-looking results
- No verification that cipher implementation matches specification
- Debugging complex attack logic instead of simple test cases

**Solution:** Always create a test harness:
```
1. Generate random key K
2. Encrypt known plaintext P -> C
3. Run attack with (P, C) pair
4. Verify attack recovers K
```

### Pitfall 4: Memory-Intensive Approaches

**Problem:** Using hash tables or sorted arrays for 2^40+ entries.

**Signs of this mistake:**
- Out-of-memory errors
- Chunked processing that never completes
- Disk-based storage that's too slow

**Solution:** Linear cryptanalysis requires O(n) memory where n is the number of known pairs, not O(2^k) where k is key bits.

### Pitfall 5: Repetitive Failed Attempts

**Problem:** Trying minor variations of the same failed approach instead of fundamentally changing strategy.

**Pattern to recognize:**
1. Write brute-force code -> too slow
2. Add meet-in-the-middle -> out of memory
3. Chunk the hash table -> still too slow
4. Prioritize small keys -> doesn't find key
5. Repeat variations...

**Solution:** After 2-3 failed variations of the same approach, completely abandon it and implement the mathematically correct attack.

## Time Management Strategy

1. **First 10% of time:** Analyze the cipher and understand the attack
2. **Next 20% of time:** Implement and verify with known test vectors
3. **Remaining 70% of time:** Run the actual attack

If still attempting brute force after 30% of available time, stop and implement linear cryptanalysis.

## Complexity Sanity Check

Before running any attack, calculate:

- **Total operations:** Should be polynomial in the number of pairs, not exponential in key size
- **Memory usage:** Should be O(pairs), not O(2^key_bits)
- **Expected runtime:** Should complete in minutes, not hours

If calculations show infeasibility, the approach is wrong.

## Resources

For detailed technical information on FEAL structure and linear approximation derivation, refer to:
- `references/linear_cryptanalysis_guide.md` - Detailed guide on linear cryptanalysis techniques and FEAL-specific approximations
