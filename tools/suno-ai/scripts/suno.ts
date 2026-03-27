#!/usr/bin/env npx tsx

/**
 * Suno AI CLI - Generate music, lyrics, and process audio via Suno API.
 *
 * Setup: export SUNO_API_KEY=your_key
 *
 * Usage:
 *   npx tsx suno.ts generate "prompt" [options]
 *   npx tsx suno.ts lyrics "prompt"
 *   npx tsx suno.ts status <taskId>
 *   npx tsx suno.ts wait <taskId>
 *   npx tsx suno.ts extend <audioId> [options]
 *   npx tsx suno.ts separate <taskId> <audioId>
 *   npx tsx suno.ts wav <taskId> <audioId>
 *   npx tsx suno.ts credits
 */

const API_BASE = "https://api.sunoapi.org/api/v1";
const API_KEY = process.env.SUNO_API_KEY;

if (!API_KEY) {
  console.error("Error: SUNO_API_KEY environment variable is required.");
  console.error("Get your key from https://sunoapi.org");
  process.exit(1);
}

const headers = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

async function apiPost(endpoint: string, body: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

async function apiGet(endpoint: string) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// --- Commands ---

async function generate(args: string[]) {
  const prompt = args[0];
  if (!prompt) {
    console.error("Usage: suno.ts generate <prompt> [--instrumental] [--custom --title <t> --style <s>] [--model <m>]");
    process.exit(1);
  }

  const instrumental = args.includes("--instrumental");
  const custom = args.includes("--custom");
  const model = getFlagValue(args, "--model") || "V4_5ALL";
  const title = getFlagValue(args, "--title");
  const style = getFlagValue(args, "--style");

  const body: Record<string, unknown> = {
    prompt,
    customMode: custom,
    instrumental,
    model,
  };

  if (custom) {
    if (!title || !style) {
      console.error("Custom mode requires --title and --style flags.");
      process.exit(1);
    }
    body.title = title;
    body.style = style;
  }

  const result = await apiPost("/generate", body);
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.taskId) {
    console.log(`\nTask ID: ${result.data.taskId}`);
    console.log(`Check status: npx tsx suno.ts status ${result.data.taskId}`);
    console.log(`Wait for completion: npx tsx suno.ts wait ${result.data.taskId}`);
  }
}

async function lyrics(args: string[]) {
  const prompt = args[0];
  if (!prompt) {
    console.error("Usage: suno.ts lyrics <prompt>");
    process.exit(1);
  }

  const result = await apiPost("/lyrics", { prompt });
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.taskId) {
    console.log(`\nTask ID: ${result.data.taskId}`);
    console.log(`Wait for completion: npx tsx suno.ts wait ${result.data.taskId}`);
  }
}

async function status(args: string[]) {
  const taskId = args[0];
  if (!taskId) {
    console.error("Usage: suno.ts status <taskId>");
    process.exit(1);
  }

  const result = await apiGet(`/generate/record-info?taskId=${taskId}`);
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.status === "SUCCESS" && result.data?.response?.data) {
    console.log("\n--- Generated Tracks ---");
    for (const track of result.data.response.data) {
      console.log(`  Title: ${track.title || "Untitled"}`);
      console.log(`  Duration: ${track.duration}s`);
      console.log(`  Audio: ${track.audio_url}`);
      if (track.video_url) console.log(`  Video: ${track.video_url}`);
      console.log(`  ID: ${track.id}`);
      console.log();
    }
  }
}

async function wait(args: string[]) {
  const taskId = args[0];
  const maxWait = parseInt(getFlagValue(args, "--timeout") || "600", 10);

  if (!taskId) {
    console.error("Usage: suno.ts wait <taskId> [--timeout <seconds>]");
    process.exit(1);
  }

  const start = Date.now();
  const pollInterval = 15_000; // 15 seconds

  console.log(`Waiting for task ${taskId} (timeout: ${maxWait}s)...`);

  while ((Date.now() - start) / 1000 < maxWait) {
    const result = await apiGet(`/generate/record-info?taskId=${taskId}`);
    const taskStatus = result.data?.status;

    if (taskStatus === "SUCCESS") {
      console.log("\nGeneration complete!");
      console.log(JSON.stringify(result, null, 2));

      if (result.data?.response?.data) {
        console.log("\n--- Generated Tracks ---");
        for (const track of result.data.response.data) {
          console.log(`  Title: ${track.title || "Untitled"}`);
          console.log(`  Duration: ${track.duration}s`);
          console.log(`  Audio: ${track.audio_url}`);
          if (track.video_url) console.log(`  Video: ${track.video_url}`);
          console.log(`  ID: ${track.id}`);
          console.log();
        }
      }
      return;
    }

    if (taskStatus === "FAILED") {
      console.error("\nGeneration failed!");
      console.log(JSON.stringify(result, null, 2));
      process.exit(1);
    }

    const elapsed = Math.round((Date.now() - start) / 1000);
    process.stdout.write(`\r  Status: ${taskStatus || "PENDING"} (${elapsed}s elapsed)`);
    await new Promise((r) => setTimeout(r, pollInterval));
  }

  console.error(`\nTimeout after ${maxWait}s. Task may still be processing.`);
  console.error(`Check manually: npx tsx suno.ts status ${taskId}`);
  process.exit(1);
}

