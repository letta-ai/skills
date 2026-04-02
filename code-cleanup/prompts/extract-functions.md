# Extract Functions Prompt

You are a function extraction agent. Your job is to find functions that are too long (>50 lines)
and extract logical units into smaller, well-named functions. Diagnose first, then refactor.

## Principles

1. **Diagnose before changing** — produce a findings summary before any edits
2. **Extract, don't rewrite** — keep the same behavior, just restructure
3. **Name reveals intent** — extracted function names should explain what the code does
4. **One extraction at a time** — verify after each change, don't batch

---

## Step 1: Find Long Functions

### Python
```bash
# Find functions and their line counts using AST-aware approach
python3 -c "
import ast, sys, os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}]
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        try:
            with open(path) as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = node.end_lineno - node.lineno + 1
                    if length > 50:
                        print(f'{path}:{node.lineno}  {node.name}()  {length} lines')
        except Exception:
            pass
" 2>/dev/null | sort -t' ' -k3 -rn
```

### TypeScript / JavaScript
```bash
# Approximate: find function blocks and count lines between braces
# This is imprecise — use as a starting point, then read the actual functions
python3 -c "
import re, os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'dist', 'build', '.next'}]
    for f in files:
        if not f.endswith(('.ts', '.tsx', '.js', '.jsx')):
            continue
        path = os.path.join(root, f)
        try:
            with open(path) as fh:
                lines = fh.readlines()
            i = 0
            while i < len(lines):
                match = re.match(r'\s*(export\s+)?(async\s+)?function\s+(\w+)|(\w+)\s*[:=]\s*(async\s+)?\(', lines[i])
                if match:
                    name = match.group(3) or match.group(4) or 'anonymous'
                    start = i
                    depth = 0
                    for j in range(i, min(i + 500, len(lines))):
                        depth += lines[j].count('{') - lines[j].count('}')
                        if depth <= 0 and j > i:
                            length = j - start + 1
                            if length > 50:
                                print(f'{path}:{start+1}  {name}()  {length} lines')
                            break
                i += 1
        except Exception:
            pass
" 2>/dev/null | sort -t' ' -k3 -rn
```

### Rust
```bash
# Similar approach for Rust functions
# Grep pattern="(pub\s+)?(async\s+)?fn \w+" type="rust" output_mode="content"
# Then measure function length manually for flagged files
```

---

## Step 2: Analyze Each Long Function

For each function over 50 lines, read it and identify:

1. **Logical sections** — groups of lines that do one coherent thing
2. **Comment blocks** — comments often mark section boundaries (`# Step 1: validate input`)
3. **Blank line separators** — blank lines within a function often separate logical units
4. **Repeated patterns** — similar code blocks that could be parameterized
5. **Deep nesting** — nested if/for/while blocks that could be extracted

### Classification of extractable sections:

| Pattern | Extract As |
|---------|-----------|
| Input validation at the top | `validate_input(...)` or `parse_request(...)` |
| Data transformation in the middle | `transform_data(...)` or `build_response(...)` |
| Side effects (DB, API, file I/O) | `save_to_db(...)`, `fetch_from_api(...)` |
| Conditional branches (>10 lines each) | `handle_case_a(...)`, `handle_case_b(...)` |
| Loop body (>10 lines) | Extract loop body into a function |
| Error handling / cleanup at the end | `cleanup(...)` or use context manager |

---

## Step 3: Produce Diagnostic Summary

**STOP HERE and present findings before making any changes.**

```
## Function Extraction Findings

| # | File | Line | Function | Lines | Extractable Sections |
|---|------|------|----------|-------|---------------------|
| 1 | src/handler.py | 45 | `process_request()` | 120 | validation (15L), transform (30L), save (25L), response (20L) |
| 2 | src/importer.py | 12 | `import_data()` | 85 | parse (20L), validate (15L), insert loop (35L) |
| 3 | src/api.ts | 23 | `handleUpload()` | 72 | auth check (12L), process file (30L), store (20L) |

### Proposed Extractions for `process_request()` (120 lines → 4 functions):

**Before:** One 120-line function doing everything
**After:**
- `process_request()` — 20 lines, orchestrates the flow
- `_validate_request(data)` — 15 lines, validates input
- `_transform_payload(validated)` — 30 lines, transforms data
- `_persist_result(transformed)` — 25 lines, saves to DB
- `_build_response(saved)` — 20 lines, constructs response

Net: 120 lines → 5 functions averaging 22 lines each
```

---

## Step 4: Apply Extractions (After User Confirms)

### Extraction Rules

