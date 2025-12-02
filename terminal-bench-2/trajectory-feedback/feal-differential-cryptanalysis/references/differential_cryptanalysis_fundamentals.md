# Differential Cryptanalysis Fundamentals

## What is Differential Cryptanalysis?

Differential cryptanalysis is a chosen-plaintext attack that analyzes how differences in input plaintexts affect the resulting differences in ciphertexts. The "difference" is typically computed using XOR.

## Key Concepts

### Differential Characteristic

A differential characteristic describes how an input difference propagates through cipher rounds:
- Input difference ΔP = P ⊕ P'
- After round 1: ΔX₁ with probability p₁
- After round 2: ΔX₂ with probability p₂
- ...
- Output difference ΔC with probability p₁ × p₂ × ... × pₙ

### Right Pair vs Wrong Pair

- **Right pair**: A plaintext pair (P, P') whose intermediate differences follow the predicted characteristic
- **Wrong pair**: A pair whose intermediate differences deviate from the characteristic

### Key Recovery Using Differentials

For the final round(s), if an attacker guesses subkey bits:
1. Partially decrypt ciphertexts using the guessed key
2. Check if the partially decrypted difference matches the expected characteristic
3. Correct key: Most pairs satisfy the expected difference
4. Wrong key: Pairs behave randomly (≈50% chance of matching)

## Feistel Network Structure

FEAL uses a Feistel structure where each round:
```
L_{i+1} = R_i
R_{i+1} = L_i ⊕ F(R_i, K_i)
```

Key property: The round function F only affects one half of the state. This creates exploitable dependencies for differential attacks.

## FEAL F-Function Differentials

FEAL's F-function uses addition modulo 256 and rotation, which creates predictable differential behavior:

1. The S-boxes in FEAL have differential characteristics with probabilities significantly higher than ideal (1/256)
2. Specific input differences produce specific output differences with high probability
3. These high-probability differentials enable practical attacks with relatively few chosen plaintexts

## Attack Complexity Factors

The complexity of a differential attack depends on:

1. **Differential probability**: Higher probability = fewer plaintexts needed
2. **Number of rounds**: More rounds = lower overall probability
3. **Key bits recovered per attack**: Determines how many times the attack must be repeated
4. **Signal-to-noise ratio**: How clearly correct keys stand out from incorrect ones

## Distinguisher Design

A good distinguisher for key recovery must:

1. **Exploit structural properties**: Use the expected differential relationship, not generic statistics
2. **Count satisfied constraints**: Track how many pairs satisfy the differential equation
3. **Provide clear separation**: Correct key should satisfy significantly more pairs than incorrect keys
4. **Scale appropriately**: Work with available number of plaintext pairs

## Example: 4-Round FEAL Differential Attack

Simplified attack structure:

1. **Choose input difference**: Select ΔP based on known high-probability characteristic
2. **Collect pairs**: Generate many (P, P') pairs with P' = P ⊕ ΔP
3. **Obtain ciphertexts**: Get (C, C') for each pair
4. **For each candidate key K**:
   - Partially decrypt to round 3 boundary
   - Compute alleged difference at round 3
   - Check if difference matches expected characteristic
   - Count matches
5. **Select key**: Candidate with most matches is likely correct

## Mathematical Foundation

For a Feistel round with:
- Input: (L, R)
- Key: K
- Output: (L', R') where L' = R and R' = L ⊕ F(R, K)

If we have two inputs (L₁, R₁) and (L₂, R₂):
- ΔL = L₁ ⊕ L₂
- ΔR = R₁ ⊕ R₂
- ΔL' = ΔR
- ΔR' = ΔL ⊕ (F(R₁, K) ⊕ F(R₂, K))

The term F(R₁, K) ⊕ F(R₂, K) is the **differential through F**, which depends only on ΔR and has a probabilistic distribution based on F's structure.
