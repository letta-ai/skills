---
name: gpt2-codegolf
description: Guidance for implementing neural network inference (like GPT-2) under extreme code size constraints. This skill should be used when tasks require implementing ML model inference in minimal code (code golf), parsing model checkpoints in constrained environments, or building transformer architectures in low-level languages like C with strict size limits.
---

# GPT-2 Code Golf

## Overview

This skill provides guidance for implementing neural network inference under extreme code size constraints. Tasks in this category typically require implementing a complete ML model (such as GPT-2) in a minimal amount of code, often in low-level languages like C with strict byte limits.

## Critical First Steps

### 1. Assess Feasibility Before Coding

Before writing any code, perform a realistic feasibility analysis:

- **Enumerate all required components**: For GPT-2, this includes tokenization (BPE), embedding lookup, 12+ transformer layers with attention and FFN, layer normalization, and final vocabulary projection
- **Estimate minimum code size**: Each component has a minimum viable implementation size
- **Identify the hardest constraint**: Often the checkpoint parsing, not the inference code itself

### 2. Clarify Requirements Immediately

Ask clarifying questions before starting implementation:

- **Checkpoint format**: Can the checkpoint be preprocessed into a simpler binary format, or must the original format (e.g., TensorFlow protobuf) be parsed directly?
- **External dependencies**: Are any libraries allowed (even minimal ones)?
- **Precision requirements**: Can lower precision (int8, float16) be used?
- **Model variant**: Which specific GPT-2 variant (117M, 345M, etc.)?

### 3. Recognize Impossible Constraints

Some combinations are essentially impossible:

- Parsing TensorFlow checkpoint protobufs in pure C under 5000 bytes is not viable
- Full BPE tokenization with vocabulary lookup requires significant code
- Proper transformer attention with softmax needs careful implementation

If constraints appear impossible, **explicitly acknowledge this and propose alternatives** rather than attempting a doomed implementation.

## Recommended Approach

### Phase 1: Design Before Implementation

1. **Write pseudocode first**: Outline every function and data structure needed
2. **Calculate byte budget**: Allocate bytes to each component
3. **Identify shortcuts**: Where can mathematical approximations reduce code?
4. **Plan weight format**: Design the simplest possible binary format for weights

### Phase 2: Incremental Implementation with Testing

Build and test components in isolation before integration:

1. **Start with weight loading**: This is often the hardest part
   - Test: Can weights be loaded and printed correctly?

2. **Implement matrix operations**: Basic matmul, add, etc.
   - Test: Verify against known input/output pairs

3. **Build single transformer layer**: Attention + FFN
   - Test: Run one layer with known inputs, verify outputs

4. **Add tokenization last**: Often can be simplified or preprocessed
   - Test: Verify token IDs match reference implementation

### Phase 3: Size Optimization

Only optimize for size after functionality is verified:

- Remove whitespace and comments
- Shorten variable names
- Combine related operations
- Use preprocessor macros strategically
- Consider algorithmic simplifications

## Verification Strategies

### Essential Testing Checkpoints

1. **Compilation is NOT verification**: A program that compiles may produce garbage output
2. **Test with known inputs**: Use reference implementations to generate expected outputs
3. **Verify intermediate values**: Check embeddings, attention weights, layer outputs
4. **End-to-end test**: Generate text and verify it's coherent, not random

### Red Flags Indicating Problems

- Code that compiles but has never been run with actual inputs
- Weight loading code that doesn't verify tensor shapes
- Missing implementation of required operations (softmax, layer norm, etc.)
- Truncated functions or incomplete logic paths

## Common Pitfalls

### 1. Underestimating Checkpoint Complexity

**Mistake**: Assuming checkpoint files can be "parsed" by reading raw bytes and looking for patterns.

**Reality**: TensorFlow checkpoints use Protocol Buffers with complex indexing. Without a protobuf parser, direct reading is not viable.

**Solution**: Request or create a preprocessed binary format with simple structure (e.g., sequential float arrays with a header describing shapes).

### 2. Claiming Completion Prematurely

**Mistake**: Declaring "complete" when code compiles but hasn't been tested with actual inference.

**Reality**: Compilation proves syntax correctness, not functional correctness.

**Solution**: Only mark complete after generating actual text output that demonstrates the model works.

### 3. Writing Incomplete Code

**Mistake**: Writing function stubs or partially implemented logic, then moving on.

**Reality**: Incomplete functions (missing closing braces, uninitialized variables, no return statements) will cause undefined behavior.

**Solution**: Complete each function fully before starting the next. Verify with compilation AND execution.

### 4. Ignoring BPE Complexity

**Mistake**: Assuming tokenization can be done with simple string splitting.

**Reality**: BPE requires iterative merging of byte pairs based on a learned vocabulary. This is not trivial.

**Solution**: Consider preprocessing text to token IDs externally, or budget significant code for proper BPE.

### 5. Missing Error Handling

**Mistake**: Skipping bounds checks and file operation validation.

**Reality**: Missing a single malloc failure or file read error leads to crashes or silent corruption.

**Solution**: At minimum, check that files opened successfully and allocations returned non-null.

## Decision Framework

When approaching a code golf neural network task:

```
1. Is checkpoint preprocessing allowed?
   YES → Design simple binary format, proceed
   NO  → Assess if parsing is feasible in byte budget
         NOT FEASIBLE → Request clarification or propose alternatives

2. Is the byte limit realistic for all components?
   Run through checklist:
   [ ] Weight loading
   [ ] Matrix operations
   [ ] Activation functions
   [ ] Layer normalization
   [ ] Attention mechanism
   [ ] Tokenization
   [ ] Main inference loop

   If any component alone exceeds budget → Task may be impossible as specified

3. Can external tools preprocess inputs?
   YES → Preprocess tokens, use simpler data formats
   NO  → Budget extra code for I/O handling
```

## Key Principles

1. **Honesty over optimism**: Acknowledge when constraints are too tight rather than delivering non-functional code
2. **Test-driven development**: Verify each component works before adding the next
3. **Incremental progress**: Build working minimal versions before optimizing for size
4. **Clear communication**: If stuck or if the task appears impossible, explain why clearly
5. **Complete visibility**: Always verify full code contents after edits; partial views lead to inconsistencies
