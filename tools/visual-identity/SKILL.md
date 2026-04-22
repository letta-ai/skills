---
name: "visual-identity"
description: "Build and maintain a persistent visual identity for your agent using Flux Kontext Pro. Use when the user asks the agent to generate selfies, avatars, character art, or any image that should look like the same person across generations."
---

# Visual Identity

Build a persistent visual identity that stays consistent across sessions. Supports OpenAI (gpt-image-1) and Flux Kontext Pro.

Two workflows:

1. **Visual identity** (primary): Establish a reference appearance, then generate new scenes that preserve the same face and features. Identity persists in the agent's memory across sessions.
2. **Text-to-image** (secondary): One-off image generation from a text prompt, no identity persistence.

## When to use

- The user asks "show me what you look like" or wants agent selfies
- The user wants an avatar, profile picture, or character art
- The user wants to create a visual identity (a consistent character across scenes)
- The user provides a reference photo and wants variations or new scenes
- The user asks you to generate or create any image

## Environment

The script auto-detects which provider to use based on environment variables:

| Priority | Env var | Provider | Notes |
|----------|---------|----------|-------|
| 1st | `OPENAI_API_KEY` | OpenAI gpt-image-1 | Recommended. Most users already have this. |
| 2nd | `BFL_API_KEY` | Flux Kontext Pro | Better face consistency. Requires BFL account. |

You can override with `--provider openai` or `--provider flux`.

If neither key is set, guide the user:
- **OpenAI** (recommended): They likely already have an `OPENAI_API_KEY` set. If not, https://platform.openai.com/api-keys
- **Flux**: https://api.bfl.ai to create an account, keys at https://api.bfl.ai/auth/login, credits at https://api.bfl.ai/credits

Never ask the user to paste the full key in chat.

## Dependencies

Install if missing (prefer `uv`):

```bash
uv pip install requests Pillow
```

If `uv` is unavailable:

```bash
pip3 install requests Pillow
```

## Workflow 1: Visual Identity (Character Consistency)

This is the primary workflow. The goal is to establish a reference appearance and then generate new scenes that preserve the same face, bone structure, and features.

### Step 1: Establish the reference

Either the user provides a photo, or you generate a base character:

**Option A -- User provides a reference photo:**
The user pastes or specifies an image file. Save it to the persistent identity directory (see "Persisting Visual Identity" below).

**Option B -- Generate a base character from text:**
Use text-to-image to create the initial character. Be very specific about physical features. Example prompt:

> A portrait of a young woman with shoulder-length auburn hair, green eyes, light freckles, wearing a black leather jacket. Clean background, studio lighting, 3:4 portrait.

Save the result as the reference image.

### Step 2: Generate scenes with the reference

Pass the reference image as base64-encoded `input_image`:

```bash
python3 <path-to-skill>/scripts/generate_image.py edit \
  --reference /path/to/canonical.jpg \
  --prompt "The same person is sitting at a desk coding late at night, lit by monitor glow" \
  --out /tmp/identity_coding.jpg
```

### Step 3: Anchor the prompt

Always include an identity-anchoring phrase in every prompt that uses a reference. This tells the model to preserve facial features:

> Keep his/her exact face, bone structure, eye color, and hair.

Or more naturally woven into the prompt:

> The same man is relaxing on a tropical beach at sunset, wearing a linen shirt. Golden hour lighting. Keep his exact face, bone structure, eye color, and hair.

### Step 4: Iterate with the user

- Show each result and ask for feedback
- Adjust scene, clothing, lighting, or setting based on feedback
- Always reuse the same reference image for consistency
- If the user wants to change the base appearance, go back to Step 1

### Example session flow

1. User: "Create a visual identity for me -- here's my photo"
2. Agent: Saves reference, generates 2-3 scenes (beach, office, hiking)
3. User: "I like the beach one but make me wearing a hat"
4. Agent: Regenerates beach scene with hat, same reference
5. User: "Now make one of me cooking"
6. Agent: New scene with same reference

## Persisting Visual Identity

Two things persist across sessions: the reference image (binary) and the identity metadata (markdown). They live in different places.

### Reference image: agent data directory

Save the canonical reference image to `~/.letta/agents/$AGENT_ID/reference/visual-identity/canonical.jpg`. This is outside memfs because binary images would bloat the git-backed memory repo. The `reference/` directory persists across sessions.

```bash
mkdir -p ~/.letta/agents/$AGENT_ID/reference/visual-identity
cp /tmp/generated_portrait.jpg ~/.letta/agents/$AGENT_ID/reference/visual-identity/canonical.jpg
```

### Identity metadata: memfs

After establishing a visual identity, create a memory file at `reference/visual-identity.md` in the agent's memory filesystem. This syncs via git like all other memory files.

Use the Memory tool to create it:

