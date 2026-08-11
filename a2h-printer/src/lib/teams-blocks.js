// src/lib/teams-blocks.js — A2UI atom -> Microsoft Teams Adaptive Cards compiler.
//
// The Teams sibling of slack-blocks.js, and deliberately the same SHAPE:
// one emitter per target element, a compileAtom that returns
// {blocks, degraded, truncated} rather than a bare array, and a
// compilePayload that applies the message-level budget. Same contract means
// render-to-slack.js's caller logic ports across almost unchanged.
//
// It is NOT a port of the Slack emitters — Adaptive Cards is a different
// schema with a different budget model, so the emitters are new. What IS
// shared is atom-heuristics.js (which prop is the title/body/list), because
// that is a question about the ATOM and has nothing to do with the
// destination. Copying those tables instead would silently lose the six
// emitter bugs AUDIT.md records finding by eye.
//
// THREE CORRECTIONS ALREADY BAKED IN (2026-08-08), each of which would
// otherwise have shipped a card that validates and renders wrong:
//
//  1. CHARTS ARE IMAGES, NOT ELEMENTS. Microsoft's docs state bot-sent
//     Adaptive Cards need PRE-RENDERED chart images. An earlier pass marked
//     Chart.* native because @copilotkit/channels-teams emits those types —
//     which proves the ADAPTER emits them, not that Teams renders them.
//     There is deliberately no eChart here; charts route to eImageRender.
//  2. NO Chart.Bar / Chart.Area EXIST. The five real types are VerticalBar,
//     HorizontalBar, Line, Pie, Donut. (Kept only as a comment now, since
//     charts do not compile to elements at all.)
//  3. MOBILE CAPS AT ADAPTIVE CARDS 1.2. Teams accepts 1.5 for bot-sent
//     cards but the mobile app only supports up to 1.2, and Table arrived in
//     1.5 — so a Table-bearing card renders inconsistently on phones. The
//     target version is a PARAMETER (see compilePayload), not an assumption.
//
// Budget model differs from Slack in kind, not degree: Slack caps BLOCKS per
// message (50), Teams caps BYTES (~28KB per card). So the truncation check
// measures serialized size rather than counting elements.
import {
  TITLE_KEYS, BODY_KEYS, VALUE_KEYS,
  titleCase, isPlainObject, first, firstList, flatten,
} from './atom-heuristics.js';

// Adaptive Cards is a declarative schema — no CSS, no scripting. Text takes
// a markdown SUBSET (bold, italic, links, bullets); anything richer is a
// reason to reach for the image path, not to invent markup here.
const AC_VERSION_DEFAULT = '1.5';
const MAX_CARD_BYTES = 28_000;

const TEXT = (s, opts = {}) => ({
  type: 'TextBlock', text: String(s ?? '—').slice(0, 3000), wrap: true, ...opts,
});

// ── emitters, one per target element ───────────────────────────────────────

