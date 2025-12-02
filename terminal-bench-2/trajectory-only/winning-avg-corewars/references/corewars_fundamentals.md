# CoreWars Fundamentals

## Core Memory and Execution Model

### Basic Structure

- **Core**: Circular memory array (typically 8000 addresses)
- **Warriors**: Programs that compete by eliminating opponent processes
- **Processes**: Execution threads; a warrior loses when all processes are killed
- **Cycle**: One instruction executed per process per cycle (round-robin)

### Addressing Modes

| Mode | Symbol | Description |
|------|--------|-------------|
| Immediate | # | Literal value, not an address |
| Direct | (none) | Relative address from current instruction |
| A-indirect | * | Use A-field of target as pointer |
| B-indirect | @ | Use B-field of target as pointer |
| A-predecrement | { | Decrement A-field before use |
| B-predecrement | < | Decrement B-field before use |
| A-postincrement | } | Increment A-field after use |
| B-postincrement | > | Increment B-field after use |

## Warrior Archetypes

### Imps

Simplest warrior: `MOV 0, 1`

- Copies itself forward one address each cycle
- Forms an "imp ring" when multiple imps spread around core
- Very hard to kill completely
- Very unlikely to kill anything

**Counter**: Imp gates (SPL 0, 0 or similar traps)

### Stones (Bombers)

Drop DAT bombs at regular intervals:

```redcode
stone   ADD #step, bomb
        MOV bomb, @bomb
        JMP stone
bomb    DAT #0, #0
```

**Key parameter**: Step size determines coverage pattern

**Counter**: Fast replication, distributed processes, position-independent code

### Papers (Replicators)

Copy themselves throughout memory:

```redcode
paper   SPL 0, <-step
        MOV.I >ptr, {ptr
ptr     JMP paper, paper+step
```

**Strength**: Many copies survive partial attacks
**Weakness**: Slow to start, vulnerable to early strikes

### Scanners

Search for non-zero memory (opponent code):

```redcode
scan    ADD #step, ptr
        SEQ.I ptr, empty    ; skip if equal to empty
        JMP attack
        JMP scan
```

**Strength**: Precise attacks, efficient
**Weakness**: Decoys can waste cycles

### Vampires

Convert opponent processes:

```redcode
vampire MOV pit, @ptr
        ADD #step, ptr
        JMP vampire
pit     JMP 0              ; target jumps to vampire's code
```

**Strength**: Gains processes from opponent
**Weakness**: Slow, needs opponent to execute the pit

## Mathematical Relationships

### Step Size Selection

For a core of size C and step size S:

- **Coverage**: After N bombs, N*S addresses affected
- **Full coverage**: Requires N = C/gcd(C,S) bombs
- **Coprime steps**: When gcd(C,S) = 1, every address eventually hit

**Example**: Core size 8000, step 17
- gcd(8000, 17) = 1 (coprime)
- Full coverage after 8000 iterations
- Coverage rate: 1 address per iteration

### Process Timing

With P processes, each process executes every P cycles.

**Trade-off**:
- More processes = more survival (harder to kill all)
- More processes = slower individual execution

**Example**: 4 SPLs = 4 processes
- Each process waits 4 cycles between instructions
- Bombing rate reduced to 1/4 of single-process bomber

### Imp Ring Formation

Imp ring with N imps at spacing D:
- All imps advance by 1 each cycle
- Ring size = N * D
- Stable when D * N = constant modulo core_size

## Testing Methodology

### Statistical Requirements

Win rates require sufficient sample size:
- 100 matches: ~±10% margin at 95% confidence
- 1000 matches: ~±3% margin at 95% confidence

**Recommendation**: Run at least 100 matches per opponent for reliable results.

### Isolation Testing

Test components separately before combining:

1. **Scanner test**: Place opponent at known positions, verify detection
2. **Bomber test**: Run alone, count addresses bombed after N cycles
3. **Replicator test**: Run alone, count copies after N cycles
4. **Imp test**: Verify imp ring formation and stability

### A/B Testing for Parameters

Change one parameter at a time:

```
Baseline: step=17, gate=1650, processes=2
Test A:   step=21, gate=1650, processes=2  (only step changed)
Test B:   step=17, gate=2000, processes=2  (only gate changed)
```

Record results against ALL opponents for each variation.

## Common Opponent Patterns

### Recognizing Archetypes

**Stone/Bomber indicators**:
- ADD instruction incrementing a pointer
- MOV to indirect address
- Small, tight loop

**Paper/Replicator indicators**:
- SPL as first instruction
- MOV.I copying instruction blocks
- Self-referential pointers

**Scanner indicators**:
- SEQ or SNE comparison instructions
- Conditional jump based on comparison
- ADD incrementing scan pointer

**Vampire indicators**:
- MOV placing JMP instructions
- Target address calculated to redirect opponents

### Analyzing Opponent Parameters

When reading opponent code:

1. **Find the step size**: Look for `ADD #N, ptr` - N is the step
2. **Find the bomb type**: What does the MOV place? DAT? SPL? JMP?
3. **Count processes**: How many SPLs before main loop?
4. **Identify vulnerabilities**:
   - Large step = sparse coverage = gaps to hide in
   - Small step = slow coverage = time to replicate
   - Single process = one kill eliminates warrior

## Debugging Tips

### Syntax Errors

Common Redcode syntax issues:
- Labels must start in column 1
- Instructions must be indented
- Comments use semicolon (;)
- Case insensitive but convention is lowercase

### Assembly Verification

Before testing against opponents:

```bash
pmars -b warrior.red
```

Check for:
- Assembly errors
- Unexpected instruction count
- Label resolution issues

### Visual Debugging

Some CoreWars simulators provide visual core dumps showing:
- Memory contents after N cycles
- Process positions
- Bomb coverage patterns

Use these to verify warrior behavior matches expectations.
