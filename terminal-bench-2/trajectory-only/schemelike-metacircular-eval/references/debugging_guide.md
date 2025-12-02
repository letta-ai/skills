# Debugging Metacircular Evaluators

## Understanding Interpretation Levels

When debugging, always be explicit about which level is failing:

- **Level 0**: Host language (e.g., Python running interp.py)
- **Level 1**: eval.scm running on the host
- **Level 2**: eval.scm interpreting eval.scm
- **Level N**: N nested interpreters

**Critical rule**: Never test at level N+1 until level N works perfectly.

## Systematic Debugging Process

### Step 1: Find the Minimal Failing Test

When something fails at level 2, bisect to find the smallest test case:

```scheme
;; If this fails at level 2:
(let ((x (read))) (display x))

;; Test these individually at level 2:
42                            ; Self-evaluating
(+ 1 2)                       ; Primitive application
(read)                        ; I/O
(let ((x 42)) x)              ; Let binding
(display 42)                  ; Output
```

Continue bisecting until you have the minimal failing case.

### Step 2: Compare Level 1 and Level 2 Behavior

For the minimal failing test:

```bash
# Level 1 test
echo 'test.scm' | python3 interp.py eval.scm

# Level 2 test
printf 'eval.scm\ntest.scm\n' | python3 interp.py eval.scm
```

**Key question**: Does it work at level 1 but fail at level 2?
- **Yes** → Issue with data structure representation at level 2
- **No** → Issue with basic implementation logic

### Step 3: Trace Data Structure Transformations

At level 2, data structures are themselves interpreted. Trace how structures transform:

```
Expression: ((lambda (x) x) 42)

At Level 1:
1. Evaluate (lambda (x) x) → closure object
2. Evaluate 42 → 42
3. Extend environment: env = (((x) . (42)) . parent)
4. Evaluate body 'x' in extended env → lookup returns 42

At Level 2:
1. Outer eval interprets (lambda (x) x)
   - Creates closure as LIST data: ('procedure '(x) '(x) env-data)
2. Outer eval interprets 42 → 42
3. Outer eval extends environment
   - Environment is now a LIST of LISTS
   - env = (((x) . (42)) . parent) but each piece is interpreted data
4. Outer eval evaluates body 'x'
   - Must traverse interpreted environment structure correctly
```

### Step 4: Verify Data Structure Invariants

Create diagnostic programs to inspect structure at both levels:

```scheme
;; test-env-structure.scm
(define test-env (extend-env '(x) '(42) '()))
(display "Frame: ")
(display (car test-env))
(newline)
(display "Vars: ")
(display (car (car test-env)))
(newline)
(display "Vals: ")
(display (cdr (car test-env)))
(newline)
```

Run at level 1 and level 2. Outputs must match.

## Common Failure Patterns

### Pattern 1: Lambda Body Not Evaluated at Level 2

**Symptoms**:
- `((lambda (x) x) 42)` returns nothing or wrong value
- No error, just missing output

**Debug sequence**:
```scheme
;; Test in order, stop at first failure
((lambda (x) x) 42)           ; Return parameter
((lambda (x) 42) 99)          ; Return constant
((lambda (x) (+ x 1)) 5)      ; Simple computation
((lambda (x) (display x)) 42) ; Side effect in body
```

**Likely causes**:
1. Environment extension creates malformed structure at level 2
2. Body extraction from closure fails
3. eval-sequence receives wrong argument type

**Solution approach**:
1. Verify `extend-env` creates correct structure at level 2
2. Verify closure body can be extracted: `(caddr closure)` or equivalent
3. Add instrumentation to verify body evaluation is attempted

### Pattern 2: Infinite Recursion with Primitives

**Symptoms**:
- Recursion limit exceeded
- Error messages mention 'not', 'null?', 'eq?'

**Cause**: Using host-level operations that share names with interpreted primitives.

**Example problem**:
```scheme
;; In evaluator code:
(if (not (null? bindings)) ...)

;; At level 2, 'not' might:
;; - Lookup 'not' in environment
;; - Find primitive
;; - Primitive tries to call interpreted 'not'
;; - Infinite loop
```

**Solutions**:
```scheme
;; Option 1: Use explicit comparisons
(if (null? bindings) #f ...)  ; Instead of (not (null? bindings))
(eq? x #f)                     ; Instead of (not x)

;; Option 2: Rename primitives internally
;; Bind 'not' to (primitive 'my-not) in environment
;; Evaluator code uses 'my-not' directly
```

