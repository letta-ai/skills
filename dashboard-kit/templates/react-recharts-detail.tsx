/**
 * Dashboard Kit — React + Recharts + Detail Panel Template
 *
 * Usage:
 *   1. Copy this file into your React project
 *   2. Replace DataItem interface with your data schema
 *   3. Replace fetchData() with your API call
 *   4. Customize the chart and detail panel fields
 *   5. Import the shared CSS: import './dashboard-common.css'
 *
 * Dependencies: react, recharts, lucide-react (optional icons)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

// ── Data Types ───────────────────────────────────────────────
// CUSTOMIZE: Replace with your data schema
interface DataItem {
  id: string;
  date: string;
  label: string;
  value: number;
  secondary: number;
  category: string;
  description: string;
  metadata: Record<string, string | number>;
}

type ChartType = 'line' | 'bar';

// ── Data Fetching ────────────────────────────────────────────
// CUSTOMIZE: Replace with your API call
async function fetchDashboardData(): Promise<DataItem[]> {
  // Example: const response = await fetch('/api/dashboard');
  // return response.json();
  const now = new Date();
  return Array.from({ length: 30 }, (_, i) => {
    const date = new Date(now);
    date.setDate(date.getDate() - (29 - i));
    return {
      id: `item-${i}`,
      date: date.toISOString().split('T')[0],
      label: `Day ${i + 1}`,
      value: Math.round(200 + Math.random() * 300),
      secondary: Math.round(50 + Math.random() * 100),
      category: ['Alpha', 'Beta', 'Gamma'][i % 3],
      description: `Data point for ${date.toLocaleDateString()}`,
      metadata: {
        source: 'api',
        confidence: Math.round(70 + Math.random() * 30),
      },
    };
  });
}

// ── Freshness Hook ───────────────────────────────────────────
function useFreshness(lastUpdated: Date | null) {
  const [label, setLabel] = useState('Loading...');
  const [status, setStatus] = useState<'fresh' | 'aging' | 'stale'>('fresh');

  useEffect(() => {
    if (!lastUpdated) return;
    const update = () => {
      const diff = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
      if (diff < 60) {
        setLabel(`Updated ${diff}s ago`);
        setStatus('fresh');
      } else if (diff < 3600) {
        setLabel(`Updated ${Math.floor(diff / 60)}m ago`);
        setStatus(diff < 300 ? 'fresh' : 'aging');
      } else {
        setLabel(`Updated ${Math.floor(diff / 3600)}h ago`);
        setStatus('stale');
      }
    };
    update();
    const interval = setInterval(update, 10000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  return { label, status };
}

// ── Custom Tooltip ───────────────────────────────────────────
interface TooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="dash-tooltip">
      <p className="dash-tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="dash-tooltip-value" style={{ color: p.color }}>
          {p.name}: {p.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

// ── Detail Sidebar ───────────────────────────────────────────
interface DetailSidebarProps {
  item: DataItem | null;
  onClose: () => void;
}

function DetailSidebar({ item, onClose }: DetailSidebarProps) {
  if (!item) {
    return (
      <aside className="dash-sidebar">
        <div className="dash-sidebar-header">
          <h3>Details</h3>
        </div>
        <div className="dash-sidebar-body">
          <p className="dash-sidebar-placeholder">
            Click a data point on the chart to see details.
          </p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="dash-sidebar open">
      <div className="dash-sidebar-header">
        <h3>{item.label}</h3>
        <button className="dash-sidebar-close" onClick={onClose} aria-label="Close">
          &times;
        </button>
      </div>
      <div className="dash-sidebar-body">
        {/* CUSTOMIZE: Replace with your detail fields */}
        <div className="dash-field">
          <span className="dash-field-label">Date</span>
          <span className="dash-field-value">{item.date}</span>
        </div>
        <div className="dash-field">
          <span className="dash-field-label">Value</span>
          <span className="dash-field-value dash-field-highlight">
            {item.value.toLocaleString()}
          </span>
        </div>
        <div className="dash-field">
          <span className="dash-field-label">Secondary</span>
          <span className="dash-field-value">{item.secondary.toLocaleString()}</span>
        </div>
        <div className="dash-field">
          <span className="dash-field-label">Category</span>
          <span className="dash-badge">{item.category}</span>
        </div>
        <div className="dash-field">
          <span className="dash-field-label">Description</span>
          <span className="dash-field-value">{item.description}</span>
        </div>
        {Object.entries(item.metadata).map(([key, val]) => (
          <div className="dash-field" key={key}>
            <span className="dash-field-label">{key}</span>
            <span className="dash-field-value">{String(val)}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

// ── Summary Card ─────────────────────────────────────────────
interface SummaryCardProps {
  label: string;
  value: string;
  delta?: string;
  direction?: 'up' | 'down';
}

function SummaryCard({ label, value, delta, direction }: SummaryCardProps) {
  return (
    <div className="dash-summary-card">
      <span className="dash-summary-label">{label}</span>
      <span className="dash-summary-value">{value}</span>
      {delta && (
        <span className={`dash-summary-delta ${direction || ''}`}>{delta}</span>
      )}
    </div>
  );
}

// ── Main Dashboard Component ─────────────────────────────────
export default function Dashboard() {
  const [data, setData] = useState<DataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selectedItem, setSelectedItem] = useState<DataItem | null>(null);
  const [chartType, setChartType] = useState<ChartType>('line');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const freshness = useFreshness(lastUpdated);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboardData();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedItem(null);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleChartClick = (data: { activePayload?: Array<{ payload: DataItem }> }) => {
    const item = data?.activePayload?.[0]?.payload;
    if (item) setSelectedItem(item);
  };

  // CUSTOMIZE: Replace with your summary calculations
  const totalValue = data.reduce((s, d) => s + d.value, 0);
  const avgSecondary = data.length ? Math.round(data.reduce((s, d) => s + d.secondary, 0) / data.length) : 0;

  return (
    <div className="dash-root" data-theme={theme}>
      {/* Header */}
      <header className="dash-header">
        <h1 className="dash-title">Analytics Dashboard</h1>
        <div className="dash-header-controls">
          <div className={`dash-freshness ${freshness.status}`}>
            <span className="dash-freshness-dot" />
            <span>{freshness.label}</span>
          </div>
          <button
            className="dash-theme-toggle"
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            title="Toggle theme"
          >
            {theme === 'dark' ? '\u263E' : '\u2600'}
          </button>
        </div>
      </header>

      {/* Summary Row */}
      <div className="dash-summary-row">
        <SummaryCard label="Total Value" value={totalValue.toLocaleString()} delta="+12%" direction="up" />
        <SummaryCard label="Avg Secondary" value={avgSecondary.toLocaleString()} delta="-3%" direction="down" />
        <SummaryCard label="Data Points" value={String(data.length)} />
        <SummaryCard label="Categories" value={String(new Set(data.map(d => d.category)).size)} />
      </div>

      {/* Chart Tabs */}
      <div className="dash-tabs">
        <button
          className={`dash-tab ${chartType === 'line' ? 'active' : ''}`}
          onClick={() => setChartType('line')}
        >
          Line
        </button>
        <button
          className={`dash-tab ${chartType === 'bar' ? 'active' : ''}`}
          onClick={() => setChartType('bar')}
        >
          Bar
        </button>
      </div>

      {/* Body */}
      <div className="dash-body">
        <div className="dash-chart-area">
          {loading && (
            <div className="dash-state">
              <div className="dash-spinner" />
              <p>Loading data...</p>
            </div>
          )}

          {error && (
            <div className="dash-state">
              <p className="dash-state-error">{error}</p>
              <button className="dash-retry" onClick={loadData}>Retry</button>
            </div>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="dash-state">
              <p>No data available</p>
              <p className="dash-state-hint">Check your data source or adjust filters.</p>
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' ? (
                <LineChart data={data} onClick={handleChartClick}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={theme === 'dark' ? '#21262d' : '#eaeef2'}
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    stroke={theme === 'dark' ? '#8b949e' : '#656d76'}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    stroke={theme === 'dark' ? '#8b949e' : '#656d76'}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#58a6ff"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                    name="Value"
                  />
                  <Line
                    type="monotone"
                    dataKey="secondary"
                    stroke="#3fb950"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                    name="Secondary"
                  />
                </LineChart>
              ) : (
                <BarChart data={data} onClick={handleChartClick}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={theme === 'dark' ? '#21262d' : '#eaeef2'}
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    stroke={theme === 'dark' ? '#8b949e' : '#656d76'}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    stroke={theme === 'dark' ? '#8b949e' : '#656d76'}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="value" fill="#58a6ff" radius={[4, 4, 0, 0]} name="Value" />
                  <Bar dataKey="secondary" fill="#3fb950" radius={[4, 4, 0, 0]} name="Secondary" />
                </BarChart>
              )}
            </ResponsiveContainer>
          )}
        </div>

        <DetailSidebar item={selectedItem} onClose={() => setSelectedItem(null)} />
      </div>
    </div>
  );
}
