# Canary Deployments Reference

Test configuration changes on isolated copies before promoting to production.

## Workflow

```bash
# 1. Deploy canary copies
lettactl apply -f fleet.yaml --canary

# 2. Test the canary agents
lettactl send CANARY-support-agent "Test message"

# 3. Promote to production
lettactl apply -f fleet.yaml --promote

# 4. Clean up canary agents
lettactl apply -f fleet.yaml --cleanup
```

## How It Works

- `--canary` creates copies with a `CANARY-` prefix (e.g., `CANARY-support-agent`)
- Canary agents get their own isolated memory blocks and conversation history
- Shared blocks, folders, and tools are reused (not duplicated)
- Canary metadata stored on agents: `lettactl.canary`, `lettactl.canary.productionName`, `lettactl.canary.prefix`, `lettactl.canary.createdAt`

## Options

| Flag | Description |
|------|-------------|
| `--canary` | Deploy isolated canary copies |
| `--canary-prefix <str>` | Custom prefix (default: `CANARY-`) |
| `--promote` | Apply canary config to production agents |
| `--cleanup` | Remove canary agents |

## Custom Prefix

```bash
lettactl apply -f fleet.yaml --canary --canary-prefix "STAGING-"
# Creates: STAGING-support-agent
```

## Rollback

If the canary fails, skip promote and clean up:

```bash
lettactl apply -f fleet.yaml --cleanup
```

For full rollback after promote: revert in git and redeploy.
