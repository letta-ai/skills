# Validation Criteria

Before contributing changes to the repository, validate that your learning is solid and will benefit others. Different types of contributions have different validation standards.

## Contribution Types

### Tool/SDK Documentation
**Purpose:** Help agents integrate widely-used tools with battle-tested insights

**What qualifies as "widely-used":**
- Has 1000+ GitHub stars OR
- Appears in top search results for its problem domain OR  
- Is a Letta product

**Validation standards:**
- Shares battle-tested insights beyond official docs (what you struggled with, not basic usage)
- Documents common pitfalls, workarounds, and agent-specific patterns
- Well-documented with working examples
- Accurate and up-to-date
- NOT just "getting started" guides (official docs already cover that)

**Examples:** 
- ✅ Claude SDK: Common pitfalls when streaming responses
- ✅ Playwright: Testing patterns for AI-driven web apps  
- ✅ MCP servers: Integration patterns for tool calling
- ❌ "How to install FastAPI" (just use official docs)

### Pattern Contributions
**Purpose:** Share patterns discovered through agent experience

**Validation standards:**
- Seen 2-3+ times across different contexts
- Tested and proven better than alternatives
- Generalizable beyond specific projects
- Explains tradeoffs and edge cases
- Framework-specific patterns require validation through real agent experience (not just "well-established practices")

**Examples:** 
- General: API rate limiting patterns, memory architecture principles, error handling strategies
- Framework-specific (validated): React patterns tested across multiple agent UI projects, FastAPI patterns proven in production

## Core Validation Questions

The questions below apply primarily to **pattern contributions**. Tool/SDK documentation follows different standards (see above).

### 1. Did You Test That Your Approach Works Better?

**What this means:**
- Compare before and after
- Measure improvement (time saved, errors prevented, clarity gained)
- Try both approaches if possible

**Example - PASS:**
```
Old approach: memory_rethink for all updates
New approach: memory_insert for concurrent writes
Test: Ran 10 concurrent update scenarios
Result: 0 data loss with memory_insert vs 7/10 data loss with memory_rethink
Validated: Yes, objectively better for concurrent scenarios
```

**Example - FAIL:**
```
Old approach: Use GPT-4o
New approach: Use Claude Sonnet  
Test: Tried once, seemed fine
Result: Personal preference, no systematic comparison
Validated: No, insufficient evidence
```

### 2. Is This Generalizable Beyond Your Specific Context?

**CRITICAL:** This is the most important validation criterion. Skills must contain **general-purpose knowledge**, not project-specific solutions.

**What this means:**
- Works across different projects/contexts
- Not dependent on your unique setup/environment
- Solves problems many agents will encounter
- Teaches patterns, principles, or widely-applicable practices

**Example - PASS (General pattern):**
```
Pattern: API rate limiting with exponential backoff
Context tested: OpenRouter, Anthropic API, OpenAI API
Result: Pattern worked across all three
Generalizable: Yes, applies to most HTTP APIs
Why general: HTTP rate limiting is universal problem with standard solution
```

**Example - FAIL (Too specific):**
```
Pattern: Our company API endpoint for user data is https://api.acme.com/v2/users
Context: My project at Acme Corp
Result: Works for my project
Generalizable: No, this is project-specific configuration
Why not general: Only applies to one company's API
```

**Example - FAIL (Environment-specific):**
```
Pattern: Restart Docker container to fix database connection
Context: My local setup with specific networking config
Result: Works for me
Generalizable: No, this is environment-specific workaround
Why not general: Root cause likely in specific environment, not universal pattern
```

**Red flags for overly-specific contributions:**
- Contains specific URLs, API keys, or credentials for one project
- Describes configuration unique to your environment
- Only tested in one narrow context
- Solution is "what I did" vs "what pattern works generally"
- Other agents won't encounter this exact situation

### 3. Have You Seen This Pattern Multiple Times?

**What this means:**
- Not a one-off occurrence
- Recurring problem or consistent improvement
- Can be demonstrated with multiple examples

**Example - PASS:**
```
Pattern: Playwright tests need networkidle wait
Occurrences: Failed 5 times across 3 projects
Fix applied: Consistent success after adding wait
Evidence: Strong, recurring pattern
```

**Example - FAIL:**
```
Pattern: Specific npm package version fixes issue
Occurrences: Once in my project
Fix applied: Worked that one time
Evidence: Weak, might be coincidental
```

### 4. Does This Address Real Gap vs Personal Preference?

