# Create Dashboard — Generation Prompt

Generate a complete dashboard page using the "interactive chart + detail sidebar" pattern.
The page should be production-ready with dark/light theme, responsive layout, loading/error/empty
states, and a data freshness indicator.

---

## INPUTS

Before generating, confirm these with the user:

1. **Data schema** — fields, types, and example values
2. **Chart type** — one of: `time-series`, `bar-chart`, `scatter`, `network-graph`, `pie`, `area`
3. **Detail panel fields** — which fields appear in the sidebar when a data point is clicked
4. **Template** — one of: `html-d3`, `html-plotly`, `react-recharts`
5. **Target path** — where to write the output file(s)

If the user doesn't specify a template, infer from context:
- Network/force graph → `html-d3`
- Time series, bar, scatter → `html-plotly`
- Inside an existing React app → `react-recharts`

---

## STEP 1: Survey the Target Project

Before generating anything, understand the existing codebase:

```bash
# Check for existing CSS themes, chart libraries, component patterns
glob "**/*.css" | head -20
glob "**/package.json"
grep -r "recharts\|plotly\|d3\|chart.js" package.json 2>/dev/null
```

- If the project already uses a chart library, prefer that library
- If the project has a dark theme CSS file, extend it instead of adding new variables
- If the project has a component pattern (e.g., `pages/`, `components/`), follow it

---

## STEP 2: Choose and Copy the Template

Based on the chosen template type, start from the corresponding starter template:

| Template | Source File |
|----------|-------------|
| `html-d3` | `skills/dashboard-kit/templates/html-d3-sidebar.html` |
| `html-plotly` | `skills/dashboard-kit/templates/html-plotly-sidebar.html` |
| `react-recharts` | `skills/dashboard-kit/templates/react-recharts-detail.tsx` |

Read the template file:
```bash
cat skills/dashboard-kit/templates/<chosen-template>
```

Copy it to the target location and begin customizing.

---

## STEP 3: Define the Data Layer

Replace the template's sample data with the user's data schema.

**For HTML templates**, create a `fetchData()` function:
```javascript
async function fetchData() {
  // Replace with real endpoint or static data
  const response = await fetch('/api/data');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
```

**For React templates**, create a data hook:
```typescript
function useDashboardData() {
  const [data, setData] = useState<DataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    fetchData()
      .then(d => { setData(d); setLastUpdated(new Date()); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error, lastUpdated };
}
```

Include type definitions matching the user's schema:
```typescript
interface DataItem {
  // Map user's fields here
  id: string;
  name: string;
  value: number;
  // ...
}
```

---

## STEP 4: Configure the Chart

Customize the chart for the user's data:

### Time Series (Plotly or Recharts)
- X-axis: date/time field
- Y-axis: value field(s)
- Hover: show formatted date + value
- Click: select point, populate sidebar

### Bar Chart (Plotly or Recharts)
- X-axis: category field
- Y-axis: value field
- Hover: show category + value
- Click: select bar, populate sidebar

### Network Graph (D3)
- Nodes: entities with id, label, optional group/type
- Links: source → target with optional weight
- Color: by group/type
- Size: by weight/importance
- Click: select node, show connections in sidebar

### Scatter Plot (Plotly or Recharts)
- X/Y: two numeric fields
- Color: optional group field
- Size: optional weight field
- Click: select point, populate sidebar

---

## STEP 5: Build the Detail Sidebar

The sidebar should:

1. **Slide in from the right** when a data point is clicked
2. **Display the user's detail fields** in a structured layout
3. **Include a close button** (top-right corner)
4. **Show related data** if available (e.g., linked items, history)
5. **Collapse on mobile** (responsive breakpoint at 768px)

Sidebar field layout pattern:
```html
<div class="detail-field">
  <span class="detail-label">Field Name</span>
  <span class="detail-value">Field Value</span>
</div>
```

For numeric fields, consider sparklines or mini-charts in the sidebar.

---

## STEP 6: Add States

Every dashboard needs four states:

### Loading State
```html
<div class="dashboard-loading">
  <div class="spinner"></div>
  <p>Loading data...</p>
</div>
```

### Error State
```html
<div class="dashboard-error">
  <p class="error-icon">!</p>
  <p>Failed to load data</p>
  <p class="error-detail">Error message here</p>
  <button onclick="location.reload()">Retry</button>
</div>
```