// Default/fallback: the markdown floor. Loses structure, never loses content.
function eTextBlock(t, p) {
  const title = first(p, TITLE_KEYS) || titleCase(t);
  const seen = new Set([title]);
  const lines = [];
  for (const k of [...VALUE_KEYS, ...BODY_KEYS]) {
    const v = p[k];
    if (v == null || isPlainObject(v) || Array.isArray(v)) continue;
    const s = String(v).trim();
    if (s && !seen.has(s)) { seen.add(s); lines.push(s); }
  }
  // Spill anything still unrepresented rather than dropping it — same
  // principle as the Slack emitters: a declared degradation beats a silent
  // loss.
  const [, items] = firstList(p);
  if (items) {
    for (const it of items.slice(0, 10)) {
      const s = flatten(it);
      if (s && !seen.has(s)) { seen.add(s); lines.push(`• ${s}`); }
    }
  }
  const out = [TEXT(title, { weight: 'Bolder', size: 'Medium' })];
  if (lines.length) out.push(TEXT(lines.join('\n\n')));

  // SPILL PASS — everything not yet shown.
  //
  // Without this the emitter silently DROPS every prop whose key isn't in
  // TITLE/BODY/VALUE_KEYS, which is most of the catalogue's domain-specific
  // fields. Measured on the full 518-atom sweep before this existed: 109
  // cards rendered as a bold title and nothing else. Three representative
  // losses — alert_banner lost its action link, audio_link lost its
  // audio_url, and ai_build_trace (model + 4 token counts) lost ALL FIVE of
  // its data fields, rendering as the words "Ai Build Trace".
  //
  // Slack's eCard has had exactly this pass since its own content audit
  // found the same class of bug by eye; porting the emitters without it
  // reintroduced the bug on a new surface. Leftover scalars go to a FactSet
  // (label/value is what FactSet is FOR — strictly better than the flat
  // text line Slack falls back to), and a URL with a plausible label becomes
  // a real action rather than a naked link.
  const shown = new Set([title, ...lines]);
  const facts = [];
  const actions = [];
  // A key whose only job is labelling a URL must not ALSO appear as a fact —
  // alert_banner rendered "Action Label = Action label" as data next to a
  // button already titled "Action label". Collected up-front because the
  // label is discovered while handling the URL, which may come later in the
  // iteration order.
  const labelKeys = new Set();
  for (const k of Object.keys(p)) {
    if (/^https?:\/\//.test(String(p[k] ?? ''))) {
      labelKeys.add(`${k.replace(/_url$/, '')}_label`);
      labelKeys.add('action_label');
      labelKeys.add('cta');
    }
  }
  for (const [k, v] of Object.entries(p)) {
    if (labelKeys.has(k)) continue;
    if (k === 'type' || v == null || isPlainObject(v) || Array.isArray(v)) continue;
    const s = String(v).trim();
    if (!s || shown.has(s)) continue;
    if (/^https?:\/\//.test(s)) {
      if (s.includes('example.com')) continue;   // placeholder, not content
      const label = first(p, [`${k}_label`, 'action_label', 'label', 'cta', ...TITLE_KEYS])
        || titleCase(k.replace(/_url$/, ''));
      actions.push({ type: 'Action.OpenUrl', title: String(label).slice(0, 60), url: s });
      continue;
    }
    facts.push({ title: titleCase(k).slice(0, 120), value: s.slice(0, 200) });
  }
  if (facts.length) out.push({ type: 'FactSet', facts: facts.slice(0, 12) });
  if (actions.length) out.push({ type: 'ActionSet', actions: actions.slice(0, 4) });
  return out;
}

// FactSet is the natural home for label/value pairs — key_value, stat rows,
// metadata. Slack has no direct equivalent (it degrades these to a table).
function eFactSet(t, p) {
  const title = first(p, TITLE_KEYS);
  const facts = [];
  const [, items] = firstList(p);
  if (items && isPlainObject(items[0])) {
    for (const it of items.slice(0, 20)) {
      const k = first(it, TITLE_KEYS) || '—';
      const v = first(it, VALUE_KEYS) ?? flatten(it);
      facts.push({ title: String(k).slice(0, 120), value: String(v).slice(0, 200) });
    }
  } else {
    for (const [k, v] of Object.entries(p)) {
      if (k === 'type' || isPlainObject(v) || Array.isArray(v)) continue;
      facts.push({ title: titleCase(k).slice(0, 120), value: String(v).slice(0, 200) });
    }
  }
  if (!facts.length) return eTextBlock(t, p);
  const out = [];
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  out.push({ type: 'FactSet', facts: facts.slice(0, 20) });
  return out;
}

// Table is Adaptive Cards 1.5 — see correction 3. compilePayload gates this
// by target version; the emitter itself just builds it.
function eTable(t, p) {
  const cell = (s) => ({
    type: 'TableCell',
    items: [TEXT(String(s ?? '—').slice(0, 120))],
  });
  const hdrs = p.headers;
  const rws = p.rows;
  const rows = [];
  if (Array.isArray(hdrs) && hdrs.length) {
    rows.push({ type: 'TableRow', cells: hdrs.slice(0, 8).map(cell), style: 'accent' });
  }
  const source = Array.isArray(rws) && rws.length ? rws : (firstList(p)[1] || []);
  const truncated = [];
  if (source.length > 20) truncated.push({ scope: 'table', omitted: source.length - 20 });
  for (const r of source.slice(0, 20)) {
    const cells = Array.isArray(r) ? r
      : isPlainObject(r) ? Object.values(r) : [r];
    rows.push({ type: 'TableRow', cells: cells.slice(0, 8).map((c) => cell(flatten(c))) });
  }
  if (!rows.length) return { blocks: eTextBlock(t, p), truncated: [] };
  const columns = Array((rows[0].cells || []).length).fill({ width: 1 });
  const out = [];
  const title = first(p, TITLE_KEYS);
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  out.push({ type: 'Table', columns, rows });
  return { blocks: out, truncated };
}

