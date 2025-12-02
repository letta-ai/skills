---
name: sanitize-git-repo
description: Guidance for sanitizing git repositories by identifying and removing sensitive credentials, API keys, tokens, and other secrets. This skill should be used when tasks involve cleaning repositories of secrets, preparing code for public release, auditing for credential exposure, or removing sensitive data from version control history.
---

# Repository Sanitization Skill

This skill provides systematic approaches for identifying and removing sensitive information from git repositories, including credentials, API keys, tokens, and other secrets.

## When to Use This Skill

- Preparing a private repository for public release
- Auditing repositories for accidentally committed secrets
- Cleaning up after a credential leak
- Removing sensitive data from git history
- Compliance and security reviews

## Critical Understanding

Repository sanitization involves two distinct scopes:

1. **Working Directory Sanitization**: Replacing secrets in current file contents
2. **Git History Sanitization**: Removing secrets from all historical commits

Simply editing files in the working directory does NOT remove secrets from git history. The `.git/objects` directory retains all historical versions of files.

## Approach

### Phase 1: Comprehensive Secret Detection

Before making any changes, perform exhaustive detection using multiple strategies:

#### 1.1 Pattern-Based Detection

Search for common secret patterns. Refer to `references/secret_patterns.md` for comprehensive regex patterns covering:

- API keys (AWS, GCP, Azure, GitHub, GitLab, Hugging Face, OpenAI, etc.)
- Authentication tokens (JWT, OAuth, Bearer tokens)
- Database credentials (connection strings, passwords)
- Private keys (RSA, SSH, PGP)
- Environment variable assignments containing secrets
- Base64-encoded secrets
- Webhook URLs with embedded tokens

#### 1.2 File-Based Detection

Check files commonly containing secrets:

- `.env`, `.env.*` files
- Configuration files: `*.yaml`, `*.yml`, `*.json`, `*.toml`, `*.ini`, `*.cfg`
- Docker files: `Dockerfile`, `docker-compose.yml`
- CI/CD configs: `.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`
- Cloud configs: `terraform.tfvars`, `*.tfstate`
- Credential files: `credentials`, `secrets`, `*.pem`, `*.key`

#### 1.3 Entropy-Based Detection

High-entropy strings often indicate secrets. Look for:

- Strings with mixed case, numbers, and special characters
- Strings longer than 20 characters without dictionary words
- Base64-encoded blobs in unexpected locations

### Phase 2: Systematic Verification

After initial detection:

1. **Document all findings** before making changes
2. **Categorize secrets** by type (API key, password, token, etc.)
3. **Identify false positives** (environment variable references vs actual values)
4. **Check all files in directories** where secrets are found (not just the first match)
5. **Examine binary files** that might contain embedded secrets

### Phase 3: Sanitization Strategy

#### 3.1 Placeholder Format

Use consistent placeholder formats:

- `<your-aws-access-key>` for AWS keys
- `<your-api-key>` for generic API keys
- `<your-database-password>` for passwords
- `${ENV_VAR_NAME}` for values that should come from environment

#### 3.2 Working Directory Sanitization

1. Create a backup branch before modifications
2. Replace secrets systematically, one type at a time
3. Verify each replacement maintains file validity (especially JSON/YAML)
4. Run syntax validation on modified configuration files

#### 3.3 Git History Sanitization

For complete sanitization, the git history must also be cleaned:

**Option A: BFG Repo-Cleaner (Recommended)**
```bash
# Remove specific strings from history
bfg --replace-text secrets.txt repo.git
```

**Option B: git filter-repo**
```bash
# Remove file containing secrets from all history
git filter-repo --path sensitive-file.txt --invert-paths
```

**Option C: git filter-branch (Legacy)**
```bash
# Use only if other tools unavailable
git filter-branch --tree-filter 'command' HEAD
```

After history rewriting:
- Force push to remote (coordinate with team)
- All collaborators must re-clone
- Invalidate/rotate all exposed credentials

### Phase 4: Verification

#### 4.1 Post-Sanitization Checks

1. Re-run all detection patterns to confirm no secrets remain
2. Verify file syntax (JSON, YAML, etc.) is still valid
3. Check that placeholder format is consistent throughout
4. Confirm application can start (may fail due to missing secrets - expected)

#### 4.2 Git History Verification

```bash
# Search git history for secret patterns
git log -p --all -S 'secret_pattern' --source
```

## Common Pitfalls

### Incomplete Detection

- **Pitfall**: Searching for only specific patterns (e.g., `ghp_` for GitHub tokens)
- **Solution**: Use comprehensive pattern list; account for older token formats and variations

### Ignoring File Types

- **Pitfall**: Only checking text files, missing secrets in JSON, notebooks, or binary files
- **Solution**: Check all file types; use specialized tools for binary inspection

### Forgetting Git History

- **Pitfall**: Only sanitizing working directory, leaving secrets in git history
- **Solution**: Always warn about git history; use BFG or git-filter-repo for complete removal

### Inconsistent Placeholders

- **Pitfall**: Using different placeholder formats (`<token>`, `YOUR_TOKEN`, `xxx`)
- **Solution**: Define placeholder convention upfront; use search-replace consistently

### Missing Related Secrets

- **Pitfall**: Finding one secret in a file but not checking for related secrets
- **Solution**: When a secret is found, thoroughly examine the entire file and directory

### Partial Directory Scanning

- **Pitfall**: Checking only the first matching file in a directory
- **Solution**: Systematically check all files matching patterns in directories where secrets are found

### Encoded Secrets

- **Pitfall**: Missing Base64-encoded or otherwise obfuscated secrets
- **Solution**: Decode suspicious Base64 strings; check for common encoding patterns

## Verification Checklist

Before declaring sanitization complete:

- [ ] All secret patterns from `references/secret_patterns.md` searched
- [ ] All common secret-containing file types checked
- [ ] All files in directories with findings examined
- [ ] Placeholder format is consistent
- [ ] Configuration file syntax validated
- [ ] Git history addressed (cleaned or documented as still containing secrets)
- [ ] Comprehensive re-scan confirms no remaining secrets
- [ ] Credential rotation recommended to user for any exposed secrets
