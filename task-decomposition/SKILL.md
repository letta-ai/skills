---
name: task-decomposition
description: Break a large or vague task into file-level Asana subtasks with scaffold custom fields
triggers:
  - "decompose this task"
  - "break this down"
  - "task decomposition"
  - "split into subtasks"
tools_required:
  - Bash
  - Read
  - Grep
  - Glob
  - Task
  - TodoWrite
---

# Task Decomposition Skill

Break large, module-level, or vague tasks into concrete file-level subtasks that autonomous
agents can execute independently. Each subtask targets specific files, has clear acceptance
criteria, and is scoped to 30 min - 2 hr of work.

Subtasks are created as Asana tasks in the Crucible Task Queue with all required custom fields
(execution_status, effort, project, task_type, validation_status, source_agent) so the
meta-orchestrator can dispatch them to the correct agent automatically.

## When to Use

- A task touches multiple files or modules and is too broad for a single executor
- A task description is vague and needs concrete file targets before execution
- An XL or L effort task needs splitting into S/M subtasks
- System 5 auto-decomposes after 5+ failed attempts on a task

## Input

The user provides one of:
1. An Asana task URL or GID
2. A task description (free text)
3. A feature request or bug report

## Workflow

Follow `prompts/decompose.md` for the full decomposition algorithm.

**Quick summary:**
1. **Understand** - Parse the task, identify the target project and repo
2. **Scan** - Find affected files using Grep/Glob, read key files
3. **Map dependencies** - Determine which changes depend on others
4. **Decompose** - Break into 3-8 file-level subtasks with targets and criteria
5. **Create in Asana** - File subtasks with proper custom fields and parent linkage

## Output

3-8 Asana subtasks under the parent task, each with:
- **Title**: `[project] Short action description` (e.g., `[scaffold] Add validation to task_executor.py`)
- **Files**: Specific file paths listed in the task notes
- **Acceptance Criteria**: Testable conditions in the task notes
- **Custom Fields**: execution_status=Pending, effort=S/M, project, task_type, validation_status=Approved

## Constraints

- Each subtask MUST target a specific file or small set of files (max 3)
- Each subtask MUST have <50 line changes expected
- Each subtask MUST be completable in 30 min - 2 hr
- Dependencies MUST form a DAG (no circular dependencies)
- Subtasks MUST be independently verifiable
- Total subtask count: 3-8 (fewer is better)
