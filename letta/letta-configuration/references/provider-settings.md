# Provider-Specific Model Settings

Configuration patterns for provider-specific features like OpenAI reasoning models and Anthropic extended thinking.

## OpenAI Reasoning Models

For models like `o1`, `o3`, and `o3-mini` that support extended reasoning:

### Python
```python
agent = client.agents.create(
    model="openai/o3-mini",
    model_settings={
        "provider_type": "openai",
        "reasoning": {
            "reasoning_effort": "medium"  # "low", "medium", or "high"
        }
    }
)
```

### TypeScript
```typescript
const agent = await client.agents.create({
  model: "openai/o3-mini",
  model_settings: {
    provider_type: "openai",
    reasoning: {
      reasoning_effort: "medium",  // "low", "medium", or "high"
    },
  },
});
```

### Reasoning Effort Levels

| Level | Use Case | Cost |
|-------|----------|------|
| `low` | Simple tasks, faster responses | Lower |
| `medium` | Balanced reasoning (recommended default) | Medium |
| `high` | Complex multi-step reasoning | Higher |

## Anthropic Extended Thinking

For Claude models with extended thinking capability:

### Python
```python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    model_settings={
        "provider_type": "anthropic",
        "thinking": {
            "type": "enabled",
            "budget_tokens": 10000
        }
    }
)
```

### TypeScript
```typescript
const agent = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  model_settings: {
    provider_type: "anthropic",
    thinking: {
      type: "enabled",
      budget_tokens: 10000,
    },
  },
});
```

### Thinking Budget

The `budget_tokens` parameter controls how many tokens Claude can use for internal reasoning before responding:

| Budget | Use Case |
|--------|----------|
| 5000 | Quick reasoning tasks |
| 10000 | Standard complex tasks (recommended) |
| 20000+ | Very complex multi-step problems |

**Note:** Higher budgets increase latency and cost but can improve quality on complex tasks.

## Combining Settings

You can combine provider-specific settings with standard settings:

```python
agent = client.agents.create(
    model="openai/o3-mini",
    model_settings={
        "provider_type": "openai",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "reasoning": {
            "reasoning_effort": "high"
        }
    },
    context_window_limit=128000
)
```

## Common Mistakes

**Wrong: Missing provider_type**
```python
# Bad - missing required provider_type field
model_settings={
    "temperature": 0.7  # Missing provider_type!
}
```

**Correct: Include provider_type**
```python
# Good - provider_type included
model_settings={
    "provider_type": "openai",
    "temperature": 0.7
}
```

**Wrong: Reasoning settings at top level**
```python
# Bad - reasoning_effort not recognized at top level
model_settings={
    "provider_type": "openai",
    "reasoning_effort": "medium"  # Wrong!
}
```

**Correct: Nested under "reasoning" key**
```python
# Good - properly nested
model_settings={
    "provider_type": "openai",
    "reasoning": {
        "reasoning_effort": "medium"
    }
}
```

**Wrong: Thinking settings without type**
```python
# Bad - missing required "type" field
model_settings={
    "provider_type": "anthropic",
    "thinking": {
        "budget_tokens": 10000  # Missing type!
    }
}
```

**Correct: Include type field**
```python
# Good - type field included
model_settings={
    "provider_type": "anthropic",
    "thinking": {
        "type": "enabled",
        "budget_tokens": 10000
    }
}
```
