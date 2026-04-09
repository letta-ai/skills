---
name: sentiment-analysis
description: LLM-based multi-source sentiment analysis with source-aware calibration for data pipelines
triggers:
  - "sentiment analysis"
  - "analyze sentiment"
  - "classify sentiment"
  - "text sentiment"
  - "sentiment scoring"
  - "is this positive or negative"
tools_required:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# Sentiment Analysis

LLM-based sentiment analysis that classifies text as positive, negative, neutral, or mixed
with a confidence score and reasoning. Calibrated for different source platforms — Reddit
sarcasm, HN understatement, news framing, academic hedging, and more.

Replaces naive word-list approaches with an LLM prompt that understands context, sarcasm,
and platform-specific norms. Available in Python and TypeScript with matching APIs.

## When to use

- Classifying scraped content (Reddit posts, HN comments, news articles)
- Adding sentiment signals to a data pipeline
- Building dashboards that show sentiment trends
- Enriching datasets before analysis or storage

## What it provides

1. **Python module** (`python/sentiment.py`) — `SentimentAnalyzer` class and `analyze_sentiment()` convenience function
2. **TypeScript module** (`typescript/sentiment.ts`) — matching API for Next.js / Node.js projects
3. **Calibrated prompt** (`prompts/classify-prompt.md`) — the LLM prompt with per-source calibration rules
4. **Source-aware scoring** — different calibration for reddit, hackernews, news, academic, social_media, review, general

See `README.md` for full usage documentation.
