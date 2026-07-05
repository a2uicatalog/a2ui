#!/usr/bin/env node
/**
 * Conformance harness: the Apps Script roadmap parser port must produce
 * payloads deep-equal to the Python reference for every fixture.
 *
 * Run: node scripts/test_roadmap_parity.mjs
 */
import { readFileSync, existsSync, writeFileSync, unlinkSync } from "fs";
import { execFileSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { tmpdir } from "os";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const FIXTURES = ["examples/artemis.roadmap.md"];
// Private-tier fixture — exercised locally when the sibling repo is present.
const PRIVATE_FIXTURE = join(ROOT, "../a2ui-private/knowledge-private/a2uicatalog.roadmap.md");
if (existsSync(PRIVATE_FIXTURE)) FIXTURES.push(PRIVATE_FIXTURE);

// Load the .gs file — plain JS by design (no GAS APIs in the parser).
(0, eval)(readFileSync(join(ROOT, "apps-script-surface/parsers/roadmap_parser.gs"), "utf8"));
const parseRoadmapMd = globalThis.parseRoadmapMd;

function canon(obj) {
  if (Array.isArray(obj)) return obj.map(canon);
  if (obj && typeof obj === "object") {
    const out = {};
    for (const k of Object.keys(obj).sort()) out[k] = canon(obj[k]);
    return out;
  }
  return obj;
}

function pyParse(path) {
  return JSON.parse(execFileSync("python3",
    [join(ROOT, "scripts/parse_roadmap_md.py"), path], { encoding: "utf8" }));
}

let failed = 0;
for (const fixture of FIXTURES) {
  const path = fixture.startsWith("/") ? fixture : join(ROOT, fixture);
  const md = readFileSync(path, "utf8");
  const js = parseRoadmapMd(md);
  const py = pyParse(path);

  const a = JSON.stringify(canon(js.payload));
  const b = JSON.stringify(canon(py));
  if (a === b) {
    console.log(`✅ ${fixture} — GAS port matches Python reference (${js.report.phases} phases, ${js.report.items} items)`);
  } else {
    failed++;
    console.error(`❌ ${fixture} — MISMATCH`);
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) {
        console.error(`  first divergence @${i}:\n   gs: …${a.slice(Math.max(0, i - 60), i + 80)}\n   py: …${b.slice(Math.max(0, i - 60), i + 80)}`);
        break;
      }
    }
    if (a.length !== b.length && failed) {
      console.error(`  lengths: gs=${a.length} py=${b.length}`);
    }
  }
}

// Error-path parity: a bad doc must fail with the same lint codes in both.
const bad = "---\nid: t\ndomain: roadmap\nname: T\nsource: s\nlicense: MIT\nrender: x\n---\n\n# Phases\n## 1 · P\n1. Thing\n   status: shipped\n   owner: me\n\n# Epics\n- x\n\n# Risks\n- catastrophic :: t\n";
const jsBad = parseRoadmapMd(bad);
const jsCodes = jsBad.report.errors.map((e) => e.split(":")[0]).sort().join(",");

const tmp = join(tmpdir(), `roadmap-parity-bad-${process.pid}.md`);
writeFileSync(tmp, bad);
let pyCodes = "";
try {
  execFileSync("python3", [join(ROOT, "scripts/parse_roadmap_md.py"), tmp], { encoding: "utf8" });
} catch (e) {
  pyCodes = (e.stderr || "").split("\n")
    .filter((l) => l.startsWith("ERROR "))
    .map((l) => l.slice(6).split(":")[0]).sort().join(",");
} finally {
  unlinkSync(tmp);
}

if (jsBad.payload === null && jsCodes === pyCodes && jsCodes.length) {
  console.log(`✅ error-path — same lint codes in both (${jsCodes})`);
} else {
  failed++;
  console.error(`❌ error-path — gs codes [${jsCodes}] vs py codes [${pyCodes}]`);
}

process.exit(failed ? 1 : 0);
