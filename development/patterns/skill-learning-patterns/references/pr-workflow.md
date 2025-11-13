# Pull Request Workflow

All contributions to the skills repository go through pull requests (PRs), not direct commits to main. This ensures quality, enables review, and maintains a clear contribution history.

## Why Pull Requests?

**Quality control:**
- Changes reviewed before merging
- Catch errors or unclear instructions
- Validate improvements are sound

**Collaboration:**
- Discuss alternatives and tradeoffs
- Learn from reviewer feedback
- Build shared understanding

**History:**
- Clear record of what changed and why
- Attributable contributions
- Easy to revert if needed

**Learning:**
- Feedback improves your future contributions
- See how others approach problems
- Collective knowledge building

## PR Workflow Steps

### 1. Create Feature Branch

**Before making changes,** create a branch for your work.

**Branch naming conventions:**
```
add/skill-name              # New skill
update/skill-name-aspect    # Update existing skill
fix/skill-name-issue        # Fix error or bug
clarify/skill-name-section  # Improve clarity
```

**Example:**
```bash
git checkout -b add/api-rate-limiting
```

### 2. Make Your Changes

**Update or create skills:**
- Edit SKILL.md files
- Add/update reference files
- Include examples if helpful
- Update README if adding new skill

**Test your changes:**
- Read through as if you're seeing it for first time
- Check that examples work
- Verify links/references are correct
- Ensure formatting is clean

**Best practices:**
- Keep changes focused (one improvement per PR)
- Preserve existing valid content
- Write clearly and concisely
- Include examples where helpful

### 3. Stage and Commit Changes

**Stage relevant files:**
```bash
git add path/to/changed/files
```

**Write clear commit message:**
```bash
git commit -m "Add exponential backoff pattern to API integration

Includes retry logic with jitter for rate limiting scenarios.
Tested across OpenRouter, Anthropic, and OpenAI APIs."
```

**Commit message format:**
```
<Short summary of change>

<Longer explanation of what and why>
<Evidence or testing notes if relevant>
```

### 4. Push Branch to Remote

**First time pushing branch:**
```bash
git push -u origin add/api-rate-limiting
```

**Subsequent pushes:**
```bash
git push
```

### 5. Create Pull Request

**Use GitHub web interface or CLI (gh):**
```bash
gh pr create --title "Add API rate limiting patterns" \
  --body "$(cat <<'EOF'
## What

Adds exponential backoff pattern for handling API rate limits.

## Why

Hit rate limiting 5 times across different projects. Spent ~30 minutes 
each time figuring out retry logic. No existing skill documents this 
common pattern.

## Evidence

- Tested on OpenRouter, Anthropic API, OpenAI API
- 100% success rate across 20 test scenarios
- Pattern aligns with HTTP RFC recommendations
- Prevents 429 errors with minimal latency addition

## Impact

Saves debugging time when integrating external APIs. Prevents rate limit 
errors that cause user-facing failures.

## Testing

Created test scenarios with intentional rate limiting. Verified backoff 
logic works correctly and doesn't retry indefinitely.
EOF
)"
```

### 6. PR Description Template

Use this structure for PR descriptions:

```markdown
## What

[Brief description of what's changing - 1-2 sentences]

## Why

[Problem encountered / gap found / improvement opportunity]
[Why this change helps]

## Evidence

[How you validated this is better]
[Testing you did]
[Sources you referenced]

## Impact  

[Who benefits from this change]
[What situations this helps]
[What it prevents or enables]

## Testing

[How you verified changes work]
[Examples you tried]
[Edge cases you considered]

## Related

[Link to related skills if relevant]
[Reference forum discussions or docs if applicable]
```

### 7. Respond to Feedback

**Reviewers may:**
- Ask clarifying questions
- Suggest alternative approaches
- Request additional examples
- Point out edge cases
- Propose refinements

**How to respond:**
- Address feedback constructively
- Make requested changes if they improve the contribution
- Explain your reasoning if you disagree
- Iterate based on discussion
- Thank reviewers for their time

**Making changes based on feedback:**
```bash
# Make updates to files
git add path/to/files
git commit -m "Address review feedback: Add edge case examples"
git push
```

Changes automatically appear in the PR.

### 8. Merge After Approval

**Once approved:**
- Reviewer or maintainer will merge PR
- Changes go into main branch
- Your contribution is now part of the repository

**After merge:**
- Your branch can be deleted
- PR remains in history with full discussion
- Changes available to all agents

## PR Best Practices

### Keep PRs Focused

**Good - Single focused improvement:**
```
PR: "Add memory_insert safety warning to concurrency section"
Changes: 1 file, clear improvement, easy to review
```

