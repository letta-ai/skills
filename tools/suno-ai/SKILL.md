---
name: suno-ai
description: Generate AI music, lyrics, and audio processing via Suno API. Create songs from text descriptions, generate lyrics, extend tracks, separate vocals, and convert audio formats. Use when the user wants to create music, generate song lyrics, or process audio.
---

# Suno AI

Generate music, lyrics, and process audio using the Suno API.

## When to Use

- User wants to create music from a text description
- Need to generate song lyrics
- Want to extend an existing track
- Need vocal/instrument separation
- Want to convert audio to WAV format
- Creating music videos or cover art

## Setup

Requires `SUNO_API_KEY` environment variable. Get one from [sunoapi.org](https://sunoapi.org).

## Quick Operations

### Generate music from a prompt
```bash
npx tsx scripts/suno.ts generate "A peaceful acoustic guitar melody with soft vocals, folk style"
```

### Generate instrumental only
```bash
npx tsx scripts/suno.ts generate "Ambient electronic with soft pads" --instrumental
```

### Generate with custom mode (title + style)
```bash
npx tsx scripts/suno.ts generate "Lyrics here or description" --custom --title "My Song" --style "Jazz"
```

### Choose a model
```bash
npx tsx scripts/suno.ts generate "A rock anthem" --model V5
```

### Generate lyrics only
```bash
npx tsx scripts/suno.ts lyrics "A song about overcoming challenges"
```

### Check task status
```bash
npx tsx scripts/suno.ts status <task-id>
```

### Wait for completion (polls until done)
```bash
npx tsx scripts/suno.ts wait <task-id>
```

### Extend an existing track
```bash
npx tsx scripts/suno.ts extend <audio-id> --prompt "Continue with a guitar solo" --continue-at 120
```

### Separate vocals from a track
```bash
npx tsx scripts/suno.ts separate <task-id> <audio-id>
```

### Convert to WAV
```bash
npx tsx scripts/suno.ts wav <task-id> <audio-id>
```

### Check remaining credits
```bash
npx tsx scripts/suno.ts credits
```

## Models

| Model | Max Duration | Notes |
|-------|-------------|-------|
| `V4` | 4 min | Highest audio quality |
| `V4_5` | 8 min | Advanced features, smarter prompts |
| `V4_5PLUS` | 8 min | Richer, more musical sound |
| `V4_5ALL` | 8 min | Better song structure (default) |
| `V5` | 8 min | Fastest generation, superior musicality |

## Prompt Tips

- Describe musical style and genre explicitly
- Include mood and atmosphere ("melancholy", "upbeat", "dreamy")
- Specify instruments ("acoustic guitar", "synth pads", "piano")
- Add vocal style ("soft female vocals", "raspy male voice", "choir")
- Mention tempo ("slow ballad", "upbeat dance", "moderate groove")
- V4 prompts: max 3000 chars. V4_5+: max 5000 chars.

## Typical Workflow

1. **Generate lyrics** with `lyrics` command (optional)
2. **Generate music** with `generate` command using the lyrics or a description
3. **Wait** for the task with `wait` command
4. **Extend** the track if you want it longer
5. **Separate** vocals if you need stems
6. **Convert** to WAV for high-quality output

## Notes

- Generation typically takes 1-3 minutes
- Each generation produces 2 tracks to choose from
- Audio files are stored for 15 days, then auto-deleted
- Download important files promptly
- Custom mode requires both `--title` and `--style` flags