async function extend(args: string[]) {
  const audioId = args[0];
  if (!audioId) {
    console.error("Usage: suno.ts extend <audioId> [--prompt <p>] [--continue-at <seconds>] [--model <m>]");
    process.exit(1);
  }

  const prompt = getFlagValue(args, "--prompt") || "";
  const continueAt = parseInt(getFlagValue(args, "--continue-at") || "0", 10);
  const model = getFlagValue(args, "--model") || "V4_5ALL";
  const defaultParams = !getFlagValue(args, "--prompt");

  const body: Record<string, unknown> = {
    audioId,
    defaultParamFlag: defaultParams,
    model,
  };

  if (prompt) body.prompt = prompt;
  if (continueAt > 0) body.continueAt = continueAt;

  const result = await apiPost("/generate/extend", body);
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.taskId) {
    console.log(`\nTask ID: ${result.data.taskId}`);
    console.log(`Wait: npx tsx suno.ts wait ${result.data.taskId}`);
  }
}

async function separate(args: string[]) {
  const taskId = args[0];
  const audioId = args[1];
  if (!taskId || !audioId) {
    console.error("Usage: suno.ts separate <taskId> <audioId>");
    process.exit(1);
  }

  const result = await apiPost("/vocal-removal/generate", { taskId, audioId });
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.taskId) {
    console.log(`\nTask ID: ${result.data.taskId}`);
    console.log(`Wait: npx tsx suno.ts wait ${result.data.taskId}`);
  }
}

async function wav(args: string[]) {
  const taskId = args[0];
  const audioId = args[1];
  if (!taskId || !audioId) {
    console.error("Usage: suno.ts wav <taskId> <audioId>");
    process.exit(1);
  }

  const result = await apiPost("/wav/generate", { taskId, audioId });
  console.log(JSON.stringify(result, null, 2));

  if (result.data?.taskId) {
    console.log(`\nTask ID: ${result.data.taskId}`);
    console.log(`Wait: npx tsx suno.ts wait ${result.data.taskId}`);
  }
}

async function credits() {
  const result = await apiGet("/get-credits");
  console.log(JSON.stringify(result, null, 2));
  if (result.data?.credits !== undefined) {
    console.log(`\nRemaining credits: ${result.data.credits}`);
  }
}

// --- Helpers ---

function getFlagValue(args: string[], flag: string): string | undefined {
  const idx = args.indexOf(flag);
  if (idx !== -1 && idx + 1 < args.length) {
    return args[idx + 1];
  }
  return undefined;
}

function printHelp() {
  console.log(`Suno AI CLI - Generate music, lyrics, and process audio

Usage:
  npx tsx suno.ts <command> [args] [options]

Commands:
  generate <prompt>     Generate music from a text description
    --instrumental      Generate without vocals
    --custom            Enable custom mode (requires --title and --style)
    --title <title>     Song title (custom mode)
    --style <style>     Music style (custom mode)
    --model <model>     Model version: V4, V4_5, V4_5PLUS, V4_5ALL (default), V5

  lyrics <prompt>       Generate lyrics only (no audio)

  status <taskId>       Check task status

  wait <taskId>         Poll until task completes
    --timeout <secs>    Max wait time in seconds (default: 600)

  extend <audioId>      Extend an existing track
    --prompt <text>     Description for the extension
    --continue-at <s>   Timestamp in seconds to continue from
    --model <model>     Model version

  separate <taskId> <audioId>   Separate vocals from instrumentals
  wav <taskId> <audioId>        Convert track to WAV format
  credits                       Check remaining API credits

Environment:
  SUNO_API_KEY          Required. Get from https://sunoapi.org

Examples:
  npx tsx suno.ts generate "A chill lo-fi beat with piano and rain sounds"
  npx tsx suno.ts generate "Love song" --custom --title "Forever" --style "R&B" --model V5
  npx tsx suno.ts generate "Epic orchestral" --instrumental
  npx tsx suno.ts lyrics "A breakup song about letting go"
  npx tsx suno.ts wait suno_task_abc123
  npx tsx suno.ts credits`);
}

// --- Main ---

const command = process.argv[2];
const args = process.argv.slice(3);

switch (command) {
  case "generate":
    generate(args);
    break;
  case "lyrics":
    lyrics(args);
    break;
  case "status":
    status(args);
    break;
  case "wait":
    wait(args);
    break;
  case "extend":
    extend(args);
    break;
  case "separate":
    separate(args);
    break;
  case "wav":
    wav(args);
    break;
  case "credits":
    credits();
    break;
  case "--help":
  case "-h":
  case "help":
  case undefined:
    printHelp();
    break;
  default:
    console.error(`Unknown command: ${command}`);
    printHelp();
    process.exit(1);
}