**What this means:**
- Objective improvement vs subjective style
- Solves actual problem vs changes working approach
- Benefits others vs just how you like to work

**Example - PASS:**
```
Gap: No documentation on handling streaming responses
Impact: Agents repeatedly implement from scratch
Benefit: Common pattern that saves time
Real gap: Yes
```

**Example - FAIL:**
```
Preference: I prefer using arrow functions in JavaScript
Current: Skill uses regular functions
Benefit: Purely stylistic
Real gap: No, just preference
```

### 5. Are There Edge Cases or Tradeoffs?

**What this means:**
- Identified when approach doesn't work
- Documented limitations
- Considered alternatives

**Example - PASS:**
```
Approach: Use memory_insert for concurrent writes
Tradeoff: Block grows faster, need monitoring
Edge case: Single-agent can still use memory_replace for precision
Documented: Yes, included both benefits and tradeoffs
```

**Example - FAIL:**
```
Approach: Always use GPT-4o-mini for cost savings
Tradeoff: Not considered - some tasks need GPT-4o
Edge case: Not identified - complex reasoning suffers
Documented: No, presented as universal solution
```

## Evidence Strength Levels

### Strong Evidence ✅
- Multiple independent occurrences (3+)
- Measured improvement (time, errors, cost)
- Tested across different contexts
- Confirmed with documentation/community
- Has clear before/after comparison

### Moderate Evidence ⚠️
- 2-3 occurrences
- Logical reasoning for improvement
- Works in your context reliably
- Some validation but not exhaustive
- Can articulate trade-offs

### Weak Evidence ❌
- Single occurrence
- "Feels better" without measurement
- Untested in other contexts
- Based on assumption not experience
- No comparison with alternatives

**Contribution guideline:** 
- Strong evidence → Contribute confidently
- Moderate evidence → Contribute with caveats noted
- Weak evidence → More testing needed before contributing

## Specific vs General: Examples

Understanding the difference between project-specific solutions and general-purpose knowledge is critical.

### ❌ Too Specific (Do NOT contribute)

**Example 1: Project configuration**
```
Skill: "How to connect to our company database"
Content: "Use postgres://user:pass@db.acme.com:5432/production"
Why bad: Only applies to one company's infrastructure
```

**Example 2: One-off workaround**
```
Skill: "Fix for my Docker networking issue"
Content: "Run docker network prune && restart container"
Why bad: Addresses symptom in specific environment, not root cause or pattern
```

**Example 3: Personal workflow**
```
Skill: "My preferred way to organize code"
Content: "I like to put all API calls in src/api/ folder"
Why bad: Personal preference without objective benefit or widespread adoption
```

**Example 4: Narrow tool usage**
```
Skill: "How I used library X for project Y"
Content: Specific implementation details for one project
Why bad: Too narrow - describes one implementation vs teaching general patterns
```

### ✅ Appropriately General (Good contributions)

**Example 1: General pattern**
```
Skill: "Database connection pooling patterns"
Content: When to use pooling, configuration strategies, common pitfalls
Why good: Applies to any database connection, teaches principles
```

**Example 2: Universal problem**
```
Skill: "Handling API rate limits with exponential backoff"
Content: Pattern, implementation strategies, when to use
Why good: Common problem with well-established solution, broadly applicable
```

**Example 3: Framework-agnostic principle**
```
Skill: "Error handling in async operations"
Content: Strategies for retry, timeout, graceful degradation
Why good: Teaches concepts that apply across languages/frameworks
```

**Example 4: Tool pattern**
```
Skill: "Testing strategies for web applications"
Content: When to use unit vs integration vs e2e tests, how to structure tests
Why good: Principles apply regardless of specific testing framework
```

### The Test: "Would this help an agent working on a different project?"

**Ask yourself:**
- Would an agent working on a completely different project find this useful?
- Does this teach a pattern/principle or just document my specific setup?
- Am I solving a universal problem or my unique situation?
- Is this "how to think about X" or "what I did for Y"?

**If the answer is "this only helps agents working on my exact project" → Too specific**

## Validation Methods

### Method 1: Direct Testing

**Process:**
1. Implement old approach
2. Implement new approach
3. Compare objectively
4. Document results

**Example:**
```
Testing model selection for code review task:

GPT-4o-mini:
- Time: 2.3s average
- Cost: $0.002 per review
- Quality: Missed 2/10 subtle issues

GPT-4o:
- Time: 3.1s average  
- Cost: $0.012 per review
- Quality: Caught all issues

Conclusion: GPT-4o worth cost for code review quality
```

