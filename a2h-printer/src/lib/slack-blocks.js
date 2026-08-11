// src/slack-blocks.js — A2UI atom -> Slack Block Kit compiler (Bucket A).
//
// Ported from slack-compiler/compile_atoms.py's EMITTERS (2026-08-06,
// slack-compiler/DESIGN.md decision 1: "ONE implementation, in JS, in the
// Worker"). Slack is Worker-only ground — its servers POST to a public
// endpoint expecting a 3s answer, so a Python compiler could never be in the
// production path. This file IS that production path. The Python harness
// (compile_atoms.py) now calls it via `node`, the same idiom
// a2ui-catalogue/scripts/gen_server_card.py already uses to read tools.js —
// one implementation, two consumers, no drift to guard against.
//
// Pure functions only: no network, no Worker globals (no `env`, no
// `crypto.subtle`), imports limited to catalog-data.js — same posture as
// validate-payload.js, for the same reason (its own header explains why).
//
// Field mapping is HEURISTIC — atoms name the same concept differently
// (title/label/heading/headline/plan_name), so emitters guess by candidate
// key. Verified against a real workspace (slack-compiler/AUDIT.md records
// six emitter bugs schema validation could not see, all found by looking at
// rendered output); this port carries every fix from that process.
//
// One exception to "pure functions only, no crypto.subtle" above:
// signRenderUrl (D-bucket image-fallback signing) needs real HMAC, and lives
// in crypto-utils.js instead, imported below — genuinely platform-agnostic,
// not Slack-shaped, so it isn't duplicated here.
import { signRenderUrl } from './crypto-utils.js';

// ── candidate keys, in priority order ───────────────────────────────────────
const TITLE_KEYS = ['title', 'heading', 'headline', 'label', 'name', 'plan_name',
  'course', 'question', 'term', 'service', 'key', 'summary',
  'nav_slug', 'slug', 'text', 'message'];
const BODY_KEYS = ['message', 'text', 'body', 'description', 'detail', 'details',
  'content', 'summary', 'subtitle', 'sub', 'note', 'caption',
  'answer', 'situation', 'rationale'];
// stat_card/pull_stat/metric_delta keep the actual number in value/
// current_value, none of which were in BODY_KEYS — the card rendered a
// label with no statistic at all until VALUE_KEYS was added.
const VALUE_KEYS = ['value', 'current_value', 'stat', 'number', 'count', 'amount',
  'score', 'metric', 'delta', 'delta_value', 'total', 'percent',
  'stars', 'price', 'unit'];
const LIST_KEYS = ['rows', 'items', 'points', 'events', 'entries', 'options', 'stats',
  'data', 'series', 'segments', 'metrics', 'steps', 'cards', 'columns',
  'risks', 'incidents', 'features', 'tasks', 'services', 'people'];