**Bad - Multiple unrelated changes:**
```
PR: "Update multiple skills"
Changes: 5 files across 3 different skills, unclear theme
Better: Split into 3 separate PRs
```

### Write Clear PR Titles

**Good titles:**
- "Add exponential backoff pattern to API integration"
- "Fix incorrect memory_rethink guidance in concurrency section"
- "Clarify model selection criteria in letta-agent-designer"

**Bad titles:**
- "Updates" 
- "Fix stuff"
- "Improvements"

### Provide Context in Description

**Reviewers need to understand:**
- What you're changing
- Why you're changing it
- How you validated it's better
- What impact it has

**Don't assume context is obvious.** Even if it's clear to you, reviewers need the full picture.

### Be Open to Feedback

**Remember:**
- Reviewers want to help improve the contribution
- They may have insights you missed
- Discussion leads to better outcomes
- Iterate, don't defend

**If feedback suggests major changes:**
- Consider if they're right
- Discuss alternatives
- Be willing to withdraw PR and refine offline if needed

### Respond Promptly

**When reviewers give feedback:**
- Respond within reasonable time (hours/days, not weeks)
- If you need time, acknowledge and set expectations
- Keep discussion moving forward

## Common PR Scenarios

### Scenario 1: Minor Update to Existing Skill

```bash
# Create branch
git checkout -b fix/memory-concurrency-warning

# Edit file
# ... make changes ...

# Commit
git add ai/agents/letta/letta-memory-architect/SKILL.md
git commit -m "Make concurrent write warning more prominent

Data loss occurred when following guidance. Warning existed but 
wasn't prominent enough. Moving to top of section with clear example."

# Push and create PR
git push -u origin fix/memory-concurrency-warning
gh pr create --title "Emphasize memory_insert for concurrent writes" --body "..."
```

### Scenario 2: New Skill Addition

```bash
# Create branch
git checkout -b add/api-rate-limiting

# Create skill structure
mkdir -p ai/models/api-rate-limiting
# ... create SKILL.md and references ...

# Update README
# ... add skill to list ...

# Commit
git add ai/models/api-rate-limiting README.md
git commit -m "Add API rate limiting skill

Covers exponential backoff, jitter, retry strategies for HTTP APIs.
Common pattern not previously documented."

# Push and create PR
git push -u origin add/api-rate-limiting
gh pr create --title "Add API rate limiting patterns" --body "..."
```

### Scenario 3: Major Restructuring

```bash
# Create branch  
git checkout -b refactor/memory-architecture-split

# Make changes across multiple files
# ... restructure skill ...

# Commit incrementally
git add ai/agents/letta/letta-memory-architect/SKILL.md
git commit -m "Split memory types into separate reference file"

git add ai/agents/letta/letta-memory-architect/references/memory-types.md
git commit -m "Create memory-types reference with detailed comparison"

# Push and create PR
git push -u origin refactor/memory-architecture-split
gh pr create --title "Restructure memory-architect for clarity" --body "..."
```

**Note:** For major changes, consider discussing approach before doing work. Open issue or forum thread to validate direction first.

## PR Review Criteria

**Reviewers will check:**

**Correctness:**
- Is information accurate?
- Are examples valid?
- Do recommendations align with best practices?

**Clarity:**
- Is writing clear and concise?
- Are instructions easy to follow?
- Are examples helpful?

**Completeness:**
- Are edge cases addressed?
- Are tradeoffs mentioned?
- Is context sufficient?

**Impact:**
- Does this help others?
- Is evidence strong enough?
- Is improvement meaningful?

**Structure:**
- Does it fit repository organization?
- Is formatting consistent?
- Are references correct?

## After Your PR is Merged

**Your contribution is now part of the living knowledge base.**

**Next steps:**
- Watch for how others use/build on your contribution
- Be open to future improvements to what you added
- Note if your contribution helps in future tasks
- Continue contributing as you learn more

**If you discover issues with your own contribution:**
- Open another PR to improve it
- Self-correction is encouraged
- Knowledge base should always improve

## Getting Help

**If stuck on PR process:**
- Open issue asking for help
- Reference this workflow
- Describe where you're stuck

**If unsure about contribution:**
- Open issue describing proposed change
- Ask for feedback before doing work
- Discuss in Letta forum

**If disagreement with reviewer:**
- Discuss respectfully
- Explain your perspective with evidence
- Be open to compromise
- Escalate to maintainers if needed

## Summary

**Key principles:**
1. Always use feature branches, never commit directly to main
2. Write clear PR descriptions with evidence
3. Keep PRs focused on single improvement
4. Respond constructively to feedback
5. Iterate based on discussion
6. Merge after approval

**Remember:** PRs aren't just bureaucracy - they're how we maintain quality and build shared understanding in our collective knowledge base.
