#!/usr/bin/env node
/**
 * a2uicatalog-mcp — local MCP server for the A2UI Atomic Catalog.
 *
 * Implements the official A2UI-over-MCP pattern (a2ui.org/guides/a2ui_over_mcp):
 * an agent browses the atom vocabulary, authors a wired surface, validates it
 * (a hallucinated atom is a parse error, not a broken screen), and either gets
 * a shareable preview URL or deploys straight to its own Google Apps Script.
 *
 * list_atoms / get_atom_schema / validate_payload / encode_url / get_ui are
 * pure-local: bundled catalog data (mcp/data/, see scripts/sync-data.mjs),
 * no secret, no network. build_app is the one tool that calls out — to the
 * caller's OWN Apps Script deployment, with the caller's own token (BYO,
 * never a shared secret; see README's Security section). stdio transport.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { gzipSync } from "zlib";

// Bundled inside THIS package (mcp/data/, synced by scripts/sync-data.mjs)
// rather than read via "../public/..." out of the wider a2ui-catalogue repo
// tree — that relative path only resolves in a git checkout of the whole
// monorepo, and breaks the moment this package is installed standalone
// (`npm install @a2uicatalog/mcp` ships only mcp/'s own files). See sync-data.mjs's
// header for why bundling a snapshot, not a live fetch, is the fix.
const DATA = join(dirname(fileURLToPath(import.meta.url)), "data");
const A2UI_MIME = "application/a2ui+json";

// ── bundled, public, read-only ──────────────────────────────────────────────
const index = JSON.parse(readFileSync(join(DATA, "atoms-index.json"), "utf8"));
const ATOMS = new Map(index.atoms.map((a) => [a.type, a]));
// Full field contracts (for get_atom_schema) from the published spec.
const SPEC = JSON.parse(readFileSync(join(DATA, "spec.json"), "utf8"));
const ATOM_SPEC = new Map(SPEC.atoms.map((a) => [a.type, a]));
for (const a of SPEC.atoms) for (const al of a.aliases || []) ATOM_SPEC.set(al, a);
// Resolve published aliases (data_table -> data_table_sortable) from the catalog.
for (const a of index.atoms) for (const al of a.aliases || []) ATOMS.set(al, a);
// The a2ui-state catalog: the behavioral vocabulary a wired surface also speaks.
// Migrated to the A2UI-v1.0 catalog shape (components/functions objects keyed
// by name) since this file was last touched — the old flat `primitives` array
// with `.id` fields no longer exists (confirmed broken here, 2026-07-31: this
// package's own test.mjs threw on startup). STATE_PRIMITIVES is the union of
// both — a wired surface's state_primitives can reference either a stateful
// component (ValueStore, ...) or a derived-value function (elapsed_seconds, ...).
const stateCatalog = JSON.parse(readFileSync(join(DATA, "a2ui-state-v1.json"), "utf8"));
const STATE_PRIMITIVE_DOCS = new Map([
  ...Object.entries(stateCatalog.components || {}),
  ...Object.entries(stateCatalog.functions || {}),
]);
const STATE_PRIMITIVES = new Set(STATE_PRIMITIVE_DOCS.keys());
// Reference wired UIs served over MCP (public payloads only).
const UIS = {
  "expenses-demo": "expenses-demo.json",
  "artemis-roadmap": "artemis-roadmap.json",
};
function loadUI(name) {
  return JSON.parse(readFileSync(join(DATA, UIS[name]), "utf8"));
}

// Structural layout wrappers (not atoms). Atom aliases now resolve from the
// PUBLISHED catalog (ATOMS includes them), so the earlier harvest hack is gone —
// the validator references the real a2ui-atoms-v1 + a2ui-state-v1 catalogs.
const WIRED_ATOMS = new Set(["row_open", "row_close", "subheading", "body", "divider", "jump_nav"]);
// carry over any layout atoms used in reference UIs not yet promoted to schema
for (const name of Object.keys(UIS)) {
  for (const el of loadUI(name).layout || []) {
    const t = el.atom || el.type;
    if (t && !ATOMS.has(t)) WIRED_ATOMS.add(t);
  }
}

// Structural validation: every layout atom's type must be a known atom, and a
// wired surface's wires must reference declared nodes. (No execution.)
function validate(payload) {
  const errors = [];
  const layout = payload.layout || [];
  const nodeIds = new Set([
    ...(payload.state_primitives || []).map((p) => p.id),
    ...(payload.actions || []).map((a) => a.id),
    ...layout.map((el) => el.id).filter(Boolean),
  ]);
  const known = (t) => ATOMS.has(t) || WIRED_ATOMS.has(t);
  // state_primitives validate against the a2ui-state catalog (the behavioral half)
  for (const p of payload.state_primitives || []) {
    if (p.primitive && !STATE_PRIMITIVES.has(p.primitive)) {
      errors.push(`unknown state primitive: ${p.primitive} (id ${p.id || "?"})`);
    }
  }
  for (const el of layout) {
    const t = el.atom || el.type;
    if (t && !known(t)) errors.push(`unknown atom type: ${t} (id ${el.id || "?"})`);
    for (const expr of Object.values(el.wire || {})) {
      const m = /^#(\w+)\./.exec(String(expr));
      if (m && !nodeIds.has(m[1])) errors.push(`wire references undeclared node #${m[1]} (id ${el.id || "?"})`);
    }
  }
  const wired = payload.type === "a2ui_wired_surface";
  return {
    ok: errors.length === 0,
    wired,
    counts: { atoms: layout.length, state: (payload.state_primitives || []).length, actions: (payload.actions || []).length },
    errors,
  };
}

function encodeUrl(payload, base = "<public_exec>") {
  const enc = gzipSync(Buffer.from(JSON.stringify(payload))).toString("base64url");
  return `${base}/exec?p=${enc}`;
}

const MAX_INPUT = 256 * 1024; // 256KB cap on agent-supplied payloads/docs
// Never let a token surface in any response/error text (query-param token leak guard).
function redact(text) {
  let t = String(text);
  if (process.env.BUILD_API_TOKEN) t = t.split(process.env.BUILD_API_TOKEN).join("***");
  return t.replace(/([?&]token=)[^&\s"']+/gi, "$1***");
}
function tooBig(s) { return typeof s === "string" && s.length > MAX_INPUT; }

const server = new McpServer({ name: "a2uicatalog-mcp", version: "0.1.0" });

// ── OFFICIAL SERVING PATTERN: A2UI as MCP Resource (application/a2ui+json) ──
for (const name of Object.keys(UIS)) {
  server.registerResource(
    name,
    `a2ui://${name}`,
    { title: `A2UI: ${name}`, description: `Wired A2UI surface (${name})`, mimeType: A2UI_MIME },
    async (uri) => ({
      contents: [{ uri: uri.href, mimeType: A2UI_MIME, text: JSON.stringify(loadUI(name)) }],
    })
  );
}

// ── OFFICIAL SERVING PATTERN: dynamic UI via Tool -> EmbeddedResource ──
server.registerTool(
  "get_ui",
  { title: "Get A2UI surface", description: "Return a wired A2UI surface as an EmbeddedResource (application/a2ui+json).",
    inputSchema: { name: z.enum(Object.keys(UIS)) } },
  async ({ name }) => {
    const payload = loadUI(name);
    return {
      content: [{ type: "resource", resource: { uri: `a2ui://${name}`, mimeType: A2UI_MIME, text: JSON.stringify(payload) } }],
    };
  }
);

// ── AUTHORING TOOLS: vocabulary + validation (the wired-authoring surface) ──
server.registerTool(
  "list_atoms",
  { title: "List A2UI atoms", description: "Browse the atom vocabulary (compact descriptions).",
    inputSchema: { query: z.string().optional() } },
  async ({ query }) => {
    let atoms = index.atoms;
    if (query) atoms = atoms.filter((a) => (a.type + " " + a.compact).toLowerCase().includes(query.toLowerCase()));
    return { content: [{ type: "text", text: JSON.stringify(atoms.slice(0, 40).map((a) => ({ type: a.type, compact: a.compact })), null, 1) }] };
  }
);

server.registerTool(
  "get_atom_schema",
  { title: "Get an atom's field contract",
    description: "Full field contract + surfaces for one atom (or state primitive), from the published catalogs.",
    inputSchema: { type: z.string().describe("atom type or state primitive id") } },
  async ({ type }) => {
    const atom = ATOM_SPEC.get(type);
    if (atom) return { content: [{ type: "text", text: JSON.stringify(atom, null, 1) }] };
    const prim = STATE_PRIMITIVE_DOCS.get(type);
    if (prim) return { content: [{ type: "text", text: JSON.stringify({ id: type, ...prim, catalog: "a2ui-state-v1" }, null, 1) }] };
    return { isError: true, content: [{ type: "text", text: `unknown type: ${type} — not in a2ui-atoms-v1 or a2ui-state-v1` }] };
  }
);

server.registerTool(
  "validate_payload",
  { title: "Validate an A2UI payload", description: "Structural validation of an authored A2UI payload (atom types + wire references). No execution.",
    inputSchema: { payload: z.any() } },
  async ({ payload }) => {
    if (tooBig(JSON.stringify(payload))) return { isError: true, content: [{ type: "text", text: `payload too large (max ${MAX_INPUT} bytes)` }] };
    return { content: [{ type: "text", text: JSON.stringify(validate(payload), null, 1) }] };
  }
);

server.registerTool(
  "encode_url",
  { title: "Encode preview URL", description: "gzip+base64url an A2UI payload into a renderer ?p= URL.",
    inputSchema: { payload: z.any() } },
  async ({ payload }) => ({ content: [{ type: "text", text: encodeUrl(payload) }] })
);

// ── THE KILLER TOOL: build_app — author -> Build API -> LIVE Apps Script URL ──
// BYO-local: BUILD_API_URL + BUILD_API_TOKEN come from the dev's own env; this
// deploys to the DEV's own Apps Script, never a shared surface. Token never in code.
server.registerTool(
  "build_app",
  { title: "Build a live Apps Script web app",
    description: "Deploy a training.md document to YOUR Apps Script via the A2UI Build API — returns a live GAS web app URL. Requires env BUILD_API_URL and BUILD_API_TOKEN (BYO, local).",
    inputSchema: { training_md: z.string().describe("A compliant training.md document") } },
  async ({ training_md }) => {
    const url = process.env.BUILD_API_URL, token = process.env.BUILD_API_TOKEN;
    if (!url || !token) {
      return { isError: true, content: [{ type: "text", text: "Set BUILD_API_URL and BUILD_API_TOKEN in your environment (BYO Apps Script). The build tool never carries a token in code." }] };
    }
    if (tooBig(training_md)) return { isError: true, content: [{ type: "text", text: `training_md too large (max ${MAX_INPUT} bytes)` }] };
    try {
      const res = await fetch(`${url}?api=training&token=${encodeURIComponent(token)}`, {
        method: "POST", headers: { "Content-Type": "text/plain" }, body: training_md,
      });
      const body = await res.json();
      if (!body.ok) return { isError: true, content: [{ type: "text", text: redact("Build failed: " + (body.error || JSON.stringify(body))) }] };
      return { content: [{ type: "text", text: JSON.stringify({ ok: true, url: body.url, coverage: body.coverage, steps: body.steps, warnings: body.warnings }, null, 1) }] };
    } catch (e) {
      return { isError: true, content: [{ type: "text", text: redact("build_app error: " + (e.message || String(e))) }] };
    }
  }
);

export async function buildApp(training_md) {
  const url = process.env.BUILD_API_URL, token = process.env.BUILD_API_TOKEN;
  const res = await fetch(`${url}?api=training&token=${encodeURIComponent(token)}`,
    { method: "POST", headers: { "Content-Type": "text/plain" }, body: training_md });
  return res.json();
}

// Export internals for the test harness (when imported, not run over stdio).
export { validate, encodeUrl, loadUI, ATOMS };

if (process.argv[1] && process.argv[1].endsWith("server.mjs")) {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("a2uicatalog-mcp test harness on stdio");
}
