# Incremental Implementation Strategy

## Core Principle

The metacircular property (self-interpretation) must be tested **continuously**, not at the end. Every feature addition must be verified at both level 1 and level 2 before proceeding.

## Phase 1: Minimal Bootstrap

### Goal: Smallest Possible Self-Interpreting Core

Implement only what's needed for the evaluator to interpret itself running a simple program.

**Required features**:
1. Self-evaluating: numbers, booleans
2. Symbol lookup
3. Define (variable definition)
4. If (conditional)
5. Lambda (closure creation)
6. Application (function call)
7. Primitives: +, -, *, /, =, <, >, cons, car, cdr, null?, display, newline

**Bootstrap test program**:
```scheme
;; factorial.scm - tests recursion, conditionals, arithmetic
(define (fact n)
  (if (= n 0)
      1
      (* n (fact (- n 1)))))
(display (fact 5))
(newline)
```

**Testing sequence**:
```bash
# Level 1: Must output 120
echo 'factorial.scm' | python3 interp.py eval.scm

# Level 2: Must also output 120
printf 'eval.scm\nfactorial.scm\n' | python3 interp.py eval.scm
```

**Do not proceed until both levels produce identical output.**

## Phase 2: Adding Features Safely

### Feature Addition Protocol

For each new feature:

1. **Implement the feature**
2. **Create minimal test case**
   ```scheme
   ;; test-quote.scm
   (display (car '(1 2 3)))
   (newline)
   ;; Expected: 1
   ```
3. **Test at level 1**
4. **Test at level 2**
5. **Only proceed if both pass**

### Recommended Feature Order

**Group A: Data manipulation (low risk)**
```
Quote → Let → Begin/Progn
```

**Group B: Control flow (medium risk)**
```
Cond → And/Or (if not primitives)
```

**Group C: Mutation (higher risk)**
```
Set! → Set-car!/Set-cdr!
```

**Group D: I/O (highest risk)**
```
Read → File operations
```

Add Group A completely before Group B. Add each feature one at a time within groups.

## Phase 3: Test Programs

### Minimal Test for Each Feature

**Quote**:
```scheme
;; test-quote.scm
(display 'hello)
(newline)
(display (car '(a b c)))
(newline)
```

**Let**:
```scheme
;; test-let-minimal.scm
(let ((x 42)) (display x) (newline))
```

**Let with multiple bindings**:
```scheme
;; test-let-multiple.scm
(let ((x 1) (y 2))
  (display (+ x y))
  (newline))
```

**Begin/Progn**:
```scheme
;; test-begin.scm
(begin
  (display 1)
  (display 2)
  (display 3)
  (newline))
```

**Cond**:
```scheme
;; test-cond.scm
(cond
  ((= 1 2) (display "wrong"))
  ((= 2 2) (display "right"))
  (else (display "also wrong")))
(newline)
```

**Set!**:
```scheme
;; test-set.scm
(define x 1)
(set! x 2)
(display x)
(newline)
```

**Read**:
```scheme
;; test-read.scm
(display (read))
(newline)
```

### Running Tests at Both Levels

```bash
# Template for all tests
# Level 1
echo 'test-XXX.scm' | python3 interp.py eval.scm

# Level 2
printf 'eval.scm\ntest-XXX.scm\n' | python3 interp.py eval.scm

# For tests requiring input
printf 'test-read.scm\n42\n' | python3 interp.py eval.scm
printf 'eval.scm\ntest-read.scm\n42\n' | python3 interp.py eval.scm
```

## Feature Implementation Details

### Let: Transformation vs Direct Implementation

**Recommended: Lambda transformation**

Transform `let` into lambda application:
```scheme
(let ((x 1) (y 2)) body)
;; Becomes:
((lambda (x y) body) 1 2)
```

This approach:
- Reuses tested lambda implementation
- Avoids new environment manipulation code
- Reduces metacircular bugs

**Implementation**:
```scheme
(define (eval-let expr env)
  (let ((bindings (cadr expr))
        (body (cddr expr)))
    (let ((vars (map car bindings))
          (vals (map cadr bindings)))
      (eval (cons (cons 'lambda (cons vars body))
                  vals)
            env))))
```

**Verification**:
```scheme
;; These must produce identical results:
(let ((x 1)) x)
((lambda (x) x) 1)

;; Test at both levels before considering let complete
```

### Quote: Simple but Critical

Quote must prevent evaluation of its argument:
```scheme
(define (eval-quote expr env)
  (cadr expr))  ; Return the quoted form unevaluated
```

**Common mistake**: Accidentally evaluating the quoted form.

**Test**:
```scheme
(define x 42)
(display 'x)      ; Should print: x (the symbol, not 42)
(display x)       ; Should print: 42
```

### Begin/Progn: Sequential Evaluation

Evaluate each expression in order, return last result:
```scheme
(define (eval-begin expr env)
  (eval-sequence (cdr expr) env))

(define (eval-sequence exprs env)
  (if (null? (cdr exprs))
      (eval (car exprs) env)
      (begin
        (eval (car exprs) env)
        (eval-sequence (cdr exprs) env))))
```

**Test**:
```scheme
(begin
  (define x 1)
  (set! x 2)
  (display x))
;; Should print: 2
```

### Cond: Multi-Branch Conditional

```scheme
(define (eval-cond expr env)
  (eval-cond-clauses (cdr expr) env))

(define (eval-cond-clauses clauses env)
  (if (null? clauses)
      '()  ; No clause matched
      (let ((clause (car clauses)))
        (if (or (eq? (car clause) 'else)
                (eval (car clause) env))
            (eval-sequence (cdr clause) env)
            (eval-cond-clauses (cdr clauses) env)))))
```

**Test edge cases**:
```scheme
;; No match
(cond ((= 1 2) 'never))  ; Returns empty/undefined

;; Else clause
(cond ((= 1 2) 'no)
      (else 'yes))       ; Returns 'yes

;; First match wins
(cond ((= 1 1) 'first)
      ((= 1 1) 'second)) ; Returns 'first
```

## Common Implementation Mistakes

### Mistake 1: Forgetting to Test at Level 2

After implementing a feature:
```
WRONG: "Works at level 1, ship it"
RIGHT: "Works at level 1, now test level 2"
```

### Mistake 2: Adding Multiple Features Before Testing

```
WRONG: Implement quote, let, begin, cond, then test
RIGHT: Implement quote → test L1/L2 → implement let → test L1/L2 → ...
```

### Mistake 3: Complex Tests Before Simple Tests

For let:
```
WRONG: First test (let ((f (lambda (x) (+ x 1)))) (f 5))
RIGHT: First test (let ((x 1)) x)
```

### Mistake 4: Assuming Level 1 Success Implies Level 2 Success

Level 2 has different failure modes related to data structure interpretation. Always test both.

## Verification Checklist

**Phase 1 complete when**:
- [ ] `((lambda (x) x) 42)` works at level 2
- [ ] `(define x 5) x` works at level 2
- [ ] Factorial program works at level 2

**Phase 2 complete when**:
- [ ] Quote works at level 2
- [ ] Let (single binding) works at level 2
- [ ] Let (multiple bindings) works at level 2
- [ ] Begin works at level 2
- [ ] Cond works at level 2

**Phase 3 complete when**:
- [ ] All provided test programs pass at level 1
- [ ] All provided test programs pass at level 2
- [ ] Double metacircular test passes (eval.scm → eval.scm → test.scm)
