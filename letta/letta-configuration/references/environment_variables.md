# Environment Variables for Self-Hosted Deployments

Complete guide to configuring providers via environment variables for Docker and self-hosted Letta servers.

## Overview

Environment variables are the recommended way to configure providers for self-hosted Letta deployments. This approach:
- Keeps credentials out of code
- Works seamlessly with Docker
- Supports multiple providers simultaneously
- Simplifies deployment automation

**Note:** Environment variables are ONLY for self-hosted deployments. Letta Cloud uses BYOK providers exclusively.

## Core Environment Variables

### Database Configuration

**PostgreSQL (Recommended):**
```bash
LETTA_PG_URI=postgresql://user:password@localhost/letta
```

**SQLite (Development only):**
```bash
LETTA_PG_URI=sqlite:///~/.letta/letta.db
```

### Security

**Production:**
```bash
SECURE=true
LETTA_SERVER_PASSWORD=your-secure-password
```

**Development (no auth):**
```bash
# Leave SECURE unset or set to false
```

### Server Configuration

```bash
# Port (default: 8283)
LETTA_SERVER_PORT=8283

# CORS origins
LETTA_SERVER_CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Log level
LETTA_LOG_LEVEL=INFO
```

## Provider Environment Variables

### OpenAI

```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

Optional custom endpoint:
```bash
OPENAI_BASE_URL=https://custom-endpoint.com/v1
```

### Anthropic

```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### Azure OpenAI

```bash
AZURE_API_KEY=your-azure-key
AZURE_BASE_URL=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-09-01-preview
```

### Google AI

```bash
GOOGLE_AI_API_KEY=your-google-ai-key
```

### Google Vertex AI

```bash
GOOGLE_VERTEX_API_KEY='{"type": "service_account", "project_id": "...", ...}'
GOOGLE_VERTEX_REGION=us-central1
```

### Groq

```bash
GROQ_API_KEY=gsk-your-groq-key
```

### DeepSeek

```bash
DEEPSEEK_API_KEY=your-deepseek-key
```

### Together AI

```bash
TOGETHER_API_KEY=your-together-key
```

### Mistral AI

```bash
MISTRAL_API_KEY=your-mistral-key
```

### xAI (Grok)

```bash
XAI_API_KEY=your-xai-key
```

### Z.ai

```bash
ZAI_API_KEY=your-zai-key
```

### Ollama (Self-Hosted)

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

**Docker Networking:**
- macOS/Windows: `http://host.docker.internal:11434`
- Linux: `http://172.17.0.1:11434` or use `--network host`

**Important:** Ollama must be configured with:
```bash
export OLLAMA_HOST=0.0.0.0
ollama serve
```

### AWS Bedrock

```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

## Complete .env File Example

```bash
# Letta Environment Configuration
# Generated: 2026-01-28

# ============================================
# Database Configuration
# ============================================
LETTA_PG_URI=postgresql://letta:letta@localhost/letta

# ============================================
# Security (Production)
# ============================================
# SECURE=true
# LETTA_SERVER_PASSWORD=your-secure-password

# ============================================
# Server Configuration
# ============================================
LETTA_SERVER_PORT=8283
LETTA_LOG_LEVEL=INFO

# ============================================
# Provider API Keys
# ============================================

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Azure OpenAI
AZURE_API_KEY=your-azure-key
AZURE_BASE_URL=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-09-01-preview

# Google AI
GOOGLE_AI_API_KEY=your-google-ai-key

# Groq
GROQ_API_KEY=your-groq-key

# ============================================
# Self-Hosted Providers
# ============================================

# Ollama (local models)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# ============================================
# Optional: Advanced Configuration
# ============================================

# Redis (for caching and background streaming)
# REDIS_URL=redis://localhost:6379

# E2B (for sandboxed tool execution)
# E2B_API_KEY=your-e2b-key

# Exa (for web search tool)
# EXA_API_KEY=your-exa-key
```

## Docker Usage

### Basic Docker Run

```bash
docker run -p 8283:8283 --env-file .env letta/letta:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  letta:
    image: letta/letta:latest
    ports:
      - "8283:8283"
    env_file:
      - .env
    volumes:
      - letta-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  letta-data:
```

### Docker with Ollama

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

  letta:
    image: letta/letta:latest
    ports:
      - "8283:8283"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - ollama

volumes:
  ollama-data:
```

## Multi-Provider Configuration

You can configure multiple providers simultaneously:

```bash
# Multiple cloud providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...
GROQ_API_KEY=...

# Plus self-hosted
OLLAMA_BASE_URL=http://localhost:11434
```

Letta will auto-discover all configured providers and their models.

## Environment Variable Loading

Letta loads environment variables in this order:

1. System environment variables
2. `.env` file in current directory
3. `.env` file in Letta config directory (`~/.letta/.env`)

**Priority:** System env vars > `.env` in current dir > `.env` in config dir

## Security Best Practices

1. **Never commit .env files** - Add to `.gitignore`
2. **Use production passwords** - Generate strong passwords for `LETTA_SERVER_PASSWORD`
3. **Restrict file permissions** - `chmod 600 .env`
4. **Rotate keys regularly** - Change API keys periodically
5. **Use secrets management** - Consider Vault, AWS Secrets Manager, etc. for production
6. **Enable SECURE mode** - Always set `SECURE=true` in production
7. **Use HTTPS** - Put reverse proxy (nginx/Caddy) in front of Letta

## Troubleshooting

### Provider Not Appearing

```bash
# Check if environment variable is set
echo $OPENAI_API_KEY

# Check Letta logs for provider loading
docker logs letta-container
```

### Connection Issues with Ollama

```bash
# From inside Docker container, test connectivity
docker exec -it letta-container curl http://host.docker.internal:11434/api/tags

# Check Ollama is listening on all interfaces
curl http://localhost:11434/api/tags
```

### Models Not Auto-Discovered

```bash
# Manually trigger provider refresh via API
curl -X PATCH http://localhost:8283/v1/providers/{provider_id}/refresh
```

### Permission Denied on .env File

```bash
# Fix permissions
chmod 600 .env
```

## Migration from API-Created Providers

If you have providers created via API and want to move to environment variables:

1. Export existing provider credentials (if possible)
2. Add to `.env` file
3. Restart Letta server
4. Delete API-created providers if redundant

Note: Environment variable providers and API-created providers coexist. Use whichever approach fits your workflow.

## Advanced: Custom Provider Configuration

For custom OpenAI-compatible endpoints, use `base_url`:

```bash
# Example: LiteLLM Proxy
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=http://localhost:4000/v1

# Example: Text Generation WebUI
OPENAI_API_KEY=placeholder
OPENAI_BASE_URL=http://localhost:5000/v1
```

This allows using any OpenAI-compatible API without creating a separate provider type.
