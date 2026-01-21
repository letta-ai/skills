# Model Selection Guide

## Production Recommendations

### High-Quality Reasoning
- **GPT-4o**: Best overall, reliable tool calling (`openai/gpt-4o`)
- **Claude Sonnet 4**: Excellent reasoning, strong with memory tools (`anthropic/claude-sonnet-4-20250514`)
- **Gemini 2.0 Flash**: Fast, good capability (`google/gemini-2.0-flash`)

### Cost-Efficient
- **GPT-4o-mini**: Best balance of cost and capability (`openai/gpt-4o-mini`)
- **Claude Haiku 3.5**: Fast, lightweight, good for simple tasks (`anthropic/claude-3-5-haiku-20241022`)

### Local/Self-Hosted
- **Qwen 2.5**: Strong local model with good tool calling
- **Llama 3.3 70B**: Excellent local option
- **Mistral Small**: Good tool calling for its size

## Avoid for Production

### Tool Calling Issues
- Ollama models < 7B parameters
- Models without function calling support
- Untested vision models in tool-calling contexts

### Proxy Provider Issues
- OpenRouter: Inconsistent tool calling across providers
- Groq: Limited tool calling support

## Context Window Considerations

**Default: 32k tokens**
- Team recommends 32k as sweet spot
- Larger windows (100k+) cause two issues:
  1. Agent reliability decreases
  2. Response latency increases

**When to increase:**
- Specific use case requires larger context
- Willing to accept performance trade-offs
- Have tested reliability at target size

## Reasoning Models

**Native reasoning (v1 agents only):**
- GPT-4o and newer
- Claude Sonnet 4 with extended thinking
- Gemini 2.0 Flash Thinking

**Prompted reasoning (v2 agents):**
- Better for smaller models
- Uses tool call arguments for inner monologue

## Cost Management

**Self-hosted:**
- Pay per token directly to provider
- No Letta overhead

**Letta Cloud:**
- Per-message pricing (not per token)
- 1 credit = 1 standard model request
- Premium models have different multipliers
