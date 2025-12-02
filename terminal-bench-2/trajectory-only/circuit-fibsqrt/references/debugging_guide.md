# Circuit Debugging Guide

## Systematic Debugging Methodology

When a circuit produces incorrect output, follow this systematic approach to isolate and fix the problem.

### Step 1: Verify Input Handling

First, confirm inputs are being read correctly:

1. Create a passthrough test - output should equal input directly
2. Test with multiple input values to confirm they differ
3. If all outputs are identical regardless of input, check input signal initialization

Common input initialization patterns:
- Some simulators require explicit identity: `out{i} = in{i}` or `out{i} = out{i}`
- Some simulators auto-pass inputs
- Setting inputs to constant 0 is a common mistake

### Step 2: Test Primitive Operations

Verify basic gates work as expected:

1. **AND gate** - Test: `1 AND 1 = 1`, `1 AND 0 = 0`
2. **OR gate** - Test: `0 OR 1 = 1`, `0 OR 0 = 0`
3. **XOR gate** - Test: `1 XOR 1 = 0`, `1 XOR 0 = 1`
4. **NOT gate** - Test: `NOT 0 = 1`, `NOT 1 = 0`

### Step 3: Test Compound Operations

Build up complexity incrementally:

1. **N-bit adder** - Test: `3 + 5 = 8`, verify carry propagation with `255 + 1 = 256`
2. **Comparator** - Test: `5 < 10 = 1`, `10 < 5 = 0`, `5 < 5 = 0`
3. **Multiplexer** - Test selector with both 0 and 1, verify correct value selected

### Step 4: Isolate Component Failures

For composite circuits, test components independently:

1. Extract the isqrt subcircuit - test: `isqrt(16) = 4`, `isqrt(17) = 4`, `isqrt(0) = 0`
2. Extract the Fibonacci subcircuit - test: `fib(0) = 0`, `fib(1) = 1`, `fib(10) = 55`
3. Test control logic separately - verify state transitions

### Step 5: Add Debug Outputs

Expose intermediate signals to trace execution:

```
# Example: expose isqrt result as debug output
debug_isqrt_result = [output bits of isqrt component]

# Example: expose Fibonacci state
debug_fib_a = [current 'a' register]
debug_fib_b = [current 'b' register]
debug_counter = [iteration counter]
```

Run simulation and examine intermediate values at each step.

## Common Bug Patterns and Fixes

### Pattern: Output Always Zero

**Symptoms**: Output is 0 regardless of input.

**Likely Causes**:
1. Input signals not connected properly
2. Gate output not routed to final output
3. Control signal stuck, causing mux to always select 0

**Debug Steps**:
1. Add debug output for raw input
2. Trace signal path from input to output
3. Check control/selector signals

### Pattern: Output Constant But Non-Zero

**Symptoms**: Output is always the same non-zero value.

**Likely Causes**:
1. Sequential logic not iterating (counter stuck)
2. Feedback not connected
3. Initial value being output without updates

**Debug Steps**:
1. Output the iteration counter
2. Verify feedback connections
3. Check done/ready signal logic

### Pattern: Off-By-One Errors

**Symptoms**: Output is close to expected but consistently wrong.

**Likely Causes**:
1. Loop bounds incorrect (< vs <=)
2. Counter initialized to wrong value
3. Output taken from wrong state variable

**Debug Steps**:
1. Trace state through iterations
2. Verify initial counter value
3. Check which variable holds final result

### Pattern: Correct for Small Inputs, Wrong for Large

**Symptoms**: Works for inputs like 0, 1, 4 but fails for larger values.

**Likely Causes**:
1. Bit width insufficient (overflow)
2. Algorithm only handles subset of cases
3. Carry propagation issues in adders

**Debug Steps**:
1. Check bit widths of all intermediate values
2. Verify adder handles full range
3. Test boundary values explicitly

### Pattern: Intermittent Failures

**Symptoms**: Sometimes correct, sometimes wrong for same input.

**Likely Causes**:
1. Race conditions in asynchronous logic
2. Uninitialized state
3. Timing-dependent feedback behavior

**Debug Steps**:
1. Add extra propagation steps
2. Verify all state is properly initialized
3. Check feedback timing

## Testing Framework Pattern

Create a reusable testing harness to avoid duplicating test code:

```python
class CircuitTester:
    def __init__(self, circuit_generator, simulator):
        self.generator = circuit_generator
        self.simulator = simulator

    def test_case(self, input_val, expected_output):
        circuit = self.generator()
        result = self.simulator.run(circuit, input_val)
        return result == expected_output

    def run_suite(self, test_cases):
        results = []
        for input_val, expected in test_cases:
            passed = self.test_case(input_val, expected)
            results.append((input_val, expected, passed))
        return results
```

### Standard Test Suites

**isqrt test cases**:
- (0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (8, 2), (9, 3), (15, 3), (16, 4), (100, 10)

**Fibonacci test cases**:
- (0, 0), (1, 1), (2, 1), (3, 2), (4, 3), (5, 5), (10, 55), (20, 6765)

**Combined fib(isqrt(N)) test cases**:
- (0, 0), (1, 1), (4, 1), (9, 2), (16, 3), (25, 5), (100, 55), (208, 377)

## Gate Count Estimation

Estimate gate requirements before implementation:

| Component | Approximate Gates |
|-----------|------------------|
| N-bit ripple adder | 5N |
| N-bit carry-lookahead adder | 10N |
| N-bit comparator | 3N |
| N-bit multiplexer (2:1) | 3N |
| N-bit AND/OR/XOR | N |
| N-bit multiplier | N² to N²log(N) |

For a 32-bit fib(isqrt(N)) implementation:
- isqrt (bit-by-bit): ~16 iterations × ~200 gates = ~3200 gates
- Fibonacci iteration: ~3 adders + muxes = ~500 gates
- Control logic: ~100 gates
- Total estimate: ~4000-5000 gates

If approaching gate limits, consider:
1. Reducing bit width where safe
2. Sharing logic between components
3. Using more efficient algorithms
