# Dashboard Kit

Generate dashboard pages with the "interactive chart + detail sidebar" pattern.

## What it does

Provides starter templates and a generation prompt for creating dashboard pages where:
- The **left side** has an interactive chart or graph (flex: 1)
- The **right side** has a detail sidebar (360px) that updates on click
- Both support dark/light themes, responsive layout, and loading/error/empty states

## Usage

In Claude Code:
```
/dashboard-kit
```

Or trigger with natural language:
- "create a dashboard with sidebar"
- "add a graph with detail panel"
- "new dashboard page"

## Templates

| Template | Stack | Best For |
|----------|-------|----------|
| `html-d3-sidebar.html` | Vanilla HTML + D3.js v7 | Force graphs, network visualizations |
| `html-plotly-sidebar.html` | HTML + Plotly.js | Time series, bar charts, scatter plots |
| `react-recharts-detail.tsx` | React + Recharts + TypeScript | React app dashboards |

## How It Works

1. **Survey** — Check what chart libraries and theme systems the project already uses
2. **Choose template** — Pick the matching starter template (D3, Plotly, or React)
3. **Define data** — Map the user's data schema to the chart and sidebar fields
4. **Configure chart** — Set axes, colors, click handlers for the chart type
5. **Build sidebar** — Wire up detail fields that populate on data point click
6. **Add states** — Loading spinner, error with retry, empty state, freshness badge
7. **Apply theme** — Dark/light toggle using CSS custom properties
8. **Make responsive** — Sidebar collapses to bottom sheet on mobile

## Common Elements

All templates share these patterns:

- **Dark background**: `#0d1117` (GitHub) or `#0f172a` (Tailwind slate)
- **Layout**: Chart area (`flex: 1`) + sidebar (`360px`)
- **Sidebar**: Slides in from right, close button, structured detail fields
- **Responsive**: Sidebar becomes bottom sheet below 1024px
- **States**: Loading, error (with retry), empty, data freshness indicator
- **Theme**: Dark/light toggle via `[data-theme]` attribute + CSS variables
- **Keyboard**: `Esc` closes sidebar, `/` focuses search (D3 template)

## Shared CSS

`css/dashboard-common.css` provides the full theme system and layout classes.
HTML templates inline their own styles; React components import the shared CSS.

CSS custom properties start with `--dash-` to avoid conflicts:
- `--dash-bg`, `--dash-surface`, `--dash-border`
- `--dash-text`, `--dash-text-muted`, `--dash-accent`
- `--dash-success`, `--dash-warning`, `--dash-error`
- `--dash-chart-1` through `--dash-chart-6`

## Customization

Each template has `CUSTOMIZE:` comments marking the sections to replace:
- **Data schema** — TypeScript interface or JS object structure
- **fetchData()** — Replace sample data with your API endpoint
- **Chart config** — Axes, traces, colors, click handlers
- **Detail fields** — Sidebar content for selected data point
- **Summary cards** — Top-row metric calculations

## File Structure

```
skills/dashboard-kit/
  SKILL.md                              # Skill trigger and metadata
  README.md                             # This file
  prompts/
    create-dashboard.md                 # Full generation prompt (10 steps)
  templates/
    html-d3-sidebar.html                # D3.js force graph + sliding sidebar
    html-plotly-sidebar.html            # Plotly chart + sidebar panel
    react-recharts-detail.tsx           # React Recharts + detail panel
  css/
    dashboard-common.css                # Shared dark/light theme CSS
```
