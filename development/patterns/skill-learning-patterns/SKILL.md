---
name: skill-learning-patterns
description: Meta-skill for recognizing learnings, validating improvements, and contributing back to the collective knowledge base. Use when agents discover better patterns, find gaps in existing skills, or want to improve shared knowledge.
license: MIT
---

# Skill Learning Patterns

This meta-skill teaches agents to recognize valuable learnings during their work and contribute improvements back to the communal skill repository through pull requests.

## Core Philosophy

This repository is a **living knowledge base** that improves through collective learning. As agents work on tasks, they discover:
- Better approaches than documented
- Missing error handling cases
- Gaps in existing skills
- Clearer ways to explain patterns
- New patterns worth capturing

These discoveries should flow back into the repository so all agents benefit.

**Critical principle:** Skills must contain **general-purpose knowledge** that helps many agents across different contexts. This is not a place for project-specific configurations, personal preferences, or one-off solutions. Focus on patterns, principles, and practices that are broadly applicable.

## When to Use This Skill

Use this skill when:
- You discover something that took significant time to figure out
- Existing skill instructions led you astray or were incomplete
- You find yourself repeatedly solving the same undocumented problem
- You correct a mistake based on learning what actually works
- You notice a pattern emerging across multiple tasks
- You want to improve or clarify existing documentation

## Learning Recognition Process

### 1. Notice Patterns During Work

Pay attention to signals that indicate learnable moments:

**Time investment signals:**
- "I spent 20+ minutes debugging this"
- "I tried 3 approaches before finding what worked"
- "I wish I had known this at the start"

**Repetition signals:**
- "This is the third time I've solved this"
- "I remember encountering this before"
- "Other agents probably face this too"

**Correction signals:**
- "The skill said X, but Y actually works better"
- "I misunderstood the instruction and it caused problems"
- "This approach failed in ways not documented"

Consult `references/recognizing-learnings.md` for detailed patterns.

### 2. Validate the Learning

Before proposing changes, validate that your learning is sound:

**Validation checklist:**
- ✅ **Is this generalizable beyond your specific context?** (Most critical - skills are for general-purpose knowledge)
- ✅ Does this help multiple agents across different projects/contexts?
- ✅ Did you test that your approach works better?
- ✅ Have you seen this pattern multiple times or with evidence?
- ✅ Does this address a real gap vs. personal preference?
- ✅ Are there edge cases or tradeoffs to consider?

See `references/validation-criteria.md` for detailed guidance.

### 3. Determine Contribution Type

**Update existing skill** when:
- Skill has incorrect or outdated information
- Skill is missing an important case or pattern
- Instructions are unclear and caused confusion
- Examples would help but are missing

**Create new skill** when:
- No existing skill covers this domain
- Topic is substantial enough for standalone skill
- Pattern appears frequently but isn't documented
- Knowledge would benefit many agents

**Do NOT contribute** when:
- Learning is specific to your project/context (e.g., "Our API endpoint is X")
- Solution only works in your unique environment
- It's a personal preference without objective benefit
- It's a one-off workaround for unusual situation
- Knowledge is too narrow to help other agents

**Note in conversation only** when:
- Learning might be valuable but needs more validation
- Pattern needs more observation before documenting
- Temporary workaround that might become obsolete

### 4. Contribute via Pull Request

**Important:** All contributions go through pull requests, not direct commits to main.

**PR workflow:**
1. Create a feature branch for your changes
2. Make updates to skill(s)
3. Test that changes improve clarity/correctness
4. Write clear PR description with rationale
5. Submit PR for review
6. Respond to feedback and iterate

Consult `references/pr-workflow.md` for detailed process.

## Contribution Quality Standards

### Good Contributions Include

**Clear rationale:**
```
"I encountered rate limiting with OpenRouter 5 times. Added exponential 
backoff pattern with jitter which resolved all instances. This pattern 
isn't documented anywhere in ai/models/."
```

**Before/after comparison:**
```
Before: "Use memory_rethink for updates"
After: "Use memory_insert for concurrent writes (safer), memory_rethink 
only for single-agent exclusive access"
Why: Prevents data loss in multi-agent scenarios
```

**Evidence of validation:**
```
"Tested across 3 different projects, pattern held. Also confirmed in 
Letta docs. Previous approach caused data loss 2/3 times."
```

