---
name: claudemd-generator
description: Generate a comprehensive CLAUDE.md for any project by scanning the codebase
triggers:
  - "generate claude md"
  - "generate claudemd"
  - "create claude md"
  - "create claudemd"
  - "write claude md"
  - "claudemd generator"
tools_required:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# CLAUDE.md Generator Skill

Scans a codebase and generates a comprehensive CLAUDE.md file (100-200 lines) that serves as
the source of truth for all future AI-assisted sessions on the project.

Analyzes package configs, directory structure, CI workflows, environment variables, test setup,
git history, and key source files to produce a complete project guide.

See `prompts/generate-prompt.md` for the full generation prompt.
