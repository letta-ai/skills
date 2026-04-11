#!/usr/bin/env npx tsx
/**
 * fetch-news.ts — Fetch recent AI news from RSS feeds and YouTube channel feeds.
 *
 * Usage:
 *   npx tsx fetch-news.ts [--limit N] [--days N] [--sources rss|youtube|all]
 *
 * Options:
 *   --limit N       Max items per source (default: 5)
 *   --days N        Only include items from the last N days (default: 7)
 *   --sources TYPE  Which sources to fetch: rss, youtube, or all (default: all)
 *
 * Output: JSON array of news items to stdout
 */

// ── Default sources ────────────────────────────────────────────────────────────

const RSS_FEEDS = [
  { name: "Hugging Face Blog",    url: "https://huggingface.co/blog/feed.xml" },
  { name: "VentureBeat AI",       url: "https://venturebeat.com/category/ai/feed/" },
  { name: "The Verge AI",         url: "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml" },
  { name: "MIT Tech Review AI",   url: "https://www.technologyreview.com/topic/artificial-intelligence/feed/" },
  { name: "Ars Technica AI",      url: "https://feeds.arstechnica.com/arstechnica/index" },
  { name: "OpenAI News",          url: "https://openai.com/news/rss.xml" },
  { name: "Google AI Blog",       url: "https://blog.google/technology/ai/rss/" },
  { name: "Anthropic News",       url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml" },
  { name: "Simon Willison",       url: "https://simonwillison.net/atom/everything/" },
  { name: "Lilian Weng",          url: "https://lilianweng.github.io/index.xml" },
  { name: "Latent Space",         url: "https://www.latent.space/feed" },
];

// YouTube channel IDs — channel RSS requires no API key
const YOUTUBE_CHANNELS = [
  { name: "Yannic Kilcher",    channelId: "UCZHmQk67mSJgfCCTn7xBfew" },
  { name: "Two Minute Papers", channelId: "UCbfYPyITQ-7l4upoX8nvctg" },
  { name: "AI Explained",      channelId: "UCNJ1Ymd5yFuUPtn21xtRbbw" },
  { name: "Matthew Berman",    channelId: "UCzi5kcwU8aT4aLR7LcYhfWQ" },
  { name: "Andrej Karpathy",   channelId: "UCXUPKJO5MZQN11PqgIvyuvQ" },
  { name: "Dwarkesh Patel",    channelId: "UCXl4i9dYBrFOabk0xGmbkRA" },
  { name: "Fireship",          channelId: "UCsBjURrPoezykLs9EqgamOA" },
  { name: "David Ondrej",      channelId: "UCPGrgwfbkjTIgPoOh2q1BAg" },
  { name: "3Blue1Brown",       channelId: "UCYO_jab_esuFRV4b17AJtAw" },
];

// ── Types ──────────────────────────────────────────────────────────────────────

interface NewsItem {
  source: string;
  type: "rss" | "youtube";
  title: string;
  url: string;
  publishedAt: string;
  summary?: string;
  videoId?: string;
}

// ── XML helpers ────────────────────────────────────────────────────────────────

function extractTag(xml: string, tag: string): string {
  // Handle both <tag>content</tag> and CDATA
  const patterns = [
    new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>`, "i"),
    new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"),
  ];
  for (const re of patterns) {
    const m = xml.match(re);
    if (m) return m[1].trim();
  }
  return "";
}

function extractAttr(xml: string, tag: string, attr: string): string {
  const re = new RegExp(`<${tag}[^>]*\\s${attr}="([^"]*)"`, "i");
  const m = xml.match(re);
  return m ? m[1] : "";
}

function splitItems(xml: string, itemTag: string): string[] {
  const items: string[] = [];
  const re = new RegExp(`<${itemTag}[\\s>][\\s\\S]*?<\\/${itemTag}>`, "gi");
  let match;
  while ((match = re.exec(xml)) !== null) {
    items.push(match[0]);
  }
  return items;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, " ").trim();
}

// ── Fetch helpers ──────────────────────────────────────────────────────────────

async function fetchXml(url: string): Promise<string> {
  const res = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; ai-news-fetcher/1.0)" },
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

// ── RSS parser ─────────────────────────────────────────────────────────────────

