#!/usr/bin/env node
/**
 * demo.mjs — the GAS-first MCP loop, narrated end to end.
 *
 * Proves (and storyboards) what an agent does through the MCP server:
 *   browse vocabulary → author → validate → DEPLOY to a live Apps Script app.
 *
 * Run:  BUILD_API_URL=… BUILD_API_TOKEN=… node demo.mjs
 * (BYO: your own Apps Script deployment + token.)
 */
import { validate, buildApp } from "./server.mjs";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const DATA = join(dirname(fileURLToPath(import.meta.url)), "data");
const step = (n, t) => console.log(`\n\x1b[36m● ${n}\x1b[0m ${t}`);

step("1", "browse the vocabulary  (list_atoms / get_atom_schema)");
const idx = JSON.parse(readFileSync(join(DATA, "atoms-index.json"), "utf8"));
const st = JSON.parse(readFileSync(join(DATA, "a2ui-state-v1.json"), "utf8"));
const primitiveCount = Object.keys(st.components || {}).length + Object.keys(st.functions || {}).length;
console.log(`   ${idx.atomCount} atoms (a2ui-atoms-v1) + ${primitiveCount} state primitives (a2ui-state-v1)`);
console.log(`   the agent speaks these — visual vocabulary + behavioral vocabulary`);

step("2", "author a wired surface  (agent composes A2UI)");
const md = `---
id: mcp-demo-live
domain: training
name: "Built by an agent, over MCP"
source: "gas-first mcp launch demo"
license: MIT
---
An interactive Apps Script web app — authored by an agent, validated, deployed.
# Steps
## 1. Speak the vocabulary
cmd: list_atoms
verify: atoms returned
## 2. Validate before deploy
cmd: validate_payload
verify: hallucination = parse error, not broken UI
## 3. Ship it
cmd: build_app
verify: live Apps Script URL
`;
console.log("   composed a training.md (doc → app)");

step("3", "validate  (parser catches mistakes — hallucination = parse error)");
const good = { type: "a2ui_wired_surface", title: "demo",
  state_primitives: [{ id: "q", primitive: "ValueStore", props: {} }],
  actions: [], layout: [{ id: "t", atom: "data_table", wire: { rows: "#q.value" } }] };
console.log("   valid wired surface →", JSON.stringify(validate(good).ok ? "OK" : validate(good).errors));
const bad = { ...good, layout: [{ id: "x", atom: "totally_made_up_atom" }] };
console.log("   hallucinated atom  → REJECTED:", validate(bad).errors[0]);

step("4", "DEPLOY  (build_app → live Apps Script web app)");
if (!process.env.BUILD_API_URL || !process.env.BUILD_API_TOKEN) {
  console.log("   [skipped — set BUILD_API_URL + BUILD_API_TOKEN to deploy live]");
} else {
  const r = await buildApp(md);
  console.log(r.ok ? `   ✅ LIVE: ${r.url}` : `   build failed`);
}
console.log("\n\x1b[32mThat's the loop.\x1b[0m Author → validate → live GAS app, over MCP. No code.\n");
