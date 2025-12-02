# Secret Detection Patterns

This reference provides regex patterns and search strategies for detecting secrets in repositories.

## Cloud Provider Credentials

### AWS

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Access Key ID | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| Secret Access Key | `[A-Za-z0-9/+=]{40}` (near AWS context) | 40-char base64 string |
| MWS Auth Token | `amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` | |

### Google Cloud Platform

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `AIza[0-9A-Za-z\\-_]{35}` | `AIzaSyDaGmWKa4JsXZ-example` |
| OAuth Client ID | `[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com` | |
| Service Account | `"type":\s*"service_account"` (in JSON) | |

### Azure

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Storage Account Key | `[A-Za-z0-9+/]{86}==` | 88-char base64 string |
| Connection String | `DefaultEndpointsProtocol=https;AccountName=` | |
| SAS Token | `sv=\d{4}-\d{2}-\d{2}&s[a-z]=` | |

## Version Control Platforms

### GitHub

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Personal Access Token (new) | `ghp_[A-Za-z0-9]{36}` | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Personal Access Token (old) | `[0-9a-f]{40}` (in GitHub context) | 40-char hex string |
| OAuth Access Token | `gho_[A-Za-z0-9]{36}` | |
| App Token | `ghu_[A-Za-z0-9]{36}` | |
| App Refresh Token | `ghr_[A-Za-z0-9]{76}` | |
| Fine-grained PAT | `github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}` | |

### GitLab

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Personal Access Token | `glpat-[A-Za-z0-9\-]{20}` | |
| Pipeline Token | `glpt-[A-Za-z0-9\-]{20}` | |
| Runner Token | `GR1348941[A-Za-z0-9\-]{20}` | |

### Bitbucket

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| App Password | `ATBB[A-Za-z0-9]{32}` | |

## AI/ML Services

### OpenAI

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `sk-[A-Za-z0-9]{48}` | `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Project Key | `sk-proj-[A-Za-z0-9]{48}` | |

### Anthropic

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `sk-ant-[A-Za-z0-9\-]{95}` | |

### Hugging Face

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Token | `hf_[A-Za-z0-9]{34}` | `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### Cohere

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `[A-Za-z0-9]{40}` (near Cohere context) | |

## Authentication Tokens

### JWT

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| JWT Token | `eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*` | Base64 encoded JSON |

### OAuth/Bearer

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Bearer Token | `[Bb]earer\s+[A-Za-z0-9\-_\.]+` | |
| OAuth Token | `ya29\.[0-9A-Za-z\-_]+` | Google OAuth |

## Database Credentials

### Connection Strings

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| PostgreSQL | `postgres(ql)?://[^:]+:[^@]+@` | `postgres://user:pass@host` |
| MySQL | `mysql://[^:]+:[^@]+@` | `mysql://user:pass@host` |
| MongoDB | `mongodb(\+srv)?://[^:]+:[^@]+@` | `mongodb://user:pass@host` |
| Redis | `redis://:[^@]+@` | `redis://:password@host` |
| JDBC | `jdbc:[a-z]+://[^:]+:[^@]+@` | |

### Password Fields

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Password assignment | `[Pp]assword\s*[=:]\s*['"][^'"]+['"]` | `password = "secret"` |
| DB Password | `DB_PASSWORD\s*=\s*['"]?[^'"\\s]+` | |

## Private Keys

### SSH/RSA Keys

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| RSA Private Key | `-----BEGIN RSA PRIVATE KEY-----` | |
| OpenSSH Private Key | `-----BEGIN OPENSSH PRIVATE KEY-----` | |
| DSA Private Key | `-----BEGIN DSA PRIVATE KEY-----` | |
| EC Private Key | `-----BEGIN EC PRIVATE KEY-----` | |
| PGP Private Key | `-----BEGIN PGP PRIVATE KEY BLOCK-----` | |
| Generic Private Key | `-----BEGIN PRIVATE KEY-----` | |
| Encrypted Private Key | `-----BEGIN ENCRYPTED PRIVATE KEY-----` | |

