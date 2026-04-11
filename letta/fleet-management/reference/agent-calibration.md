# Agent Calibration Reference

Prime agents with a boot message on creation, and recalibrate after updates.

## First Message

The `first_message` field sends a message to the agent on first creation only (never on updates). Used to make agents internalize their role.

```yaml
agents:
  - name: support-agent
    first_message: "Review your persona block and confirm you understand your role."
```

The message is sent asynchronously after creation.

## Recalibration

After updating agent config, recalibrate to re-prime agents:

```bash
# Recalibrate all changed agents
lettactl apply -f fleet.yaml --recalibrate

# Custom message
lettactl apply -f fleet.yaml --recalibrate --recalibrate-message "Review updated guidelines."

# Scope by tags
lettactl apply -f fleet.yaml --recalibrate --recalibrate-tags "role:support"

# Scope by pattern
lettactl apply -f fleet.yaml --recalibrate --recalibrate-match "support-*"

# Fire-and-forget
lettactl apply -f fleet.yaml --recalibrate --no-wait
```

## SDK

```typescript
await ctl.bulkSendMessage('Review your updated configuration.', {
  pattern: 'support-*',
});
```

## Options

| Flag | Description |
|------|-------------|
| `--skip-first-message` | Skip first_message on creation |
| `--recalibrate` | Re-send calibration messages |
| `--recalibrate-message <msg>` | Custom calibration message |
| `--recalibrate-tags <tags>` | Scope by tags (AND logic) |
| `--recalibrate-match <pattern>` | Scope by glob pattern |
| `--no-wait` | Fire-and-forget |

## Retraining vs Recalibration

- **Recalibrate**: Send a message in-place, preserves conversation history
- **Retrain**: Delete and redeploy for a fresh start (`lettactl delete agent <name>` then `lettactl apply`)