const TXT = (s) => ({ type: 'plain_text', text: String(s ?? '').slice(0, 150) || '—' });
const MD = (s) => ({ type: 'mrkdwn', text: String(s ?? '').slice(0, 2900) || '—' });
const titleCase = (t) => t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function first(props, keys) {
  for (const k of keys) {
    const v = props[k];
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return null;
}

function firstList(props, keys = LIST_KEYS) {
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

function flatten(v) {
  if (isPlainObject(v)) {
    return Object.values(v).filter((x) => typeof x === 'string' || typeof x === 'number')
      .join(' · ').slice(0, 180);
  }
  if (Array.isArray(v)) return v.map(flatten).join(', ').slice(0, 180);
  return String(v ?? '').slice(0, 180);
}

// ── emitters, one per target block ──────────────────────────────────────────
function eSection(t, p) {
  const title = first(p, TITLE_KEYS) || titleCase(t);
  const seen = new Set([title]);
  const lines = [];
  for (const [k, v] of Object.entries(p)) {
    if (k === 'type' || typeof v === 'boolean') continue;
    const f = flatten(v).trim();
    if (f && !seen.has(f) && !f.startsWith('http')) {
      seen.add(f);
      lines.push(BODY_KEYS.includes(k) ? f : `*${titleCase(k)}:* ${f}`);
    }
  }
  const txt = `*${title}*` + (lines.length ? '\n' + lines.slice(0, 12).join('\n') : '');
  return [{ type: 'section', text: MD(txt) }];
}

// header holds exactly ONE string. Any atom mapped here with more fields
// (page_header carries subtitle + meta) loses them unless they spill.
function eHeader(t, p) {
  const title = first(p, TITLE_KEYS) || t;
  const out = [{ type: 'header', text: TXT(title) }];
  const rest = Object.entries(p)
    .filter(([k, v]) => k !== 'type' && typeof v !== 'boolean' && flatten(v).trim() && flatten(v) !== title)
    .map(([, v]) => flatten(v));
  if (rest.length) out.push({ type: 'context', elements: [MD(rest.join(' · ').slice(0, 2900))] });
  return out;
}

// divider carries no content at all. section_break/dark_divider declare a
// label, so emit it as context above the rule rather than dropping it.
function eDivider(t, p) {
  const lbl = first(p, [...TITLE_KEYS, ...BODY_KEYS]);
  const out = [];
  if (lbl) out.push({ type: 'context', elements: [MD(lbl)] });
  out.push({ type: 'divider' });
  return out;
}

function eImage(t, p) {
  let url = Object.entries(p).find(
    ([k, v]) => typeof v === 'string' && v.startsWith('http')
      && ['url', 'src', 'image'].some((x) => k.toLowerCase().includes(x)),
  );
  url = url ? url[1] : null;
  if (!url || url.includes('example.com')) url = 'https://a2uicatalog.ai/favicon.ico';
  const b = { type: 'image', image_url: url, alt_text: first(p, ['alt', 'alt_text']) || t };
  const ttl = first(p, TITLE_KEYS);
  if (ttl) b.title = TXT(ttl);
  return [b];
}

// D-bucket image fallback (2026-08-07). These atoms have NO native Slack
// block (exotic chart shapes data_visualization can't express, or genuinely
// visual atoms like schema_qr/primitive_plate) -- but a real headless-
// Chromium render service already exists and is already LIVE for this exact
// need on a different surface: cloud-run-renderer, deployed as
// a2ui-renderer-public specifically --allow-unauthenticated so an anonymous
// image fetcher can retrieve it with no auth header -- Google Chat's
// `image` widget already depends on this, Slack's `image` block has the
// identical constraint (a public URL Slack's own servers fetch, never raw
// bytes this Worker could hand it directly).
//
// Mints the SAME signed-URL scheme that service already verifies (gzip ->
// urlsafe-base64, HMAC-SHA256 truncated to 16 hex chars) rather than
// inventing a new one -- see cloud-run-renderer/server.py's
// _encode_block_qs/_decode_block_qs, which this must byte-for-byte match or
// the service 403s every URL (verified against the live service before
// this landed, both from Python and from this exact function).
//
// RELOCATED to lib/crypto-utils.js (2026-08-11, imported at top of this
// file) — genuinely platform-agnostic, not Slack-shaped at all, so Chat's
// render path can call it directly without going through this file's
// Slack-Block-Kit wrapper below. See crypto-utils.js's own header comment
// for the full HMAC/async story; only the Slack-shaped wrapping
// (eImageRender) stays here.

async function eImageRender(t, p, renderConfig) {
  if (!renderConfig || !renderConfig.signingKey || !renderConfig.baseUrl) {
    throw new Error(`D-bucket atom "${t}" needs a render (signingKey + baseUrl) but none was provided`);
  }
  const url = await signRenderUrl(t, p, renderConfig);
  const b = { type: 'image', image_url: url, alt_text: first(p, ['alt', 'alt_text']) || titleCase(t) };
  const ttl = first(p, TITLE_KEYS);
  if (ttl) b.title = TXT(ttl);
  return [b];
}

function eActions(t, p) {
  const [, items] = firstList(p);
  let labels = [];
  if (items) {
    for (const it of items.slice(0, 5)) {
      labels.push(!isPlainObject(it) ? flatten(it) : (it.label || it.text || flatten(it)));
    }
  }
  if (!labels.length) labels = [first(p, TITLE_KEYS) || 'Action'];
  return [{
    type: 'actions',
    elements: labels.map((l, i) => ({
      type: 'button', text: TXT(String(l).slice(0, 70)), action_id: `${t}_${i}`,
    })),
  }];
}

// Fills every slot card offers (title/subtitle/body/subtext/hero_image).
// Filling only title+body left ~80% of a rich atom's content on the floor —
// caught by the coverage sweep, not by validation, which was happy either
// way. Leftover fields spill into a trailing context block rather than
// vanishing: card has 4 text slots and plenty of atoms carry more than 4
// fields, so "maps to card" is only full fidelity for genuinely small atoms.
function eCard(t, p) {
  const used = new Set();
  const take = (keys, limit) => {
    for (const k of keys) {
      const v = p[k];
      if (used.has(k) || v == null || typeof v === 'boolean' || Array.isArray(v) || isPlainObject(v)) continue;
      const sv = String(v).trim();
      if (sv) { used.add(k); return sv.slice(0, limit); }
    }
    return null;
  };
  // Same lookup as take(TITLE_KEYS, ...) but WITHOUT marking the key used —
  // needed below to recover the untruncated value if it turns out to be the
  // ONLY usable field on the whole atom (summary_box-shaped: one long text
  // field, nothing else), so the truncated 150-char title copy isn't the
  // only place that content survives.
  const titleKey = TITLE_KEYS.find((k) => {
    const v = p[k];
    return v != null && typeof v !== 'boolean' && !Array.isArray(v) && !isPlainObject(v) && String(v).trim();
  });
  const titleFull = titleKey ? String(p[titleKey]).trim() : null;
  const b = { type: 'card', title: TXT(take(TITLE_KEYS, 150) || titleCase(t)) };
  for (const [slot, keys, lim] of [
    ['subtitle', [...VALUE_KEYS, ...TITLE_KEYS, ...BODY_KEYS], 150],
    ['body', [...VALUE_KEYS, ...BODY_KEYS], 200],
    ['subtext', [...BODY_KEYS, ...VALUE_KEYS], 200],
  ]) {
    const v = take(keys, lim);
    if (v) b[slot] = TXT(v);
  }
  // anything sensible left over beats an empty slot
  for (const slot of ['subtitle', 'body']) {
    if (!b[slot]) {
      const v = take(Object.keys(p).filter((k) => k !== 'type' && !/(_url|color|accent)$/.test(k)), 200);
      if (v) b[slot] = TXT(v);
    }
  }
  // Single-field atoms (summary_box: just {text}) — the ONE usable field
  // filled the title and every later slot AND the spill pass (below) found
  // nothing left, since that field is now `used`; anything past the title's
  // 150-char cap silently vanished with no field left to spill it into
  // (found live: an empty card body on a real narrative atom — see
  // content_audit.json's "empty-card" flag). If body is still empty and the
  // title's real source had more content than its truncated copy shows,
  // reuse the full value there — some repeated text beats losing the rest
  // of the atom's only content outright.
  if (!b.body && titleFull && titleFull.length > 150) {
    b.body = TXT(titleFull.slice(0, 200));
  }
  const img = Object.entries(p).find(
    ([k, v]) => typeof v === 'string' && v.startsWith('http')
      && ['image', 'img', 'photo', 'avatar'].some((x) => k.toLowerCase().includes(x)),
  );
  if (img && !img[1].includes('example.com')) {
    b.hero_image = { type: 'image', image_url: img[1], alt_text: t };
  }
  const out = [b];
  const spill = Object.entries(p)
    .filter(([k, v]) => !used.has(k) && k !== 'type' && typeof v !== 'boolean'
      && flatten(v).trim() && !String(v).startsWith('http'))
    .map(([k, v]) => `*${titleCase(k)}:* ${flatten(v)}`);
  if (spill.length) out.push({ type: 'context', elements: [MD(spill.join(' · ').slice(0, 2900))] });
  return out;
}

// One card per item. Falling back to flatten(whole prop bag) produced titles
// like "video_pair · A descriptive caption · https://..." — legal, and
// visibly garbage. Scalar/imageless atoms build cards from their own
// distinct string fields instead.
function eCarousel(t, p) {
  const [, items] = firstList(p);
  let cards = [];
  if (items) {
    // NOT sliced to 10 here — the truncation check below needs the real
    // pre-cap count, or "omitted" is silently always 0 (found by testing:
    // pre-slicing here made the truncated[] report empty even when 5 of 15
    // items were genuinely dropped).
    for (const it of items) {
      let c;
      if (isPlainObject(it)) {
        const ttl = first(it, TITLE_KEYS) || first(it, BODY_KEYS) || 'Item';
        c = { type: 'card', title: TXT(String(ttl).slice(0, 150)) };
        const sub = first(it, BODY_KEYS.filter((k) => it[k] !== ttl));
        if (sub && sub !== ttl) c.body = TXT(String(sub).slice(0, 200));
        const img = Object.values(it).find((v) => typeof v === 'string' && v.startsWith('http'));
        if (img) c.hero_image = { type: 'image', image_url: img, alt_text: t };
      } else {
        c = { type: 'card', title: TXT(String(it).slice(0, 150)) };
      }
      cards.push(c);
    }
  } else {
    // no list: make cards from the atom's own distinct text fields
    const ttl = first(p, TITLE_KEYS) || titleCase(t);
    const imgs = Object.values(p).filter((v) => typeof v === 'string' && v.startsWith('http'));
    if (imgs.length) {
      imgs.forEach((u, i) => {
        cards.push({
          type: 'card', title: TXT(imgs.length > 1 ? `${ttl} ${i + 1}` : ttl),
          hero_image: { type: 'image', image_url: u, alt_text: t },
        });
      });
    } else {
      cards.push({ type: 'card', title: TXT(ttl) });
    }
  }
  while (cards.length < 2) cards.push({ type: 'card', title: TXT(`Item ${cards.length + 1}`) });
  // Budget (DESIGN.md): 10 cards per carousel. Truncate with a visible
  // marker rather than a silent drop — nothing to degrade a carousel TO, so
  // truncation is the correct outcome here, not a failure of the ladder.
  const truncated = [];
  if (cards.length > 10) {
    truncated.push({ scope: 'carousel', omitted: cards.length - 10 });
    cards = cards.slice(0, 10);
  }
  return { blocks: [{ type: 'carousel', elements: cards }], truncated };
}

function eContainer(t, p) {
  const [, items] = firstList(p);
  const source = items || [p];
  const truncated = [];
  let use = source;
  if (source.length > 10) {
    truncated.push({ scope: 'container', omitted: source.length - 10 });
    use = source.slice(0, 10);
  }
  const children = use.map((it) => {
    const d = isPlainObject(it) ? it : { text: String(it) };
    return { type: 'section', text: MD(`*${first(d, TITLE_KEYS) || 'Item'}*\n${first(d, BODY_KEYS) || flatten(d)}`) };
  });
  const blocks = [{
    type: 'container', is_collapsible: true,
    title: TXT(first(p, TITLE_KEYS) || titleCase(t)),
    child_blocks: children.length ? children : [{ type: 'section', text: MD('—') }],
  }];
  return { blocks, truncated };
}

// headers[] + rows[][] is the CANONICAL table shape (table,
// data_table_sortable, comparison_grid, feature_matrix...). Handling only
// list-of-dicts (the first cut of this emitter) collapsed every one of those
// into a SINGLE column — which renders as a plain text list, and was the
// concrete cause of "most of it looks like plain text" (Curtis, live review).
function eTable(t, p) {
  const cell = (s) => ({ type: 'raw_text', text: String(s ?? '').slice(0, 120) || '—' });
  const hdrs = p.headers, rws = p.rows;

  if (Array.isArray(hdrs) && hdrs.length && Array.isArray(rws) && rws.length) {
    const out = [hdrs.slice(0, 20).map(cell)];
    for (const r of rws.slice(0, 20)) {
      const cells = Array.isArray(r) ? r : [r];
      out.push(cells.slice(0, 20).map((c) => cell(flatten(c))));
    }
    return [{ type: 'table', rows: out }];
  }
  if (Array.isArray(rws) && rws.length && Array.isArray(rws[0])) {
    return [{ type: 'table', rows: rws.slice(0, 20).map((r) => r.slice(0, 20).map((c) => cell(flatten(c)))) }];
  }

  const [listKey, items] = firstList(p);
  if (!items) return eSection(t, p);
  let rows;
  if (isPlainObject(items[0])) {
    const cols = Object.keys(items[0]).slice(0, 20);
    rows = [cols.map((c) => cell(titleCase(c)))];
    for (const it of items.slice(0, 20)) rows.push(cols.map((c) => cell(flatten(it[c] ?? ''))));
  } else {
    // A single string-array field renders as ONE column and silently drops
    // any OTHER array field entirely — comparison_grid/feature_matrix carry
    // TWO ({products,features} / {product_names,features}), and firstList
    // only ever returns whichever LIST_KEYS ranks higher, so the second
    // vanished from the render completely (found by the content-audit
    // continuation of AUDIT.md's four-pass loop: "4 rows, every row 1 cell"
    // — the SAME single-column shape bug #1 fixed, recurring for atoms with
    // no single canonical list). Laying every other array field in as its
    // own column keeps both visible; padding to the longest with '—' rather
    // than pairing rows index-wise avoids asserting a per-row relationship
    // ("product N has feature N") the data never actually declares.
    const otherArrays = Object.entries(p)
      .filter(([k, v]) => k !== listKey && Array.isArray(v) && v.length)
      .slice(0, 3);
    if (otherArrays.length) {
      const cols = [[listKey, items], ...otherArrays];
      const maxLen = Math.min(Math.max(...cols.map(([, v]) => v.length)), 20);
      rows = [cols.map(([k]) => cell(titleCase(k)))];
      for (let i = 0; i < maxLen; i++) {
        rows.push(cols.map(([, v]) => cell(v[i] !== undefined ? flatten(v[i]) : '')));
      }
    } else {
      rows = [[cell(titleCase(t))], ...items.slice(0, 20).map((i) => [cell(flatten(i))])];
    }
  }
  return [{ type: 'table', rows }];
}

function ePlan(t, p) {
  const [, itemsRaw] = firstList(p);
  const items = itemsRaw || [p];
  const truncated = [];
  let use = items;
  // Budget (DESIGN.md): 10 child blocks — plan's own task list follows the
  // same "nowhere to degrade to, so truncate visibly" rule as container.
  if (items.length > 10) {
    truncated.push({ scope: 'plan', omitted: items.length - 10 });
    use = items.slice(0, 10);
  }
  const tasks = use.map((it, i) => {
    const d = isPlainObject(it) ? it : { title: String(it) };
    return {
      type: 'task_card', task_id: `${t}_${i}`,
      title: String(first(d, TITLE_KEYS) || `Step ${i + 1}`).slice(0, 150),
      status: 'in_progress',
    };
  });
  const blocks = [{
    type: 'plan', title: String(first(p, TITLE_KEYS) || titleCase(t)).slice(0, 150), tasks,
  }];
  return { blocks, truncated };
}

// A numeric value that may have arrived as a string (JSON round-trips,
// spreadsheet-sourced data, and this file's own test harness's synthetic
// fallback rows all do this) — the original `typeof v === 'number'` check
// silently dropped every one of those points, which for atoms whose ONLY
// candidate values were numeric strings meant EVERY point vanished and the
// hardcoded A/B fallback fired despite real data being present. Found by the
// automated content-audit continuation of AUDIT.md's four-pass correction
// loop, same "looks legal, is wrong" shape as the original six bugs.
function numOrNumericString(v) {
  if (typeof v === 'number') return v;
  if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) return Number(v);
  return undefined;
}

// Chart.js shape: {labels: [...], datasets: [{label, data: [n,...]}]}.
// Unhandled in the first cut, so chartjs_bar/line/pie and friends fell
// through to placeholder A/B->40/60 data while still validating cleanly —
// legal, and completely wrong. chartType comes from the caller (mapping.json
// carries it per DESIGN.md's chart-native decision), not guessed here.
//
// Extended (content-audit pass): three more real chart-native atoms surfaced
// shapes this branch didn't recognise at all, each falling all the way
// through to the SAME hardcoded fallback the Chart.js fix above was meant to
// close for good —
//   - stacked_area / mini_sparkline_set carry `series`, not `datasets`
//     (identical {label,data} shape, different field name — a naming
//     divergence, not a structural one)
//   - sparkline carries a bare `data: [n,...]` with no label wrapper at all
//   - donut_stat carries `value`/`max_value` (progress-of-total), which is
//     not a category/series chart shape in the first place — needs its own
//     branch, not a wider key list
function eDataviz(t, p, chartType) {
  const ctype = chartType || 'bar';
  const title = String(first(p, TITLE_KEYS) || titleCase(t)).slice(0, 50);

  // series is stacked_area/mini_sparkline_set's field name for what
  // chartjs_bar/line call datasets — identical {label, data:[n,...]} shape,
  // so treating it as an alias (not a second code path) is what "one
  // implementation" actually requires here, not a special case.
  const labels = p.labels, datasets = p.datasets || p.series;
  if (Array.isArray(datasets) && datasets.length && datasets.some(isPlainObject)) {
    // No `labels` field at all (mini_sparkline_set has none) — index-based
    // categories ("1","2","3"...) still produce a real, readable multi-line
    // chart rather than falling through to the fallback for want of a field
    // this atom's schema never declared.
    const cats = Array.isArray(labels) && labels.length
      ? labels.slice(0, 12).map((l) => String(l).slice(0, 40))
      : Array.from(
          { length: Math.min(Math.max(...datasets.map((d) => ((d || {}).data || []).length)), 12) },
          (_, i) => String(i + 1),
        );
    if (ctype === 'pie') {
      const nums = (datasets[0] || {}).data || [];
      const segs = cats.map((c, i) => ({ label: c, value: numOrNumericString(nums[i]) }))
        .filter((s) => typeof s.value === 'number');
      if (segs.length >= 2) {
        return [{ type: 'data_visualization', title, chart: { type: 'pie', segments: segs.slice(0, 12) } }];
      }
    }
    const series = [];
    for (const ds of datasets.slice(0, 12)) {
      if (!isPlainObject(ds)) continue;
      const nums = ds.data || [];
      const data = cats.map((c, i) => ({ label: c, value: numOrNumericString(nums[i]) }))
        .filter((d) => typeof d.value === 'number');
      if (data.length) series.push({ name: String(ds.label || 'series').slice(0, 40), data });
    }
    if (series.length) {
      return [{ type: 'data_visualization', title, chart: { type: ctype, series, axis_config: { categories: cats } } }];
    }
  }

  // sparkline's shape: a bare array of numbers, no label/object wrapper at
  // all. firstList/items below requires isPlainObject(it), which a raw
  // number always fails — every point silently skipped, not just some.
  if (!Array.isArray(datasets)) {
    for (const [k, v] of Object.entries(p)) {
      if (Array.isArray(v) && v.length >= 2 && v.every((x) => numOrNumericString(x) !== undefined)) {
        const data = v.slice(0, 12).map((x, i) => ({ label: String(i + 1), value: numOrNumericString(x) }));
        if (ctype === 'pie') {
          return [{ type: 'data_visualization', title, chart: { type: 'pie', segments: data } }];
        }
        return [{
          type: 'data_visualization', title,
          chart: { type: ctype, series: [{ name: title.slice(0, 40), data }],
                   axis_config: { categories: data.map((x) => x.label) } },
        }];
      }
    }
  }

  const [, items] = firstList(p);
  let pts = [];
  if (items) {
    for (const it of items.slice(0, 12)) {
      if (!isPlainObject(it)) continue;
      const lbl = first(it, ['label', 'name', 'title', 'x', 'key']) || 'item';
      const val = Object.values(it).find((v) => numOrNumericString(v) !== undefined);
      if (val === undefined) continue;
      pts.push({ label: String(lbl).slice(0, 40), value: numOrNumericString(val) });
    }
  }
  // donut_stat-shaped: a single value against a max (progress-of-total), not
  // a category list at all — items/datasets above will never find anything
  // here by design, so this needs its OWN branch, not a wider key search.
  // Two-segment pie (value vs. remaining) is the honest reading of that
  // shape; forcing it through the generic bar/line path would need a second
  // axis this data doesn't have.
  if (pts.length < 2) {
    const rawVal = VALUE_KEYS.map((k) => numOrNumericString(p[k])).find((v) => v !== undefined);
    const rawMax = numOrNumericString(p.max_value ?? p.max ?? p.total ?? p.goal);
    if (rawVal !== undefined) {
      const lbl = first(p, TITLE_KEYS) || titleCase(t);
      // Clamp rather than trust rawMax at face value — a max at or below the
      // value (bad/inconsistent source data, seen live: donut_stat specimen
      // value=75 against max_value=5) must not fall through to the generic
      // two-point-minimum check below and get silently swapped for the
      // hardcoded A/B fallback; a single real value is still real data.
      pts = rawMax !== undefined && rawMax > rawVal
        ? [{ label: lbl.slice(0, 40), value: rawVal }, { label: 'Remaining', value: rawMax - rawVal }]
        : [{ label: lbl.slice(0, 40), value: rawVal }];
    }
  }
  if (!pts.length) pts = [{ label: 'A', value: 40 }, { label: 'B', value: 60 }];
  if (ctype === 'pie') return [{ type: 'data_visualization', title, chart: { type: 'pie', segments: pts } }];
  return [{
    type: 'data_visualization', title,
    chart: { type: ctype, series: [{ name: title.slice(0, 40), data: pts }], axis_config: { categories: pts.map((x) => x.label) } },
  }];
}

const SIMPLE_EMITTERS = {
  section: eSection, header: eHeader, divider: eDivider,
  image: eImage, actions: eActions, card: eCard, table: eTable,
  // Bucket B (needs_review pass's classify.py labels its target "markdown"
  // for readability in mapping.json/AUDIT.md — Slack itself has no distinct
  // "markdown block", mrkdwn is a TEXT FORMAT any section's `text` carries.
  // eSection already IS the generic prop-bag-to-mrkdwn flattener the
  // original plan's Phase 2 called "one generic markdown flattener for
  // Bucket B" — same function, not a second implementation.
  markdown: eSection,
};
// These three return {blocks, truncated} (they enforce their own per-block
// child-count budgets); the simple ones above return a bare blocks array.
const BUDGETED_EMITTERS = { carousel: eCarousel, container: eContainer, 'plan/task_card': ePlan };

// ── budget model (DESIGN.md decision 2) ─────────────────────────────────────
// Hard Slack limits (slack-targets.json): 50 blocks/message, 2
// data_visualization/message, plus each block type's own internal limit
// (10 cards/carousel, 10 children/container — enforced inside their own
// emitters above, since those are per-BLOCK not per-MESSAGE).
const MAX_BLOCKS_PER_MESSAGE = 50;
const MAX_CHARTS_PER_MESSAGE = 2;

// series[{name, data:[{label,value}]}] + axis_config.categories maps EXACTLY
// onto table columns [category, series1, series2, ...]; pie.segments maps
// onto a two-column table. Lossless in CONTENT — every number survives —
// only the visual encoding is lost. This is why chart overflow degrades to
// table rather than being truncated (DESIGN.md: "charts past the second
// degrade to table — they do not truncate").
function chartToTable(block) {
  const cell = (s) => ({ type: 'raw_text', text: String(s ?? '').slice(0, 120) || '—' });
  const chart = block.chart || {};
  let rows;
  if (chart.type === 'pie') {
    rows = [[cell('Label'), cell('Value')], ...(chart.segments || []).map((s) => [cell(s.label), cell(s.value)])];
  } else {
    const cats = (chart.axis_config || {}).categories || [];
    const series = chart.series || [];
    rows = [[cell('Category'), ...series.map((s) => cell(s.name))]];
    cats.forEach((c, i) => {
      rows.push([cell(c), ...series.map((s) => cell((s.data[i] || {}).value))]);
    });
  }
  return { type: 'table', rows };
}

/**
 * Compile one atom to real Slack blocks for the given target.
 * Returns { blocks, degraded, truncated } — never a bare array. See
 * DESIGN.md: "payload exceeds budget" is a declared outcome, not a crash.
 *
 * ASYNC (unlike the Phase-2-era version of this function) purely because of
 * the bucket==='D' branch below — every other path is synchronous work
 * wrapped in a resolved promise, so no existing caller's behavior changes
 * beyond needing an `await`. `bucket` and `renderConfig` are both optional:
 * omitting `bucket` preserves the exact old dispatch (target==='image' goes
 * to the plain eImage path), so callers that never touch D-bucket atoms
 * need no changes at all.
 */
export async function compileAtom(atomType, props, target, chartType, bucket, renderConfig) {
  const degraded = [];
  const truncated = [];
  let blocks;
  if (target === 'image' && bucket === 'D') {
    blocks = await eImageRender(atomType, props, renderConfig);
  } else if (target === 'data_visualization') {
    blocks = eDataviz(atomType, props, chartType);
  } else if (SIMPLE_EMITTERS[target]) {
    blocks = SIMPLE_EMITTERS[target](atomType, props);
  } else if (BUDGETED_EMITTERS[target]) {
    const r = BUDGETED_EMITTERS[target](atomType, props);
    blocks = r.blocks;
    truncated.push(...r.truncated);
  } else {
    throw new Error(`no emitter for target block "${target}"`);
  }
  return { blocks, degraded, truncated, fits: true };
}

/**
 * Compile a WHOLE payload (multiple atoms) into one message's worth of
 * blocks, applying the message-level budget: charts past the second degrade
 * to table (lossless), and the block count past 50 truncates with a visible
 * marker (DESIGN.md — nowhere left to degrade to at that point).
 *
 * @param {Array<{type:string, props:object, target:string, chartType?:string, bucket?:string}>} atoms
 * @param {{signingKey:string, baseUrl:string}} [renderConfig] — required only
 *   if `atoms` contains a bucket==='D' entry; omit entirely for payloads
 *   that never touch D-bucket atoms.
 */
export async function compilePayload(atoms, renderConfig) {
  const degraded = [];
  const truncated = [];
  let chartsUsed = 0;
  let blocks = [];

  for (const a of atoms) {
    const compiled = await compileAtom(a.type, a.props, a.target, a.chartType, a.bucket, renderConfig);
    degraded.push(...compiled.degraded);
    truncated.push(...compiled.truncated);

    let atomBlocks = compiled.blocks;
    if (a.target === 'data_visualization') {
      if (chartsUsed < MAX_CHARTS_PER_MESSAGE) {
        chartsUsed += 1;
      } else {
        atomBlocks = atomBlocks.map((b) => {
          if (b.type !== 'data_visualization') return b;
          degraded.push({ atom: a.type, from: 'data_visualization', to: 'table',
                          why: `limit: ${MAX_CHARTS_PER_MESSAGE} charts/message` });
          return chartToTable(b);
        });
      }
    }
    blocks.push(...atomBlocks);
  }

  const fits = blocks.length <= MAX_BLOCKS_PER_MESSAGE;
  if (!fits) {
    // Reserve ONE slot for the marker itself — slicing to the full limit and
    // then appending would land at limit+1, silently re-breaking the exact
    // budget this path exists to enforce.
    const omitted = blocks.length - (MAX_BLOCKS_PER_MESSAGE - 1);
    blocks = blocks.slice(0, MAX_BLOCKS_PER_MESSAGE - 1);
    blocks.push({ type: 'context', elements: [MD(`+${omitted} more not shown (message block limit)`)] });
    truncated.push({ scope: 'message', omitted });
  }

  return { blocks, degraded, truncated, fits: true };
}
