# Flux Kontext Pro API Reference

## Endpoint

```
POST https://api.bfl.ai/v1/flux-kontext-pro
```

## Authentication

All requests require the `x-key` header with a valid BFL API key.

```
x-key: bfl_...
```

## Request body (JSON)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompt` | string | yes | -- | Text description of the image to generate |
| `input_image` | string | no | -- | Base64-encoded reference image for editing/identity mode |
| `aspect_ratio` | string | no | `1:1` | One of: `1:1`, `3:4`, `4:3`, `16:9`, `9:16` |
| `output_format` | string | no | `jpeg` | One of: `jpeg`, `png` |
| `seed` | integer | no | random | Seed for reproducible generations |
| `safety_tolerance` | integer | no | 2 | Range 0-6. Higher values are more permissive |
| `guidance` | float | no | varies | Prompt adherence strength. Range 1.5-100 |

## Response (submit)

```json
{
  "id": "7e08b0f7-210e-4ab6-a637-9905cfb36ed3",
  "polling_url": "https://api.bfl.ai/v1/get_result"
}
```

## Polling

```
GET {polling_url}?id={request_id}
```

Headers: `x-key: bfl_...`

### Poll response (pending)

```json
{
  "id": "7e08b0f7-...",
  "status": "Pending"
}
```

### Poll response (ready)

```json
{
  "id": "7e08b0f7-...",
  "status": "Ready",
  "result": {
    "sample": "https://delivery-prod.bfl.ai/...",
    "prompt": "..."
  }
}
```

The `sample` URL is a signed download link. It expires; save the image immediately.

## Status values

| Status | Meaning |
|--------|---------|
| `Pending` | Queued or in progress |
| `Ready` | Generation complete, download available |
| `Error` | Generation failed |

## Timing

- Text-to-image: typically 4-6 seconds
- Reference-based editing: typically 4-10 seconds
- Queue delays can push requests to 2+ minutes under load
- Recommended poll interval: 2 seconds

## Rate limits

- Maximum 6 concurrent requests per API key
- Exceeding this causes requests to queue, not fail
- No explicit requests-per-minute cap documented

## Image size constraints

- `input_image` should be under 10MB when base64-encoded
- Output dimensions are determined by `aspect_ratio`, not explicitly controllable
- Typical output: ~880x1184 for 3:4, ~1184x880 for 4:3

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Insufficient credits` | Account has no credits | Add credits at https://api.bfl.ai/credits |
| HTTP 422 | Malformed request body | Check required fields and value ranges |
| HTTP 401 | Invalid or missing API key | Verify `BFL_API_KEY` |
| Permanent `Pending` | Congestion or server issue | Retry after 120 seconds |

## CLI commands

### Text-to-image

```bash
python3 scripts/flux_image.py generate \
  --prompt "A cat astronaut floating in space" \
  --aspect-ratio 1:1 \
  --out /tmp/cat_space.jpg
```

### Reference-based editing

```bash
python3 scripts/flux_image.py edit \
  --reference /tmp/my_photo.jpg \
  --prompt "The same person hiking on a mountain trail at sunrise. Keep their exact face, bone structure, eye color, and hair." \
  --aspect-ratio 3:4 \
  --out /tmp/hiking.jpg
```

### Dry run

```bash
python3 scripts/flux_image.py generate \
  --prompt "..." \
  --dry-run
```

### With fixed seed

```bash
python3 scripts/flux_image.py generate \
  --prompt "..." \
  --seed 42 \
  --out /tmp/reproducible.jpg
```
