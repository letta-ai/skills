---
name: schemelike-metacircular-eval
description: Guide for implementing metacircular evaluators—interpreters that can interpret themselves. This skill should be used when building self-interpreting Scheme-like evaluators, debugging multi-level interpretation issues, or implementing language features like environments, closures, and special forms. Focuses on incremental development, continuous metacircular testing, and systematic debugging of nested interpretation failures.
---

# Metacircular Evaluator Implementation

## Overview

This skill provides systematic guidance for implementing metacircular evaluators—interpreters written in the language they interpret. The critical challenge is not just building a working interpreter, but building one that can interpret itself (the metacircular property).

## Critical Success Factors

### The Metacircular Property is Non-Negotiable

A metacircular evaluator must pass this test:
```bash
# Level 1: Direct interpretation
echo 'test-program.scm' | interpreter eval.scm

# Level 2: Self-interpretation (MUST produce same output)
echo -e 'eval.scm\ntest-program.scm' | interpreter eval.scm
```

Test the metacircular property **continuously throughout development**, not just at the end. Every feature must work at both levels before adding the next.

### Build Incrementally, Test at Both Levels

**Wrong approach**: Implement all features, then test metacircular property.

**Correct approach**: For each feature:
1. Implement the feature
2. Test at level 1 (direct interpretation)
3. Test at level 2 (self-interpretation) with minimal test case
4. Only proceed to next feature after both levels pass

## Implementation Strategy

### Phase 1: Minimal Self-Interpreting Core

Start with the smallest possible evaluator that can interpret itself:

**Required features for bootstrap**:
- Self-evaluating expressions (numbers, booleans)
- Variable lookup
- Define (variable form)
- If (conditional)
- Lambda (closure creation)
- Application (function call)
- Basic primitives (arithmetic, comparison, cons/car/cdr)

**Test program for bootstrap verification**:
```scheme
;; bootstrap-test.scm
(define (fact n)
  (if (= n 0)
      1
      (* n (fact (- n 1)))))
(display (fact 5))
(newline)
```

Run at both levels. If level 2 fails, **stop and debug** before adding features.

### Phase 2: Adding Features Safely

After the core works metacircularly, add features one at a time:

1. **Quote**: Prevent evaluation of literal data
2. **Let**: Variable binding (recommend lambda transformation)
3. **Begin/Progn**: Sequential evaluation
4. **Cond**: Multi-branch conditionals
5. **Set!**: Mutation
6. **I/O operations**: Read, display, file operations (last)

For each addition, create a minimal test and verify at both levels.

## Environment Implementation

### Representation Pattern

Use a structure that can be manipulated consistently at all interpretation levels:

```scheme
;; Environment as list of frames
;; Frame = (vars . vals) where vars and vals are parallel lists
;; env = (frame1 frame2 ... global-frame)

(define (extend-env vars vals base-env)
  (cons (cons vars vals) base-env))

(define (lookup var env)
  (if (null? env)
      (error "Undefined variable:" var)
      (lookup-in-frame var (car env)
                       (lambda () (lookup var (cdr env))))))
```

### Critical Invariants

After any environment operation, verify:
- Variable list and value list have same length
- Frame structure is `(vars . vals)` not `((vars vals))`
- Lookup traverses correctly through frame chain

### Common Environment Bugs

**Bug**: Dotted pairs vs. proper lists
```scheme
;; Wrong: creates single frame, not extendable
(cons vars vals)  ; If vars=(x y), vals=(1 2), result is ((x y) . (1 2))

;; Verify structure manually before proceeding
```

**Bug**: Environment extension corrupts at level 2

At level 2, environments are interpreted data structures. The same `extend-env` code manipulates different representations at different levels. Test environment operations in isolation at level 2:

```scheme
;; test-env-level2.scm
(define env (extend-env '(x) '(42) '()))
(display (lookup 'x env))
(newline)
```

## Special Form Implementation

### Let: Prefer Lambda Transformation

Direct `let` implementation is error-prone for metacircular evaluation. Transform instead:

```scheme
;; Transform: (let ((x 1) (y 2)) body...)
;; Into:      ((lambda (x y) body...) 1 2)
```

**Verification steps**:
1. Manually transform example let expressions
2. Verify the transformed expression is a proper list (not dotted pair)
3. Test: `(let ((x 1)) x)` should behave exactly like `((lambda (x) x) 1)`

### Lambda: Capture Environment Correctly

Lambda must capture the environment at definition time, not evaluation time:

```scheme
(define (make-procedure params body env)
  (list 'procedure params body env))  ; env captured here
```

**Test closure capture**:
```scheme
(define (make-adder n)
  (lambda (x) (+ x n)))  ; n must be captured

((make-adder 5) 3)  ; Must return 8
```

## Debugging Multi-Level Failures

### When Level 1 Works but Level 2 Fails

This is the most common and difficult debugging scenario.

**Step 1: Isolate the failing feature**

