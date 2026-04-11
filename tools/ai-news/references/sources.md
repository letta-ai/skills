# AI News Sources

This file documents the default sources used by the `ai-news` skill. Edit `fetch-news.ts` to add, remove, or swap sources.

## RSS Feeds

| Name | URL | Notes |
|------|-----|-------|
| Hugging Face Blog | https://huggingface.co/blog/feed.xml | Model releases, research, tutorials |
| VentureBeat AI | https://venturebeat.com/category/ai/feed/ | Industry news, funding, products |
| The Verge AI | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml | Consumer AI, policy, culture |
| MIT Tech Review AI | https://www.technologyreview.com/topic/artificial-intelligence/feed/ | Research-leaning tech journalism |
| Ars Technica AI | https://feeds.arstechnica.com/arstechnica/index | Technical depth, policy |
| OpenAI News | https://openai.com/news/rss.xml | First-party OpenAI announcements |
| Google AI Blog | https://blog.google/technology/ai/rss/ | First-party Google AI announcements |
| Anthropic News | https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml | Community-maintained (Anthropic has no native RSS) |
| Simon Willison | https://simonwillison.net/atom/everything/ | LLM tooling, prompt engineering, practical AI |
| Lilian Weng | https://lilianweng.github.io/index.xml | Deep research posts (OpenAI) |
| Latent Space | https://www.latent.space/feed | AI engineering podcast/newsletter |

### Adding More RSS Feeds

Any standard RSS/Atom feed URL works. Good candidates:
- `https://arxiv.org/rss/cs.AI` — arXiv CS.AI preprints (high volume)
- `https://arxiv.org/rss/cs.LG` — arXiv Machine Learning
- `https://www.import.ai/feed` — Jack Clark's Import AI newsletter
- `https://lastweekin.ai/feed` — Last Week in AI recap

## YouTube Channels

Fetched via YouTube's public channel RSS feed (no API key required):
`https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`

| Name | Channel ID | Focus |
|------|-----------|-------|
| Yannic Kilcher | UCZHmQk67mSJgfCCTn7xBfew | Paper walkthroughs, ML research deep dives |
| Two Minute Papers | UCbfYPyITQ-7l4upoX8nvctg | Research paper summaries |
| AI Explained | UCNJ1Ymd5yFuUPtn21xtRbbw | Accessible AI news and model breakdowns |
| Matthew Berman | UCzi5kcwU8aT4aLR7LcYhfWQ | AI tools, product launches, demos |
| Andrej Karpathy | UCXUPKJO5MZQN11PqgIvyuvQ | Deep technical ML education |
| Dwarkesh Patel | UCXl4i9dYBrFOabk0xGmbkRA | Long-form AI/tech interviews |
| Fireship | UCsBjURrPoezykLs9EqgamOA | Fast-paced dev/AI news |
| David Ondrej | UCPGrgwfbkjTIgPoOh2q1BAg | AI news and tool roundups |
| 3Blue1Brown | UCYO_jab_esuFRV4b17AJtAw | Math/ML visualizations |

**Note**: YouTube RSS feeds can go down transiently (all channels 404'd on 2026-03-30 evening, recovered by morning). Errors from YouTube are safe to ignore if temporary.

### Finding Channel IDs

To find a channel's ID:
1. Go to the channel page on YouTube
2. View page source and search for `"channelId"`
3. Or use: `https://www.youtube.com/@handle` → check the URL after redirect, or use a tool like `https://commentpicker.com/youtube-channel-id.php`

## Transcript Availability

YouTube transcripts are fetched via `fetch-transcript.ts`. They are available when:
- The video has auto-generated captions (most English videos do)
- The creator has uploaded manual captions

Transcripts are NOT available for:
- Live streams (until archived)
- Shorts (usually)
- Videos where the creator has disabled captions
