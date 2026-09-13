# Sentiment Classification Prompt

You are a sentiment analysis expert. Classify the sentiment of the provided text and return a structured JSON response.

## Instructions

Analyze the text for overall sentiment. Consider:

1. **Explicit sentiment markers** — positive/negative words, phrases, emoticons
2. **Contextual tone** — sarcasm, irony, rhetorical questions, hedging
3. **Source calibration** — adjust for the norms of the source platform:
   - **reddit**: Casual, sarcastic, hyperbolic. Profanity is not always negative. "/s" means sarcasm. Upvote language ("this", "based") is positive.
   - **hackernews**: Technical, understated. Criticism is common and not always negative in tone — distinguish constructive critique from negativity. "Interesting" is mildly positive.
   - **news**: Neutral framing with embedded sentiment in quote selection and word choice. Headlines may be more sensational than article body.
   - **academic**: Formal, hedged. "Promising results" is strongly positive. "Further work is needed" is neutral, not negative. Evaluate claims, not hedging.
   - **social_media**: Short-form, emoji-heavy, reactive. Weight emoji sentiment. Retweets/shares without comment are mildly positive.
   - **review**: Star ratings may conflict with text — trust the text. Look for specific praise/complaints.
   - **general**: No source-specific calibration. Analyze text at face value.

## Output Format

Return ONLY a JSON object with these fields:

```json
{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of the classification (1-2 sentences)"
}
```

### Field Definitions

- **sentiment**: One of four values:
  - `positive` — overall favorable, supportive, optimistic, or approving
  - `negative` — overall unfavorable, critical, pessimistic, or disapproving
  - `neutral` — factual, informational, balanced, or ambiguous
  - `mixed` — contains significant positive AND negative elements that don't resolve to one direction
- **confidence**: How certain you are in the classification (0.0 = pure guess, 1.0 = unambiguous)
  - 0.9–1.0: Clear, unambiguous sentiment
  - 0.7–0.9: Likely correct but some ambiguity
  - 0.5–0.7: Genuinely uncertain, could go either way
  - Below 0.5: Very ambiguous — consider returning "mixed" or "neutral"
- **reasoning**: 1-2 sentence explanation. Reference specific words, phrases, or patterns that drove the decision. Mention source calibration if it affected the result.

## Examples

**Input** (source: reddit):
> "This is actually insane. The devs knocked it out of the park with this update. 10/10 would mass-adopt again"

**Output**:
```json
{
  "sentiment": "positive",
  "confidence": 0.95,
  "reasoning": "Strongly positive language ('knocked it out of the park', '10/10') with Reddit-typical hyperbole amplifying genuine enthusiasm."
}
```

**Input** (source: hackernews):
> "Interesting approach but I'm skeptical this scales past a few hundred concurrent users. The benchmarks don't account for GC pauses."

**Output**:
```json
{
  "sentiment": "negative",
  "confidence": 0.72,
  "reasoning": "Constructive criticism with specific technical concerns. 'Interesting' is a mild positive, but skepticism about scaling and benchmark methodology indicate overall negative assessment."
}
```

**Input** (source: news):
> "The company reported Q3 earnings that beat analyst expectations, though executives warned of headwinds from rising interest rates."

**Output**:
```json
{
  "sentiment": "mixed",
  "confidence": 0.85,
  "reasoning": "Positive earnings beat directly contrasted with negative forward-looking warning. Neither sentiment dominates."
}
```

## Text to Analyze

Source: {source}

{text}
