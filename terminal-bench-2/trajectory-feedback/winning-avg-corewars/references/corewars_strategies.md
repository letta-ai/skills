# CoreWars Strategy Reference

This reference covers established CoreWars warrior archetypes, common patterns, and proven techniques for developing competitive warriors.

## Warrior Archetypes

### Bombers

Bombers attack by placing DAT instructions (or other damaging payloads) throughout the core at regular intervals.

**Basic Bomber Pattern:**
```redcode
step equ 4
bomb dat 0, 0
loop add #step, bomb
     mov bomb, @bomb
     jmp loop
```

**Characteristics:**
- Simple and fast execution
- Predictable patterns based on step size
- Vulnerable to faster-spreading opponents
- Step size determines coverage and collision with self

**Counter-strategy:** Avoid positions hit by the bomber's step pattern. If step=4, use positions not divisible by 4.

### Scanners

Scanners search for enemy code before attacking, allowing targeted strikes rather than blind bombing.

**Basic Scanner Pattern:**
```redcode
step equ 100
scan add #step, ptr
ptr  jmz scan, 0
     ; attack code here
```

**Characteristics:**
- More efficient use of attacks
- Slower than blind bombers
- Can be fooled by decoys
- Effective against stationary opponents

**Counter-strategy:** Use decoys or highly mobile code that moves away before being hit.

### Replicators (Paper)

Replicators copy themselves throughout the core, creating redundancy that survives partial destruction.

**Basic Replicator Pattern:**
```redcode
step equ 2667
src  spl 0, 0
     mov }src, >dst
dst  jmp @0, step
     jmz -2, -1
```

**Characteristics:**
- Highly survivable due to redundancy
- Can out-spread bombers
- Vulnerable to scanners that find copies
- Step size critical for avoiding self-collision

**Known effective step values:** 2667, 3044 (for 8000-size core)

### Imps

Imps are simple `MOV 0, 1` instructions that copy themselves forward through the core.

**Basic Imp:**
```redcode
mov 0, 1
```

**Imp Ring (multiple imps at calculated offsets):**
```redcode
imp mov 0, 1
    ; Start multiple processes at offsets that form a ring
```

**Characteristics:**
- Nearly impossible to fully kill
- Cause ties rather than wins against most opponents
- Effective against slow or stationary warriors
- Vulnerable to imp gates

### Imp Gates

Defenses specifically designed to stop imp spirals.

**Basic Imp Gate:**
```redcode
gate spl 0, 0
     dat 0, 0
```

**How it works:** The SPL creates processes that execute the DAT, killing themselves but blocking the imp's path.

### Vampires

Vampires plant JMP traps that redirect enemy processes to pit code controlled by the vampire.

**Basic Vampire Pattern:**
```redcode
trap jmp pit
loop mov trap, @ptr
     add #step, ptr
ptr  dat 0, 100
     jmp loop
pit  ; enemy processes jump here
     ; can steal processes or kill them
```

**Characteristics:**
- Can capture enemy processes
- Effective against linear or predictable code
- Vulnerable to code that checks before jumping

### Stones

Stones combine bombing with defensive SPL/JMP stuns to create resilient attackers.

**Basic Stone Pattern:**
```redcode
     spl 0, 0      ; defensive split
     spl 0, 0
     mov bomb, @ptr
bomb dat >1, 1
ptr  sub #step, @0
     jmp -3
```

**Characteristics:**
- More resilient than pure bombers
- Multiple processes make it harder to kill
- Slower due to process management overhead

### Silk-Type Replicators

Silk warriors are highly optimized replicators designed for maximum spreading speed.

**Key optimizations:**
- Minimize instruction count
- Maximize process creation rate
- Carefully chosen step sizes for core coverage

## Parameter Selection Guidelines

### Step Size Selection

Step sizes affect coverage pattern and interaction with opponents:

- **Small steps (1-10):** Dense coverage but slow total core coverage
- **Medium steps (50-200):** Balanced coverage and speed
- **Large steps (500+):** Fast coverage but gaps between hits

**Avoiding common conflicts:**
- Step=4 conflicts with standard Stone bombers
- Step=100 conflicts with common scanner intervals
- Prime number steps avoid periodic patterns

**Recommended approach:** Test multiple step sizes systematically against each opponent.

### Gate Positioning

Imp gates should be positioned to intercept expected imp paths:
- Standard core size is 8000
- Imp rings often use offsets like 2667
- Gate distance from main code affects protection vs. resource cost

### SPL Count Tradeoffs

More SPL instructions create more processes but:
- Slow down execution per process
- Consume more of the process queue
- Increase survivability against single-hit attacks
- Decrease effectiveness against process-killing attacks

## Debugging Techniques

### Using pmars Flags

```bash
# Run single battle with output
pmars -b -r 1 warrior.red opponent.red

# Run 100 rounds silently, show only scores
pmars -r 100 warrior.red opponent.red

# Show detailed core state (for debugging)
pmars -b warrior.red opponent.red
```

### Analyzing Battle Outcomes

When debugging a losing matchup:

1. **Watch the battle** - Use pmars visual mode to see what happens
2. **Identify kill sequence** - At what instruction does your warrior die?
3. **Trace backwards** - What opponent action caused that instruction to be hit?
4. **Compare timing** - Is your warrior too slow to avoid the attack?

### Common Failure Modes

| Failure Mode | Symptoms | Likely Cause | Solution |
|--------------|----------|--------------|----------|
| Quick death | Loses in <1000 cycles | Hit by early bomb/scan | Change start position or add decoy |
| Gradual decay | Processes slowly killed | Opponent out-spreading | Increase replication speed |
| Tie instead of win | Match ends without winner | Imp stalemate | Add imp gate or faster attack |
| Capture | Processes redirected | Vampire trap | Check before jumping, add decoys |

## Testing Methodology

### Statistical Significance

Due to randomness in starting positions, single battles are unreliable:
- Minimum 100 rounds for rough estimates
- 500+ rounds for reliable statistics
- 1000+ rounds for precise measurements

### Result Tracking Template

```
Version: v1.0
Parameters: step=17, gate=1650, spl_count=3

| Opponent    | Target | Result | Status |
|-------------|--------|--------|--------|
| vampire.red | 75%    | 87%    | PASS   |
| stone.red   | 75%    | 62%    | FAIL   |
| paper.red   | 75%    | 71%    | FAIL   |
| snake.red   | 33%    | 28%    | FAIL   |
| g2-clear.red| 33%    | 15%    | FAIL   |

Notes: Stone matchup needs work - try avoiding multiples of 4
```

### A/B Testing Changes

When making parameter changes:
1. Change ONE parameter at a time
2. Test against ALL opponents
3. Record results in tracking template
4. Compare to previous best version
5. Only keep changes that improve overall score

## Opponent-Specific Strategies

### Against Bombers (Stone-type)

- Use step sizes that avoid bomber's pattern
- Fast replication to spread before being hit
- Position-aware scanning to hit bomber first

### Against Replicators (Paper-type)

- Aggressive scanning to find copies
- Core clear components to wipe spreading code
- Faster replication to out-spread opponent

### Against Imps

- Imp gates at calculated positions
- Core clear strategies
- Accept ties as alternative to losses

### Against Scanners

- Decoy code to mislead scanner
- Mobile code that moves after being found
- Faster attack to hit scanner first

### Against Core Clears

- Fast spreading replicators
- Multiple redundant copies
- Accept that some losses may be unavoidable
