# Custom OpenAI-Compatible Endpoints

Configure Letta to use self-hosted models or OpenAI-compatible APIs like vLLM, LM Studio, and LocalAI.

## Basic Configuration

Use `model_endpoint` and `model_endpoint_type` in `model_settings`:

### Python
```python
agent = client.agents.create(
    model="openai/custom-model",
    model_settings={
        "provider_type": "openai",
        "model_endpoint": "https://your-api.example.com/v1",
        "model_endpoint_type": "openai"
    }
)
```

### TypeScript
```typescript
const agent = await client.agents.create({
  model: "openai/custom-model",
  model_settings: {
    provider_type: "openai",
    model_endpoint: "https://your-api.example.com/v1",
    model_endpoint_type: "openai",
  },
});
```

## Compatible Providers

This configuration works with:

| Provider | Typical Endpoint | Notes |
|----------|-----------------|-------|
| vLLM | `http://localhost:8000/v1` | High-performance serving |
| LM Studio | `http://localhost:1234/v1` | Desktop app |
| LocalAI | `http://localhost:8080/v1` | Drop-in replacement |
| Ollama | `http://localhost:11434/v1` | Use `ollama/` prefix instead |
| Text Generation Inference | `http://localhost:8080/v1` | Hugging Face TGI |

## vLLM Example

```python
# Start vLLM server:
# python -m vllm.entrypoints.openai.api_server \
#   --model mistralai/Mistral-7B-Instruct-v0.2 \
#   --port 8000

agent = client.agents.create(
    model="openai/mistralai/Mistral-7B-Instruct-v0.2",
    model_settings={
        "provider_type": "openai",
        "model_endpoint": "http://localhost:8000/v1",
        "model_endpoint_type": "openai"
    },
    embedding="openai/text-embedding-3-small"  # Still need cloud embedding
)
```

## LM Studio Example

```python
# 1. Open LM Studio
# 2. Load a model
# 3. Start local server (default port 1234)

agent = client.agents.create(
    model="openai/local-model",
    model_settings={
        "provider_type": "openai",
        "model_endpoint": "http://localhost:1234/v1",
        "model_endpoint_type": "openai"
    },
    embedding="openai/text-embedding-3-small"
)
```

## Authentication

If your endpoint requires an API key:

```python
import os

# Set via environment variable
os.environ["OPENAI_API_KEY"] = "your-custom-api-key"

agent = client.agents.create(
    model="openai/custom-model",
    model_settings={
        "model_endpoint": "https://your-secure-api.example.com/v1",
        "model_endpoint_type": "openai"
    }
)
```

## Requirements

Custom endpoints must support:

1. **Tool/Function Calling** - Required for Letta agents to work properly
2. **OpenAI-compatible API format** - `/v1/chat/completions` endpoint
3. **Streaming** (recommended) - For real-time responses

**Warning:** Many local models have poor tool calling support. Test thoroughly before production use.

## Troubleshooting

### "Tool calling not supported"
- Your model may not support function calling
- Try a different model (Mistral, Llama 3+, or fine-tuned variants)

### Connection refused
- Verify the endpoint URL is correct
- Check if the server is running
- Ensure firewall allows the connection

### Slow responses
- Local models are often slower than cloud APIs
- Consider GPU acceleration
- Reduce `context_window_limit` if needed

### JSON parsing errors
- Model may be outputting malformed JSON
- Try models specifically trained for function calling
- Consider using a larger model

## Self-Hosted Letta Server

For fully self-hosted deployments, configure via environment variables:

```bash
# Set in your environment or docker-compose
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="your-key"
```

Then create agents normally - they'll use the configured endpoint by default.
