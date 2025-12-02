# Constraint Scheduling Verification Guide

This guide provides detailed verification procedures and edge case handling for scheduling problems.

## Complete Verification Procedure

### Step 1: Constraint Inventory

Before verifying a solution, create a complete inventory of all constraints:

```
CONSTRAINT INVENTORY
====================

Participant: [Name]
  Hard Constraints:
    - Availability window: [start_time] - [end_time]
    - Day restrictions: [list blocked/required days]
    - Buffer requirements: [describe any buffer rules]
    - Calendar conflicts: [number of busy blocks]
  Soft Constraints:
    - Time preferences: [preferred times]
    - Day preferences: [preferred days]

[Repeat for each participant]

Global Constraints:
  - Meeting duration: [duration]
  - Date range: [start_date] - [end_date]
  - Granularity: [minute/hour/etc.]
```

### Step 2: Per-Constraint Verification

For each constraint, verify using this format:

```
CONSTRAINT: [Description]
TYPE: Hard / Soft
PARTICIPANT: [Name or "All"]
RULE: [Formal rule expression]
SLOT VALUE: [Relevant slot attribute]
COMPARISON: [slot_value] [operator] [constraint_value]
RESULT: PASS / FAIL
```

Example:
```
CONSTRAINT: Alice must end by 2 PM
TYPE: Hard
PARTICIPANT: Alice
RULE: slot.end_time <= 14:00
SLOT VALUE: 12:00
COMPARISON: 12:00 <= 14:00
RESULT: PASS ✓
```

### Step 3: Calendar Conflict Check

For each participant's calendar:

```
CALENDAR CONFLICTS: [Participant]
==============================

Busy Block 1: [date] [start]-[end]
  Proposed slot: [date] [start]-[end]
  Overlap check: [does slot_start < busy_end AND slot_end > busy_start?]
  Result: CONFLICT / CLEAR

[Repeat for all busy blocks]

Overall: [X conflicts found / No conflicts]
```

### Step 4: Edge Case Verification

Check these specific edge cases:

**Boundary Times**
- Does "end by 2 PM" mean < 14:00 or <= 14:00?
- Does "available from 9 AM" mean >= 9:00 or > 9:00?
- Document assumption and verify accordingly

**Day Boundaries**
- Does the slot span midnight?
- Are weekend days included/excluded?

**Buffer Calculations**
- If buffer applies after meetings ending at X or later:
  - Check all meetings that end at or after X
  - Calculate required buffer period
  - Verify proposed slot doesn't fall within buffer

**Lunch/Break Periods**
- Identify all break periods for each participant
- Verify no overlap with proposed slot

## Exhaustive Search Verification

To verify the search was exhaustive:

### Granularity Check
```
Required granularity: [X] minutes
Search increment used: [Y] minutes

If Y > X: SEARCH INCOMPLETE - may have missed valid slots
If Y <= X: SEARCH ADEQUATE
```

### Coverage Check
```
Date range: [start] to [end]
Days searched: [list all days]
Time range per day: [earliest] to [latest]

Missing coverage: [identify any gaps]
```

### Alternative Slots

List all valid slots found (not just the selected one):
```
VALID SLOTS FOUND:
==================
1. [Day, Date, Time] - [preference score]
2. [Day, Date, Time] - [preference score]
...

Selection criteria: [earliest / highest preference / etc.]
Selected: Slot #[N]
Rationale: [why this slot was chosen over others]
```

## Common Edge Cases

### Case 1: Exact Boundary Match
**Scenario**: Constraint says "end by 2 PM" and slot ends exactly at 2:00 PM
**Verification**: Clarify boundary semantics. Default assumption: "<=" (inclusive)
**Test**: Check both 13:59 and 14:00 end times

### Case 2: Adjacent Meetings
**Scenario**: Existing meeting 10:00-11:00, proposed slot 11:00-12:00
**Verification**: No overlap (adjacent is acceptable unless buffer required)
**Test**: Verify overlap logic handles adjacent correctly

### Case 3: Buffer After Late Meetings
**Scenario**: Meeting ends at 4:50 PM, 15-min buffer required after meetings ending 4:45+
**Verification**: Buffer period is 4:50-5:05 PM
**Test**: Any slot starting before 5:05 PM would conflict

### Case 4: Day-Specific Constraints
**Scenario**: "Bob leaves at 4:30 PM on Tue/Thu"
**Verification**:
- If day is Tue or Thu: slot must end by 16:30
- If day is Mon/Wed/Fri: this constraint doesn't apply
**Test**: Check day of week before applying constraint

### Case 5: Preference vs Requirement
**Scenario**: "Carol avoids Mondays" vs "Carol cannot meet Mondays"
**Verification**:
- "avoids" = soft constraint (preference)
- "cannot" = hard constraint (requirement)
**Test**: Monday slots should be filtered if hard, deprioritized if soft

## Debugging Failed Searches

If no valid slots are found:

1. **Relax one constraint at a time** to identify the blocking constraint
2. **Visualize the schedule** - create a timeline showing all busy blocks
3. **Check for constraint conflicts** - are requirements mutually exclusive?
4. **Verify calendar parsing** - are busy times correctly extracted?

## Verification Output Template

```
SCHEDULING SOLUTION VERIFICATION
================================

Proposed Slot: [Day], [Date], [Start Time] - [End Time]

HARD CONSTRAINTS:
[✓] Participant A - Availability window: [details]
[✓] Participant A - No calendar conflicts: [details]
[✓] Participant B - Day-specific rule: [details]
[✓] Participant C - Not on blocked day: [details]
[✓] Participant C - Lunch break clear: [details]
[✓] Participant C - Buffer requirement: [details]
... (ALL hard constraints)

SOFT CONSTRAINTS:
[✓] Participant A - Morning preference: satisfied
[—] Participant C - Avoids Monday: N/A (not Monday)

SEARCH COMPLETENESS:
[✓] Granularity: minute-level as required
[✓] Date coverage: all days in range checked
[✓] Alternative slots: 2 other valid slots found

FINAL RESULT: VERIFIED ✓
```
