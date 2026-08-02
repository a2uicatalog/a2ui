#!/usr/bin/env node
// cli.mjs — the A2UI command line.
//
// The on-ramp for someone who wants the vocabulary and none of the protocol:
// no MCP client, no connector, no deployment, no account. Compose a payload
// against spec.json, render it, get HTML.
//
//   npx @a2uicatalog/mcp render page.json > page.html
//   npx @a2uicatalog/mcp validate page.json
//   npx @a2uicatalog/mcp atoms --surface email
//   npx @a2uicatalog/mcp surfaces quiz_set
//
// ZERO DEPENDENCIES. Node 18+ has fetch built in, and the vocabulary ships in
// data/ so validate and atoms work with no network at all. Only `render`
// leaves the machine, and only to the public endpoint.
//
// This file exists because package.json has described this package as
// "CLI + local MCP server" since 0.1.0 while `bin` pointed at the stdio MCP
// server and no command line existed. Same class of overclaim the catalogue
// spent 2026-08-02 removing from its own schema; the honest fix is to build
// the thing that was advertised.

import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.A2UI_BASE || 'https://a2uicatalog.ai';
const KEY = process.env.A2UI_RENDER_KEY || '';

const die = (msg, code = 1) => { process.stderr.write(`a2ui: ${msg}\n`); process.exit(code); };

function loadSpec() {
  for (const p of [join(HERE, 'data', 'spec.json'), join(HERE, '..', 'public', 'spec.json')]) {
    if (existsSync(p)) return JSON.parse(readFileSync(p, 'utf8'));
  }
  die('vocabulary not found — reinstall the package, or run from a repo checkout');
}

function readPayload(file) {
  const raw = file && file !== '-' ? readFileSync(file, 'utf8') : readFileSync(0, 'utf8');
  let p;
  try { p = JSON.parse(raw); } catch (e) { die(`${file || 'stdin'} is not valid JSON: ${e.message}`); }
  return Array.isArray(p) ? { blocks: p } : p;
}

// Walk nested blocks the way the render endpoint does, so validate sees the
// same atoms the server will.
function collect(blocks, out = new Set(), depth = 0) {
  if (depth > 20 || !Array.isArray(blocks)) return out;
  for (const b of blocks) {
    if (!b || typeof b !== 'object') continue;
    const t = b.component || b.type;
    if (typeof t === 'string') out.add(t);
    for (const v of Object.values(b)) {
      if (Array.isArray(v)) collect(v.filter((x) => x && typeof x === 'object'), out, depth + 1);
      else if (v && typeof v === 'object') collect([v], out, depth + 1);
    }
  }
  return out;
}

const CMD = {
  async render(args) {
    const surface = takeFlag(args, '--surface');
    const payload = readPayload(args[0]);
    const url = `${BASE}/api/render${surface ? `?surface=${encodeURIComponent(surface)}` : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(KEY ? { 'x-a2ui-render-key': KEY } : {}) },
      body: JSON.stringify(payload),
    });
    const body = await res.text();
    if (!res.ok) die(`render failed (${res.status}): ${body.slice(0, 300)}`);
    // Degradation is reported on stderr so stdout stays pipeable to a file.
    for (const [h, label] of [['x-a2ui-incompatible', 'omitted (incompatible)'],
                              ['x-a2ui-degraded', 'degraded'],
                              ['x-a2ui-unpublished', 'not published']]) {
      const v = res.headers.get(h);
      if (v) process.stderr.write(`a2ui: ${label} on ${surface || 'this surface'}: ${v}\n`);
    }
    process.stdout.write(body);
  },

  validate(args) {
    const spec = loadSpec();
    const known = new Map((spec.atoms || []).map((a) => [a.type, a]));
    const surface = takeFlag(args, '--surface');
    const payload = readPayload(args[0]);
    if (!Array.isArray(payload.blocks) || !payload.blocks.length) die('payload has no blocks');
    const used = [...collect(payload.blocks)];
    let bad = 0;
    for (const t of used) {
      const a = known.get(t);
      if (!a) { console.error(`  unknown atom  ${t}`); bad++; continue; }
      if (!surface) continue;
      const s = a.surfaces || {};
      if ((s.incompatible_on || []).some((x) => x.surface === surface)) {
        console.error(`  incompatible  ${t} on ${surface}`); bad++;
      } else if ((s.degraded_on || []).some((x) => x.surface === surface)) {
        console.error(`  degraded      ${t} on ${surface}`);
      }
    }
    console.log(`${used.length} atom(s) checked${surface ? ` for ${surface}` : ''}: ` +
                `${bad ? `${bad} problem(s)` : 'all valid'}`);
    process.exit(bad ? 1 : 0);
  },

  atoms(args) {
    const spec = loadSpec();
    const surface = takeFlag(args, '--surface');
    const grep = args[0];
    let list = spec.atoms || [];
    if (surface) list = list.filter((a) => ((a.surfaces || {}).works_on || []).includes(surface));
    if (grep) list = list.filter((a) => a.type.includes(grep) ||
      (a.compact_description || '').toLowerCase().includes(grep.toLowerCase()));
    for (const a of list) console.log(`${a.type.padEnd(28)} ${a.compact_description || ''}`);
    console.error(`\n${list.length} atom(s)${surface ? ` on ${surface}` : ''}`);
  },

  surfaces(args) {
    const t = args[0] || die('usage: a2ui surfaces <atom>');
    const a = (loadSpec().atoms || []).find((x) => x.type === t) || die(`unknown atom '${t}'`);
    const s = a.surfaces || {};
    console.log(`${t} — ${a.compact_description || ''}\n`);
    for (const x of s.works_on || []) console.log(`  works        ${x}`);
    for (const d of s.degraded_on || []) console.log(`  degraded     ${d.surface}  ${d.note || ''}`);
    for (const d of s.incompatible_on || []) console.log(`  incompatible ${d.surface}  ${d.reason || ''}`);
  },

  help() {
    process.stdout.write(`a2ui — the A2UI Atomic Catalog command line

  render <file|->  [--surface S]   payload in, HTML on stdout
  validate <file|-> [--surface S]  check atoms exist and are supported; exit 1 if not
  atoms [match] [--surface S]      browse the vocabulary
  surfaces <atom>                  where one atom works, degrades, or cannot go

Surfaces for --surface: web · mcp-apps · google-apps-script-web · google-meet-stage

  A2UI_BASE         override the endpoint (default https://a2uicatalog.ai)
  A2UI_RENDER_KEY   unmetered rendering, if you have a key

validate and atoms are fully offline — the vocabulary ships with the package.
Only render makes a network call. No account, no API key, no MCP client.

  npx @a2uicatalog/mcp render page.json > page.html
`);
  },
};

function takeFlag(args, name) {
  const i = args.indexOf(name);
  if (i === -1) return null;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
}

const [cmd, ...rest] = process.argv.slice(2);
const fn = CMD[cmd] || (cmd === undefined || cmd === '--help' || cmd === '-h' ? CMD.help : null);
if (!fn) die(`unknown command '${cmd}' — try: a2ui help`);
await fn(rest);
