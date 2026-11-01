// Canonical architecture graph + validator. Pure ES module, no dependencies.
//
// graph = {
//   title?: string,
//   direction: 'LR' | 'RL' | 'TB' | 'BT',
//   groups:   [{id, label}],
//   nodes:    [{id, label, kind?, sub?, group?}],
//   edges:    [{from, to, label?, style: 'sync'|'async'|'optional', both?, step?, relation?}],
//   messages: [{from, to, text, back?}],
//   numbered?, pace?, duration?, relationColumn?: boolean, relationName?: string (max 20, default 'Relation'),
// }
//
// Limits are the motion_arch atom's own (atoms/schema.yaml, renderers/web_article.py).

export const LIMITS = Object.freeze({
  nodes: 12, edges: 16, groups: 4, messages: 12,
  label: 40, sub: 40, groupLabel: 40, edgeLabel: 48, msgText: 40, title: 80, relation: 20,
});
export const KINDS = Object.freeze(['device', 'app', 'server', 'tool', 'model', 'store', 'surface', 'user']);
export const STYLES = Object.freeze(['sync', 'async', 'optional']);
export const PACES = Object.freeze({ slow: 1.4, normal: 1.0, fast: 0.75 });
export const DIRECTIONS = Object.freeze(['LR', 'RL', 'TB', 'BT']);
export const normDirection = (d) => (d === 'TD' ? 'TB' : d);
export const ID_RE = /^[a-z][a-z0-9_-]{0,31}$/;

// Friendly names that map onto the 8 atom kinds.
export const KIND_ALIASES = Object.freeze({
  client: 'device', browser: 'device', phone: 'device', mobile: 'device', laptop: 'device', device: 'device',
  db: 'store', database: 'store', cache: 'store', bucket: 'store', storage: 'store', datastore: 'store', store: 'store',
  queue: 'tool', mcp: 'tool', auth: 'tool', tool: 'tool',
  gateway: 'server', cdn: 'server', proxy: 'server', backend: 'server', server: 'server', worker: 'server',
  service: 'app', agent: 'app', app: 'app', application: 'app', frontend: 'app',
  llm: 'model', ai: 'model', model: 'model',
  external: 'surface', ui: 'surface', screen: 'surface', renderer: 'surface', surface: 'surface',
  person: 'user', actor: 'user', human: 'user', user: 'user',
});

export class ArchError extends Error {
  constructor(errors, warnings = []) {
    const list = Array.isArray(errors) ? errors : [errors];
    super(list.join('\n'));
    this.name = 'ArchError';
    this.errors = list;
    this.warnings = warnings;
  }
}

export function resolveKind(name) {
  if (typeof name !== 'string') return undefined;
  const k = name.trim().toLowerCase();
  return Object.hasOwn(KIND_ALIASES, k) ? KIND_ALIASES[k] : undefined;
}

export function levenshtein(a, b) {
  const m = a.length, n = b.length;
  if (!m) return n;
  if (!n) return m;
  let prev = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[n];
}

// Closest candidate, or undefined when nothing is plausibly a typo.
export function didYouMean(word, candidates) {
  const w = String(word).toLowerCase();
  let best, bestD = Infinity;
  for (const c of candidates) {
    const d = levenshtein(w, String(c).toLowerCase());
    if (d < bestD) { bestD = d; best = c; }
  }
  const limit = Math.max(1, Math.min(3, Math.floor(Math.max(w.length, 3) / 3)));
  return bestD <= limit ? best : undefined;
}

function hint(word, candidates) {
  const s = didYouMean(word, candidates);
  return s !== undefined ? ` (did you mean "${s}"?)` : '';
}

function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }

// Step numbers for the edges. Default: the order of the edges in the source. An edge may carry `step`
// (from a `%% step: a->b 3` line) to override; the other edges then take the lowest unused numbers in
// source order. Returns {steps: number[] (per edge), errors: string[]}.
export function assignSteps(graph) {
  const edges = Array.isArray(graph.edges) ? graph.edges : [];
  const n = edges.length, errors = [], steps = new Array(n).fill(0);
  const owner = new Map();
  edges.forEach((e, i) => {
    if (e.step === undefined) return;
    const d = `edge ${i + 1} (${e.from} -> ${e.to})`;
    if (!Number.isInteger(e.step) || e.step < 1) { errors.push(`${d}: step must be a whole number from 1 to ${n}`); return; }
    if (e.step > n) { errors.push(`${d}: step ${e.step} is larger than the number of edges (${n}); steps must run 1 to ${n} with no gaps`); return; }
    if (owner.has(e.step)) { errors.push(`step ${e.step} is given to both edge ${owner.get(e.step) + 1} and edge ${i + 1}; each step number can be used once`); return; }
    owner.set(e.step, i); steps[i] = e.step;
  });
  let next = 1;
  edges.forEach((e, i) => {
    if (steps[i]) return;
    if (e.step !== undefined) return;
    while (owner.has(next)) next++;
    owner.set(next, i); steps[i] = next;
  });
  if (!errors.length) {
    for (let k = 1; k <= n; k++) if (!owner.has(k)) errors.push(`step ${k} is missing; steps must run 1 to ${n} with no gaps`);
  }
  return { steps, errors };
}

