# Commit Conventions

## Standard Commit Format

All commits should follow this format:

```
<summary line>

🐾 Generated with [Letta Code](https://letta.com)

Co-Authored-By: Letta <noreply@letta.com>
```

## Summary Line Guidelines

**Length:** Keep under 72 characters (GitHub truncates at 72)

**Style:**
- Use imperative mood: "Add feature" not "Added feature"
- Start with a verb: Add, Update, Fix, Remove, Refactor, etc.
- Be specific and descriptive
- Don't end with a period

**Good examples:**
```
Add git-workflow-manager skill
Fix memory concurrency warning in letta-memory-architect
Update PR description template with quote requirement
Refactor API rate limiting to use exponential backoff
Remove deprecated authentication method
```

**Bad examples:**
```
Updated stuff
Fixed bug
Changes
WIP
.
```

## Common Prefixes

- `Add` - New features, files, or functionality
- `Update` - Modifications to existing features
- `Fix` - Bug fixes
- `Remove` - Deletion of code or features
- `Refactor` - Code restructuring without changing behavior
- `Improve` - Performance or quality improvements
- `Document` - Documentation changes
- `Test` - Test additions or modifications
- `Chore` - Maintenance tasks (dependencies, config, etc.)

## Conventional Commits (Optional)

Some projects use the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style changes (formatting, semicolons, etc.)
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `perf:` - Performance improvement
- `test:` - Adding or correcting tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat(auth): add OAuth2 authentication
fix(api): resolve race condition in rate limiter
docs(readme): update installation instructions
```

## Multi-line Commits

When more context is needed:

```
Add comprehensive git workflow skill

This skill provides standardized workflows for:
- Branch management and naming conventions
- Commit message formatting
- PR creation and description templates
- Merge strategies and best practices

Includes validation scripts and reference documentation
to ensure consistency across repositories.

🐾 Generated with [Letta Code](https://letta.com)

Co-Authored-By: Letta <noreply@letta.com>
```

**Body guidelines:**
- Wrap at 72 characters
- Explain what and why, not how
- Separate from subject with blank line
- Use bullet points for multiple items

## Amending Commits

If pre-commit hooks modify files:
```bash
git commit --amend --no-edit
```

If you need to fix the last commit message:
```bash
git commit --amend -m "New message"
```

## What NOT to Commit

Never commit:
- Secrets, API keys, passwords
- Personal information
- Large binary files (unless intentional)
- Generated files (unless required)
- IDE-specific files (add to .gitignore)
- Debug logs

## Using HEREDOC for Commit Messages

Always use HEREDOC syntax for multi-line commits to ensure proper formatting:

```bash
git commit -m "$(cat <<'EOF'
Your commit message here
Can span multiple lines

🐾 Generated with [Letta Code](https://letta.com)

Co-Authored-By: Letta <noreply@letta.com>
EOF
)"
```

The `<<'EOF'` syntax (with quotes) prevents variable expansion, ensuring literal text.
