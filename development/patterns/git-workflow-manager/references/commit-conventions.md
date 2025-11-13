# Commit Conventions

## General Guidelines

### Summary Line

**Length:** Keep under 72 characters (GitHub truncates at 72)

**Style:**
- Use imperative mood: "Add feature" not "Added feature"
- Start with a verb: Add, Update, Fix, Remove, Refactor, etc.
- Be specific and descriptive
- Don't end with a period (common convention)

**Good examples:**
```
Add API rate limiting with exponential backoff
Fix memory concurrency issue in write operations
Update documentation to clarify installation steps
Refactor authentication logic for better testability
Remove deprecated OAuth v1 endpoints
```

**Bad examples:**
```
Updated stuff
Fixed bug
Changes
WIP
.
```

### Common Prefixes

- `Add` - New features, files, or functionality
- `Update` - Modifications to existing features
- `Fix` - Bug fixes
- `Remove` - Deletion of code or features
- `Refactor` - Code restructuring without changing behavior
- `Improve` - Performance or quality improvements
- `Document` - Documentation changes
- `Test` - Test additions or modifications
- `Chore` - Maintenance tasks (dependencies, config, etc.)

## Conventional Commits

Many projects use the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style changes (formatting, semicolons, etc.)
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `perf:` - Performance improvement
- `test:` - Adding or correcting tests
- `chore:` - Maintenance tasks
- `build:` - Build system changes
- `ci:` - CI/CD changes

### Examples

```
feat(auth): add OAuth2 authentication
fix(api): resolve race condition in rate limiter
docs(readme): update installation instructions
refactor(parser): simplify token handling logic
test(api): add integration tests for rate limiting
```

### With Breaking Changes

```
feat(api): redesign authentication flow

BREAKING CHANGE: The authenticate() function now returns a Promise
instead of accepting a callback. Update all calls accordingly.
```

## Multi-line Commits

When more context is needed:

```
Add comprehensive API rate limiting

Implements exponential backoff with jitter to handle rate limits
gracefully across different API providers. Includes:
- Configurable retry attempts and backoff multiplier
- Request queue management
- Detailed error messages with retry timing

Fixes #123
```

**Body guidelines:**
- Wrap at 72 characters
- Explain what and why, not how
- Separate from subject with blank line
- Use bullet points for multiple items
- Reference issues: `Fixes #123`, `Closes #456`, `Refs #789`

## Repository-Specific Conventions

**Always check the repository first:**

1. Review recent commits:
   ```bash
   git log --oneline -20
   git log --format="%s" -10
   ```

2. Look for contribution guidelines:
   - `CONTRIBUTING.md`
   - `DEVELOPERS.md`
   - `.github/COMMIT_CONVENTION.md`

3. Check for commit linters:
   - `.commitlintrc`
   - `commitlint.config.js`
   - `.git/hooks/commit-msg`

## Git Commands for Commits

### Basic commit
```bash
git commit -m "Add feature X"
```

### Multi-line commit (using HEREDOC)
```bash
git commit -m "$(cat <<'EOF'
Add comprehensive feature X

This implements the following:
- Component A
- Component B
- Component C

Fixes #123
EOF
)"
```

The `<<'EOF'` syntax (with quotes) prevents variable expansion.

### Amending commits

**Amend without changing message:**
```bash
git commit --amend --no-edit
```

**Amend with new message:**
```bash
git commit --amend -m "New message"
```

**Amend with editor:**
```bash
git commit --amend
```

## What NOT to Commit

Never commit:
- Secrets, API keys, passwords, tokens
- Personal information (emails, phone numbers, addresses)
- Large binary files (unless intentional and necessary)
- Generated files (build artifacts, unless required)
- IDE-specific files (add to `.gitignore` instead)
- Debug logs and temporary files
- `node_modules/`, `vendor/`, or similar dependency directories

## Commit Message Examples by Scenario

### Adding a feature
```
Add user authentication with OAuth2

Implements OAuth2 flow for Google and GitHub providers.
Includes token refresh logic and session management.

Refs #456
```

### Fixing a bug
```
Fix race condition in concurrent writes

Prevents data loss when multiple threads write simultaneously
by adding proper locking mechanism.

Fixes #789
```

### Refactoring
```
Refactor database connection pool

Simplifies connection management and improves error handling.
No functional changes.
```

### Documentation
```
docs: update API endpoints documentation

Clarifies authentication requirements and adds examples
for all GET and POST endpoints.
```

### Dependencies
```
chore: update dependencies to latest versions

Updates React to 18.2, TypeScript to 5.0, and other
dependencies with security patches.
```

## Pre-commit Hooks

If the repository has pre-commit hooks that modify files:

1. The commit may initially fail or succeed with modifications
2. Check `git status` after committing
3. If files were modified by hooks, amend the commit:
   ```bash
   git add .
   git commit --amend --no-edit
   ```

## Signing Commits

Some repositories require signed commits:

```bash
git commit -S -m "Commit message"
```

Check repository requirements for GPG key setup.