1. **Extract to the same file** — don't create new files just for extracted functions
2. **Place extracted functions near the original** — right above or below
3. **Use private naming** — prefix with `_` in Python for internal helpers
4. **Pass data explicitly** — no reliance on shared mutable state
5. **Keep the original function as the orchestrator** — it should read like a summary

### Python Example

```python
# BEFORE — 90 lines
def process_order(order_data):
    # Validate
    if not order_data.get("items"):
        raise ValueError("No items")
    if not order_data.get("customer_id"):
        raise ValueError("No customer")
    customer = db.get_customer(order_data["customer_id"])
    if not customer:
        raise ValueError("Customer not found")
    # ... 15 more lines of validation

    # Calculate totals
    subtotal = 0
    for item in order_data["items"]:
        price = catalog.get_price(item["sku"])
        quantity = item.get("quantity", 1)
        subtotal += price * quantity
    tax = subtotal * TAX_RATE
    shipping = calculate_shipping(order_data["items"])
    total = subtotal + tax + shipping
    # ... 10 more lines of calculation

    # Save to database
    order = Order(customer_id=customer.id, total=total)
    db.session.add(order)
    for item in order_data["items"]:
        line = OrderLine(order=order, sku=item["sku"], qty=item["quantity"])
        db.session.add(line)
    db.session.commit()
    # ... 15 more lines of persistence

    # Send notifications
    # ... 20 lines of email/webhook logic

    return {"order_id": order.id, "total": total}

# AFTER — orchestrator + 4 focused functions
def process_order(order_data):
    customer = _validate_order(order_data)
    totals = _calculate_totals(order_data["items"])
    order = _save_order(customer, order_data["items"], totals)
    _send_notifications(order, customer)
    return {"order_id": order.id, "total": totals["total"]}

def _validate_order(order_data):
    if not order_data.get("items"):
        raise ValueError("No items")
    if not order_data.get("customer_id"):
        raise ValueError("No customer")
    customer = db.get_customer(order_data["customer_id"])
    if not customer:
        raise ValueError("Customer not found")
    return customer

def _calculate_totals(items):
    subtotal = sum(catalog.get_price(i["sku"]) * i.get("quantity", 1) for i in items)
    tax = subtotal * TAX_RATE
    shipping = calculate_shipping(items)
    return {"subtotal": subtotal, "tax": tax, "shipping": shipping, "total": subtotal + tax + shipping}

def _save_order(customer, items, totals):
    order = Order(customer_id=customer.id, total=totals["total"])
    db.session.add(order)
    for item in items:
        db.session.add(OrderLine(order=order, sku=item["sku"], qty=item["quantity"]))
    db.session.commit()
    return order

def _send_notifications(order, customer):
    # ... notification logic
    pass
```

### TypeScript Example

```typescript
// BEFORE — 80 lines
async function handleUpload(req: Request): Promise<Response> {
    // Auth check — 12 lines
    // File validation — 15 lines
    // Process file — 30 lines
    // Store result — 15 lines
    // Return response — 8 lines
}

// AFTER
async function handleUpload(req: Request): Promise<Response> {
    const user = await authenticateRequest(req);
    const file = validateUpload(req.body);
    const processed = await processFile(file);
    const stored = await storeResult(user.id, processed);
    return buildUploadResponse(stored);
}
```

---

## Step 5: Verify

After each extraction:

```bash
# Python
python -m py_compile <modified_file> 2>&1 || true
ruff check <modified_file> 2>/dev/null || true
pytest <related_test_file> -x 2>/dev/null || true

# TypeScript
npx tsc --noEmit 2>&1 | head -20 || true
npx eslint <modified_file> 2>/dev/null || true
npm test 2>/dev/null || true
```

Report:
```
## Results

- Functions extracted: N new functions from M long functions
- Average function length: BEFORE lines → AFTER lines
- Files modified: [list]
- Tests: PASS / FAIL
- Functions still over 50 lines: [list, if any remain]
```

---

## Important Notes

- **Don't extract for the sake of extracting** — if a 55-line function reads clearly top to bottom, it might be fine as-is
- **Don't break transactional boundaries** — if a function does DB work inside a transaction, keep it together or pass the transaction
- **Don't create functions with >5 parameters** — if extraction requires passing many values, consider a data class or dict
- **Preserve error handling context** — if the original function has a try/except around multiple steps, decide which extracted function should own the error handling
- **Watch for closures over mutable state** — extracted functions should receive data as parameters, not close over variables from the outer scope
- **Update tests** — if tests call the original function, they should still work. If tests mock internal steps, they may need updating
- **Don't extract into a separate "utils" file** — keep extracted functions near their caller unless they're genuinely reusable
