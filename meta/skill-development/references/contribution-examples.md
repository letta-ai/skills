# Contribution Examples

Real-world examples of good contributions to help you understand what makes an effective PR.

## Example 1: Correcting Guidance That Led to Errors

### The Situation

Agent followed `letta-memory-architect` guidance to use `memory_rethink` for updating shared memory blocks. Result: Data loss when two agents wrote simultaneously.

### The Investigation

```
1. Checked references/concurrency.md
2. Found memory_insert is safer for concurrent writes
3. Realized warning existed but wasn't prominent
4. Tested memory_insert with concurrent writes - no data loss
5. Identified that warning needs to be more visible
```

###PR Created

**Title:** "Emphasize memory_insert for concurrent writes"

**Description:**
```markdown
## What

Makes the concurrent write warning more prominent in letta-memory-architect 
and adds concrete example of data loss scenario.

## Why

I followed the skill's guidance and used memory_rethink for updates in a 
multi-agent scenario. Result: Data loss when two agents wrote simultaneously.

The warning about concurrent writes existed in references/concurrency.md but 
wasn't prominent in the main SKILL.md. This led me to miss it.

## Evidence

- Reproduced data loss with memory_rethink (7/10 concurrent writes lost data)
- Tested memory_insert with same scenario (0/10 data loss)
- Confirmed in references/concurrency.md that this is documented behavior
- Pattern is clear: append-only is safer for concurrency

## Impact

Prevents other agents from making same mistake that causes data loss.
Makes critical safety information visible where agents first look.

## Testing

Added concrete example showing data loss scenario. Verified example is 
clear and illustrative. Checked that warning now appears in main skill body.
```

**Changes:**
- Move warning to prominent position in SKILL.md
- Add concrete "what goes wrong" example
- Bold the safety recommendation
- Link to detailed concurrency patterns

**Outcome:** Merged. Prevents future agents from data loss.

---

## Example 2: Adding Missing Pattern

### The Situation

Agent hit API rate limiting 5 times across different projects (OpenRouter, Anthropic, OpenAI). Each time spent 20-30 minutes implementing exponential backoff from scratch.

### The Investigation

```
1. Searched skills repository for rate limiting patterns - not found
2. Checked ai/models/ and ai/tools/ - no coverage
3. Researched best practices - exponential backoff with jitter is standard
4. Validated pattern works across all three APIs
5. Determined this is generalizable, not project-specific
```

### PR Created

**Title:** "Add API rate limiting patterns"

**Description:**
```markdown
## What

Creates new skill `ai/models/api-rate-limiting` covering exponential backoff, 
jitter, and retry strategies for HTTP APIs.

## Why

Encountered rate limiting 5 times across different projects:
- OpenRouter (2 times)
- Anthropic API (2 times)
- OpenAI API (1 time)

Each time spent 20-30 minutes implementing retry logic from scratch. This is a 
common pattern that should be documented.

## Evidence

- Tested pattern across all three APIs successfully
- Pattern is HTTP standard (RFC 6585 for 429 responses)
- Exponential backoff with jitter is documented best practice
- Saved ~25 minutes per instance after documenting

## Impact

Prevents repeated implementation of same pattern. Helps any agent integrating 
external APIs handle rate limiting correctly.

## Testing

Created test scenarios with intentional rate limiting. Verified:
- Backoff timing works correctly
- Jitter prevents thundering herd
- Max retry limit prevents infinite loops
- Pattern works across different API providers
```

**Changes:**
- New skill: `ai/models/api-rate-limiting/SKILL.md`
- Includes code examples for implementation
- Documents when to use and when not to use
- Covers different retry strategies and tradeoffs
- Updates README.md to list new skill

**Outcome:** Merged. Now saves time for all agents working with APIs.

---

## Example 3: Clarifying Ambiguous Instructions

### The Situation

Agent working on code review task. Skill said "use appropriate model" but didn't define criteria. Tried GPT-4o, then Claude Sonnet, then GPT-4o-mini before finding GPT-4o was best fit.

### The Investigation

```
1. Noted that "appropriate model" is ambiguous
2. Through testing, identified factors: task complexity, budget, latency
3. Compared three models systematically on code review task
4. Found GPT-4o caught all issues, GPT-4o-mini missed subtle ones
5. Determined decision tree would have prevented trial-and-error
```

### PR Created

**Title:** "Add model selection decision tree to letta-agent-designer"

**Description:**
```markdown
## What

Adds decision tree to references/model-recommendations.md for choosing 
between GPT-4o, GPT-4o-mini, and Claude Sonnet based on task requirements.

## Why

Skill said "use appropriate model" without criteria. Spent 1 hour testing 
three models for code review before finding GPT-4o was needed.

Decision criteria weren't clear:
- When is cost-savings worth quality trade-off?
- How to assess task complexity?
- What defines "production-critical"?

## Evidence

Tested systematically on code review task:

GPT-4o-mini: Fast, cheap, missed 2/10 subtle issues
Claude Sonnet: Good quality, caught 9/10 issues
GPT-4o: Caught all 10 issues, worth cost for code review

Clear pattern: Task criticality and complexity drive choice.

## Impact

Helps agents choose right model upfront instead of trial-and-error.
Saves time and helps balance cost vs quality appropriately.

## Testing

Applied decision tree to 5 different task types. In each case, tree 
led to correct model choice. Validated criteria with team.
```

