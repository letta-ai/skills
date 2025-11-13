# Pull Request Templates

## Discovering Repository PR Format

**Always check the repository first:**

1. Look for PR templates:
   ```bash
   cat .github/PULL_REQUEST_TEMPLATE.md
   cat .github/pull_request_template.md
   ls .github/PULL_REQUEST_TEMPLATE/
   ```

2. Review recent PRs:
   ```bash
   gh pr list --limit 5
   gh pr view <PR-number>
   ```

3. Check contribution guidelines:
   - `CONTRIBUTING.md` often includes PR requirements
   - Look for sections on "Submitting Changes" or "Pull Requests"

## Common PR Description Formats

### Format 1: Summary + Changes + Testing

```markdown
## Summary

Brief overview of what this PR does and why.

## Changes

- Change 1
- Change 2
- Change 3

## Testing

How these changes were tested:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
```

### Format 2: What + Why + How

```markdown
## What

What changes are being made.

## Why

Why these changes are necessary (problem being solved, feature being added).

## How

How the changes were implemented (technical approach).

## Testing

- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manually verified functionality
```

### Format 3: Description + Checklist

```markdown
## Description

Detailed description of the changes, including:
- Problem being solved
- Approach taken
- Any tradeoffs or considerations

## Checklist

- [ ] Tests added
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No breaking changes
- [ ] All CI checks pass
```

### Format 4: User Story Format

```markdown
## User Story

As a [user type], I want [goal] so that [benefit].

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Notes

Technical details about the implementation...

## Screenshots / Demo

[If UI changes, include screenshots or demo links]
```

## Issue References

**Linking issues in PR descriptions:**

- `Fixes #123` - Closes issue when PR is merged
- `Closes #456` - Same as Fixes
- `Resolves #789` - Same as Fixes
- `Refs #111` - References without closing
- `Related to #222` - Mentions relationship

**Multiple issues:**
```markdown
Fixes #123, #456
Closes #789

This PR addresses multiple related issues...
```

## Breaking Changes

If the PR introduces breaking changes, highlight them prominently:

```markdown
## ⚠️ BREAKING CHANGES

- The `authenticate()` function now returns a Promise instead of using callbacks
- Configuration format has changed (see migration guide below)

## Migration Guide

### Before
```js
auth.authenticate(user, (err, result) => {
  // handle result
});
```

### After
```js
const result = await auth.authenticate(user);
```
```

## Screenshots and Media

For UI changes:

```markdown
## Screenshots

### Before
![before](url-to-image)

### After
![after](url-to-image)
```

For demos:
```markdown
## Demo

[Link to deployed preview]
[Link to demo video]
```

## PR Title Guidelines

**Good PR titles:**
- `Add user authentication with OAuth2`
- `Fix memory leak in connection pool`
- `Update documentation for API endpoints`
- `Refactor database query builder`

**Following Conventional Commits:**
- `feat: add user authentication with OAuth2`
- `fix: resolve memory leak in connection pool`
- `docs: update API endpoint documentation`
- `refactor: simplify database query builder`

**With scope:**
- `feat(auth): add OAuth2 support`
- `fix(db): resolve connection pool leak`
- `docs(api): update endpoint documentation`

## Creating PRs with GitHub CLI

### Basic PR creation
```bash
gh pr create --title "Title" --body "Description"
```

### With editor for body
```bash
gh pr create --title "Title" --body-file body.md
```

### Interactive mode
```bash
gh pr create
```

### With template (using HEREDOC)
```bash
gh pr create --title "Add feature X" --body "$(cat <<'EOF'
## Summary
This PR adds feature X to improve Y.

## Changes
- Implemented component A
- Updated component B
- Added tests for A and B

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manually tested scenarios X, Y, Z

Fixes #123
EOF
)"
```

### To specific base branch
```bash
gh pr create --base develop --title "Title" --body "Description"
```

## Draft PRs

For work-in-progress:

```bash
gh pr create --draft --title "WIP: Feature X"
```

Mark ready when complete:
```bash
gh pr ready <PR-number>
```

