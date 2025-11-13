# Memory Block Description Patterns

Good descriptions guide the agent on when to read and update blocks. Use instructional style that clearly indicates purpose and usage.

## Template Structure

```
[What this block contains]. [When to reference it]. [When/how to update it].
```

## Examples by Use Case

### Read-Only Reference Blocks

**Brand Guidelines:**
```
"Brand tone, voice, and style guidelines. Reference this when generating any customer-facing content to ensure consistency with brand identity."
```

**Company Policies:**
```
"Company policies and procedures for customer support. Reference when handling returns, warranties, or service requests."
```

**API Documentation:**
```
"API endpoints and authentication patterns for [Service]. Reference when building integrations or debugging API calls."
```

### Actively Updated Blocks

**Customer Profile:**
```
"Current customer's business context and preferences. Update as you learn more about their needs, priorities, and constraints."
```

**Project Context:**
```
"Current project architecture, active tasks, and goals. Update when the user shares new information about the project or shifts focus."
```

**Interaction History:**
```
"Recent interactions and key decisions. Update after significant conversations to track context and progress."
```

### Task Management Blocks

**Current Task:**
```
"Active task, planned approach, and progress. Update as work advances, blockers emerge, or requirements change."
```

**Todo List:**
```
"Outstanding tasks and priorities. Add tasks when identified, remove when completed, update priorities as needed."
```

### User Preference Blocks

**Communication Preferences:**
```
"User's preferred communication style, level of detail, and response format. Update when the user corrects your approach or expresses preferences."
```

**Working Constraints:**
```
"User's time zone, availability, and scheduling constraints. Update when planning or scheduling activities."
```

## Anti-Patterns to Avoid

### Too Vague

❌ Bad:
```
"Contains customer information"
```

✅ Good:
```
"Current customer's business context and preferences. Update as you learn more about their needs, priorities, and constraints."
```

### Missing Update Guidance

❌ Bad:
```
"Project architecture and stack information."
```

✅ Good:
```
"Current project architecture, active tasks, and goals. Update when the user shares new information about the project or shifts focus."
```

### Passive Voice

❌ Bad:
```
"This block should be referenced when brand consistency is needed."
```

✅ Good:
```
"Reference this when generating customer-facing content to ensure brand consistency."
```

## Label Conventions

**Use underscores, not spaces:**
- ✅ `customer_profile`
- ❌ `customer profile`

**Keep short and descriptive:**
- ✅ `project_context`
- ✅ `brand_guidelines`
- ❌ `information_about_the_current_project_and_context`

**Think like variable names:**
- ✅ `current_task`
- ✅ `interaction_history`
- ✅ `communication_preferences`