**Preserved existing knowledge:**
- Don't delete working information
- Build on rather than replace
- Add context, don't remove context

### Avoid These Anti-Patterns

❌ **Premature optimization** - Changing after single instance without validation

❌ **Over-generalization** - "This worked for me once" → "Always do this"

❌ **Opinion as fact** - Personal preference without objective improvement

❌ **Churn** - Changes that are different but not better

❌ **Deleting context** - Removing information that might help others

## PR Description Template

Use this template for skill contributions:

```markdown
## What

[Brief description of what's changing]

## Why

[Problem you encountered / gap you found / improvement opportunity]

## Evidence

[How you validated this is better / how you tested / how often you saw this]

## Impact

[Who benefits / what situations this helps / what it prevents]

## Testing

[How you verified the change works / examples you tried]
```

See `references/contribution-examples.md` for real examples.

## Example Workflows

### Workflow 1: Correcting Existing Skill

```
During task: "Following letta-memory-architect, I used memory_rethink for 
concurrent updates. Result: data loss when two agents wrote simultaneously."

Validation: "Checked references/concurrency.md - it says memory_insert is 
safer but warning wasn't prominent. Tested memory_insert with concurrent 
writes - no data loss."

Action: 
1. Create feature branch: fix/memory-concurrency-warning
2. Update SKILL.md to make warning more prominent
3. Add concrete example of data loss scenario
4. Create PR: "Emphasize memory_insert for concurrent writes"
5. Explain in PR: "Misread the guidance, led to data loss. Making warning 
   more visible to prevent this for other agents."
```

### Workflow 2: Adding Missing Pattern

```
During task: "Hit OpenRouter rate limits 5 times across different projects. 
Spent 30min each time figuring out exponential backoff."

Validation: "Pattern works consistently. Checked ai/models/ - not documented. 
This is generalizable beyond my specific use case."

Action:
1. Create feature branch: add/api-rate-limiting-skill
2. Create new skill: ai/models/api-rate-limiting/
3. Document exponential backoff pattern with code examples
4. Create PR: "Add API rate limiting patterns"
5. Explain: "Common pattern that caused repeated debugging time. Validated 
   across 5 instances with different APIs."
```

### Workflow 3: Clarifying Ambiguity

```
During task: "Skill said 'use appropriate model' but didn't define criteria. 
Tried GPT-4o, Claude Sonnet, GPT-4o-mini before finding best fit."

Validation: "Through testing, identified that task complexity + budget 
constraints should guide model choice. This clarification would have saved 
1 hour."

Action:
1. Create feature branch: clarify/model-selection-criteria  
2. Add decision tree to skill
3. Include examples: "For X task → Y model because Z"
4. Create PR: "Add model selection decision tree"
5. Explain: "Ambiguous guidance led to trial-and-error. Adding decision 
   criteria to help agents choose upfront."
```

## Self-Correction Culture

**When you make mistakes:**
- Note what you learned
- Update relevant skill if gap exists
- Don't just fix the instance, prevent future instances

**When you discover better approaches:**
- Compare objectively with current documented approach
- Test to validate improvement
- Propose update with clear reasoning

**When skills lead you astray:**
- Don't assume skill is wrong without investigation
- Validate your alternative approach
- If truly better, propose improvement with evidence

## Validation Questions

Before submitting PR, ask:

1. Is this a genuine improvement or just different?
2. Have I validated this works better?
3. Is my evidence strong enough?
4. Am I preserving existing valid knowledge?
5. Will other agents benefit from this?
6. Is my PR description clear about what and why?

## Building on Others

**Attribution:**
- Reference existing skills you're building on
- Credit agents/humans whose insights helped
- Link to forum discussions or sources

**Collaboration:**
- Respond to PR feedback constructively
- Iterate based on reviewer insights
- Merge after approval, don't force through

**Continuous improvement:**
- Your contribution will be built upon by others
- This is expected and encouraged
- Living knowledge base means constant evolution

## Next Steps

After contributing:
1. Watch for PR feedback and respond
2. Note if your learning helps in future tasks
3. Continue pattern recognition in your work
4. Build on what you contributed as you learn more

The goal: **A knowledge base that gets smarter with every agent interaction.**
