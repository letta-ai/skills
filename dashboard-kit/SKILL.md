---
name: dashboard-kit
description: Generate dashboard pages with interactive graph/chart + detail sidebar panel pattern
triggers:
  - "create dashboard"
  - "dashboard with sidebar"
  - "graph with detail panel"
  - "add dashboard page"
  - "chart with sidebar"
  - "new dashboard"
  - "dashboard kit"
tools_required:
  - Read
  - Write
  - Glob
  - Grep
  - Edit
  - TodoWrite
---

# Dashboard Kit Skill

Generate complete dashboard pages following the "interactive graph/chart on the left,
detail panel on the right" pattern. Supports three output modes:

| Template | Stack | Use Case |
|----------|-------|----------|
| `html-d3-sidebar` | Vanilla HTML + D3.js | Force graphs, network visualizations |
| `html-plotly-sidebar` | HTML + Plotly + Chart.js | Time series, bar charts, scatter plots |
| `react-recharts-detail` | React + Recharts + TypeScript | React app dashboards |

## When to Use

- Building a new dashboard page with chart + detail panel
- Adding a visualization page to an existing project
- Creating an admin/analytics view with interactive data display
- Any page where clicking chart elements reveals detail in a sidebar

## Input

The user provides:
1. **Data schema** - what fields/columns exist in the data
2. **Chart type** - time series, network graph, bar chart, scatter plot, etc.
3. **Detail panel fields** - what to show when a data point is selected
4. **Template** - which stack to use (D3, Plotly, or React)

## Workflow

Follow `prompts/create-dashboard.md` for the full generation algorithm.

## Templates

Starter templates in `templates/` can be copied and customized:
- `templates/html-d3-sidebar.html` - D3.js force graph with sliding sidebar
- `templates/html-plotly-sidebar.html` - Plotly chart with sidebar panel
- `templates/react-recharts-detail.tsx` - React Recharts with detail panel

Shared styles in `css/dashboard-common.css` provide dark/light theme support.
