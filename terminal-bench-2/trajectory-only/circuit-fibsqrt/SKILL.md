---
name: circuit-fibsqrt
description: Guidance for building digital logic circuits that compute composite functions like Fibonacci of integer square root. This skill applies when implementing combinational and sequential logic in gate-level simulators, particularly when combining algorithms (like isqrt and Fibonacci) under resource constraints (gate counts, simulation steps). Use for circuit synthesis, HDL-style logic design, or gate-level algorithm implementation tasks.
---

# Circuit Fibsqrt

## Overview

This skill provides guidance for designing and implementing digital logic circuits that compute composite mathematical functions. The canonical example is computing `fib(isqrt(N))` - the Fibonacci number at the index equal to the integer square root of N. These tasks require combining combinational logic (pure functions like isqrt) with sequential logic (stateful computations like Fibonacci iteration) while respecting resource constraints.

## Problem Analysis Framework

### Before Implementation: Understanding the Execution Model

Before writing any circuit logic, verify understanding of the simulator's execution model:

1. **Input handling** - Determine how input signals are initialized and whether they need explicit identity mappings (`out{i} = out{i}`) or are passed through automatically
2. **Feedback propagation** - Understand how the simulator handles cycles and when signal values stabilize
3. **Timing semantics** - Determine whether the simulator is synchronous (clock-driven) or asynchronous (event-driven with propagation delays)
4. **Step limits** - Identify maximum simulation steps allowed and verify the algorithm can complete within this budget

Create minimal test cases to validate each assumption before building the full circuit.

### Algorithm Decomposition

Decompose the problem into independent components:

1. **Combinational components** - Pure functions computed in a single pass (e.g., isqrt)
2. **Sequential components** - Stateful computations requiring iteration (e.g., Fibonacci)
3. **Control logic** - State machines coordinating the sequential computation
4. **Glue logic** - Multiplexers, comparators, and routing between components

### Resource Estimation

Before implementing, estimate resource usage:

- **Gate count per component** - Rough estimates prevent wasted effort on infeasible approaches
- **Iteration count** - For sequential logic, calculate worst-case iterations (e.g., `isqrt(2^32-1) ≈ 65535` for 32-bit inputs)
- **Simulation steps** - Verify maximum iterations fit within step limits

## Implementation Approach

### Integer Square Root (isqrt)

The bit-by-bit isqrt algorithm builds the result one bit at a time from MSB to LSB:

```
result = 0
for bit from (output_bits-1) down to 0:
    test = result | (1 << bit)
    if test * test <= N:
        result = test
```

Key implementation considerations:
- Avoid multiplication-based approaches if gate count is constrained
- Use the identity: `(result + 2^bit)^2 = result^2 + 2*result*2^bit + 2^(2*bit)`
- Track the running square incrementally to avoid recomputation
- Verify the mathematical relationships on paper before coding

### Fibonacci Sequence

Fibonacci requires sequential state updates:

```
state: (a, b, counter)
initial: (0, 1, target_index)
update: (b, a+b, counter-1)
done: counter == 0
output: a
```

Key implementation considerations:
- Use multiplexers to select between initial values and updated values based on state
- Ensure proper feedback loop timing - new values must propagate before next iteration
- Handle edge cases: `fib(0) = 0`, `fib(1) = 1`

### State Machine Design

For sequential components, define states explicitly:

1. **INIT** - Load initial values, compute combinational components
2. **ITERATE** - Perform one step of sequential computation
3. **DONE** - Output final result

Use a counter or explicit state register to track progress. Multiplexers select between:
- Initial values (when starting)
- Previous iteration values (when continuing)
- Final values (when done)

## Verification Strategy

### Component-Level Testing

Test each component in isolation before integration:

1. **Adder verification** - Test with known values across bit width
2. **isqrt verification** - Test perfect squares and non-perfect squares
3. **Fibonacci verification** - Test small indices with known values
4. **Multiplexer verification** - Verify selector logic and value routing

### Integration Testing

Test the combined circuit with progressively complex inputs:

1. **Trivial cases** - N=0, N=1 (edge cases for both algorithms)
2. **Perfect squares** - N=4, N=9, N=16 (isqrt returns exact values)
3. **Non-perfect squares** - N=5, N=10, N=20 (isqrt truncates)
4. **Larger values** - Verify correct behavior with multi-digit Fibonacci results

### Debugging Approach

When the circuit produces incorrect output:

1. **Add intermediate outputs** - Expose internal signals to verify component behavior
2. **Trace execution** - Follow signal values through iterations
3. **Isolate failures** - Determine which component produces the first incorrect value
4. **Check selector logic** - Multiplexer argument order is a common source of bugs

## Common Pitfalls

### Input Signal Initialization

A critical bug pattern: setting input signals to constant 0 instead of passing them through. If the simulator expects identity mappings for inputs (`out{i} = out{i}`), omitting this causes all inputs to read as 0.

**Symptom**: Circuit produces the same output regardless of input value.

### Algorithm Implementation Errors

Working through algorithms on paper before implementing prevents:
- Using incorrect formulas (e.g., wrong square difference calculation in isqrt)
- Off-by-one errors in bit positions or loop bounds
- Missing edge cases in conditional logic

### Multiplexer Argument Order

Multiplexers select between inputs based on a control signal. Reversing the argument order causes inverted selection logic:
- `mux(sel, a, b)` might mean "if sel then a else b" or "if sel then b else a"
- Verify the semantics of your mux implementation before use

### Feedback Loop Timing

In sequential circuits with feedback:
- Values from the previous iteration must be stable before computing the next iteration
- The control signal (counter/state) must update consistently with data values
- Test that the state machine transitions correctly through all phases

### Gate Count Overflow

Complex operations like multiplication can exceed gate limits:
- Prefer incremental algorithms (bit-by-bit) over direct computation
- Estimate gate counts before implementation
- Consider alternative algorithms if approaching limits

## Resource References

When implementing, load `references/debugging_guide.md` for detailed debugging strategies specific to gate-level circuit simulation.