// Returns {errors:[string], warnings:[string]}. Numbering in messages is 1-based.
export function validateGraph(g) {
  const errors = [], warnings = [];
  if (!g || typeof g !== 'object') return { errors: ['graph must be an object with nodes and edges'], warnings };
  const nodes = Array.isArray(g.nodes) ? g.nodes : [];
  const edges = Array.isArray(g.edges) ? g.edges : [];
  const groups = Array.isArray(g.groups) ? g.groups : [];
  const messages = Array.isArray(g.messages) ? g.messages : [];

  if (g.direction !== undefined && !DIRECTIONS.includes(normDirection(g.direction))) {
    errors.push(`direction "${g.direction}" is not one of ${DIRECTIONS.join(', ')}`);
  }
  if (!nodes.length) errors.push('the graph has no nodes; add at least one node');

  // groups
  const groupIds = new Set();
  groups.forEach((gr, i) => {
    if (!gr || typeof gr.id !== 'string' || !gr.id) { errors.push(`group ${i + 1}: needs an id`); return; }
    if (groupIds.has(gr.id)) errors.push(`group ${i + 1}: id "${gr.id}" is used twice; group ids must be unique`);
    groupIds.add(gr.id);
    if (typeof gr.label !== 'string' || !gr.label.trim()) errors.push(`group ${i + 1} ("${gr.id}"): needs a label`);
    else if (gr.label.length > LIMITS.groupLabel) {
      warnings.push(`group "${gr.id}": label is ${gr.label.length} characters; the atom shows at most ${LIMITS.groupLabel}, so it will be cut. Shorten it.`);
    }
  });

  // nodes
  const ids = new Set();
  nodes.forEach((n, i) => {
    const at = `node ${i + 1}`;
    if (!n || typeof n.id !== 'string' || !n.id) { errors.push(`${at}: needs an id`); return; }
    if (!ID_RE.test(n.id)) {
      errors.push(`${at}: id "${n.id}" is not valid; use a lowercase letter first, then lowercase letters, digits, "_" or "-", up to 32 characters`);
    }
    if (ids.has(n.id)) errors.push(`${at}: id "${n.id}" is used twice; node ids must be unique`);
    ids.add(n.id);
    if (typeof n.label !== 'string' || !n.label.trim()) errors.push(`${at} ("${n.id}"): needs a label`);
    else if (n.label.length > LIMITS.label) {
      warnings.push(`node "${n.id}": label is ${n.label.length} characters; the atom shows at most ${LIMITS.label}, so it will be cut. Shorten it or move detail into the sub-label.`);
    }
    if (n.sub !== undefined && String(n.sub).length > LIMITS.sub) {
      warnings.push(`node "${n.id}": sub-label is ${String(n.sub).length} characters; the atom shows at most ${LIMITS.sub}.`);
    }
    if (n.kind !== undefined && !KINDS.includes(n.kind)) {
      errors.push(`node "${n.id}": kind "${n.kind}" is not one of ${KINDS.join(', ')}` + (resolveKind(n.kind) ? ` (did you mean "${resolveKind(n.kind)}"?)` : hint(n.kind, KINDS)));
    }
    if (n.group !== undefined && !groupIds.has(n.group)) {
      errors.push(`node "${n.id}": group "${n.group}" is not a group id` + hint(n.group, [...groupIds]));
    }
  });

  // edges
  const ndList = [...ids];
  const touched = new Set();
  edges.forEach((e, i) => {
    const at = `edge ${i + 1}`;
    if (!e || typeof e !== 'object') { errors.push(`${at}: must be an object with from and to`); return; }
    let bad = false;
    for (const end of ['from', 'to']) {
      if (typeof e[end] !== 'string' || !ids.has(e[end])) {
        errors.push(`${at}: "${e[end]}" is not a node id${hint(e[end] ?? '', ndList)}`);
        bad = true;
      }
    }
    if (bad) return;
    if (e.from === e.to) { errors.push(`${at}: "${e.from}" points at itself; the atom cannot draw self-loops. Remove the edge or add a second node.`); return; }
    if (e.style !== undefined && !STYLES.includes(e.style)) {
      errors.push(`${at}: style "${e.style}" is not one of ${STYLES.join(', ')}`);
    }
    if (e.label !== undefined && String(e.label).length > LIMITS.edgeLabel) {
      warnings.push(`${at}: label is ${String(e.label).length} characters; the atom shows at most ${LIMITS.edgeLabel}.`);
    }
    touched.add(e.from); touched.add(e.to);
  });
  const seen = new Map();
  edges.forEach((e, i) => {
    if (!e || e.from === e.to) return;
    const k = e.from + '>' + e.to + '|' + (e.style || 'sync') + '|' + (e.label || '');
    if (seen.has(k)) warnings.push(`edge ${i + 1}: duplicates edge ${seen.get(k)} (${e.from} -> ${e.to}); consider merging them into one labelled edge.`);
    else seen.set(k, i + 1);
  });
  nodes.forEach((n) => {
    if (n && ids.has(n.id) && !touched.has(n.id) && nodes.length > 1) {
      warnings.push(`node "${n.id}" has no edges; it will sit on its own in the layout. Connect it or remove it.`);
    }
  });

  // messages
  messages.forEach((m, i) => {
    const at = `message ${i + 1}`;
    if (!m || typeof m !== 'object') { errors.push(`${at}: must be an object with from, to and text`); return; }
    let bad = false;
    for (const end of ['from', 'to']) {
      if (typeof m[end] !== 'string' || !ids.has(m[end])) {
        errors.push(`${at}: "${m[end]}" is not a node id${hint(m[end] ?? '', ndList)}`);
        bad = true;
      }
    }
    if (bad) return;
    if (typeof m.text !== 'string' || !m.text.trim()) { errors.push(`${at}: needs text (the payload chip)`); return; }
    if (m.text.length > LIMITS.msgText) warnings.push(`${at}: text is ${m.text.length} characters; the atom shows at most ${LIMITS.msgText}.`);
    const fwd = edges.some((e) => e && e.from === m.from && e.to === m.to);
    const rev = edges.some((e) => e && e.from === m.to && e.to === m.from);
    if (!fwd && !rev) {
      errors.push(`${at}: there is no edge between "${m.from}" and "${m.to}" for the chip to ride; add that edge or fix the ids`);
    } else if (!fwd && rev) {
      warnings.push(`${at}: only the edge ${m.to} -> ${m.from} exists, so the chip "${m.text}" rides it backwards (reply direction).`);
    }
  });

  edges.forEach((e, i) => {
    if (e && e.relation !== undefined && (typeof e.relation !== 'string' || e.relation.length > LIMITS.relation)) errors.push(`edge ${i + 1}: relation must be text of at most ${LIMITS.relation} characters (for example "calls" or "reports back")`);
  });
  if (g.relationName !== undefined && (typeof g.relationName !== 'string' || !g.relationName.trim() || g.relationName.length > LIMITS.relation)) errors.push(`relationName must be 1 to ${LIMITS.relation} characters`);
  if (g.relationColumn !== undefined && typeof g.relationColumn !== 'boolean') errors.push('relationColumn must be true or false');
  if (g.pace !== undefined && !Object.hasOwn(PACES, g.pace)) errors.push(`pace "${g.pace}" is not one of ${Object.keys(PACES).join(', ')}`);
  if (g.duration !== undefined && !(typeof g.duration === 'number' && g.duration >= 2 && g.duration <= 120)) errors.push(`duration "${g.duration}" must be a number of seconds from 2 to 120`);
  if (g.numbered || edges.some((e) => e && e.step !== undefined)) {
    if (!errors.some((e) => /^edge \d+: "/.test(e))) errors.push(...assignSteps(g).errors);
  }
  // caps: never truncate silently, tell the user how to split
  const groupSizes = groups.map((gr) => [gr.label || gr.id, nodes.filter((n) => n && n.group === gr.id).length]).sort((a, b) => b[1] - a[1]);
  if (nodes.length > LIMITS.nodes) {
    const over = nodes.length - LIMITS.nodes;
    let how = 'Split it into two diagrams (one per subsystem), or merge small nodes into one.';
    if (groupSizes.length > 1) how = `Split it by group: ${groupSizes.slice(0, 4).map(([l, c]) => `"${l}" has ${plural(c, 'node', 'nodes')}`).join(', ')}; draw one diagram per group, or collapse a group into a single node.`;
    errors.push(`the graph has ${nodes.length} nodes; the atom draws at most ${LIMITS.nodes} (${over} over). ${how}`);
  }
  if (edges.length > LIMITS.edges) {
    errors.push(`the graph has ${edges.length} edges; the atom draws at most ${LIMITS.edges}. Remove the ${edges.length - LIMITS.edges} least important, merge duplicate calls into one labelled edge, or split into two diagrams.`);
  }
  if (groups.length > LIMITS.groups) {
    errors.push(`the graph has ${groups.length} groups; the atom draws at most ${LIMITS.groups}. Merge related groups, or turn the smallest into plain nodes.`);
  }
  if (messages.length > LIMITS.messages) {
    errors.push(`the graph has ${messages.length} messages; the atom animates at most ${LIMITS.messages}. Keep the ${LIMITS.messages} that tell the story.`);
  }
  if (g.title !== undefined && String(g.title).length > LIMITS.title) {
    warnings.push(`title is ${String(g.title).length} characters; the atom keeps at most ${LIMITS.title} for the accessible name.`);
  }
  return { errors, warnings };
}
