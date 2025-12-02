---
name: constraints-scheduling
description: Provides systematic approaches for solving multi-person scheduling problems with complex constraints. This skill should be used when finding meeting times, scheduling events, or solving optimization problems involving multiple calendars, availability windows, time-based constraints, preferences, and buffer requirements.
---

# Constraints Scheduling

## Overview

This skill provides a systematic methodology for solving scheduling problems that involve multiple participants with individual constraints, calendar conflicts, preferences, and time-based rules. It emphasizes exhaustive search, proper constraint encoding, and rigorous verification to avoid common pitfalls.

## When to Use This Skill

- Finding meeting times across multiple calendars
- Scheduling events with complex availability constraints
- Optimizing time slots based on preferences and hard requirements
- Any problem requiring intersection of multiple time-based constraints

## Core Methodology

### Phase 1: Constraint Extraction and Classification

Before attempting any search, systematically extract and classify all constraints:

**1. Hard Constraints (Must be satisfied)**
- Availability windows (e.g., "Alice: 9 AM - 2 PM only")
- Calendar conflicts (existing meetings from ICS/calendar files)
- Day-specific rules (e.g., "Bob must leave by 4:30 PM on Tue/Thu")
- Buffer requirements (e.g., "15-min buffer after meetings ending at 4:45 PM or later")
- Blocked days (e.g., "Carol avoids Mondays")

**2. Soft Constraints (Preferences for tie-breaking)**
- Time preferences (e.g., "Alice prefers mornings")
- Day preferences
- Location preferences

**3. Meta-Constraints**
- Slot duration requirements
- Granularity requirements (e.g., "minute granularity" vs "hour boundaries")
- Date range boundaries

### Phase 2: Data Acquisition

**Calendar File Parsing**
- When reading ICS files, ensure complete data retrieval - if output is truncated, request specific date ranges or parse in chunks
- Extract busy times with exact start and end timestamps
- Pay attention to timezone specifications
- Verify parsed data matches the raw file content

**Constraint Documentation**
- Create an explicit checklist of every constraint extracted
- For each constraint, note: participant, type, parameters, and source

### Phase 3: Candidate Generation

**Critical: Respect granularity requirements**

If the task specifies "minute granularity":
- Generate slots starting at every minute, not just hour boundaries
- A slot at 9:15-10:15 may be valid when 9:00-10:00 and 10:00-11:00 are not
- Never assume hourly boundaries unless explicitly stated

**Generation approach:**
```
for each_day in date_range:
    for start_minute in range(day_start, day_end - duration):
        candidate = (day, start_minute, start_minute + duration)
        add candidate to search space
```

### Phase 4: Systematic Constraint Filtering

Apply constraints in order of restrictiveness (most restrictive first):

1. **Day-level filters**: Eliminate entire days that violate constraints (blocked days, weekends if applicable)
2. **Time window filters**: For each participant, eliminate slots outside their availability window
3. **Calendar conflict filters**: Eliminate slots that overlap with existing meetings
4. **Buffer requirement filters**: Check post-meeting buffers and other time-gap requirements
5. **Apply remaining hard constraints**

### Phase 5: Preference-Based Ranking

After filtering to valid slots:
1. Apply soft constraints as ranking criteria
2. Sort by preference satisfaction
3. Select earliest slot among equally-preferred options (unless instructed otherwise)

### Phase 6: Verification Checklist

For the selected slot, explicitly verify EVERY constraint:

```
Selected slot: [Day], [Date], [Start]-[End]

Hard Constraint Verification:
[ ] Participant A: Start >= earliest_start ✓/✗
[ ] Participant A: End <= latest_end ✓/✗
[ ] Participant A: No calendar conflicts ✓/✗
[ ] Participant B: Start >= earliest_start ✓/✗
[ ] Participant B: Day-specific rules satisfied ✓/✗
... (continue for ALL constraints)

Soft Constraint Status:
[ ] Preference 1: satisfied/not satisfied
[ ] Preference 2: satisfied/not satisfied
```

## Common Pitfalls to Avoid

### Pitfall 1: Ignoring Granularity Requirements
**Problem**: Only checking hourly slots when minute granularity is specified
**Solution**: Always check the granularity requirement and generate candidates accordingly

### Pitfall 2: Incomplete Calendar Parsing
**Problem**: Truncated calendar data leading to missed conflicts
**Solution**: Verify complete data retrieval; if truncated, parse in sections

### Pitfall 3: Missing Buffer/Gap Constraints
**Problem**: Forgetting time-gap requirements like "15-min buffer after meetings ending at X"
**Solution**: Include buffer constraints in the filtering phase explicitly

### Pitfall 4: Conflating Preferences with Requirements
**Problem**: Treating soft constraints as hard constraints or vice versa
**Solution**: Clearly separate preferences (tie-breakers) from requirements (filters)

### Pitfall 5: Incomplete Verification
**Problem**: Not explicitly checking each constraint for the final answer
**Solution**: Use the verification checklist for EVERY constraint before reporting

### Pitfall 6: Edge Case Boundaries
**Problem**: Missing slots at exact boundary times (e.g., ending exactly at 2:00 PM when constraint is "must end by 2 PM")
**Solution**: Clarify boundary semantics (< vs <=) and test boundary values explicitly

### Pitfall 7: Disorganized Search
**Problem**: Jumping between days/times without systematic coverage
**Solution**: Use programmatic exhaustive search, not manual reasoning

## Implementation Approach

### Recommended: Programmatic Solution

For complex scheduling problems, implement a programmatic solution:

```python
# Pseudocode structure
def find_valid_slots(constraints, calendars, date_range, duration, granularity_minutes=1):
    # 1. Parse all calendars
    busy_times = parse_all_calendars(calendars)

    # 2. Generate all candidate slots at specified granularity
    candidates = generate_candidates(date_range, duration, granularity_minutes)

    # 3. Filter by hard constraints
    valid = []
    for slot in candidates:
        if satisfies_all_hard_constraints(slot, constraints, busy_times):
            valid.append(slot)

    # 4. Rank by preferences
    valid.sort(key=lambda s: preference_score(s, constraints))

    # 5. Return earliest among best-ranked
    return valid[0] if valid else None

def satisfies_all_hard_constraints(slot, constraints, busy_times):
    # Check EVERY hard constraint explicitly
    for constraint in constraints.hard:
        if not constraint.is_satisfied(slot):
            return False

    # Check calendar conflicts
    for busy in busy_times:
        if overlaps(slot, busy):
            return False

    return True
```

### Verification Script

After finding a solution, run verification:

```python
def verify_solution(slot, all_constraints):
    print(f"Verifying: {slot}")
    all_passed = True

    for constraint in all_constraints:
        passed = constraint.check(slot)
        status = "✓" if passed else "✗"
        print(f"  [{status}] {constraint.description}")
        if not passed:
            all_passed = False

    return all_passed
```

## Output Format

When presenting the solution:

1. **State the answer clearly**: Day, Date, Time range
2. **Show the verification checklist**: Every constraint checked with ✓/✗
3. **Note preference satisfaction**: Which soft constraints were satisfied
4. **If multiple valid slots exist**: List alternatives and explain selection criteria