If `(let ((x 5)) (display x))` fails at level 2:
- Test `((lambda (x) x) 5)` at level 2
- Test `(define x 5) x` at level 2
- Test `(display 42)` at level 2

Find the smallest failing case.

**Step 2: Trace data structure transformations**

At level 2, data structures are themselves interpreted. Manually trace:
```
Expression: ((lambda (x) x) 42)

Level 1:
- Create closure: (procedure (x) ((x)) env1)
- Extend env: env2 = (((x) . (42)) . env1)
- Lookup x: 42

Level 2:
- Outer eval creates inner closure as data structure
- Inner closure's environment is also a data structure
- Verify: Can lookup still traverse this nested representation?
```

**Step 3: Check representation invariants**

Create diagnostic programs:
```scheme
;; test-structure.scm
(define env (extend-env '(x) '(42) '()))
(display (car env))        ; Frame
(display (car (car env)))  ; Variables list
(display (cdr (car env)))  ; Values list
```

Run at level 1 and level 2. Compare outputs.

### Common Failure Patterns

**Pattern: Lambda body not evaluated at level 2**

Symptom: `((lambda (x) (display x)) 42)` prints nothing at level 2.

Likely cause: Environment extension creates malformed structure at level 2, causing body evaluation to fail silently.

Debug: Test `((lambda (x) x) 42)` first (simpler body).

**Pattern: Infinite recursion with primitive names**

Symptom: Recursion error mentioning primitives like 'not', 'null?', 'eq?'.

Likely cause: Host-level operations in evaluator code conflicting with interpreted primitives.

Solution: Use explicit comparisons in evaluator code:
```scheme
;; Instead of: (not (null? x))
;; Use: (if (null? x) #f #t)
;; Or: (eq? x #f)
```

**Pattern: EOF/input confusion**

Symptom: Read returns wrong values or EOF too early at level 2.

Likely cause: Input stream consumed at wrong level.

Debug: Use `printf` not `echo -e` (behavior varies by shell):
```bash
# Reliable input formatting
printf 'eval.scm\ntest.scm\ninput-line\n' | interpreter eval.scm
```

## Verification Checklist

Before considering the evaluator complete:

**Core features at level 1**:
- [ ] Numbers, booleans self-evaluate
- [ ] Variable lookup works
- [ ] Define creates bindings
- [ ] Lambda creates closures
- [ ] Application evaluates and applies
- [ ] If evaluates correct branch only
- [ ] Primitives (+, -, *, /, =, <, >, cons, car, cdr, null?) work

**Metacircular property (level 2)**:
- [ ] `42` evaluates to 42
- [ ] `(+ 1 2)` evaluates to 3
- [ ] `((lambda (x) x) 42)` evaluates to 42
- [ ] `((lambda (x) (+ x 1)) 5)` evaluates to 6
- [ ] `(define x 5) x` evaluates to 5
- [ ] Factorial program produces correct output
- [ ] All test programs produce same output at level 1 and level 2

**Full self-interpretation**:
- [ ] `eval.scm` can interpret `eval.scm` interpreting test programs
- [ ] Double metacircular (`eval.scm` → `eval.scm` → `test.scm`) works

## Anti-Patterns to Avoid

### Don't implement all features before testing metacircular property

Every untested feature may introduce bugs that cascade. Test at both levels after each feature.

### Don't use trial-and-error debugging

When level 2 fails, systematically:
1. Find minimal failing test
2. Trace data structure transformations
3. Verify representation invariants

Don't randomly modify code hoping it works.

### Don't assume primitives work identically at all levels

`(eq? 'x 'x)` may behave differently when symbols are interpreted data at level 2. Test primitive operations on interpreted data structures explicitly.

### Don't write extensive code before incremental testing

The initial evaluator should be as small as possible while still being self-interpreting. Add complexity only after the core works metacircularly.

## I/O Handling

### Input stream management

When eval.scm interprets itself:
```
stdin: "eval.scm\ntest.scm\ninput1\n"
       ^-- outer eval reads this
              ^-- inner eval reads this
                       ^-- interpreted program reads this
```

Each read consumes from the same sequential stream across all levels.

### Testing I/O in isolation

```bash
# Test read works at level 1
echo "42" | python3 interp.py test-read.scm

# Test read works at level 2
printf 'test-read.scm\n42\n' | python3 interp.py eval.scm

# Verify input bytes are correct
printf 'line1\nline2\n' | cat -A
```

## Recovery Strategies

### When completely stuck

1. **Simplify**: Remove features until something works at level 2
2. **Verify host**: Confirm the host interpreter works as expected
3. **Test components**: Verify environment operations separately
4. **Minimal rewrite**: Sometimes starting the core evaluator fresh with lessons learned is faster than debugging

### When level 2 seems impossible

The core insight: if level 2 fails, the evaluator is making assumptions about data representation that break when the evaluator interprets itself.

1. Identify what assumption is failing
2. Make the assumption explicit (verify it with test code)
3. Fix the assumption or change the representation

The evaluator and the interpreted program must handle data structures identically.