```
memory(command="create", reason="Store visual identity metadata",
  file_path="reference/visual-identity.md",
  description="Agent's persistent visual identity -- reference image path and appearance description.",
  file_text="## Reference Image\n~/.letta/agents/$AGENT_ID/reference/visual-identity/canonical.jpg\n\n## Appearance\n- Hair: shoulder-length auburn, slight wave\n- Eyes: green\n- Skin: light with freckles\n- Build: athletic\n- Distinguishing: small scar above left eyebrow\n\n## Anchoring Phrase\nKeep the exact same face, bone structure, eye color, and hair from the reference image.\n\n## History\n- Established: 2026-04-15\n- User feedback: \"make the hair a bit darker\" -> regenerated, approved")
```

### Auto-detect on load

When this skill is loaded, check the agent's memory tree for `reference/visual-identity.md`. If it exists:

- The agent already has an established identity
- Use the stored reference image path for all image generation requests
- Prepend the stored anchoring phrase to every prompt
- Do not ask the user to re-establish their identity

If it does not exist, the agent has no visual identity yet. Offer to create one if the user asks for images.

### Updating the identity

If the user wants to change their visual identity:

1. Generate or receive the new reference image
2. Overwrite `canonical.jpg` in the reference directory
3. Update the memory file with new appearance details
4. Note the change in the History section

## Workflow 2: Text-to-Image

For one-off image generation that does not need identity persistence.

```bash
python3 <path-to-skill>/scripts/generate_image.py generate \
  --prompt "A corgi wearing a tiny space helmet on the moon" \
  --out /tmp/corgi_moon.jpg
```

Or inline with `requests` (OpenAI):

```python
import requests, base64, os

resp = requests.post(
    "https://api.openai.com/v1/images/generations",
    headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-image-1",
        "prompt": "A corgi wearing a tiny space helmet on the moon",
        "n": 1,
        "size": "1024x1024",
        "quality": "medium",
    },
).json()

img = base64.b64decode(resp["data"][0]["b64_json"])
with open("/tmp/corgi_moon.png", "wb") as f:
    f.write(img)
```

## Parameters

| Parameter | Values | Default | Provider | Notes |
|-----------|--------|---------|----------|-------|
| `--prompt` | string | required | Both | Scene description |
| `--reference` | file path | none | Both | Reference photo for identity mode (edit only) |
| `--provider` | `openai`, `flux` | auto | Both | Override provider auto-detection |
| `--aspect-ratio` | `1:1`, `3:4`, `4:3`, `16:9`, `9:16` | `3:4` | Both | Use `3:4` for portraits |
| `--output-format` | `png`, `jpeg`, `webp` | `png` | Both | |
| `--quality` | `low`, `medium`, `high` | `medium` | OpenAI | Image quality |
| `--seed` | integer | random | Flux | Fix for reproducible results |
| `--safety-tolerance` | 0-6 | 2 | Flux | Higher = more permissive |
| `--guidance` | 1.5-100 | varies | Flux | Prompt adherence strength |

## Prompting best practices

- Be specific about physical setting, lighting, clothing, and pose
- For portraits, specify aspect ratio `3:4` or `4:3`
- For landscapes/scenes, use `16:9`
- Include lighting direction: "golden hour", "studio lighting", "neon-lit"
- Describe clothing and accessories explicitly
- For identity mode, always include the anchoring phrase about preserving facial features
- Avoid contradicting the reference photo (e.g., don't say "blonde hair" if the reference has dark hair)

## Rate limits and costs

- Maximum 6 concurrent requests per API key
- Queue times: typically 4-10 seconds, can spike to 2+ minutes under load
- If a request stays in `Pending` for over 120 seconds, retry once
- Polling interval: 2 seconds is sufficient
- Download URLs in the `Ready` response are signed and expire; save images immediately

## CLI reference

Full CLI documentation: `references/api.md`

Common commands:

```bash
# Text-to-image
python3 <path-to-skill>/scripts/generate_image.py generate \
  --prompt "..." --out output.jpg

# Reference-based editing (visual identity)
python3 <path-to-skill>/scripts/generate_image.py edit \
  --reference photo.jpg --prompt "..." --out output.jpg

# Dry run (show request without sending)
python3 <path-to-skill>/scripts/generate_image.py generate \
  --prompt "..." --dry-run

# Custom aspect ratio and seed
python3 <path-to-skill>/scripts/generate_image.py generate \
  --prompt "..." --aspect-ratio 16:9 --seed 42 --out wide.jpg
```

## Error handling

**OpenAI:**
- `HTTP 400/422`: Usually a malformed request or content policy violation
- `HTTP 429`: Rate limited -- wait and retry
- Missing `OPENAI_API_KEY`: Guide the user to https://platform.openai.com/api-keys

**Flux:**
- `Insufficient credits`: Direct user to https://api.bfl.ai/credits
- `HTTP 422`: Usually a malformed request -- check prompt and parameters
- `Pending` timeout: Retry the request; the queue may be congested
- Missing `BFL_API_KEY`: Guide the user to https://api.bfl.ai

**Both:**
- Image too large for base64: Resize to under 10MB before encoding
- No API key found: See Environment section