async function fetchRssFeed(source: { name: string; url: string }, limit: number, cutoff: Date): Promise<NewsItem[]> {
  const xml = await fetchXml(source.url);

  // Try RSS <item> and Atom <entry>
  const rawItems = splitItems(xml, "item").length > 0 ? splitItems(xml, "item") : splitItems(xml, "entry");

  const items: NewsItem[] = [];
  for (const raw of rawItems.slice(0, limit * 2)) {
    const title = stripHtml(extractTag(raw, "title"));
    const url =
      extractTag(raw, "link") ||
      extractAttr(raw, "link", "href") ||
      extractTag(raw, "url");
    const pubDate =
      extractTag(raw, "pubDate") ||
      extractTag(raw, "published") ||
      extractTag(raw, "updated") ||
      extractTag(raw, "dc:date");
    const descRaw = extractTag(raw, "description") || extractTag(raw, "summary") || extractTag(raw, "content");
    const summary = stripHtml(descRaw).slice(0, 300);

    if (!title || !url) continue;

    const date = pubDate ? new Date(pubDate) : new Date();
    if (date < cutoff) continue;

    items.push({
      source: source.name,
      type: "rss",
      title,
      url: url.trim(),
      publishedAt: date.toISOString(),
      summary: summary || undefined,
    });

    if (items.length >= limit) break;
  }

  return items;
}

// ── YouTube channel RSS ────────────────────────────────────────────────────────

async function fetchYouTubeChannel(channel: { name: string; channelId: string }, limit: number, cutoff: Date): Promise<NewsItem[]> {
  const feedUrl = `https://www.youtube.com/feeds/videos.xml?channel_id=${channel.channelId}`;
  const xml = await fetchXml(feedUrl);

  const entries = splitItems(xml, "entry");
  const items: NewsItem[] = [];

  for (const raw of entries.slice(0, limit * 2)) {
    const title = stripHtml(extractTag(raw, "title"));
    const videoId = extractTag(raw, "yt:videoId") || extractAttr(raw, "link", "href").match(/v=([^&]+)/)?.[1] || "";
    const url = videoId ? `https://www.youtube.com/watch?v=${videoId}` : extractAttr(raw, "link", "href");
    const published = extractTag(raw, "published");
    const summary = stripHtml(extractTag(raw, "media:description") || extractTag(raw, "summary")).slice(0, 300);

    if (!title || !url) continue;

    const date = published ? new Date(published) : new Date();
    if (date < cutoff) continue;

    items.push({
      source: channel.name,
      type: "youtube",
      title,
      url,
      publishedAt: date.toISOString(),
      summary: summary || undefined,
      videoId: videoId || undefined,
    });

    if (items.length >= limit) break;
  }

  return items;
}

// ── Main ───────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
let limit = 5;
let days = 7;
let sourcesFilter: "rss" | "youtube" | "all" = "all";

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--limit" && args[i + 1]) limit = parseInt(args[++i]);
  else if (args[i] === "--days" && args[i + 1]) days = parseInt(args[++i]);
  else if (args[i] === "--sources" && args[i + 1]) sourcesFilter = args[++i] as typeof sourcesFilter;
}

const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

async function main() {
  const results: NewsItem[] = [];
  const errors: string[] = [];

  const rssTasks = sourcesFilter !== "youtube"
    ? RSS_FEEDS.map(feed =>
        fetchRssFeed(feed, limit, cutoff)
          .then(items => results.push(...items))
          .catch(e => errors.push(`${feed.name}: ${e.message}`))
      )
    : [];

  const ytTasks = sourcesFilter !== "rss"
    ? YOUTUBE_CHANNELS.map(ch =>
        fetchYouTubeChannel(ch, limit, cutoff)
          .then(items => results.push(...items))
          .catch(e => errors.push(`${ch.name}: ${e.message}`))
      )
    : [];

  await Promise.all([...rssTasks, ...ytTasks]);

  // Sort by date descending
  results.sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());

  const output = {
    fetchedAt: new Date().toISOString(),
    cutoffDate: cutoff.toISOString(),
    totalItems: results.length,
    errors: errors.length > 0 ? errors : undefined,
    items: results,
  };

  console.log(JSON.stringify(output, null, 2));
}

main().catch(e => {
  console.error("Fatal error:", e.message);
  process.exit(1);
});
