# Memory import workflow — quick reference

This is a condensed checklist. See `SKILL.md` for full details.

## Workflow phases

1. **Locate** — find the export zip (usually `~/Downloads/`)
2. **Inventory** — `list-conversations.py` to understand scale
3. **Extract + preview** — `build-memory-preview.py <export.zip>` (one step)
4. **Write active memory** — high-confidence items to `system/human.md`
5. **Write progressive memory** — audit file + historical context to `reference/chatgpt/`
6. **Enrich** — optional archive mining (parallel for 50+ conversations)
7. **Validate** — run `/doctor`

## Write-immediately checklist

Active memory (`system/human.md`):
- [ ] Name and stable identity basics
- [ ] Current role / employer (when explicit and recent)
- [ ] Durable response preferences (from hidden saved memory)
- [ ] Formatting preferences
- [ ] Collaboration preferences (directness, question volume, anti-sycophancy)

Progressive memory (always create):
- [ ] `reference/chatgpt/import-YYYY-MM-DD.md` — audit trail of the import
- [ ] `reference/chatgpt/work-and-technical-background.md` — if historical work context found
- [ ] `reference/chatgpt/collaboration-preferences.md` — if detailed interaction patterns found
- [ ] `[[reference/chatgpt/...]]` links in `system/human.md` pointing to progressive files

## Hold-for-review checklist

- [ ] Historical or possibly stale facts
- [ ] Contradictions with newer material
- [ ] Sensitive or intimate material
- [ ] Facts based on assistant interpretation rather than user statements
- [ ] Broad claims that risk a malformed memory layout

## Safe write targets

| Destination | Content |
|---|---|
| `system/human.md` | Compact durable user facts, in-context every turn |
| `reference/chatgpt/import-YYYY-MM-DD.md` | Import audit trail |
| `reference/chatgpt/work-and-technical-background.md` | Historical work context |
| `reference/chatgpt/collaboration-preferences.md` | Mined interaction patterns |
| `reference/chatgpt/mining/chunk-NNN.md` | Subagent mining output |
| `reference/chatgpt/transcripts/` | Curated transcript exports |

## Confidence rubric

**High confidence** (safe to write immediately):
- Explicitly present in hidden saved memory
- Repeated across multiple conversations
- Restated later as current/canonical
- Low sensitivity

**Low confidence** (hold for review):
- Old and time-sensitive
- Contradicted by newer conversations
- Sensitive and not clearly collaboration-relevant
- Only weakly implied by assistant summaries

## Retraction sweep queries

```bash
python3 scripts/search-conversations.py <export.zip> \
  --query "not doing" --query "no longer" --query "forget that" \
  --query "remove from memory" --query "used to" --query "don't assume" \
  --role user
```

Prefer newer explicit corrections over older historical context.

## Personality / collaboration extraction

Extract:
- tone preferences (direct, warm, dry, playful, formal)
- formatting preferences (bullets, terse paragraphs, code-first, no preamble)
- proactivity preferences (ask first vs. act first)
- question-volume preferences (single follow-up vs. many questions)
- correction patterns (how the user signals something is off)
- anti-patterns they dislike (sycophancy, hedging, pedantry, over-explaining)

Treat as weak evidence unless confirmed:
- one-off frustration
- temporary sadness or stress
- intimate relationship details
- medical or mental-health information not necessary for collaboration

## Store by default

Personal details are part of knowing the user: family, pets, hobbies, interests, life circumstances, personality, personal projects, relationship status. The user imported their memory because they want to be known.

## Ask before storing

Only material with real consequences if mishandled:
- Health/mental health specifics (diagnosis, medication, treatment — not general "handle sensitively" flags)
- Intimate relationship dynamics (not the fact of relationships, but conflict/emotional specifics)
- Financial specifics (debt, income, amounts)
- Contradictions where the current truth is unclear