## PR Best Practices

### Description Quality
- Be clear and concise
- Explain the "why" not just the "what"
- Include context for reviewers
- Reference relevant issues or discussions
- Add screenshots for UI changes

### Checklist Items
- Make reviewers' job easier with clear testing instructions
- Include relevant verification steps
- Note any areas needing special attention

### Size
- Keep PRs focused and reasonably sized
- Large PRs are harder to review
- Consider breaking into multiple PRs if possible

### Communication
- Respond to review comments promptly
- Explain your reasoning when disagreeing
- Be open to feedback
- Update the PR based on review feedback

## Repository-Specific Requirements

Some repositories may require:

- **Code coverage:** Minimum test coverage threshold
- **Documentation:** Updates to docs for any API changes
- **Changelog:** Entry in CHANGELOG.md
- **Screenshots:** For all UI changes
- **Performance:** Benchmark results for performance changes
- **Security:** Security review for authentication/authorization changes
- **Breaking changes:** Migration guide and version bump
- **Dependencies:** Justification for new dependencies

Always check `CONTRIBUTING.md` for specific requirements.

## Example Complete PRs

### Example 1: Bug Fix

```markdown
## Summary

Fixes race condition in concurrent database writes that caused data loss in multi-threaded scenarios.

## Problem

When multiple threads attempted to write to the database simultaneously, the connection pool's lock mechanism failed, resulting in data loss. This occurred approximately 5-10% of the time under high load.

## Solution

Implemented proper mutex locking in the connection pool manager and added connection state validation before executing queries.

## Changes

- Add mutex lock to `ConnectionPool.acquire()`
- Add connection state validation in `ConnectionPool.execute()`
- Update tests to cover concurrent write scenarios

## Testing

- [ ] Added 10 new concurrency tests
- [ ] All existing tests pass
- [ ] Stress tested with 100 concurrent writes - 0% data loss
- [ ] Verified fix in staging environment under production load

Fixes #456
```

### Example 2: New Feature

```markdown
## Summary

Adds OAuth2 authentication support for Google and GitHub providers.

## What's New

This PR implements OAuth2 authentication flow, allowing users to sign in with their Google or GitHub accounts instead of creating separate credentials.

## Changes

- New `OAuth2Provider` interface and implementations for Google/GitHub
- Authentication middleware for handling OAuth callbacks
- Session management with token refresh logic
- User account linking for existing email addresses
- UI updates for OAuth sign-in buttons

## Configuration

New environment variables required:
```
OAUTH_GOOGLE_CLIENT_ID=xxx
OAUTH_GOOGLE_CLIENT_SECRET=xxx
OAUTH_GITHUB_CLIENT_ID=xxx
OAUTH_GITHUB_CLIENT_SECRET=xxx
```

## Testing

- [ ] Unit tests for OAuth providers (95% coverage)
- [ ] Integration tests for full auth flow
- [ ] Manually tested with Google account
- [ ] Manually tested with GitHub account
- [ ] Verified account linking works correctly
- [ ] Tested token refresh after expiration

## Screenshots

[Include screenshots of new OAuth sign-in UI]

Closes #789
```

### Example 3: Refactoring

```markdown
## Summary

Refactors database query builder to improve readability and maintainability. No functional changes.

## Motivation

The existing query builder had grown complex and difficult to extend. This refactoring simplifies the code structure without changing any behavior.

## Changes

- Extract query building logic into separate strategy classes
- Simplify the main QueryBuilder interface
- Add comprehensive JSDoc documentation
- Improve error messages for invalid queries

## Testing

- [ ] All existing tests pass without modification
- [ ] Added tests for edge cases
- [ ] Verified performance is equivalent (benchmarked)
- [ ] No breaking changes to public API

## Before/After

### Before
```js
const query = builder.select('*').from('users').where('id', '=', 1).and('active', '=', true).build();
```

### After
```js
const query = builder.select('*').from('users').where('id', '=', 1).and('active', '=', true).build();
```

Same API, cleaner internal implementation.
```