function eImage(t, p) {
  let url = Object.entries(p).find(
    ([k, v]) => typeof v === 'string' && v.startsWith('http')
      && ['image', 'img', 'photo', 'avatar', 'url', 'src'].some((x) => k.toLowerCase().includes(x)),
  );
  url = url ? url[1] : null;
  if (!url || url.includes('example.com')) return eTextBlock(t, p);
  const out = [];
  const title = first(p, TITLE_KEYS);
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  // selectAction: Action.OpenUrl on the SAME url — Teams' native "tap to
  // enlarge" for an image, no task/fetch invoke handling needed (that's a
  // separate, unbuilt mechanism — see README's v1 scope cut on Action.Submit
  // invoke activities). Teams recognizes an image-typed URL and opens it in
  // its own in-app viewer rather than an external browser tab.
  out.push({ type: 'Image', url, altText: first(p, TITLE_KEYS) || titleCase(t), size: 'Auto',
    selectAction: { type: 'Action.OpenUrl', url } });
  return out;
}

function eActionSet(t, p) {
  const [, items] = firstList(p);
  const src = (items && items.length) ? items : [p];
  const actions = [];
  for (const it of src.slice(0, 6)) {
    const d = isPlainObject(it) ? it : { label: String(it) };
    const label = String(first(d, TITLE_KEYS) || 'Open').slice(0, 60);
    const href = Object.values(d).find((v) => typeof v === 'string' && v.startsWith('http'));
    // Action.OpenUrl when there is a real destination, Action.Submit
    // otherwise — Submit round-trips to the bot, which is the Teams analogue
    // of Slack's block_actions payload.
    actions.push(href
      ? { type: 'Action.OpenUrl', title: label, url: href }
      : { type: 'Action.Submit', title: label, data: { atom: t, label } });
  }
  if (!actions.length) return eTextBlock(t, p);
  return [{ type: 'ActionSet', actions }];
}

// ColumnSet — real multi-column layout, which Slack has NO equivalent for.
// One of the few places Teams is genuinely more capable.
function eColumnSet(t, p) {
  const [, items] = firstList(p);
  if (!items || !items.length) return eTextBlock(t, p);
  const cols = items.slice(0, 4).map((it) => ({
    type: 'Column', width: 'stretch',
    items: isPlainObject(it) ? eTextBlock(t, it) : [TEXT(flatten(it))],
  }));
  const out = [];
  const title = first(p, TITLE_KEYS);
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  out.push({ type: 'ColumnSet', columns: cols });
  const truncated = items.length > 4 ? [{ scope: 'columnset', omitted: items.length - 4 }] : [];
  return { blocks: out, truncated };
}

function eContainer(t, p) {
  const [, items] = firstList(p);
  const kids = (items || []).slice(0, 10);
  const truncated = (items && items.length > 10)
    ? [{ scope: 'container', omitted: items.length - 10 }] : [];
  const inner = kids.length
    ? kids.flatMap((it) => (isPlainObject(it) ? eTextBlock(t, it) : [TEXT(flatten(it))]))
    : eTextBlock(t, p);
  const out = [];
  const title = first(p, TITLE_KEYS);
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  out.push({ type: 'Container', items: inner, style: 'emphasis' });
  return { blocks: out, truncated };
}

// ── D-bucket escape hatch ──────────────────────────────────────────────────
// Identical contract to slack-blocks.js's eImageRender, and deliberately the
// SAME signed-URL scheme against the SAME renderer — this is the piece that
// is genuinely shared across every surface, so a second signing
// implementation here would be indefensible.
async function signRenderUrl(atomType, props, renderConfig) {
  const { signingKey, baseUrl, width = 620, theme } = renderConfig;
  const block = { type: atomType, ...props };
  const spec = theme ? { block, width, theme } : { block, width };
  const payload = JSON.stringify(spec);
  const cs = new CompressionStream('gzip');
  const writer = cs.writable.getWriter();
  writer.write(new TextEncoder().encode(payload));
  writer.close();
  const compressed = new Uint8Array(await new Response(cs.readable).arrayBuffer());
  let bin = '';
  for (const b of compressed) bin += String.fromCharCode(b);
  const token = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(signingKey), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(token));
  const sig = Array.from(new Uint8Array(mac)).map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
  return `${baseUrl}/render.png?b=${token}.${sig}`;
}

