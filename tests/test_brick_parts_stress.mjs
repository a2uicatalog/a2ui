// Microduck-scale stress test for the real-parts validator (spec/brick-parts-v0.1.md §8: "Phase 3 adds ... a
// Microduck-scale stress model"). The literal Microduck is a 141-page external PDF booklet, not machine-readable
// data in this repo, so this builds a SYNTHETIC model of comparable scale and vocabulary instead: a solid
// running-bond block of 2x4 bricks (~1000 parts) plus a mixed-type cap layer (plates, tiles, slopes, a round
// part, a corner part) -- all placed by construction to be a valid build. Evals the REAL validateParts() out of
// atoms_brick.gs (no reimplementation). Asserts CORRECTNESS at scale (zero collisions, nothing floating, every
// check passing), not just "did not crash", plus a generous time budget so an accidental O(n^3) shows up.
import { readFileSync } from "fs";
import vm from "vm";

const root = new URL("../", import.meta.url);
const gs = readFileSync(new URL("apps-script-surface/gas-wired-renderer/atoms_brick.gs", root), "utf8");
const ctx = { _RENDERERS: {}, console };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const kit = vm.runInContext("_brickKit()", ctx);

for (const id of ["3001", "3024", "3070b", "3040b", "6141", "2357"]) {
  kit._setPartMesh(id, JSON.parse(readFileSync(new URL("public/parts/" + id + ".json", root), "utf8")));
}

// 3001 = 2x4 brick, 80 (X) x 40 (Z) LDU, origin at its centre; brick y=-24*(layer+1). Running bond: odd layers
// shift 40 LDU (one half-brick) along X so studs of each layer engage the layer below.
const COLS = 10, ROWS = 10, LAYERS = 10;
const parts = [];
for (let L = 0; L < LAYERS; L++) {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      parts.push({ p: "3001", x: 40 + c * 80 + (L % 2 ? 40 : 0), y: -24 * (L + 1), z: 20 + r * 40, r: 0 });
    }
  }
}
// cap layer on top of the last layer (even/odd parity of LAYERS decides the X shift of the top layer)
const topShift = (LAYERS - 1) % 2 ? 40 : 0, topY = -24 * LAYERS;
for (let c = 0; c < COLS; c++) parts.push({ p: "3024", x: 10 + topShift + c * 80, y: topY - 8, z: 10, r: 0 });
parts.push({ p: "6141", x: 10 + topShift + 20, y: topY - 8, z: 30, r: 0 });
parts.push({ p: "3070b", x: 10 + topShift + 60, y: topY - 8, z: 30, r: 0 });

const t0 = Date.now();
const r = kit.validateParts(parts);
const ms = Date.now() - t0;

let fail = 0;
const ok = (name, cond, extra = "") => { console.log((cond ? "  ✓ " : "  ✗ ") + name + (cond ? "" : "  " + extra)); if (!cond) fail++; };
console.log(`${parts.length} parts validated in ${ms} ms`);
ok("scale: at least 1000 parts", parts.length >= 1000, String(parts.length));
ok("no collisions", r.collisions.length === 0, JSON.stringify(r.collisions.slice(0, 5)));
ok("nothing floating", r.floating.length === 0, JSON.stringify(r.floating.slice(0, 10)));
ok("every check passes", r.ok && r.checks.every(c => c.status === "pass"), JSON.stringify(r.checks));
ok("time budget (30 s)", ms < 30000, ms + " ms");
console.log(fail ? `${fail} failed` : "stress test passed");
if (fail) process.exit(1);
