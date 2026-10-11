# RLM: Recursive Language Models

Use the RLM pattern when a task requires processing more content than fits in your context window, or when you need to analyze an entire codebase, directory, or large document.

## The Pattern

**DON'T** try to read large inputs directly into your context. Treat them as external data.

**DO** follow this workflow:

1. **Get metadata first** - understand the scope before processing
2. **Decide a chunking strategy** - based on the metadata
3. **Write prompt files** - one per chunk, each containing the chunk content + the task
4. **Fan out with rlm-batch** - process all chunks in parallel
5. **Collect results** - read all output files
6. **Aggregate findings** - merge, deduplicate, and produce final report

## Tool Reference

### rlm-query

Run a single sub-agent with a prompt file.

```bash
rlm-query <prompt.md> <output.out> [timeout]
```

**Parameters:**
- `prompt.md` - Path to markdown file containing the prompt and data
- `output.out` - Path where the sub-agent's output will be written
- `timeout` - Optional timeout in seconds (default: from RLM_TIMEOUT env var)

**Example:**
```bash
rlm-query /tmp/prompts/analyze_file_1.md /tmp/results/file_1.out 120
```

### rlm-batch

Fan out multiple sub-agents in parallel.

```bash
rlm-batch <prompt_dir/> <output_dir/> [timeout]
```

**Parameters:**
- `prompt_dir/` - Directory containing prompt markdown files
- `output_dir/` - Directory where output files will be written (created if needed)
- `timeout` - Optional timeout in seconds per sub-agent (default: from RLM_TIMEOUT env var)

**Behavior:**
- Processes all `.md` files in `prompt_dir/`
- Creates matching `.out` files in `output_dir/` (e.g., `chunk_1.md` → `chunk_1.out`)
- Runs up to `RLM_MAX_PARALLEL` sub-agents concurrently
- Blocks until all sub-agents complete or timeout

**Example:**
```bash
rlm-batch /tmp/rlm-todo/prompts /tmp/rlm-todo/results 120
```

### Environment Variables

- `RLM_MAX_DEPTH` - Maximum recursion depth (default: 3)
- `RLM_MAX_PARALLEL` - Maximum concurrent sub-agents (default: 5)
- `RLM_TIMEOUT` - Default timeout per sub-agent in seconds (default: 1200)

## Chunking Strategies

Choose your chunking strategy based on the data structure:

### 1. By File
**Use when:** Analyzing a codebase or directory of files
**Strategy:** One prompt per source file
**Best for:** Finding patterns across files, analyzing individual modules

### 2. By Line Range
**Use when:** Processing a single large file
**Strategy:** Split into N-line chunks (e.g., 1000 lines per chunk)
**Best for:** Log files, large data files, transcripts

### 3. By Directory
**Use when:** Analyzing a hierarchical project structure
**Strategy:** One prompt per module/package/subdirectory
**Best for:** Architecture analysis, dependency mapping

### 4. By Semantic Unit
**Use when:** Processing structured documents
**Strategy:** Split on headers, sections, or natural boundaries
**Best for:** Documentation, markdown files, structured text

## Prompt File Format

Each prompt file should be self-contained and include:

1. **Task description** - What to find/analyze
2. **Context** - Which chunk this is (e.g., "chunk 3 of 10")
3. **The data** - The actual content to process
4. **Output format** - Specify structured output (JSON recommended)

**Template:**

```markdown
# Task: [what to find/analyze]
# Context: chunk {i} of {n}, file: {filename}

Analyze the following and output ONLY a JSON object with your findings:

```
[chunk content here]
```

Output format: {"findings": [...], "summary": "..."}
```