async function eImageRender(t, p, renderConfig) {
  if (!renderConfig || !renderConfig.signingKey || !renderConfig.baseUrl) {
    throw new Error(`D-bucket atom "${t}" needs a render (signingKey + baseUrl) but none was provided`);
  }
  // Teams renders on a WHITE surface, unlike the renderer's dark default —
  // observed directly in the M365 Agents Playground, 2026-08-08. Pass
  // theme:'light' unless the caller has already decided.
  const url = await signRenderUrl(t, p, { theme: 'light', ...renderConfig });
  const out = [];
  const title = first(p, TITLE_KEYS);
  if (title) out.push(TEXT(title, { weight: 'Bolder', size: 'Medium' }));
  // Same tap-to-enlarge selectAction as eImage above — see its comment.
  out.push({ type: 'Image', url, altText: title || titleCase(t), size: 'Auto',
    selectAction: { type: 'Action.OpenUrl', url } });
  return out;
}

const SIMPLE_EMITTERS = {
  TextBlock: eTextBlock,
  FactSet: eFactSet,
  Image: eImage,
  ActionSet: eActionSet,
};
const BUDGETED_EMITTERS = {
  Table: eTable,
  ColumnSet: eColumnSet,
  Container: eContainer,
};

// Elements gated by Adaptive Cards version — see correction 3.
const MIN_VERSION_FOR = { Table: 1.5, ActionSet: 1.2 };

/**
 * Compile one atom to Adaptive Card elements.
 * Returns { blocks, degraded, truncated } — never a bare array, matching
 * slack-blocks.js's contract so callers port across.
 */
export async function compileAtom(atomType, props, target, bucket, renderConfig, acVersion = AC_VERSION_DEFAULT) {
  const degraded = [];
  const truncated = [];
  let blocks;

  // Version gate BEFORE dispatch: an element the target version can't render
  // degrades to the image path, where it renders identically everywhere.
  const need = MIN_VERSION_FOR[target];
  if (need && need > parseFloat(acVersion)) {
    degraded.push({ atom: atomType, from: target, to: 'Image',
                    why: `requires Adaptive Cards ${need}, target ${acVersion}` });
    blocks = await eImageRender(atomType, props, renderConfig);
    return { blocks, degraded, truncated, fits: true };
  }

  if (target === 'Image' && bucket === 'D') {
    blocks = await eImageRender(atomType, props, renderConfig);
  } else if (SIMPLE_EMITTERS[target]) {
    blocks = SIMPLE_EMITTERS[target](atomType, props);
  } else if (BUDGETED_EMITTERS[target]) {
    const r = BUDGETED_EMITTERS[target](atomType, props);
    blocks = r.blocks || r;
    truncated.push(...(r.truncated || []));
  } else {
    blocks = eTextBlock(atomType, props);
    degraded.push({ atom: atomType, from: target || 'unknown', to: 'TextBlock',
                    why: 'no emitter for this target' });
  }
  return { blocks, degraded, truncated, fits: true };
}

/**
 * Compile a whole payload into ONE Adaptive Card.
 *
 * Budget is BYTES (~28KB), not element count — the real difference from
 * Slack's model. Overflow truncates with a visible marker rather than
 * silently dropping, same principle as the Slack compiler.
 *
 * @param {Array<{type, props, target, bucket}>} atoms
 * @param {{signingKey, baseUrl, theme?}} [renderConfig] — required if any atom is bucket D
 * @param {string} [acVersion] — '1.5' desktop/web (default), '1.2' mobile-safe
 */
export async function compilePayload(atoms, renderConfig, acVersion = AC_VERSION_DEFAULT) {
  const degraded = [];
  const truncated = [];
  let body = [];

  for (const a of atoms) {
    const c = await compileAtom(a.type, a.props, a.target, a.bucket, renderConfig, acVersion);
    degraded.push(...c.degraded);
    truncated.push(...c.truncated);
    body.push(...c.blocks);
  }

  const card = () => ({
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: acVersion,
    body,
  });

  // Trim from the END until it fits, leaving room for the marker. Measured
  // on the serialized card because that is what Teams actually rejects.
  let omitted = 0;
  while (body.length > 1 && JSON.stringify(card()).length > MAX_CARD_BYTES) {
    body.pop();
    omitted += 1;
  }
  if (omitted) {
    body.push(TEXT(`_+${omitted} element(s) not shown (card size limit)_`, { isSubtle: true, size: 'Small' }));
    truncated.push({ scope: 'card', omitted });
  }

  return { card: card(), blocks: body, degraded, truncated, fits: true };
}
