# Sentiment Analysis

LLM-based multi-source sentiment analysis with source-aware calibration. Classifies text as positive, negative, neutral, or mixed with a confidence score and reasoning.

Available in **Python** and **TypeScript** with matching APIs.

## Why LLM over word lists?

Word-list approaches (VADER, AFINN) fail on sarcasm, context, domain-specific language, and platform norms. "This is insane" is positive on Reddit, negative in a medical report. An LLM prompt with source calibration handles these cases correctly.

## Features

- **Four sentiment classes** — positive, negative, neutral, mixed
- **Confidence scoring** — 0.0 to 1.0 with calibrated thresholds
- **Reasoning** — every result includes a 1-2 sentence explanation
- **Source-aware calibration** — adjusts for platform norms (Reddit sarcasm, HN understatement, academic hedging, news framing)
- **Seven source types** — reddit, hackernews, news, academic, social_media, review, general
- **Batch processing** — analyze multiple texts in sequence
- **Configurable model** — defaults to Sonnet for speed; switch to Opus for judgment-heavy analysis

## Python Usage

```python
from sentiment import SentimentAnalyzer, SentimentConfig

# Basic usage
analyzer = SentimentAnalyzer()
result = analyzer.analyze("This product is absolutely fantastic!", source="review")
print(result.sentiment)    # "positive"
print(result.confidence)   # 0.95
print(result.reasoning)    # "Strongly positive language..."

# One-shot convenience function
from sentiment import analyze_sentiment

result = analyze_sentiment("Meh, it's okay I guess", source="reddit")

# Batch processing
results = analyzer.analyze_batch([
    ("Great update! The devs nailed it", "reddit"),
    ("Earnings missed analyst estimates by 12%", "news"),
    ("Further work is needed to validate these findings", "academic"),
])

# Custom configuration
config = SentimentConfig(
    model="claude-opus-4-6",      # Use Opus for higher-stakes analysis
    temperature=0.0,               # Deterministic (default)
    default_source="hackernews",   # Default source if not specified
    max_text_length=8000,          # Allow longer texts
)
analyzer = SentimentAnalyzer(config=config)
```

## TypeScript Usage

```typescript
import { SentimentAnalyzer, analyzeSentiment } from "./sentiment";

// Basic usage
const analyzer = new SentimentAnalyzer();
const result = await analyzer.analyze("This product is amazing!", "review");
console.log(result.sentiment);    // "positive"
console.log(result.confidence);   // 0.95
console.log(result.reasoning);    // "Strongly positive language..."

// One-shot convenience function
const result = await analyzeSentiment("Meh, it's okay", "reddit");

// Batch processing
const results = await analyzer.analyzeBatch([
  ["Great update!", "reddit"],
  ["Earnings missed estimates.", "news"],
]);

// Custom configuration
const analyzer = new SentimentAnalyzer({
  model: "claude-opus-4-6",
  defaultSource: "hackernews",
  maxTextLength: 8000,
});
```

## Source Calibration

| Source | Calibration Notes |
|---|---|
| `reddit` | Accounts for sarcasm, hyperbole, profanity-as-emphasis, `/s` tags |
| `hackernews` | Adjusts for understated praise, constructive criticism norms |
| `news` | Reads through neutral framing to detect embedded sentiment |
| `academic` | Interprets hedging correctly ("promising" = strong positive) |
| `social_media` | Weights emoji sentiment, short-form reactive language |
| `review` | Trusts text over ratings, looks for specific praise/complaints |
| `general` | No special calibration — analyzes text at face value |

## Configuration Reference

| Python field | TypeScript field | Default | Description |
|---|---|---|---|
| `model` | `model` | `claude-sonnet-4-6` | Claude model to use |
| `max_tokens` | `maxTokens` | 256 | Maximum response tokens |
| `temperature` | `temperature` | 0.0 | Sampling temperature |
| `api_key` | `apiKey` | env `ANTHROPIC_API_KEY` | API key |
| `default_source` | `defaultSource` | `general` | Default source when not specified |
| `max_text_length` | `maxTextLength` | 4000 | Truncate input beyond this length |

## Result Schema

Both implementations return the same structure:

```json
{
  "sentiment": "positive",
  "confidence": 0.92,
  "reasoning": "Strongly positive language with enthusiasm markers.",
  "source": "reddit",
  "textPreview": "This is actually insane. The devs knocked it out of th..."
}
```

## File Structure

```
skills/data-pipeline/sentiment-analysis/
  SKILL.md                          # Skill metadata and triggers
  README.md                         # This file
  prompts/
    classify-prompt.md              # The LLM prompt with source calibration
  python/
    sentiment.py                    # Python implementation (requires anthropic SDK)
  typescript/
    sentiment.ts                    # TypeScript implementation (requires @anthropic-ai/sdk)
```
