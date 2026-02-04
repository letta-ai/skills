# Self-Hosted Provider Configuration

Configuration for local and self-hosted LLM providers.

## Ollama

**Provider Type:** `ollama`

**Required Fields:**
- `api_key` - Use `"ollama"` (placeholder value)
- `base_url` - Ollama endpoint URL

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Ollama",
    "provider_type": "ollama",
    "api_key": "ollama",
    "base_url": "http://localhost:11434"
  }'
```

**Environment Variables:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

**Docker Networking:**

**macOS/Windows:**
```bash
# Letta in Docker → Ollama on host
docker run -p 8283:8283 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  letta/letta:latest

# Ollama must listen on all interfaces
export OLLAMA_HOST=0.0.0.0
ollama serve
```

**Linux:**
```bash
# Option 1: Use host network mode
docker run --network host letta/letta:latest

# Option 2: Use Docker bridge IP
docker run -p 8283:8283 \
  -e OLLAMA_BASE_URL=http://172.17.0.1:11434 \
  letta/letta:latest
```

**Model Selection:**
```bash
# Pull models with specific tags
ollama pull qwen2.5:32b
ollama pull llama3.2:3b-instruct-q6_K

# Use in Letta
model="ollama/qwen2.5:32b"
```

**Common Issues:**
- Connection refused: Check `OLLAMA_HOST=0.0.0.0` is set
- Models not appearing: Use specific tags (`:32b` not just model name)
- Poor tool calling: Smaller models struggle with function calling
- Use Q6_K or higher quantization for better reliability

---

## vLLM

**Provider Type:** `vllm`

**Required Fields:**
- `api_key` - Use `"vllm"` (placeholder)
- `base_url` - vLLM server endpoint

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vLLM Server",
    "provider_type": "vllm",
    "api_key": "vllm",
    "base_url": "http://localhost:8000"
  }'
```

**Starting vLLM Server:**
```bash
# Start vLLM with OpenAI-compatible API
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --host 0.0.0.0 \
  --port 8000
```

**Docker:**
```bash
docker run -p 8000:8000 \
  --gpus all \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.2
```

---

## LM Studio

**Provider Type:** `lmstudio_openai`

**Required Fields:**
- `api_key` - Use `"lmstudio"` (placeholder)
- `base_url` - LM Studio endpoint (default: `http://localhost:1234/v1`)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LM Studio",
    "provider_type": "lmstudio_openai",
    "api_key": "lmstudio",
    "base_url": "http://localhost:1234/v1"
  }'
```

**LM Studio Setup:**
1. Open LM Studio
2. Load a model
3. Go to "Local Server" tab
4. Start server (default port: 1234)
5. Enable "CORS" if accessing from browser

**Known Limitations:**
- Context window capped at 30K regardless of model (LM Studio validation bug)
- Use Desktop version for better compatibility

---

## SGLang

**Provider Type:** `sglang`

**Required Fields:**
- `api_key` - Use `"sglang"` (placeholder)
- `base_url` - SGLang server endpoint

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SGLang Server",
    "provider_type": "sglang",
    "api_key": "sglang",
    "base_url": "http://localhost:30000"
  }'
```

**Starting SGLang:**
```bash
python -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --port 30000
```

---

## Text Generation WebUI (oobabooga)

**Provider Type:** `openai` (with custom base_url)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Text Generation WebUI",
    "provider_type": "openai",
    "api_key": "placeholder",
    "base_url": "http://localhost:5000/v1"
  }'
```

**WebUI Setup:**
1. Start with `--api` flag
2. Load model
3. Enable "OpenAI-compatible API" extension
4. Use `http://localhost:5000/v1` as base_url

---

## LocalAI

**Provider Type:** `openai` (with custom base_url)

**API Example:**
```bash
curl -X POST http://localhost:8283/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LocalAI",
    "provider_type": "openai",
    "api_key": "local",
    "base_url": "http://localhost:8080/v1"
  }'
```

**Docker:**
```bash
docker run -p 8080:8080 \
  --name localai \
  localai/localai:latest
```

---

## General Self-Hosted Best Practices

### Model Selection
- Use instruction-tuned models for better results
- Prefer Q6_K or higher quantization
- Smaller models (<7B) struggle with complex tool calling
- Test tool calling reliability before production use

### Performance Optimization
- Enable GPU acceleration when available
- Use smaller context windows (8K-32K) for speed
- Consider vLLM for production (better throughput)
- Ollama good for development, vLLM for production

### Networking
- Always set `OLLAMA_HOST=0.0.0.0` when serving from host
- Use `host.docker.internal` on macOS/Windows Docker
- Use `172.17.0.1` or host network on Linux Docker
- Test connectivity with `curl http://endpoint/v1/models`

### Troubleshooting
- Connection refused: Check firewall and host binding
- Models not listed: Verify model is loaded in server
- Poor quality: Try larger model or better quantization
- Slow responses: Reduce context window or use GPU

### Security
- Self-hosted servers often don't require auth
- Use reverse proxy (nginx/Caddy) for auth if exposing
- Keep servers on local network only
- Don't expose to public internet without security
