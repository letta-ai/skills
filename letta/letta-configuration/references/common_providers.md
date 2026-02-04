# Common Provider Configuration

Detailed configuration examples for the most popular providers.

## OpenAI

**Provider Type:** `openai`

**Required Fields:**
- `api_key` - OpenAI API key (starts with `sk-`)

**Optional Fields:**
- `base_url` - Custom endpoint (for OpenAI-compatible servers)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My OpenAI",
    "provider_type": "openai",
    "api_key": "sk-your-key-here"
  }'
```

**Environment Variables:**
```bash
OPENAI_API_KEY=sk-your-key-here
```

**Docker:**
```bash
docker run -p 8283:8283 \
  -e OPENAI_API_KEY=sk-your-key-here \
  letta/letta:latest
```

---

## Anthropic (Claude)

**Provider Type:** `anthropic`

**Required Fields:**
- `api_key` - Anthropic API key (starts with `sk-ant-`)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Anthropic",
    "provider_type": "anthropic",
    "api_key": "sk-ant-your-key-here"
  }'
```

**Environment Variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Docker:**
```bash
docker run -p 8283:8283 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key-here \
  letta/letta:latest
```

---

## Azure OpenAI

**Provider Type:** `azure`

**Required Fields:**
- `api_key` - Azure OpenAI key
- `base_url` - Azure resource endpoint (e.g., `https://your-resource.openai.azure.com`)

**Optional Fields:**
- `api_version` - API version (default: `2024-09-01-preview`)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Azure OpenAI",
    "provider_type": "azure",
    "api_key": "your-azure-key",
    "base_url": "https://your-resource.openai.azure.com",
    "api_version": "2024-09-01-preview"
  }'
```

**Environment Variables:**
```bash
AZURE_API_KEY=your-azure-key
AZURE_BASE_URL=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-09-01-preview
```

**Docker:**
```bash
docker run -p 8283:8283 \
  -e AZURE_API_KEY=your-key \
  -e AZURE_BASE_URL=https://your-resource.openai.azure.com \
  -e AZURE_API_VERSION=2024-09-01-preview \
  letta/letta:latest
```

**Common Issues:**
- Ensure `base_url` does NOT include `/openai/deployments` path
- Model field must be deployment name, not model name
- Check API version compatibility with your deployment

---

## Google AI (Gemini)

**Provider Type:** `google_ai`

**Required Fields:**
- `api_key` - Google AI API key

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Google AI",
    "provider_type": "google_ai",
    "api_key": "your-google-ai-key"
  }'
```

**Environment Variables:**
```bash
GOOGLE_AI_API_KEY=your-google-ai-key
```

**Docker:**
```bash
docker run -p 8283:8283 \
  -e GOOGLE_AI_API_KEY=your-key \
  letta/letta:latest
```

---

## Google Vertex AI

**Provider Type:** `google_vertex`

**Required Fields:**
- `api_key` - Service account key (JSON)
- `region` - GCP region (e.g., `us-central1`)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Vertex AI",
    "provider_type": "google_vertex",
    "api_key": "{\"type\": \"service_account\", ...}",
    "region": "us-central1"
  }'
```

**Environment Variables:**
```bash
GOOGLE_VERTEX_API_KEY='{"type": "service_account", ...}'
GOOGLE_VERTEX_REGION=us-central1
```

---

## Groq

**Provider Type:** `groq`

**Required Fields:**
- `api_key` - Groq API key

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Groq",
    "provider_type": "groq",
    "api_key": "your-groq-key"
  }'
```

**Environment Variables:**
```bash
GROQ_API_KEY=your-groq-key
```

---

## Together AI

**Provider Type:** `together`

**Required Fields:**
- `api_key` - Together AI API key

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Together AI",
    "provider_type": "together",
    "api_key": "your-together-key"
  }'
```

**Environment Variables:**
```bash
TOGETHER_API_KEY=your-together-key
```

---

## Best Practices

1. **Never commit API keys** - Use `.env` files and add them to `.gitignore`
2. **Test credentials** - Use `/v1/providers/check` endpoint to validate before saving
3. **Monitor usage** - Most providers offer usage dashboards
4. **Rotate keys** - Regularly rotate API keys for security
5. **Use BYOK on Cloud** - For production, use BYOK to keep costs separate
6. **Set rate limits** - Configure rate limits at provider level when possible
