# Self-Diagnosis Reference

Analyze agent memory health across the fleet.

## Usage

```bash
lettactl report memory                  # Basic usage stats
lettactl report memory --analyze        # LLM-powered deep analysis
lettactl report memory --analyze --confirm  # Skip confirmation
lettactl report memory -o json          # JSON output
```

## Basic Report

Shows per-agent memory block fill percentages:

- Green: <50% full
- Yellow: 50–79% full
- Red: 80%+ full

## LLM-Powered Analysis

With `--analyze`, each agent analyzes its own memory and reports:

- **TOPICS**: Count of distinct topics in memory
- **STATUS**: Overall health assessment
- **SPLIT**: Recommendation to split the block if too large
- **SUMMARY**: What the memory contains
- **STALE**: Detection of outdated information
- **MISSING**: Knowledge gaps identified

Fleet-wide analysis runs 5 agents concurrently.

## Options

| Flag | Description |
|------|-------------|
| `--analyze` | Enable LLM-powered deep analysis |
| `--confirm` | Skip confirmation prompt for bulk |
| `-o json` | JSON output |
