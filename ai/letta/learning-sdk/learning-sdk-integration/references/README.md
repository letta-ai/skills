# Agentic Learning SDK Integration Examples

This directory contains practical examples of integrating the Agentic Learning SDK with various LLM providers.

## Files

### universal_examples.py
Examples showing the universal 3-line pattern working with OpenAI, Claude, and Gemini.

### provider_specific_examples.py
Detailed examples for each LLM provider with provider-specific optimizations.

### multi_provider_agent.py
Example of an agent that can use multiple LLM providers and share memory across them.

### testing_examples.py
Test patterns for validating memory integration works correctly.

## Usage

Run examples with:
```bash
# Set your API keys first
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key" 
export GOOGLE_API_KEY="your-key"

python universal_examples.py
python provider_specific_examples.py
python multi_provider_agent.py
python testing_examples.py
```

## Requirements

- Provider SDKs you want to use (`openai`, `anthropic`, `google-generativeai`)
- `agentic-learning-sdk` package
- Valid API keys for chosen providers