### Method 2: Comparative Analysis

**Process:**
1. Search for alternative approaches
2. Compare pros/cons
3. Identify use cases for each
4. Document decision criteria

**Example:**
```
Analyzing memory update tools:

memory_insert:
+ Safe for concurrent writes
+ Simple append operation
- Block grows unbounded

memory_replace:
+ Precise edits
+ Control over size
- Race conditions possible

memory_rethink:
+ Complete reorganization
+ Can consolidate/summarize
- Highest concurrency risk

Recommendation: Choose based on concurrency needs and update patterns
```

### Method 3: Community Validation

**Process:**
1. Check official documentation
2. Search community discussions
3. Verify with examples from others
4. Cite sources

**Example:**
```
Pattern: Streaming responses from OpenAI

Verified:
- OpenAI docs show stream=true parameter
- Letta forum has 3 threads about streaming
- Pattern documented in OpenAI cookbook

Confidence: High, community-validated pattern
```

### Method 4: Reasoning from First Principles

**Process:**
1. Understand underlying mechanism
2. Reason about why approach works
3. Identify assumptions
4. Test assumptions if possible

**Example:**
```
Pattern: Use environment variables for API keys

Reasoning:
- Keeps secrets out of code
- Different keys per environment (dev/prod)
- Standard practice across platforms
- Security principle: separation of config and code

Assumptions:
- Environment is secure
- Deployment supports env vars

Validation: Principle-based, industry standard
```

## Red Flags (Don't Contribute Yet)

🚩 **"It worked once so it must be the answer"**
→ Need more instances

🚩 **"This is obviously better"**  
→ Need objective comparison

🚩 **"Everyone should do it this way"**
→ Consider different use cases

🚩 **"I prefer this approach"**
→ Separate preference from improvement

🚩 **"The skill is wrong because I had a problem"**
→ Verify skill isn't right for different context

🚩 **"This hack fixes it"**
→ Understand why it works, ensure it's reliable

## Validation Checklist

Before submitting PR, confirm:

- [ ] I tested my approach works reliably
- [ ] I compared it with existing approach or alternatives
- [ ] I've seen this pattern 2+ times OR have strong evidence
- [ ] This helps others, not just my specific case
- [ ] I documented tradeoffs and edge cases
- [ ] I considered when NOT to use this approach
- [ ] I can explain WHY this is better
- [ ] I preserved valid existing information

If all checked → Strong contribution

If 5-6 checked → Good contribution with caveats

If <5 checked → More validation needed

## Examples of Validated Contributions

### Example 1: Well-Validated

**Contribution:** Add rate limiting pattern to API integration

**Validation:**
- ✅ Tested across 5 different APIs
- ✅ Prevented 100% of rate limit errors in testing
- ✅ Pattern is standard (documented in HTTP RFCs)
- ✅ Generalizable to any HTTP API
- ✅ Documented when to use (high-traffic scenarios)
- ✅ Noted trade-off (adds retry latency)

**Verdict:** Ready to contribute

### Example 2: Needs More Work

**Contribution:** Always use Claude Sonnet instead of GPT-4o

**Validation:**
- ❌ Only tried on one type of task
- ❌ Subjective assessment ("felt better")
- ❌ Didn't measure quality difference
- ❌ Presented as universal when context-dependent
- ❌ No discussion of trade-offs
- ✅ Used both models at least

**Verdict:** Need systematic comparison across task types

### Example 3: Validated with Caveats

**Contribution:** Add warning about interactive git commands

**Validation:**
- ✅ git add -i failed consistently in Bash tool
- ✅ Clear reason why (non-interactive environment)
- ✅ Helps others avoid same error
- ⚠️ Only tested in Letta Code Bash tool environment
- ✅ Documented the limitation clearly
- ✅ Provided alternative approach

**Verdict:** Good contribution, specify environment context

## When in Doubt

**Ask yourself:**
- "Would I want to find this information if I were another agent?"
- "Is my evidence strong enough that I'd bet on it working?"
- "Have I done due diligence to validate this?"

**If unsure:**
- Add more testing
- Seek feedback in discussion before PR
- Mark contribution as "preliminary" or "needs validation"
- Include your uncertainty in the PR description

**Remember:** It's better to validate thoroughly than to contribute questionable information that misleads others.
