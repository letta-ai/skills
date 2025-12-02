# Linear Cryptanalysis Technical Guide

## Introduction to Linear Cryptanalysis

Linear cryptanalysis is a known-plaintext attack that exploits linear approximations of non-linear cipher components. It was first applied successfully to DES by Matsui in 1993, but FEAL is particularly vulnerable due to its simpler structure.

## FEAL Cipher Structure

### The G-Function

The fundamental building block of FEAL:

```
G(a, b, mode) = ROL2((a + b + mode) mod 256)
```

Where:
- `a`, `b` are 8-bit inputs
- `mode` is 0 or 1
- `ROL2` rotates left by 2 bits
- Addition is modulo 256

### The F-Function (Round Function)

The F-function processes a 32-bit input with a 16-bit subkey:

```
F(x, k) where x = (x0, x1, x2, x3) and k = (k0, k1)

t1 = x0 XOR x1
t2 = x2 XOR x3
y1 = G(t1 XOR k0, t2, 1)
y0 = G(x0, y1, 0)
y2 = G(y1, t2 XOR k1, 0)
y3 = G(y2, x3, 1)

Return (y0, y1, y2, y3)
```

### FEAL-4 Structure

For 4-round FEAL:
- 64-bit plaintext split into two 32-bit halves (L0, R0)
- Initial mixing with subkeys K4, K5
- 4 rounds of Feistel structure
- Final mixing with subkeys K4, K5

## Linear Approximations for FEAL

### G-Function Linear Properties

The addition operation in G has exploitable linear properties:

**Key observation:** For the G-function:
- Input bit i XOR output bit (i+2 mod 8) has bias
- The carry propagation creates predictable linear relationships

**Primary approximations for G(a,b):**
- MSB(a) XOR MSB(b) XOR MSB(output) has bias ~1/4
- Certain bit combinations show bias of 1/2 (deterministic)

### Building Linear Trails

To build a linear trail through FEAL:

1. **Identify active S-boxes (G-functions)**
   - Each round has 4 G-function calls
   - Choose which to include in the approximation

2. **Connect input/output masks**
   - Input mask: which plaintext/key bits affect the approximation
   - Output mask: which ciphertext bits are predicted

3. **Calculate cumulative bias**
   - Use piling-up lemma: ε_total = 2^(n-1) * Π(2ε_i)
   - Where ε_i is bias of each component approximation

### Example Linear Approximation for FEAL-4

A useful approximation:
```
P[5] XOR P[13] XOR P[21] XOR C[5] XOR C[13] XOR C[21] = K[relevant bits]
```

This approximation:
- Involves specific plaintext bits (P)
- Involves specific ciphertext bits (C)
- Equals XOR of specific key bits (K)
- Has bias sufficient for attack with ~2^12 known pairs

## Attack Procedure

### Step 1: Derive Linear Equations

For FEAL-4, derive equations of form:
```
f(P, C) = g(K)
```

Where f is a linear function of plaintext/ciphertext bits and g is a linear function of subkey bits.

### Step 2: Count Statistics

For each known pair (P_i, C_i):
1. Evaluate f(P_i, C_i)
2. Increment count for result (0 or 1)

After processing all pairs:
- If count[0] >> count[1]: g(K) = 0
- If count[1] >> count[0]: g(K) = 1
- If count[0] ≈ count[1]: approximation has wrong key guess

### Step 3: Key Recovery

Two approaches:

**Approach A: Direct Key Bit Recovery**
- Each approximation reveals one linear equation on key bits
- Collect enough equations to solve for key
- Requires multiple independent approximations

**Approach B: Last-Round Attack**
- Guess last round subkey (16 bits)
- Partially decrypt ciphertext to round 3 output
- Evaluate approximation on reduced cipher
- Correct subkey gives maximum bias

### Step 4: Key Schedule Reversal

Once subkeys are known:
- FEAL key schedule is invertible
- Derive master key from subkeys
- Verify by encryption test

## Implementation Guidelines

### Data Structures

```python
# Efficient counting structure
counts = {}  # key_guess -> [count_0, count_1]

# Or for simple approximations
count_0 = 0
count_1 = 0
```

### Bias Calculation

```python
def calculate_bias(count_0, count_1):
    total = count_0 + count_1
    return abs(count_0 - count_1) / total
```

### Key Ranking

```python
def rank_keys(counts, total_pairs):
    rankings = []
    for key_guess, (c0, c1) in counts.items():
        bias = abs(c0 - c1) / total_pairs
        rankings.append((bias, key_guess))
    return sorted(rankings, reverse=True)
```

## Complexity Analysis

### Data Complexity

Number of known pairs needed:
- Depends on total bias of linear trail
- For bias ε: need ~1/ε² pairs
- FEAL-4: typically 20-100 pairs sufficient
- FEAL-8: typically 2^12-2^16 pairs

### Time Complexity

- O(pairs × key_guesses) for last-round attack
- For 16-bit subkey guess: O(pairs × 2^16)
- Much better than O(2^64) brute force

### Memory Complexity

- O(key_guesses) for counting
- O(pairs) for storing known data
- NOT exponential in key size

## Debugging Linear Cryptanalysis

### Verify Approximations

Test with random keys:
```python
def test_approximation(num_tests=10000):
    for _ in range(num_tests):
        key = random_key()
        p = random_plaintext()
        c = encrypt(p, key)
        result = evaluate_approximation(p, c)
        # Should show bias != 0.5
```

### Check for Implementation Errors

Common bugs:
- Bit numbering (MSB vs LSB first)
- Byte ordering (big vs little endian)
- XOR vs addition confusion
- Off-by-one in bit masks

### Validate with Known Key

Always test:
```python
known_key = generate_key()
test_pairs = [(p, encrypt(p, known_key)) for p in random_plaintexts(100)]
recovered_key = run_attack(test_pairs)
assert recovered_key == known_key
```

## References

For further study:
- Matsui, M. "Linear Cryptanalysis Method for DES Cipher" (1993)
- Biham, E. and Shamir, A. "Differential Cryptanalysis of the Data Encryption Standard" (1993)
- FEAL original paper: Shimizu and Miyaguchi (1987)
