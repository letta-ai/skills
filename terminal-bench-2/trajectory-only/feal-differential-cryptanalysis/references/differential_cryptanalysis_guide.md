# Differential Cryptanalysis: Theory and FEAL Application

## Theoretical Foundation

Differential cryptanalysis, introduced by Biham and Shamir in the early 1990s, exploits the non-uniform distribution of output differences when specific input differences are applied to a cipher.

### Core Principle

For a cipher function E with key K:
- Given plaintext pair (P, P') where P' = P XOR delta_P
- Ciphertexts (C, C') = (E_K(P), E_K(P'))
- The output difference delta_C = C XOR C' is not uniformly distributed

The attack exploits that certain (delta_P -> delta_C) transitions occur with probability higher than 2^(-n) for an n-bit block cipher.

## Building a Differential Characteristic

### Single-Round Differential

For a Feistel round with function F:
```
Input:  (L, R)
Output: (L', R') = (R, L XOR F(R, K))
```

With input difference (delta_L, delta_R):
```
Output difference: (delta_R, delta_L XOR delta_F)
```
where delta_F is the difference in F outputs.

### Multi-Round Characteristic

Chain single-round differentials:

```
Round 0: (a0, b0) --p0--> (a1, b1)
Round 1: (a1, b1) --p1--> (a2, b2)
Round 2: (a2, b2) --p2--> (a3, b3)
```

Total probability: p = p0 * p1 * p2

### Choosing Good Characteristics

Properties of useful characteristics:
1. High overall probability (p >> 2^(-n))
2. Allow key recovery from final round
3. Reduce search space for subkey candidates

## FEAL-Specific Analysis

### The G-Function

FEAL's G-function is defined as:
```
G(a, b, mode) = ROT2((a + b + mode) mod 256)
```

Where ROT2 is a 2-bit left rotation within a byte.

### G-Function Differential Properties

For addition modulo 256:
- Input difference 0x80 in one operand often produces output difference 0x80
- This creates high-probability byte-level differentials

Key observation: The combination of addition and rotation creates biased output differences that can be exploited.

### The F-Function Structure

```
F(X, K) where X = (x0, x1, x2, x3) and K = (k0, k1)

t1 = x0 XOR x1
t2 = x2 XOR x3
y1 = G(t1 XOR k0, t2, 1)
y0 = G(x0, y1, 0)
y2 = G(y1, t2 XOR k1, 0)
y3 = G(y2, x3, 1)

return (y0, y1, y2, y3)
```

### F-Function Differential Distribution

To analyze F-function differentials:

1. Fix an input difference delta_X
2. For each possible X value:
   - Compute F(X) and F(X XOR delta_X)
   - Record the output difference
3. Count frequency of each output difference
4. High-count entries indicate exploitable differentials

### Known High-Probability FEAL Differentials

For FEAL-4, useful differentials include:
- Input differences concentrated in specific bytes
- Output differences that propagate predictably through multiple rounds

## Key Recovery Process

### Last-Round Attack

For a 4-round Feistel cipher:

1. Use a 3-round differential characteristic
2. The characteristic predicts the difference after 3 rounds: (delta_L3, delta_R3)
3. From ciphertext pair (C, C'), compute the actual difference
4. For each candidate last-round subkey:
   - Partially decrypt to get (L3, R3) and (L3', R3')
   - Check if L3 XOR L3' = delta_L3

### Counting Methodology

```
For each candidate subkey K:
    count[K] = 0
    For each plaintext pair (P, P'):
        Partially decrypt (C, C') using K
        If resulting difference matches characteristic:
            count[K] += 1

The correct key should have count significantly higher than 2^(-b) * N
where b is the characteristic probability and N is the number of pairs
```

### Statistical Distinguisher

Expected count for correct key: N * p (where p is characteristic probability)
Expected count for wrong key: N * 2^(-n) (random chance)

For the attack to work: p >> 2^(-n)

## Implementation Checklist

### Before Writing Code

- [ ] Identify the F-function differential distribution
- [ ] Select a high-probability differential characteristic
- [ ] Calculate expected count for correct vs wrong keys
- [ ] Determine number of pairs needed: O(1/p) pairs

### During Implementation

- [ ] Verify F-function implementation matches specification exactly
- [ ] Verify partial decryption formulas are inverses of encryption
- [ ] Test encryption/decryption roundtrip
- [ ] Implement the counting distinguisher

### Verification Steps

- [ ] Test with known key: correct key must score highest
- [ ] Verify score distribution matches theory
- [ ] Check characteristic holds at expected rate for correct key

## Debugging Failed Attacks

### If Correct Key Doesn't Score Highest

1. **Verify F-function**: Compare outputs against reference implementation or test vectors
2. **Check partial decryption**: Verify decrypt(encrypt(x)) = x
3. **Validate characteristic**: Manually trace the differential through rounds with correct key
4. **Confirm pair generation**: Ensure pairs actually have the claimed input difference

### If All Keys Score Similarly

1. **Characteristic probability too low**: Need better characteristic or more pairs
2. **Wrong differential used**: Verify the input difference matches the characteristic
3. **Implementation bug**: Some operation is destroying the differential structure

### If Attack Is Slow

1. **Reduce search space**: Use key schedule constraints
2. **Filter pairs**: Only process pairs where ciphertext difference is consistent with characteristic
3. **Optimize inner loop**: Avoid redundant computations

## Theoretical References

For deeper understanding:
- Biham & Shamir's original differential cryptanalysis papers
- Murphy's analysis of FEAL differential attacks
- The "Handbook of Applied Cryptography" Chapter 7

## Summary: The Right Mental Model

Differential cryptanalysis succeeds because:

1. **Specific input differences** (not random ones) are chosen based on cipher analysis
2. **Predictable output differences** occur at each round with known probability
3. **The characteristic** defines exactly what difference to expect at each stage
4. **Key recovery** works because only the correct key makes intermediate differences match

The attack is deterministic in structure and probabilistic only in how often the characteristic holds. Random statistical heuristics cannot substitute for this principled approach.
