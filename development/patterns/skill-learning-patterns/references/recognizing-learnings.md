# Recognizing Learnings

Valuable learnings often reveal themselves through specific signals during your work. Train yourself to notice these patterns.

## Time Investment Signals

### Debugging Time
**Signal:** "I spent 20+ minutes debugging this issue"

**Questions to ask:**
- Was this documented anywhere?
- Did I search existing skills first?
- Would documenting this prevent future debugging time?
- Is this a one-off or recurring pattern?

**Example:**
```
Spent 45 minutes figuring out why Playwright tests were flaky. 
Root cause: Need to wait for network idle, not just element presence.
Pattern documented? No. Should be? Yes - common issue with webapp-testing.
```

### Trial and Error
**Signal:** "I tried 3+ approaches before finding what worked"

**Questions to ask:**
- Were the failed approaches reasonable attempts?
- What made the winning approach better?
- Could guidance have prevented the trial-and-error?

**Example:**
```
Tried git rebase -i (failed - interactive not supported)
Tried git reset (lost work)
Finally: git rebase HEAD~3 worked
Could this be documented in git-workflows? Yes.
```

### "Wish I Had Known"
**Signal:** "I wish I had known this at the start"

**Questions to ask:**
- Where would I have looked for this info?
- What skill should contain this?
- How much time would it have saved?

**Example:**
```
Spent hour implementing custom retry logic for API calls.
Later discovered: Most API libraries have built-in retry with backoff.
Should be in api-integration skill: "Check library features first"
```

## Repetition Signals

### Recurring Problem
**Signal:** "This is the third time I've solved this exact problem"

**Strong indicator** that knowledge should be captured.

**Questions to ask:**
- Am I solving it the same way each time?
- Have I refined my approach across iterations?
- Would other agents encounter this?

**Example:**
```
Third time setting up Letta agent with file system access.
Same steps each time: attach folder, verify tools appear, test read access.
Create quick-start pattern in letta-agent-designer.
```

### Deja Vu Moments
**Signal:** "I remember doing something similar before"

**Questions to ask:**
- What was different about the previous context?
- What was the same (the generalizable pattern)?
- Can I extract the common pattern?

**Example:**
```
Configuring environment variables for third different framework.
Pattern: All frameworks need .env file, loading mechanism differs.
Extract: Common env var patterns, framework-specific loading details.
```

### Teaching Moments
**Signal:** "Let me explain how this works..."

**When you explain something to a user, you're identifying knowledge worth documenting.**

**Questions to ask:**
- Did I explain this clearly?
- Would this explanation help in a skill?
- Are there examples that made it click?

**Example:**
```
Explained memory_insert vs memory_replace to user with concurrent scenario.
User understood immediately with the example.
Capture example in letta-memory-architect for future clarity.
```

## Correction Signals

### Skill Led Astray
**Signal:** "The skill said X, but Y actually works better"

**Critical learning moment - either skill is wrong or you misunderstood.**

**Questions to ask:**
- Did I follow instructions correctly?
- Are there conditions where X is right but Y is better for my case?
- Is the skill outdated or incomplete?

**Example:**
```
Skill said: "Use GPT-4 for complex tasks"
But: GPT-4o is newer, faster, same quality, lower cost
Skill needs update: GPT-4o is now preferred over GPT-4
```

### Approach Failed
**Signal:** "This approach failed in ways not documented"

**Questions to ask:**
- Was the failure predictable?
- Should the skill warn about this?
- What's the workaround?

**Example:**
```
Followed git-workflows to use git add -i (interactive add)
Failed: Interactive mode not supported in Bash tool
Add warning to skill about non-interactive environment
```

### Misunderstanding Caused Issue
**Signal:** "I misunderstood the instruction and it caused problems"

**Even if you made the mistake, ambiguous instructions should be clarified.**

**Questions to ask:**
- Would others misunderstand the same way?
- What clarification would have prevented this?
- Are there examples that would make it clearer?

**Example:**
```
Skill said: "Use appropriate model for task"
I chose GPT-4 (expensive) when GPT-4o-mini would've worked
Add decision criteria: task complexity, budget, latency needs
```

## Discovery Signals

### Gap Found
**Signal:** "I needed to know X but no skill covers it"

**Questions to ask:**
- Is this narrow domain or broadly applicable?
- Have I validated my approach?
- Would this help others or just me?

**Example:**
```
Needed to parse YAML frontmatter from markdown files.
No skill covers this common pattern in document processing.
Create: parsing-markdown skill or add to document patterns.
```

