#!/usr/bin/env node
/**
 * Conformance harness: the Apps Script parser port must produce payloads
 * deep-equal to the Python reference implementation for every fixture.
 *
 * Run: node scripts/test_parser_parity.mjs
 */
import { readFileSync } from "fs";
import { execFileSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const FIXTURES = [
  "examples/clasp-deployment.training.md",
  "sampledocs/cloudflare-workers-get-started.training.md",
];

// Load the .gs file — plain JS by design (no GAS APIs in the parser).
// Indirect eval → global scope, so the .gs function declarations land on globalThis.
(0, eval)(readFileSync(join(ROOT, "apps-script-surface/gas-wired-renderer/training_parser.gs"), "utf8"));
const parseTrainingMd = globalThis.parseTrainingMd;

function canon(obj) {
  if (Array.isArray(obj)) return obj.map(canon);
  if (obj && typeof obj === "object") {
    const out = {};
    for (const k of Object.keys(obj).sort()) out[k] = canon(obj[k]);
    return out;
  }
  return obj;
}

let failed = 0;
for (const fixture of FIXTURES) {
  const md = readFileSync(join(ROOT, fixture), "utf8");
  const js = parseTrainingMd(md);
  const pyOut = execFileSync("python3", [join(ROOT, "scripts/parse_training_md.py"), join(ROOT, fixture)],
                             { encoding: "utf8" });
  const py = JSON.parse(pyOut);

  const a = JSON.stringify(canon(js.payload));
  const b = JSON.stringify(canon(py));
  if (a === b) {
    console.log(`✅ ${fixture} — GAS port matches Python reference (${js.report.step_count} steps, ${js.report.coverage})`);
  } else {
    failed++;
    console.error(`❌ ${fixture} — MISMATCH`);
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) {
        console.error(`  first divergence @${i}:\n   gs: …${a.slice(Math.max(0, i - 60), i + 80)}\n   py: …${b.slice(Math.max(0, i - 60), i + 80)}`);
        break;
      }
    }
  }
}

// Error-path parity: a file that must fail with the same codes in both.
const bad = "---\nid: t\ndomain: training\nname: T\nsource: s\nlicense: MIT\n---\n\n# Steps\n## 1. A\ncmd: x\ndo: y\n";
const jsBad = parseTrainingMd(bad);
const jsCodes = jsBad.report.errors.map((e) => e.split(":")[0]).sort().join(",");
if (jsBad.payload === null && jsCodes.includes("E05")) {
  console.log(`✅ error-path: E05 raised, payload withheld`);
} else {
  failed++;
  console.error(`❌ error-path mismatch: ${JSON.stringify(jsBad.report.errors)}`);
}

process.exit(failed ? 1 : 0);
