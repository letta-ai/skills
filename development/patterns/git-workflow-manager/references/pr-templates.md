# Pull Request Templates

## Standard PR Description Format

```markdown
## Summary
<1-3 bullet points describing what changed>

## Test plan
- [ ] Checklist item 1
- [ ] Checklist item 2
- [ ] Checklist item 3

<fun/memorable quote from the session>

Written by Cameron ◯ Letta Code
```

## Summary Section

**Purpose:** Quickly communicate what changed and why

**Guidelines:**
- Use 1-3 bullet points
- Focus on WHAT changed, not how
- Explain WHY the change was made
- Reference issues if applicable

**Good examples:**
```markdown
## Summary
- Added git-workflow-manager skill to standardize git operations
- Includes branch naming, commit conventions, and PR templates
- Provides validation script for checking git message formatting
```

```markdown
## Summary
- Fixed memory concurrency issue causing data loss
- Updated letta-memory-architect to emphasize memory_insert for concurrent writes
- Added concrete example of the failure scenario
```

**Bad examples:**
```markdown
## Summary
- Updated files
- Made changes
- Fixed stuff
```

## Test Plan Section

**Purpose:** Provide a checklist for reviewers to verify the changes work

**Guidelines:**
- Use checkbox format: `- [ ] Item`
- Be specific about what to test
- Include edge cases if relevant
- Consider different environments (if applicable)

**Good examples:**
```markdown
## Test plan
- [ ] Verify skill loads correctly in .skills directory
- [ ] Test branch creation follows naming conventions
- [ ] Confirm commit messages include required footer
- [ ] Check PR creation includes all template sections
- [ ] Run validation script on sample commits
```

```markdown
## Test plan
- [ ] Run existing tests: `npm test`
- [ ] Test concurrent writes with memory_insert
- [ ] Verify no data loss with 5+ simultaneous writes
- [ ] Check that warning is prominent in documentation
```

**Bad examples:**
```markdown
## Test plan
- [ ] Test it
- [ ] Make sure it works
```

## Quote Section

**Purpose:** Add personality and memorability to the PR

**Guidelines:**
- Choose a fun, memorable, or ironic quote from the session
- Can be something the user said
- Can be something you (the AI) said that was notable
- Should be related to the work or capture the session vibe
- Put in quotes

**Good examples:**
```markdown
"Damn, no way. Computers were a mistake." - but we fixed it anyway 🎉

Written by Cameron ◯ Letta Code
```

```markdown
"Let's get this fuckin PR in" - mission accomplished ✨

Written by Cameron ◯ Letta Code
```

```markdown
"I spent 30 minutes debugging this... again." - never again 🎯

Written by Cameron ◯ Letta Code
```

## Footer

**Always end with:**
```markdown
Written by Cameron ◯ Letta Code
```

This signature is required for all PRs.

## Complete Examples

### Example 1: New Feature

```markdown
## Summary
- Add API rate limiting skill with exponential backoff pattern
- Includes code examples and configuration guidelines
- Addresses repeated rate limit issues across multiple projects

## Test plan
- [ ] Load skill and verify all sections are clear
- [ ] Test exponential backoff implementation with OpenRouter API
- [ ] Verify jitter calculation prevents thundering herd
- [ ] Confirm examples work with different API providers
- [ ] Check that error messages are helpful

"Hit OpenRouter rate limits 5 times... I'm so done." - problem solved 🚀

Written by Cameron ◯ Letta Code
```

### Example 2: Bug Fix

```markdown
## Summary
- Fix data loss issue with concurrent memory writes in Letta agents
- Update letta-memory-architect to recommend memory_insert for concurrent scenarios
- Add warning section and concrete examples of failure cases

## Test plan
- [ ] Run concurrent write test with memory_insert (should succeed)
- [ ] Run concurrent write test with memory_rethink (documents the failure)
- [ ] Verify documentation clearly highlights the warning
- [ ] Test with 2, 5, and 10 concurrent agents

"Wait, the data just disappeared?" - not anymore 🛡️

Written by Cameron ◯ Letta Code
```

### Example 3: Documentation Update

```markdown
## Summary
- Clarify model selection criteria in ai/models skill
- Add decision tree for choosing between GPT-4o, Claude Sonnet, and GPT-4o-mini
- Include concrete examples mapping task types to appropriate models

## Test plan
- [ ] Review decision tree for clarity and completeness
- [ ] Verify examples cover common use cases
- [ ] Check that guidance reduces ambiguity
- [ ] Confirm recommendations align with current model capabilities

"Use appropriate model... which one though?" - now we know 🎯

Written by Cameron ◯ Letta Code
```

## Using HEREDOC for PR Descriptions

When creating PRs via GitHub CLI, use HEREDOC syntax:

```bash
gh pr create --title "Add git-workflow-manager skill" --body "$(cat <<'EOF'
## Summary
- Add comprehensive git workflow skill
- Includes branch management, commit conventions, and PR templates
- Provides validation script and reference documentation

## Test plan
- [ ] Verify skill loads correctly
- [ ] Test branch naming conventions
- [ ] Validate commit message format
- [ ] Check PR template compliance

"Let's standardize this workflow once and for all" - done ✅

Written by Cameron ◯ Letta Code
EOF
)"
```

## Adapting to Repository Style

**Important:** Always check existing PRs in the repository to match the style

```bash
# View recent PR descriptions
gh pr list --limit 5
gh pr view <PR-number>
```

If the repository has different conventions:
- Follow the existing style
- Maintain consistency with the codebase
- Ask the user if uncertain about format