## Communication Services

### Slack

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Bot Token | `xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}` | |
| User Token | `xoxp-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}` | |
| Webhook URL | `https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+` | |

### Discord

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Bot Token | `[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}` | |
| Webhook URL | `https://discord(app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+` | |

### Twilio

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Account SID | `AC[a-z0-9]{32}` | |
| Auth Token | `[a-f0-9]{32}` (near Twilio context) | |

## Payment Services

### Stripe

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Secret Key (Live) | `sk_live_[A-Za-z0-9]{24,}` | |
| Secret Key (Test) | `sk_test_[A-Za-z0-9]{24,}` | |
| Publishable Key | `pk_(live\|test)_[A-Za-z0-9]{24,}` | |

### PayPal

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Client ID | `A[A-Za-z0-9_-]{79}` | |

### Square

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Access Token | `sq0atp-[A-Za-z0-9_-]{22}` | |
| OAuth Secret | `sq0csp-[A-Za-z0-9_-]{43}` | |

## Other Services

### SendGrid

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}` | |

### Mailchimp

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `[a-f0-9]{32}-us[0-9]{1,2}` | |

### NPM

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Token | `npm_[A-Za-z0-9]{36}` | |

### PyPI

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| Token | `pypi-[A-Za-z0-9_-]{50,}` | |

### Heroku

| Secret Type | Pattern | Example |
|-------------|---------|---------|
| API Key | `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}` (in Heroku context) | |

## Generic Patterns

### High-Entropy Strings

Strings matching these patterns warrant investigation:

| Description | Pattern |
|-------------|---------|
| API Key Generic | `[Aa]pi[_-]?[Kk]ey\s*[=:]\s*['"]?[A-Za-z0-9_\-]{20,}` |
| Secret Generic | `[Ss]ecret\s*[=:]\s*['"]?[A-Za-z0-9_\-]{20,}` |
| Token Generic | `[Tt]oken\s*[=:]\s*['"]?[A-Za-z0-9_\-]{20,}` |
| Credential | `[Cc]redential\s*[=:]\s*['"]?[A-Za-z0-9_\-]{20,}` |

### Environment Variable Values

| Description | Pattern |
|-------------|---------|
| Inline assignment | `[A-Z_]+_KEY=[^\\s]+` |
| Export statement | `export\s+[A-Z_]+(KEY\|SECRET\|TOKEN\|PASSWORD)=[^\\s]+` |

## Search Commands

### Comprehensive grep search

```bash
# Search for common secret indicators
grep -rniE '(api[_-]?key|secret|token|password|credential|auth)\s*[=:]\s*['\''"][^'\''"]{8,}['\''"]' .

# Search for AWS keys
grep -rniE 'AKIA[0-9A-Z]{16}' .

# Search for private keys
grep -rl '-----BEGIN.*PRIVATE KEY-----' .

# Search for connection strings
grep -rniE '(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@' .
```

### Using git to search history

```bash
# Search all commits for pattern
git log -p --all -S 'AKIA' --source

# Search for pattern in specific branch
git log -p -S 'secret_value' branch_name
```

## Files to Prioritize

Always check these files first:

1. `.env`, `.env.*`, `.env.local`, `.env.production`
2. `config/*.json`, `config/*.yaml`, `config/*.yml`
3. `secrets.*`, `credentials.*`
4. `*.pem`, `*.key`, `*.p12`, `*.pfx`
5. `docker-compose*.yml`, `Dockerfile*`
6. `.github/workflows/*.yml`, `.gitlab-ci.yml`
7. `terraform.tfvars`, `*.tfstate`
8. `application.properties`, `application.yml` (Java/Spring)
9. `settings.py`, `local_settings.py` (Django)
10. `wp-config.php` (WordPress)