### Empty State
```html
<div class="dashboard-empty">
  <p>No data available</p>
  <p class="empty-hint">Try adjusting your filters or check back later.</p>
</div>
```

### Data Freshness Indicator
```html
<div class="freshness-badge" id="freshness">
  <span class="freshness-dot"></span>
  <span class="freshness-text">Updated 2 min ago</span>
</div>
```

The freshness badge should:
- Show green dot + "Updated X ago" when data is < 5 min old
- Show yellow dot + "Updated X ago" when data is 5-60 min old
- Show red dot + "Stale — Updated X ago" when data is > 60 min old

Freshness JavaScript:
```javascript
function updateFreshness(lastUpdated) {
  const now = new Date();
  const diff = Math.floor((now - lastUpdated) / 1000);
  const badge = document.getElementById('freshness');
  const dot = badge.querySelector('.freshness-dot');
  const text = badge.querySelector('.freshness-text');

  let label, color;
  if (diff < 60) { label = `${diff}s ago`; color = 'fresh'; }
  else if (diff < 3600) { label = `${Math.floor(diff/60)}m ago`; color = diff < 300 ? 'fresh' : 'aging'; }
  else { label = `${Math.floor(diff/3600)}h ago`; color = 'stale'; }

  dot.className = `freshness-dot ${color}`;
  text.textContent = `Updated ${label}`;
}
```

---

## STEP 7: Apply Theme

Use the shared CSS from `skills/dashboard-kit/css/dashboard-common.css`.

**For HTML templates:** include via `<link>` or inline the relevant variables:
```html
<link rel="stylesheet" href="dashboard-common.css">
```

**For React templates:** import the CSS or use CSS-in-JS with the same variables.

If the project already has a theme system, map the dashboard variables to existing tokens:
```css
:root {
  --dash-bg: var(--existing-bg, #0d1117);
  --dash-surface: var(--existing-surface, #161b22);
  /* etc. */
}
```

Both dark and light themes should work. The template includes a theme toggle.

---

## STEP 8: Make It Responsive

Responsive breakpoints:

| Breakpoint | Layout |
|-----------|--------|
| > 1024px | Chart + sidebar side by side |
| 768-1024px | Chart full width, sidebar as overlay |
| < 768px | Chart full width, sidebar as bottom sheet |

Key responsive rules:
```css
@media (max-width: 1024px) {
  .dashboard-layout { flex-direction: column; }
  .detail-sidebar {
    position: fixed; bottom: 0; left: 0; right: 0;
    height: 50vh; width: 100%;
    transform: translateY(100%);
    border-top: 1px solid var(--dash-border);
    border-left: none;
  }
  .detail-sidebar.open { transform: translateY(0); }
}
```

---

## STEP 9: Write the File(s)

Write the generated dashboard to the target path. For React, this may be multiple files:
- `Dashboard.tsx` — main component
- `Dashboard.css` or styles — component styles
- `types.ts` — TypeScript interfaces (if not inline)

For HTML, it's a single file (styles and scripts inline for portability).

---

## STEP 10: Verify

After generating, verify:

1. **File exists** at the target path
2. **No syntax errors** — for HTML, open in browser; for React, run `npx tsc --noEmit`
3. **Chart renders** with sample data
4. **Sidebar opens** on click and closes on X
5. **Responsive** — check at 1200px, 900px, and 500px widths
6. **Theme toggle** switches between dark and light
7. **Freshness badge** updates correctly
8. **Loading/error/empty states** display when triggered

---

## TIPS

- **Don't over-customize.** Start from the template and make minimal changes for the user's schema.
  The templates are designed to work out of the box — resist the urge to rewrite them.

- **Inline styles for HTML templates.** HTML dashboards should be self-contained single files.
  Copy the CSS variables inline rather than requiring an external stylesheet.

- **Use CDN imports for HTML.** D3, Plotly, and Chart.js should come from CDN in HTML templates.
  Don't bundle or require npm install for standalone HTML dashboards.

- **Match the project's existing patterns.** If the project uses Tailwind, use Tailwind classes.
  If it uses CSS modules, use CSS modules. Don't introduce a new styling system.

- **Data freshness is non-negotiable.** Every dashboard must show when data was last updated.
  Users need to know if they're looking at stale data.

- **Sidebar width: 320-400px.** Narrower than 320px is cramped; wider than 400px steals
  too much chart space. Default to 360px.
