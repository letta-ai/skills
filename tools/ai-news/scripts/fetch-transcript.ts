#!/usr/bin/env npx tsx
/**
 * fetch-transcript.ts — Fetch the transcript for a YouTube video.
 *
 * Usage:
 *   npx tsx fetch-transcript.ts <video-url-or-id> [--lang en] [--summary]
 *
 * Arguments:
 *   video-url-or-id   YouTube URL (any format) or bare video ID (e.g. dQw4w9WgXcQ)
 *
 * Options:
 *   --lang CODE   Language code for transcript (default: en)
 *   --summary     Print a condensed version (first 4000 chars) instead of full transcript
 *
 * Output: JSON with video metadata and full transcript text
 *
 * Requires: npm install (run once in this directory to install youtube-transcript)
 */

const { YoutubeTranscript } = require("./node_modules/youtube-transcript/dist/youtube-transcript.common.js");

function extractVideoId(input: string): string {
  if (/^[a-zA-Z0-9_-]{11}$/.test(input)) return input;
  const patterns = [
    /[?&]v=([a-zA-Z0-9_-]{11})/,
    /youtu\.be\/([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/,
  ];
  for (const re of patterns) {
    const m = input.match(re);
    if (m) return m[1];
  }
  throw new Error(`Could not extract video ID from: ${input}`);
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ── CLI ────────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
if (args.length === 0 || args[0] === "--help") {
  console.log(`Usage: npx tsx fetch-transcript.ts <video-url-or-id> [--lang en] [--summary]`);
  process.exit(0);
}

const input = args[0];
let lang = "en";
let summaryMode = false;

for (let i = 1; i < args.length; i++) {
  if (args[i] === "--lang" && args[i + 1]) lang = args[++i];
  else if (args[i] === "--summary") summaryMode = true;
}

async function main() {
  const videoId = extractVideoId(input);

  let segments: Array<{ text: string; offset: number; duration: number; lang: string }>;
  try {
    segments = await YoutubeTranscript.fetchTranscript(videoId, { lang });
  } catch (e: any) {
    throw new Error(`Could not fetch transcript: ${e.message}. The video may have captions disabled or the language '${lang}' may not be available.`);
  }

  const fullText = segments.map(s => s.text.replace(/\n/g, " ").trim()).join(" ");
  const durationMs = segments.length > 0 ? segments[segments.length - 1].offset + segments[segments.length - 1].duration : 0;

  if (summaryMode) {
    const output = {
      videoId,
      url: `https://www.youtube.com/watch?v=${videoId}`,
      language: lang,
      segmentCount: segments.length,
      durationSeconds: Math.round(durationMs / 1000),
      transcript: fullText.slice(0, 4000) + (fullText.length > 4000 ? "... [truncated]" : ""),
    };
    console.log(JSON.stringify(output, null, 2));
  } else {
    const output = {
      videoId,
      url: `https://www.youtube.com/watch?v=${videoId}`,
      language: lang,
      segmentCount: segments.length,
      durationSeconds: Math.round(durationMs / 1000),
      transcript: fullText,
      segments: segments.map(s => ({
        time: formatTime(s.offset),
        text: s.text.replace(/\n/g, " ").trim(),
      })),
    };
    console.log(JSON.stringify(output, null, 2));
  }
}

main().catch(e => {
  console.error(JSON.stringify({ error: e.message, input }, null, 2));
  process.exit(1);
});
