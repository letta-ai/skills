/**
 * freshness-badge.js — Vanilla JS data freshness badge.
 *
 * Drop-in usage:
 *   <link rel="stylesheet" href="freshness-badge.css" />
 *   <script src="freshness-badge.js"></script>
 *
 *   // Create a badge
 *   const badge = createFreshnessBadge({ updatedAt: '2026-03-04T12:00:00Z' });
 *   document.getElementById('status').appendChild(badge);
 *
 *   // Or auto-bind to elements with data attributes:
 *   //   <span data-freshness-badge data-updated-at="2026-03-04T12:00:00Z"></span>
 *   initFreshnessBadges();
 */

// ── Default thresholds (ms) ─────────────────────────────────────────
var FRESHNESS_DEFAULTS = {
  fresh: 60 * 60 * 1000,             // 1 hour
  ok: 24 * 60 * 60 * 1000,           // 1 day
  warning: 3 * 24 * 60 * 60 * 1000,  // 3 days
};

/**
 * Resolve a timestamp to epoch milliseconds.
 * @param {Date|string|number} value
 * @returns {number}
 */
function toEpochMs(value) {
  if (value instanceof Date) return value.getTime();
  if (typeof value === 'number') return value;
  return new Date(value).getTime();
}

/**
 * Determine freshness level from age in ms.
 * @param {number} ageMs
 * @param {object} [thresholds]
 * @returns {'fresh'|'ok'|'warning'|'stale'}
 */
function getFreshnessLevel(ageMs, thresholds) {
  var t = thresholds || FRESHNESS_DEFAULTS;
  if (ageMs < t.fresh) return 'fresh';
  if (ageMs < t.ok) return 'ok';
  if (ageMs < t.warning) return 'warning';
  return 'stale';
}

/**
 * Human-readable relative time string.
 * @param {number} ageMs
 * @returns {string}
 */
function formatRelativeTime(ageMs) {
  var seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) return 'just now';

  var minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + 'm ago';

  var hours = Math.floor(minutes / 60);
  if (hours < 24) return hours + 'h ago';

  var days = Math.floor(hours / 24);
  if (days === 1) return '1 day ago';
  return days + ' days ago';
}

/**
 * Build the badge display text.
 * @param {number} ageMs
 * @param {string} level
 * @param {string} label
 * @returns {string}
 */
function getBadgeText(ageMs, level, label) {
  var relative = formatRelativeTime(ageMs);
  if (level === 'stale') {
    var days = Math.floor(ageMs / (24 * 60 * 60 * 1000));
    return '\u26A0\uFE0F Data may be stale (' + days + 'd)';
  }
  return label + ' ' + relative;
}

/**
 * Create a freshness badge DOM element.
 *
 * @param {object} options
 * @param {Date|string|number} options.updatedAt - Timestamp of last update
 * @param {object}  [options.thresholds] - Custom thresholds { fresh, ok, warning } in ms
 * @param {string}  [options.label='Updated'] - Prefix label
 * @param {string}  [options.className=''] - Extra CSS classes
 * @returns {HTMLSpanElement}
 */
function createFreshnessBadge(options) {
  var updatedAt = options.updatedAt;
  var thresholds = Object.assign({}, FRESHNESS_DEFAULTS, options.thresholds || {});
  var label = options.label || 'Updated';
  var extraClass = options.className || '';

  var now = Date.now();
  var epoch = toEpochMs(updatedAt);
  var ageMs = Math.max(0, now - epoch);

  var level = getFreshnessLevel(ageMs, thresholds);
  var text = getBadgeText(ageMs, level, label);

  var badge = document.createElement('span');
  badge.className = 'freshness-badge freshness-badge--' + level + (extraClass ? ' ' + extraClass : '');
  badge.title = new Date(epoch).toISOString();

  var dot = document.createElement('span');
  dot.className = 'freshness-badge__dot';

  badge.appendChild(dot);
  badge.appendChild(document.createTextNode(text));

  return badge;
}

/**
 * Auto-initialize badges from data attributes.
 *
 * Finds all elements with `data-freshness-badge` and replaces their content
 * with a freshness badge. The timestamp is read from `data-updated-at`.
 *
 * Optional attributes:
 *   data-label         — override "Updated" prefix
 *   data-fresh-ms      — custom fresh threshold (ms)
 *   data-ok-ms         — custom ok threshold (ms)
 *   data-warning-ms    — custom warning threshold (ms)
 */
function initFreshnessBadges() {
  var elements = document.querySelectorAll('[data-freshness-badge]');
  for (var i = 0; i < elements.length; i++) {
    var el = elements[i];
    var updatedAt = el.getAttribute('data-updated-at');
    if (!updatedAt) continue;

    var thresholds = {};
    if (el.getAttribute('data-fresh-ms')) thresholds.fresh = Number(el.getAttribute('data-fresh-ms'));
    if (el.getAttribute('data-ok-ms')) thresholds.ok = Number(el.getAttribute('data-ok-ms'));
    if (el.getAttribute('data-warning-ms')) thresholds.warning = Number(el.getAttribute('data-warning-ms'));

    var badge = createFreshnessBadge({
      updatedAt: updatedAt,
      thresholds: thresholds,
      label: el.getAttribute('data-label') || 'Updated',
    });

    el.innerHTML = '';
    el.appendChild(badge);
  }
}

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    createFreshnessBadge: createFreshnessBadge,
    initFreshnessBadges: initFreshnessBadges,
    getFreshnessLevel: getFreshnessLevel,
    formatRelativeTime: formatRelativeTime,
    getBadgeText: getBadgeText,
    FRESHNESS_DEFAULTS: FRESHNESS_DEFAULTS,
  };
}
