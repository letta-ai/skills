---
name: provider-configuration
description: Configure LLM providers for Letta servers, covering both self-hosted environment variable setup and programmatic BYOK provider management via REST API. Use when setting up new providers, validating credentials, generating Docker env files, or configuring custom endpoints for OpenAI, Anthropic, Azure, Ollama, and 20+ other providers.
---

# Provider Configuration

This skill helps you configure LLM providers for Letta, supporting both:
- **Self-hosted setup** - Environment variables for Docker/local deployments
- **BYOK via API** - Programmatic provider management for Cloud and self-hosted

## Quick Start

### Add Provider via API

```bash
python scripts/setup_provider.py --type openai --api-key sk-...
```

### Generate .env File for Docker

```bash
python scripts/generate_env.py --providers openai,anthropic,ollama
```

### Validate Provider Credentials

```bash
python scripts/validate_provider.py --provider-id provider-xxx
```

## Common Workflows

### Workflow 1: Add OpenAI BYOK Provider

```python
# Using the setup script
python scripts/setup_provider.py \
  --type openai \
  --name "My OpenAI" \
  --api-key sk-your-key-here

# Or via REST API directly
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My OpenAI",
    "provider_type": "openai",
    "api_key": "sk-your-key-here"
  }'
```

### Workflow 2: Configure Self-Hosted Server

```bash
# Generate environment file
python scripts/generate_env.py --providers openai,anthropic,ollama --output .env

# Use with Docker
docker run -p 8283:8283 --env-file .env letta/letta:latest
```

### Workflow 3: Validate and Refresh Provider

```bash
# Check credentials
python scripts/validate_provider.py --provider-id provider-abc123

# Refresh available models
curl -X PATCH http://localhost:8283/v1/providers/provider-abc123/refresh
```

## Reference Documentation

### Common Providers
For detailed OpenAI, Anthropic, Azure OpenAI, and Google AI configuration:
**Read [references/common_providers.md](references/common_providers.md)**

### Self-Hosted Providers
For Ollama, vLLM, LM Studio, and other local providers:
**Read [references/self_hosted_providers.md](references/self_hosted_providers.md)**

### All Provider Types
For comprehensive reference covering all 20+ supported providers:
**Read [references/all_providers.md](references/all_providers.md)**

### Environment Variables
For Docker setup and multi-provider configuration:
**Read [references/environment_variables.md](references/environment_variables.md)**

## Scripts

### setup_provider.py
Add providers programmatically via REST API.

**Required flags:**
- `--type` - Provider type (openai, anthropic, azure, etc.)
- `--api-key` - API key for the provider

**Optional flags:**
- `--name` - Display name (defaults to provider type)
- `--base-url` - Custom endpoint URL
- `--api-version` - API version (for Azure)
- `--region` - Region (for Bedrock)
- `--access-key` - Access key (for AWS)
- `--server` - Letta server URL (default: http://localhost:8283)

### validate_provider.py
Check if provider credentials are valid and list available models.

**Required flags:**
- `--provider-id` - Provider ID to validate

**Optional flags:**
- `--server` - Letta server URL (default: http://localhost:8283)

### generate_env.py
Generate `.env` file for Docker deployments.

**Required flags:**
- `--providers` - Comma-separated list of providers (openai,anthropic,ollama)

**Optional flags:**
- `--output` - Output file path (default: .env)
- `--ollama-url` - Ollama endpoint URL (default: http://host.docker.internal:11434)

## Provider Types

Supported provider types:
- `openai` - OpenAI (GPT models)
- `anthropic` - Anthropic (Claude models)
- `azure` - Azure OpenAI
- `google_ai` - Google AI (Gemini)
- `google_vertex` - Google Vertex AI
- `ollama` - Ollama (local models)
- `groq` - Groq
- `deepseek` - DeepSeek
- `xai` - xAI (Grok)
- `zai` - Z.ai
- `together` - Together AI
- `mistral` - Mistral AI
- `cerebras` - Cerebras
- `bedrock` - AWS Bedrock
- `vllm` - vLLM
- `sglang` - SGLang
- `hugging_face` - Hugging Face
- `lmstudio_openai` - LM Studio (OpenAI compatible)
- `minimax` - MiniMax
- `chatgpt_oauth` - ChatGPT OAuth

For detailed configuration of each provider, see the reference files.

## Notes

- All API-created providers are automatically BYOK (bring your own key)
- Provider IDs are prefixed with `provider-`
- After creating a provider, models are auto-discovered
- Use `PATCH /v1/providers/{provider_id}/refresh` to rescan models
- Environment variables are only for self-hosted deployments
- Letta Cloud uses BYOK providers exclusively (no env vars)
