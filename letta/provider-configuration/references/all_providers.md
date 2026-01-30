# All Supported Providers

Comprehensive reference for all 20+ supported provider types.

## Provider Reference Table

| Provider Type | Required Fields | Optional Fields | Auth Type | Notes |
|--------------|----------------|----------------|-----------|-------|
| `openai` | `api_key` | `base_url` | API Key | OpenAI GPT models |
| `anthropic` | `api_key` | - | API Key | Claude models |
| `azure` | `api_key`, `base_url` | `api_version` | API Key | Azure OpenAI |
| `google_ai` | `api_key` | - | API Key | Gemini models |
| `google_vertex` | `api_key`, `region` | - | Service Account | Vertex AI |
| `groq` | `api_key` | - | API Key | Groq inference |
| `deepseek` | `api_key` | - | API Key | DeepSeek models |
| `xai` | `api_key` | - | API Key | xAI Grok models |
| `zai` | `api_key` | - | API Key | Z.ai models |
| `together` | `api_key` | - | API Key | Together AI |
| `mistral` | `api_key` | - | API Key | Mistral AI |
| `cerebras` | `api_key` | - | API Key | Cerebras inference |
| `bedrock` | `api_key`, `access_key`, `region` | - | AWS | AWS Bedrock |
| `ollama` | `api_key`, `base_url` | - | None | Local Ollama |
| `vllm` | `api_key`, `base_url` | - | None | vLLM server |
| `sglang` | `api_key`, `base_url` | - | None | SGLang server |
| `lmstudio_openai` | `api_key`, `base_url` | - | None | LM Studio |
| `hugging_face` | `api_key` | `base_url` | API Key | HuggingFace |
| `minimax` | `api_key` | - | API Key | MiniMax |
| `chatgpt_oauth` | `api_key` | - | OAuth | ChatGPT OAuth |

## Quick Reference by Category

### Cloud Providers (API Key Auth)
**OpenAI Family:**
- `openai` - OpenAI GPT models
- `azure` - Azure OpenAI (requires base_url + api_version)

**Anthropic:**
- `anthropic` - Claude models

**Google:**
- `google_ai` - Gemini via API key
- `google_vertex` - Gemini via service account (requires region)

**Fast Inference:**
- `groq` - Ultra-fast inference
- `cerebras` - Fast inference
- `together` - Together AI

**Chinese Providers:**
- `deepseek` - DeepSeek models
- `minimax` - MiniMax models

**Other:**
- `xai` - xAI Grok models
- `zai` - Z.ai models
- `mistral` - Mistral AI
- `hugging_face` - HuggingFace Inference API

### AWS Bedrock
- `bedrock` - Requires `api_key` (secret key), `access_key`, and `region`

### Self-Hosted / Local
- `ollama` - Local Ollama server
- `vllm` - vLLM OpenAI-compatible server
- `sglang` - SGLang server
- `lmstudio_openai` - LM Studio local server

### OAuth
- `chatgpt_oauth` - ChatGPT OAuth integration

## Detailed Configuration

### openai
```json
{
  "name": "OpenAI",
  "provider_type": "openai",
  "api_key": "sk-..."
}
```

Optional `base_url` for OpenAI-compatible endpoints.

### anthropic
```json
{
  "name": "Anthropic",
  "provider_type": "anthropic",
  "api_key": "sk-ant-..."
}
```

### azure
```json
{
  "name": "Azure OpenAI",
  "provider_type": "azure",
  "api_key": "xxx",
  "base_url": "https://resource.openai.azure.com",
  "api_version": "2024-09-01-preview"
}
```

Model field must be deployment name.

### google_ai
```json
{
  "name": "Google AI",
  "provider_type": "google_ai",
  "api_key": "xxx"
}
```

### google_vertex
```json
{
  "name": "Vertex AI",
  "provider_type": "google_vertex",
  "api_key": "{\"type\": \"service_account\", ...}",
  "region": "us-central1"
}
```

API key is service account JSON.

### groq
```json
{
  "name": "Groq",
  "provider_type": "groq",
  "api_key": "gsk_..."
}
```

### deepseek
```json
{
  "name": "DeepSeek",
  "provider_type": "deepseek",
  "api_key": "xxx"
}
```

### xai
```json
{
  "name": "xAI",
  "provider_type": "xai",
  "api_key": "xxx"
}
```

### zai
```json
{
  "name": "Z.ai",
  "provider_type": "zai",
  "api_key": "xxx"
}
```

### together
```json
{
  "name": "Together AI",
  "provider_type": "together",
  "api_key": "xxx"
}
```

### mistral
```json
{
  "name": "Mistral",
  "provider_type": "mistral",
  "api_key": "xxx"
}
```

### cerebras
```json
{
  "name": "Cerebras",
  "provider_type": "cerebras",
  "api_key": "xxx"
}
```

### bedrock
```json
{
  "name": "AWS Bedrock",
  "provider_type": "bedrock",
  "api_key": "AWS_SECRET_KEY",
  "access_key": "AWS_ACCESS_KEY",
  "region": "us-east-1"
}
```

### ollama
```json
{
  "name": "Ollama",
  "provider_type": "ollama",
  "api_key": "ollama",
  "base_url": "http://localhost:11434"
}
```

See self_hosted_providers.md for detailed setup.

### vllm
```json
{
  "name": "vLLM",
  "provider_type": "vllm",
  "api_key": "vllm",
  "base_url": "http://localhost:8000"
}
```

### sglang
```json
{
  "name": "SGLang",
  "provider_type": "sglang",
  "api_key": "sglang",
  "base_url": "http://localhost:30000"
}
```

### lmstudio_openai
```json
{
  "name": "LM Studio",
  "provider_type": "lmstudio_openai",
  "api_key": "lmstudio",
  "base_url": "http://localhost:1234/v1"
}
```

### hugging_face
```json
{
  "name": "HuggingFace",
  "provider_type": "hugging_face",
  "api_key": "hf_..."
}
```

Optional `base_url` for inference endpoints.

### minimax
```json
{
  "name": "MiniMax",
  "provider_type": "minimax",
  "api_key": "xxx"
}
```

### chatgpt_oauth
```json
{
  "name": "ChatGPT OAuth",
  "provider_type": "chatgpt_oauth",
  "api_key": "oauth_token"
}
```

## Provider Categories

Letta classifies providers into two categories:

1. **base** - Built-in providers managed by Letta Cloud
2. **byok** - Bring Your Own Key providers created via API

All API-created providers are automatically `byok` category.

## Model Discovery

After creating a provider, Letta automatically discovers available models by querying the provider's API. For most providers, this happens immediately. For self-hosted providers, you may need to manually refresh:

```bash
curl -X PATCH http://localhost:8283/v1/providers/{provider_id}/refresh
```

## Provider Validation

To check if provider credentials are valid:

```bash
# For new credentials
curl -X POST http://localhost:8283/v1/providers/check \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "openai",
    "api_key": "sk-..."
  }'

# For existing provider
curl -X POST http://localhost:8283/v1/providers/{provider_id}/check
```

## Environment Variables

For self-hosted deployments, you can configure providers via environment variables instead of the API. See environment_variables.md for details.

## Notes

- Provider IDs are prefixed with `provider-`
- All providers support model auto-discovery
- Self-hosted providers use placeholder API keys
- OAuth providers require special setup
- Some providers have rate limits at the API level