**Changes:**
- Add decision tree flowchart to model-recommendations.md
- Include examples: "For X task → Y model because Z"
- Document factors: complexity, budget, latency, criticality
- Link from main SKILL.md to decision tree

**Outcome:** Merged. Agents can now choose models systematically.

---

## Example 4: Documenting Edge Case

### The Situation

Agent tried to use `git add -i` (interactive add) as documented in git-workflows skill. Command failed: "interactive mode not supported".

### The Investigation

```
1. Tested command - consistently fails in Bash tool
2. Reason: Non-interactive environment doesn't support -i flag
3. Checked if other interactive commands fail - yes (git rebase -i also fails)
4. Found alternative: git add <files> works fine
5. Determined this is environment limitation worth documenting
```

### PR Created

**Title:** "Add warning about interactive git commands"

**Description:**
```markdown
## What

Adds warning to git-workflows about non-interactive environment limitations.

## Why

Followed skill guidance to use `git add -i` for selective staging.
Command failed: "interactive mode not supported"

Root cause: Bash tool environment doesn't support interactive commands.
This affects any git command with -i flag.

## Evidence

Tested:
- git add -i → fails
- git rebase -i → fails  
- git add <files> → works
- git rebase HEAD~3 → works (non-interactive rebase)

Pattern: Interactive flags don't work, non-interactive alternatives do.

## Impact

Prevents agents from trying interactive commands that will fail.
Provides working alternatives for same functionality.

## Testing

Verified non-interactive alternatives work:
- git add with explicit file paths
- git rebase with commit count
- Other non-interactive git operations

All work correctly in Bash tool environment.
```

**Changes:**
- Add warning box at top of git-workflows SKILL.md
- Document which commands don't work (-i flag commands)
- Provide non-interactive alternatives
- Explain environment limitation

**Outcome:** Merged. Saves agents from hitting known limitation.

---

## Example 5: Building on Existing Skill

### The Situation

Agent working on multi-agent coordination. `letta-agent-designer` mentions multi-agent briefly but doesn't cover coordination patterns in detail. Agent discovered 3 patterns that keep recurring.

### The Investigation

```
1. Reviewed letta-agent-designer - covers basics but not coordination
2. Worked on 4 different multi-agent projects
3. Identified 3 recurring patterns:
   - Supervisor-worker
   - Peer-to-peer with shared state
   - Pipeline/sequential processing
4. Each has different trade-offs and use cases
5. Substantial enough for separate skill
```

### PR Created

**Title:** "Add letta-multi-agent-coordinator skill"

**Description:**
```markdown
## What

Creates new skill `letta/multi-agent-coordinator` covering 
coordination patterns for multi-agent systems.

## Why

letta-agent-designer mentions multi-agent capabilities but doesn't detail 
coordination patterns. Worked on 4 multi-agent projects and found 3 patterns 
recurring:

1. Supervisor-worker (1 coordinator, N workers)
2. Peer-to-peer with shared state (agents coordinate via shared memory)
3. Pipeline (sequential processing, output of A feeds to B)

Each pattern has different trade-offs. This knowledge is substantial enough 
for dedicated skill.

## Evidence

Patterns emerged consistently across projects:
- Customer support system (supervisor-worker)
- Code review team (peer-to-peer)
- Document processing (pipeline)
- Data analysis team (supervisor-worker)

Clear that these are generalizable patterns, not project-specific.

## Impact

Helps agents design multi-agent systems without rediscovering patterns.
Documents trade-offs so agents choose right pattern for use case.

## Testing

Applied patterns retrospectively to 4 projects - each pattern clearly 
fits specific use cases. Documented when to use each pattern and why.
```

**Changes:**
- New skill: `letta/multi-agent-coordinator/SKILL.md`
- Three pattern reference files, one per coordination pattern
- Examples for each pattern
- Decision criteria for pattern selection
- Links from letta-agent-designer to new skill
- Updates README.md

**Outcome:** Merged. Complements existing skill with deeper coverage.

---

## Common Patterns in Good Contributions

### Clear Problem Statement
Every example starts with: "I encountered X problem"

### Validation Through Testing
Every example includes: "I tested this and here are results"

### Evidence of Generalizability
Every example shows: "This pattern appeared multiple times / across contexts"

### Impact on Others
Every example explains: "This helps future agents by preventing/enabling X"

### Concrete Changes
Every example specifies exactly what files changed and why

### Respectful Tone
Every example is collaborative, not accusatory ("skill was wrong")

## What Makes These PRs Effective

1. **Specificity:** Exact problem, exact solution, exact results
2. **Evidence:** Testing, measurement, validation
3. **Impact:** Clear benefit to others
4. **Completeness:** All context needed to evaluate
5. **Humility:** Open to feedback, willing to iterate
6. **Attribution:** Credits sources, builds on existing work

Use these examples as templates for your own contributions. The pattern is consistent: recognize learning, validate thoroughly, document clearly, contribute via PR.
