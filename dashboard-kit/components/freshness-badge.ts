/**
 * freshness-badge.ts — React component for data freshness display.
 *
 * Shows a color-coded badge with relative time since the last data update.
 *
 * Usage:
 *   import { FreshnessBadge } from './freshness-badge';
 *   <FreshnessBadge updatedAt={new Date('2026-03-04T12:00:00Z')} />
 *
 * Import the companion CSS file for styling:
 *   import './freshness-badge.css';
 */

import React from 'react';

// ── Staleness levels ────────────────────────────────────────────────
export type FreshnessLevel = 'fresh' | 'ok' | 'warning' | 'stale';

// ── Threshold configuration ─────────────────────────────────────────
export interface FreshnessThresholds {
  /** Max age in ms to be considered "fresh" (default: 1 hour) */
  fresh: number;
  /** Max age in ms to be considered "ok" (default: 1 day) */
  ok: number;
  /** Max age in ms to be considered "warning" (default: 3 days) */
  warning: number;
  // Anything beyond `warning` is "stale"
}

const DEFAULT_THRESHOLDS: FreshnessThresholds = {
  fresh: 60 * 60 * 1000,          // 1 hour
  ok: 24 * 60 * 60 * 1000,        // 1 day
  warning: 3 * 24 * 60 * 60 * 1000, // 3 days
};

// ── Props ───────────────────────────────────────────────────────────
export interface FreshnessBadgeProps {
  /** Timestamp of the last data update (Date, ISO string, or epoch ms) */
  updatedAt: Date | string | number;
  /** Custom staleness thresholds */
  thresholds?: Partial<FreshnessThresholds>;
  /** Override the label prefix (default: "Updated") */
  label?: string;
  /** Extra CSS class names */
  className?: string;
}

// ── Helpers ─────────────────────────────────────────────────────────

/** Resolve any supported timestamp into epoch ms. */
function toEpoch(value: Date | string | number): number {
  if (value instanceof Date) return value.getTime();
  if (typeof value === 'number') return value;
  return new Date(value).getTime();
}

/** Determine freshness level from age in ms. */
export function getFreshnessLevel(
  ageMs: number,
  thresholds: FreshnessThresholds = DEFAULT_THRESHOLDS,
): FreshnessLevel {
  if (ageMs < thresholds.fresh) return 'fresh';
  if (ageMs < thresholds.ok) return 'ok';
  if (ageMs < thresholds.warning) return 'warning';
  return 'stale';
}

/** Human-readable relative time string (e.g. "2 hours ago", "3 days ago"). */
export function formatRelativeTime(ageMs: number): string {
  const seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) return 'just now';

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days === 1) return '1 day ago';
  return `${days} days ago`;
}

/** Badge label including optional staleness warning. */
export function getBadgeText(
  ageMs: number,
  level: FreshnessLevel,
  label: string,
): string {
  const relative = formatRelativeTime(ageMs);
  if (level === 'stale') {
    const days = Math.floor(ageMs / (24 * 60 * 60 * 1000));
    return `\u26A0\uFE0F Data may be stale (${days}d)`;
  }
  return `${label} ${relative}`;
}

// ── Component ───────────────────────────────────────────────────────
export const FreshnessBadge: React.FC<FreshnessBadgeProps> = ({
  updatedAt,
  thresholds,
  label = 'Updated',
  className = '',
}) => {
  const now = Date.now();
  const epoch = toEpoch(updatedAt);
  const ageMs = Math.max(0, now - epoch);

  const merged: FreshnessThresholds = { ...DEFAULT_THRESHOLDS, ...thresholds };
  const level = getFreshnessLevel(ageMs, merged);
  const text = getBadgeText(ageMs, level, label);

  const cls = [
    'freshness-badge',
    `freshness-badge--${level}`,
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={cls} title={new Date(epoch).toISOString()}>
      <span className="freshness-badge__dot" />
      {text}
    </span>
  );
};
