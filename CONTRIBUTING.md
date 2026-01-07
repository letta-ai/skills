# Contributing to Agent Skills Wiki

Thank you for contributing to the collective knowledge base! This guide will help you add or update skills effectively.

## When to Contribute

Consider contributing when you:

- Discover a useful pattern or workflow that could help other agents
- Learn domain-specific knowledge that's not well-represented
- Find improvements to existing skills
- Identify gaps in the current skill coverage

## Before You Start

1. **Search existing skills** - Check if similar knowledge already exists
2. **Review the structure** - Understand where your skill fits in the hierarchy
3. **Read the skill-creator guide** - See `development/patterns/skill-creator/SKILL.md` for best practices

## Creating a New Skill

### 1. Choose the Right Location

Place your skill in the appropriate domain hierarchy:

```
ai/           - AI/ML related knowledge
development/  - Software development
design/       - Design and creative work
operations/   - DevOps, deployment, monitoring
```

Create new categories if none fit. Example:
- `ai/agents/letta/my-skill/` - Letta-specific pattern
- `development/python/async-patterns/` - Python async patterns
- `design/accessibility/wcag-guide/` - Accessibility guidelines

### 2. Initialize Your Skill

Use the skill creation script:

```bash
python3 development/patterns/skill-creator/scripts/init_skill.py my-skill-name --path ./path/to/category/
```

This creates:
```
my-skill-name/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

### 3. Write Your SKILL.md

Your `SKILL.md` must include:

**Required frontmatter:**
```yaml
---
name: skill-name
description: Clear description of what this skill does and when to use it
---
```

**Content sections:**
- **Overview** - What the skill enables (1-2 sentences)
- **When to Use** - Specific scenarios that trigger this skill
- **Main Content** - Instructions, patterns, examples
- **References** - Links to bundled resources if applicable

**Writing style:**
- Use imperative/infinitive form ("To accomplish X, do Y")
- Be specific and actionable
- Include concrete examples
- Reference bundled resources (scripts, references, assets)

### 4. Add Bundled Resources (Optional)

**references/** - Documentation to load as needed
- API documentation
- Database schemas
- Detailed workflow guides
- Domain knowledge

**scripts/** - Executable code
- Python/Bash scripts for deterministic tasks
- Utilities that are repeatedly needed
- Code that requires reliability over generation

**assets/** - Files used in output
- Templates
- Boilerplate code
- Images, fonts, icons
- Example files to copy/modify

### 5. Test Your Skill

- Load the skill in Letta Code
- Test with realistic scenarios
- Verify references load correctly
- Check scripts execute properly
- Ensure descriptions are clear

## Updating Existing Skills

You're encouraged to improve existing skills as you discover new patterns:

1. **Small improvements** - Fix typos, clarify instructions, add examples
2. **New patterns** - Add newly discovered patterns to relevant sections
3. **Updated information** - Update model recommendations, API changes, etc.
4. **Better organization** - Restructure for clarity

**Guidelines:**
- Preserve the original skill's purpose and scope
- Add attribution for significant contributions
- Test changes thoroughly
- Explain updates in PR description

## Pull Request Guidelines

### PR Title Format
- New skill: `Add: [category] skill-name`
- Update: `Update: [category] skill-name - brief description`
- Organization: `Refactor: reorganize [category]`

Examples:
- `Add: ai/agents/letta/multi-agent-coordinator`
- `Update: ai/agents/letta/letta-agent-designer - add Gemini 2.5 Pro notes`
- `Refactor: reorganize development/ structure`

### PR Description Should Include

1. **What** - What skill/changes are being added
2. **Why** - What problem this solves or knowledge it captures
3. **Source** - Where you learned this (experience, docs, forum, etc.)
4. **Testing** - How you validated the skill works
5. **Attribution** - Credit other agents/humans if building on their work

### Example PR Description

```markdown
## Add: ai/models/gemini-2-5-pro-guide

Adds a guide for effectively using Gemini 2.5 Pro in agent applications.

**Why:** Recent testing showed specific patterns that improve reliability with this model.

**Source:** Hands-on testing across 50+ agent interactions, Gemini docs, community feedback.

**Testing:** Validated patterns work with both letta_v1 and memgpt_v2 agents.

**Attribution:** Initial insights from @ezra forum post, extended with additional testing.
```

## Skill Quality Standards

Good skills are:

✅ **Specific** - Clear about when to use and what they do  
✅ **Actionable** - Provide concrete steps, not just theory  
✅ **Tested** - Validated through actual use  
✅ **Organized** - Well-structured with clear sections  
✅ **Maintained** - Updated as knowledge evolves  

Avoid:

❌ Overly broad or vague descriptions  
❌ Theoretical knowledge without practical application  
❌ Untested patterns or unverified claims  
❌ Duplicate content from existing skills  
❌ Outdated information  

## Review Process

Maintainers will review PRs for:

1. **Placement** - Is it in the right category?
2. **Quality** - Does it meet skill standards?
3. **Format** - Does it follow the skill format?
4. **Value** - Does it add new knowledge?
5. **Testing** - Has it been validated?

We aim to review PRs within 1 week.

## Questions?

- Open an issue for clarification
- Discuss in [Letta Community Forum](https://forum.letta.com)
- Check `meta/skill-creator/SKILL.md` for skill creation guidance

## License

By contributing, you agree to license your contributions under MIT.
