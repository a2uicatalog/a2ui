// src/lib/atom-heuristics.js — SURFACE-AGNOSTIC atom field heuristics.
//
// Extracted from slack-blocks.js (2026-08-08) when the Teams/Adaptive Cards
// compiler needed the identical logic. Nothing in here knows what a Slack
// block or an Adaptive Card is — it answers "which prop of this atom is the
// title / the body / the list / a number", which is a question about the
// ATOM, not about the destination.
//
// WHY EXTRACTED RATHER THAN COPIED: a second copy of these tables is exactly
// the drift this estate keeps paying for — two stale copies of
// slack-mapping.js and a parallel classifier that put five atoms in the wrong
// bucket, both found the same day this was written. The key lists below
// encode real bugs found by looking at rendered output (see
// slack-compiler/AUDIT.md: six emitter bugs schema validation could not see);
// a divergent copy would silently lose those fixes on one surface only.
//
// Pure functions, no imports, no platform globals — safe for any consumer.

// ── candidate keys, in priority order ───────────────────────────────────────
export const TITLE_KEYS = ['title', 'heading', 'headline', 'label', 'name', 'plan_name',
  'course', 'question', 'term', 'service', 'key', 'summary',
  'nav_slug', 'slug', 'text', 'message'];
export const BODY_KEYS = ['message', 'text', 'body', 'description', 'detail', 'details',
  'content', 'summary', 'subtitle', 'sub', 'note', 'caption',
  'answer', 'situation', 'rationale'];
// stat_card/pull_stat/metric_delta keep the actual number in value/
// current_value, none of which were in BODY_KEYS — the card rendered a
// label with no statistic at all until VALUE_KEYS was added.
export const VALUE_KEYS = ['value', 'current_value', 'stat', 'number', 'count', 'amount',
  'score', 'metric', 'delta', 'delta_value', 'total', 'percent',
  'stars', 'price', 'unit'];
export const LIST_KEYS = ['rows', 'items', 'points', 'events', 'entries', 'options', 'stats',
  'data', 'series', 'segments', 'metrics', 'steps', 'cards', 'columns',
  'risks', 'incidents', 'features', 'tasks', 'services', 'people'];

export const titleCase = (t) => t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

export function first(props, keys) {
  for (const k of keys) {
    const v = props[k];
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return null;
}

export function firstList(props, keys = LIST_KEYS) {
  for (const k of keys) {
    const v = props[k];
    if (Array.isArray(v) && v.length) return [k, v];
  }
  for (const k of Object.keys(props)) {
    const v = props[k];
    if (Array.isArray(v) && v.length) return [k, v];
  }
  return [null, null];
}

export function flatten(v) {
  if (isPlainObject(v)) {
    return Object.values(v).filter((x) => typeof x === 'string' || typeof x === 'number')
      .join(' · ').slice(0, 180);
  }
  if (Array.isArray(v)) return v.map(flatten).join(', ').slice(0, 180);
  return String(v ?? '').slice(0, 180);
}

export function numOrNumericString(v) {
  if (typeof v === 'number') return v;
  if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) return Number(v);
  return undefined;
}