**Key principles:**
- Make each prompt self-contained (don't rely on previous context)
- Request structured output (JSON) for easy aggregation
- Include enough context so the sub-agent understands its role
- Be specific about the output format to simplify parsing

## Aggregation Patterns

After `rlm-batch` completes, aggregate the results:

```bash
# Read all output files
for file in /tmp/results/*.out; do
    cat "$file"
done

# Parse JSON and merge (example with Python)
python3 -c "
import sys, json, glob

all_findings = []
for outfile in glob.glob('/tmp/results/*.out'):
    with open(outfile) as f:
        try:
            data = json.load(f)
            all_findings.extend(data.get('findings', []))
        except:
            pass

# Deduplicate and sort
unique_findings = list(set(all_findings))
unique_findings.sort()

print(json.dumps({'total': len(unique_findings), 'findings': unique_findings}, indent=2))
"
```

## Worked Example: Finding TODO Comments

Let's find all TODO/FIXME/HACK comments in a Python codebase.

### Step 1: Get Metadata

```bash
# Count Python files
find . -name "*.py" | wc -l
# Output: 200 files

# Spot check a few files
head -20 ./src/main.py
```

### Step 2: Write Prompt Files

```bash
# Create directories
mkdir -p /tmp/rlm-todo/prompts /tmp/rlm-todo/results

# Generate one prompt per file
for f in $(find . -name "*.py"); do
    # Create safe filename
    name=$(echo "$f" | tr '/' '_' | sed 's/^\._//')

    # Write prompt file
    cat > "/tmp/rlm-todo/prompts/${name}.md" << EOF
# Task: Find all TODO/FIXME/HACK comments
# File: $f

Scan the following Python code and find all comments containing TODO, FIXME, or HACK.

\`\`\`python
$(cat "$f")
\`\`\`

Output a JSON array of objects with this format:
[{"line": N, "text": "...", "type": "TODO|FIXME|HACK"}]

If no comments found, output: []
EOF
done

# Verify prompt files created
ls -1 /tmp/rlm-todo/prompts/*.md | wc -l
```

### Step 3: Fan Out

```bash
# Process all files in parallel (5 at a time, 120s timeout per file)
rlm-batch /tmp/rlm-todo/prompts /tmp/rlm-todo/results 120
```

### Step 4: Aggregate Results

```bash
# Collect and merge all findings
python3 << 'EOF'
import json, glob

all_todos = []
for outfile in glob.glob('/tmp/rlm-todo/results/*.out'):
    with open(outfile) as f:
        content = f.read().strip()
        if not content:
            continue
        try:
            todos = json.loads(content)
            if isinstance(todos, list):
                all_todos.extend(todos)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse {outfile}: {e}")
            continue

# Group by type
by_type = {}
for todo in all_todos:
    todo_type = todo.get('type', 'UNKNOWN')
    by_type.setdefault(todo_type, []).append(todo)

# Report
print(f"\n=== TODO Comment Summary ===")
print(f"Total: {len(all_todos)}")
for todo_type, items in sorted(by_type.items()):
    print(f"{todo_type}: {len(items)}")

print(f"\n=== All TODOs ===")
print(json.dumps(all_todos, indent=2))
EOF
```

## Cost Awareness

**IMPORTANT:** Each `rlm-query` spawns a full Claude instance.

- 100 files × 1 sub-agent each = **100 Claude API calls**
- Each call counts toward your API quota and costs money
- Fan-out of 1000 files = 1000 API calls ≈ significant cost

**Guidelines:**

1. **Estimate before executing:**
   ```bash
   file_count=$(find . -name "*.py" | wc -l)
   echo "This will spawn $file_count sub-agents"
   ```

2. **Use mechanical tools for mechanical tasks:**
   - Use `grep` for literal string searches
   - Use `awk` for simple parsing and filtering
   - Use `find` for file listing and basic patterns
   - Save RLM for semantic analysis that requires understanding

3. **When RLM is worth it:**
   - Finding patterns that require code understanding (not literal strings)
   - Analyzing intent, bugs, or complex logic
   - Tasks that would be error-prone with regex
   - Cross-referencing or reasoning about code structure

4. **Reduce fan-out when possible:**
   - Pre-filter files with `grep` before creating prompts
   - Combine small files into larger chunks
   - Process only relevant subdirectories

## Best Practices

### ✅ DO:

- Get metadata first (`wc -l`, `ls -la`, `find | wc -l`)
- Estimate cost before fan-out
- Use structured output (JSON) for easy parsing
- Include context in each prompt (chunk N of M, filename)
- Test with a small sample first (1-2 files)
- Handle parse errors gracefully during aggregation
- Clean up temporary files after completion

### ❌ DON'T:

- Read massive files directly into context
- Spawn thousands of sub-agents without checking quota
- Use RLM for tasks that `grep`/`awk` can handle
- Forget to set appropriate timeouts
- Assume all sub-agents will succeed (handle failures)
- Leave sensitive data in prompt files

## Debugging

### Check RLM Environment

```bash
echo "RLM_MAX_DEPTH=${RLM_MAX_DEPTH:-3}"
echo "RLM_MAX_PARALLEL=${RLM_MAX_PARALLEL:-5}"
echo "RLM_TIMEOUT=${RLM_TIMEOUT:-1200}"
```

### Test Single Query

Before fan-out, test a single prompt:

```bash
# Create test prompt
cat > /tmp/test_prompt.md << 'EOF'
# Task: Count lines
Count the number of lines in the following text:

```
line 1
line 2
line 3
```

Output: {"line_count": N}
EOF

# Run single query
rlm-query /tmp/test_prompt.md /tmp/test_output.out 30

# Check result
cat /tmp/test_output.out
```

### Monitor Progress

```bash
# Watch output directory during rlm-batch
watch -n 1 'ls -1 /tmp/results/*.out 2>/dev/null | wc -l'

# Check for errors in outputs
grep -i "error\|failed\|exception" /tmp/results/*.out
```

## Common Pitfalls

1. **Context overflow in prompt files** - Even prompt files can be too large. If a single file is > 100k lines, split it further.

2. **Timeout too short** - Large files need more time. Adjust timeout based on chunk size.

3. **Malformed JSON output** - Sub-agents might return prose instead of JSON. Be defensive in parsing:
   ```python
   try:
       data = json.loads(content)
   except:
       # Try to extract JSON from prose
       import re
       match = re.search(r'\{.*\}', content, re.DOTALL)
       if match:
           data = json.loads(match.group())
   ```

4. **Filename collisions** - When converting file paths to prompt filenames, ensure uniqueness:
   ```bash
   # BAD: ./foo/bar.py and ./baz/bar.py both become bar.py.md
   # GOOD: Use full path with safe characters
   name=$(echo "$f" | tr '/' '_' | sed 's/^\._//')
   ```

5. **Resource exhaustion** - Running 1000 parallel sub-agents will likely hit system limits. The `RLM_MAX_PARALLEL` setting prevents this, but be aware of the queue depth.

## When NOT to Use RLM

- Simple file searches (use `grep`, `find`)
- Counting lines, words, files (use `wc`)
- Literal string replacement (use `sed`)
- File tree navigation (use `ls`, `tree`)
- Tasks that fit in context (just read the files directly)

RLM is for **semantic analysis at scale** - when you need Claude to understand and reason about more content than fits in one context window.

---

## Quick Reference

```bash
# Single query
rlm-query prompt.md output.out [timeout]

# Batch processing
rlm-batch prompts_dir/ outputs_dir/ [timeout]

# Typical workflow
mkdir -p /tmp/rlm/{prompts,results}
# ... generate prompts ...
rlm-batch /tmp/rlm/prompts /tmp/rlm/results 120
# ... aggregate results ...
```

**Remember:** Estimate cost, test small samples first, use structured output, aggregate carefully.