### Pattern 3: List Construction Creates Dotted Pairs

**Symptoms**:
- Expressions appear malformed
- Error about improper lists
- `cdr` returns element instead of list

**Example**:
```scheme
;; Intention: create application ((lambda ...) arg1 arg2)
(cons lambda-expr args)

;; If args = (val1 val2), result is:
;; ((lambda ...) . (val1 val2))  -- WRONG: dotted pair

;; Needed:
;; ((lambda ...) val1 val2)      -- CORRECT: proper list
```

**Debug check**:
```scheme
;; Verify list structure
(define test (cons 'a '(b c)))
(display (cdr test))           ; Should be (b c) not c
(display (cdr (cdr test)))     ; Should be (c) not error
```

### Pattern 4: EOF/Empty List/False Confusion

**Symptoms**:
- Conditionals make wrong decisions
- File reading terminates early
- Empty lists treated as false

**Understanding truthiness**:
```scheme
(if #f 'wrong 'right)     ; → right (false is falsy)
(if '() 'right 'wrong)    ; → right (empty list is TRUTHY!)
(if 0 'right 'wrong)      ; → right (zero is truthy)
```

**Check what operations return**:
```scheme
;; What does fread return at EOF?
;; Could be: '() or #f or implementation-specific null
;; Test explicitly to know

(define result (fread file-handle))
(if (null? result)
    (display "got empty list")
    (if (eq? result #f)
        (display "got false")
        (display "got something else")))
```

### Pattern 5: Input Stream Consumed at Wrong Level

**Symptoms**:
- Read returns unexpected values
- EOF reached too early
- Intermittent failures depending on input

**Understanding input flow**:
```
Input: "eval.scm\ntest.scm\nhello\n"

Outer eval.scm reads: "eval.scm"  ← first line
Inner eval.scm reads: "test.scm"  ← second line
test.scm reads:       "hello"     ← third line
```

**Debug with explicit input verification**:
```bash
# Show exactly what bytes are being sent
printf 'eval.scm\ntest.scm\nhello\n' | xxd

# Use tee to see input as it's consumed
printf 'eval.scm\ntest.scm\nhello\n' | tee /dev/stderr | python3 interp.py eval.scm
```

## Testing Without Print Statements

If instrumentation is difficult:

**Test return values**:
```scheme
;; Temporarily make function return sentinel
(define (extend-env vars vals env)
  'EXTEND-CALLED)  ; Verify this path executes
```

**Test with strategic errors**:
```scheme
;; Add error at specific point
(define (eval expr env)
  (if (eq? expr 'TRIGGER)
      (error "Reached checkpoint 1")
      ...))
```

**Use file I/O**:
```scheme
;; Write to file instead of stdout
(define debug-file (fopen "debug.log" "w"))
(fdisplay debug-file "checkpoint reached")
(fclose debug-file)
```

## Recovery Strategies

### When Stuck on Level 2

1. **Verify level 1 exhaustively**
   - Every feature
   - Edge cases (empty lists, zero, negative numbers)
   - Combinations of features

2. **Test environment operations in isolation**
   ```scheme
   ;; Create test program just for environment
   (define env1 (extend-env '() '() '()))
   (define env2 (extend-env '(x) '(1) env1))
   (define env3 (extend-env '(y) '(2) env2))
   (display (lookup 'x env3))  ; Should be 1
   (display (lookup 'y env3))  ; Should be 2
   ```

3. **Consider transformation approach**
   - Convert complex forms to simpler ones
   - `let` → `lambda` application
   - `cond` → nested `if`

4. **Start core evaluator fresh**
   - Sometimes faster than debugging
   - Apply lessons learned
   - Build minimally, test at both levels immediately

### When Nothing Seems to Work

The core insight: bugs in metacircular evaluators often stem from **implicit assumptions** about data representation that break when the evaluator interprets itself.

**Find the assumption**:
- What does the code assume about environment structure?
- What does it assume about closure representation?
- What does it assume about list structure?

**Make it explicit**:
- Add verification code
- Test the assumption at level 2

**Fix or change**:
- Either the assumption needs fixing
- Or the representation needs changing

The evaluator and the interpreted code must handle data structures identically—the same operations must produce the same results regardless of interpretation level.
