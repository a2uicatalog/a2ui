#!/usr/bin/env node
/**
 * sync-data.mjs — refresh mcp/data/, the bundled catalog snapshot @a2ui/mcp
 * ships with.
 *
 * server.mjs used to read these files via a relative "../" path straight out
 * of the a2ui-catalogue repo tree (public/atoms/index.json, public/spec.json,
 * public/catalogue/a2ui-state-v1.json, payloads/*.json). That works from a
 * git checkout but breaks the moment this package is actually published and
 * installed standalone (`npm install @a2ui/mcp`): only mcp/'s own files ship
 * in the tarball, so "../public/..." would resolve to node_modules/@a2ui/'s
 * parent, not this repo — a crash on first run for every real installer,
 * caught here (2026-07-31) before ever publishing. Fetching the same data
 * live from a2uicatalog.ai at runtime was the other option; deliberately
 * NOT taken, because list_atoms/get_atom_schema/validate_payload/encode_url
 * are documented and designed as pure-local, no-network tools (see README's
 * Security section) — bundling a point-in-time snapshot keeps that promise.
 *
 * Run after any atom-change / state-catalog change, and always before
 * `npm publish` (also wired as this package's own prepublishOnly hook —
 * belt + braces, matches the repo's own "declare it, don't improvise it"
 * discipline: see ops/project-ops.yaml's mcp-sdk-sync-data process).
 */
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const MCP_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPO_ROOT = join(MCP_ROOT, "..");
const DATA_DIR = join(MCP_ROOT, "data");

const FILES = [
  ["public/atoms/index.json", "atoms-index.json"],
  ["public/spec.json", "spec.json"],
  ["public/catalogue/a2ui-state-v1.json", "a2ui-state-v1.json"],
  ["payloads/expenses-demo.json", "expenses-demo.json"],
  ["payloads/artemis-roadmap.json", "artemis-roadmap.json"],
];

mkdirSync(DATA_DIR, { recursive: true });
for (const [src, dest] of FILES) {
  const content = readFileSync(join(REPO_ROOT, src), "utf8");
  JSON.parse(content); // fail loudly on a malformed source rather than bundle garbage
  writeFileSync(join(DATA_DIR, dest), content);
  console.log(`  ${src} -> mcp/data/${dest} (${(content.length / 1024).toFixed(0)} KB)`);
}
console.log(`synced ${FILES.length} files into mcp/data/`);
