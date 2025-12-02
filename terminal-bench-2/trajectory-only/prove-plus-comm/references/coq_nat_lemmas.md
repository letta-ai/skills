# Coq Natural Number Arithmetic Lemmas Reference

This reference documents standard lemmas from Coq's Arith library commonly used in proofs about natural number arithmetic.

## Core Addition Lemmas

### Identity and Zero

| Lemma | Type | Description |
|-------|------|-------------|
| `plus_O_n` | `forall n, 0 + n = n` | Left identity (definitional) |
| `plus_n_O` | `forall n, n = n + 0` | Right identity (requires proof) |

### Successor Lemmas

| Lemma | Type | Description |
|-------|------|-------------|
| `plus_Sn_m` | `forall n m, S n + m = S (n + m)` | Successor on left (definitional) |
| `plus_n_Sm` | `forall n m, S (n + m) = n + S m` | Successor on right |

### Commutativity and Associativity

| Lemma | Type | Description |
|-------|------|-------------|
| `plus_comm` | `forall n m, n + m = m + n` | Addition commutativity |
| `plus_assoc` | `forall n m p, n + (m + p) = (n + m) + p` | Addition associativity |

## Definitional Equalities in Coq

These hold by computation (reflexivity after simpl):

```coq
0 + n = n           (* By definition of plus *)
S n + m = S (n + m) (* By definition of plus *)
```

These require lemmas (not definitional):

```coq
n + 0 = n           (* Requires plus_n_O *)
n + S m = S (n + m) (* Requires plus_n_Sm *)
```

## Induction on Natural Numbers

The `induction` tactic on `nat` generates two subgoals:

1. **Base case**: Prove property holds for `0`
2. **Inductive case**: Given property holds for `n'` (the IH), prove it holds for `S n'`

Standard form:

```coq
induction n as [| n' IHn'].
- (* Base case: n = 0 *)
  ...
- (* Inductive case: n = S n', with IHn' : P n' *)
  ...
```

## Rewrite Tactic Reference

### Direction

- `rewrite H` : Replace LHS of H with RHS (left-to-right)
- `rewrite <- H` : Replace RHS of H with LHS (right-to-left)

### Multiple Rewrites

- `rewrite H1, H2` : Apply H1 then H2
- `rewrite !H` : Apply H repeatedly until it fails

### In Specific Hypothesis

- `rewrite H in H'` : Rewrite in hypothesis H' instead of goal

## Common Proof Tactics for Arithmetic

| Tactic | Effect |
|--------|--------|
| `simpl` | Simplify using definitions |
| `reflexivity` | Solve goals of form `x = x` |
| `rewrite H` | Replace using equality H |
| `symmetry` | Swap sides of equality goal |
| `f_equal` | Reduce `f x = f y` to `x = y` |
| `ring` | Solve ring arithmetic goals (requires Ring import) |
| `omega` / `lia` | Solve linear arithmetic goals |

## Proof Template for Commutative Property

General pattern for proving `forall n m, f n m = f m n`:

```coq
Theorem f_comm : forall n m, f n m = f m n.
Proof.
  intros n m.
  induction n as [| n' IHn'].
  - (* Base case *)
    simpl.
    (* Apply base case lemmas *)
    reflexivity.
  - (* Inductive case *)
    simpl.
    rewrite IHn'.
    (* Apply successor lemmas *)
    reflexivity.
Qed.
```

## Troubleshooting

### "Cannot find a physical path bound to logical path"

Import the Arith library:

```coq
Require Import Arith.
```

### Goal has wrong form after rewrite

Check lemma direction with `Check lemma_name.` and use `<-` if needed.

### Inductive hypothesis doesn't match

Ensure induction is on the correct variable and the IH pattern matches the goal structure.