### Better Pattern Emerged
**Signal:** "I've found a better way to structure this"

**Questions to ask:**
- Better in what way? (Faster, clearer, more reliable?)
- What's the tradeoff?
- Is this preference or objective improvement?

**Example:**
```
Initially: Put all customer info in one block
Better: Split into customer_business, customer_contact, customer_history
Why: Each grows independently, clearer boundaries, easier to manage
Objective improvement: Addresses size management and clarity
```

### New Tool/Technique
**Signal:** "This tool/approach is much better than what we're using"

**Questions to ask:**
- Is this genuinely better or just different?
- What's the learning curve?
- Are there situations where old approach is still better?

**Example:**
```
Discovered ripgrep (rg) is much faster than grep for codebase search.
Already in use: Grep tool actually uses ripgrep under the hood
No action needed, but validates existing choice.
```

## False Positives to Avoid

### One-Off Edge Case
**Signal:** "This weird situation needed a weird fix"

**Usually NOT worth documenting unless:**
- Edge case is common
- Others will likely hit it
- The fix is non-obvious

### Personal Preference
**Signal:** "I prefer doing it this way"

**Only document if:**
- Preference has objective advantages
- Multiple valid approaches exist and should be explained
- Tradeoffs are worth documenting

### Temporary Workaround
**Signal:** "This hack works for now"

**Document IF:**
- Others will hit same issue
- Workaround is reliable enough
- Note it as temporary/workaround

**Don't document IF:**
- Proper fix is known and achievable
- Workaround is fragile
- Problem is specific to your environment

## Building Recognition Habit

**During work:**
- Keep mental note of "moments of friction"
- Notice when you reference external docs repeatedly
- Track time spent on recurring problems

**After completing task:**
- Review: What was hard? What took time?
- Ask: Could this be prevented next time?
- Consider: Would documenting this help others?

**Over time:**
- Pattern recognition improves
- You'll spot learnings faster
- Contributing becomes natural

## When NOT to Contribute

**CRITICAL:** Skills must be **general-purpose knowledge**, not project-specific solutions.

Sometimes the learning is valuable for you but not for the repository:

### ❌ Project-Specific Information

**Do NOT contribute:**
- Your company's API endpoints or credentials
- Configuration specific to your environment
- Project-specific file paths or structure
- Internal tool names or processes unique to your organization
- Solutions that only work in your exact setup

**Example of what NOT to contribute:**
```
"Our API endpoint for user data is https://api.acme.com/v2/users. 
Use header X-Acme-Key for authentication."

This is configuration for one specific project, not generalizable knowledge.
```

### ❌ Personal Preferences

**Do NOT contribute:**
- "I prefer approach X" without objective benefit
- Code organization that's just your style
- Tool choices based on personal taste
- Workflows that work for you but aren't broadly better

**Example of what NOT to contribute:**
```
"I like to organize my code with all API calls in src/api/ directory."

This is personal preference, not a pattern with clear advantages.
```

### ❌ One-Off Situations

**Do NOT contribute:**
- Temporary workarounds that will be obsolete soon
- One-time edge cases unlikely to recur
- Unusual situations unique to your context
- Hacks that address symptoms not root causes

**Example of what NOT to contribute:**
```
"When Docker container won't start, run docker network prune then restart."

This addresses a symptom in your environment, not a general pattern.
```

### ❌ Overly Narrow Knowledge

**Do NOT contribute:**
- How you implemented one specific feature
- Step-by-step for your exact use case
- Details that only matter in narrow contexts
- Information too specific to be broadly useful

**Example of what NOT to contribute:**
```
"How I built the user authentication for my todo app using Firebase Auth 
with Google OAuth and custom claims for role-based access."

This is one specific implementation, not teaching general patterns.
```

### ✅ What TO Contribute Instead

Transform specific learnings into general patterns:

**Bad (too specific):**
```
"Fix Docker networking issue by running docker network prune"
```

**Good (general pattern):**
```
"Debugging network connectivity in containerized environments: 
systematic approaches to isolate network vs. application issues"
```

**Bad (too specific):**
```
"Our database connection string for production"
```

**Good (general pattern):**
```
"Database connection pooling patterns and configuration strategies 
for high-traffic applications"
```

**The test:** Would this help an agent working on a completely different project? If no → too specific.

Focus contributions on **generalizable, validated, impactful learnings** that help the collective across different projects and contexts.
