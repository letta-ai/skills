---
name: ai-news
description: Fetch and summarize recent AI news from curated RSS feeds (Hugging Face, VentureBeat, The Verge, OpenAI, Anthropic, DeepMind, etc.) and YouTube channels (Yannic Kilcher, Two Minute Papers, AI Explained, etc.). Also fetches full transcripts for specific YouTube videos. Use when the user asks about recent AI news, what's happened in AI lately, summaries of AI research or product announcements, or wants a digest of what's going on in the AI space.
---

# AI News

Fetch recent AI news from RSS feeds and YouTube channel feeds, then synthesize into a digest. Optionally fetch full transcripts for YouTube videos.

## Setup (one-time)

```bash
cd ~/.letta/skills/ai-news/scripts && npm install
```

## Workflow

### 1. Fetch recent news

```bash
npx tsx scripts/fetch-news.ts [--days 7] [--limit 5] [--sources all|rss|youtube]
```

- Outputs a JSON object with `items[]` sorted newest-first
- Each item has: `source`, `type` (rss/youtube), `title`, `url`, `publishedAt`, `summary`, `videoId`
- Failed sources are listed in `errors[]` — safe to ignore individual failures

### 2. Synthesize a digest

Read the JSON output and write a digest grouped by theme (e.g. model releases, research, tools, policy). Lead with the most significant items. For YouTube videos, note they have transcripts available.

### 3. (Optional) Fetch a video transcript

For any YouTube item worth deeper coverage:

```bash
npx tsx scripts/fetch-transcript.ts <video-url-or-id> [--summary] [--lang en]
```

- `--summary` returns first ~4000 chars (good for quick context)
- Without `--summary`, returns full transcript + timestamped segments
- Works with any YouTube URL format or bare video ID

## Customizing Sources

See `references/sources.md` for the full list of default RSS feeds and YouTube channels, how to find channel IDs, and additional feed recommendations.

To add/remove sources, edit the `RSS_FEEDS` and `YOUTUBE_CHANNELS` arrays at the top of `scripts/fetch-news.ts`.

## Tips

- Use `--days 1` for daily briefings, `--days 7` for weekly digests
- Use `--sources rss` if YouTube fetches are slow or failing
- Some feeds (arXiv) can be very high volume — use a lower `--limit` or filter by keyword after fetching
- Transcripts require captions to be enabled on the video; auto-generated captions work fine
