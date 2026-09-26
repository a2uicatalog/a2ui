// brick_build_3d real-parts validator (spec/brick-parts-v0.1.md §2-4, Phase 3) — evals the ACTUAL JS out of
// apps-script-surface/gas-wired-renderer/atoms_brick.gs (no reimplementation, same convention as
// test_brick_validate_js.mjs) and replays all 15 fixtures in tests/fixtures/bricks/parts_fixtures-v0.1.json
// (a self-contained copy of a2ui-private/spec/brick-parts/fixtures-v0.1.json, vendored the same way
// tests/fixtures/a2ui_v1_0_spec/ is -- so CI, which does not check out the private sibling, actually runs
// this) against K.validateParts(). Part JSON is seeded into partMeshCache via the _setPartMesh test hook,
// read from public/parts/ locally (not fetched) since there is no `document`/canvas/WebGL in this Node
// environment to drive the normal async load path.
//
// This is the harness that found three real bugs while it was being built, none of them in validateParts()
// itself: a bake-time axis swap in generated_occupancy (scripts/ldraw/parts.py), a missing hand-authored
// occupancy override for 11211, and a wrong CONNECTOR_OVERRIDES entry for 15573 that halved its real
// bottom-socket count (see tests/test_ldraw_parts.py's test_jumper_plate_has_two_bottom_sockets_and_one_offgrid_top_stud
// for the bake-side lock). All 15 fixtures pass against the corrected bake output; this test keeps them passing.
import { readFileSync } from "fs";
import vm from "vm";

const root = new URL("../", import.meta.url);
const F = JSON.parse(readFileSync(new URL("tests/fixtures/bricks/parts_fixtures-v0.1.json", root), "utf8"));

const gs = readFileSync(new URL("apps-script-surface/gas-wired-renderer/atoms_brick.gs", root), "utf8");
const ctx = { _RENDERERS: {}, console };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const kit = vm.runInContext("_brickKit()", ctx);

const PART_ID_ALIAS = {"3023": "3023b", "3665": "3665a", "3660": "3660a", "60481": "60481a", "4032": "4032a",
                        "2654": "2654a", "4073": "6141"};
const meshCache = {};
function loadMesh(id) {
  id = PART_ID_ALIAS[id] || id;
  if (meshCache[id]) return meshCache[id];
  const m = JSON.parse(readFileSync(new URL("public/parts/" + id + ".json", root), "utf8"));
  meshCache[id] = m;
  kit._setPartMesh(id, m);
  return m;
}
for (const f of F.fixtures) for (const p of f.parts) loadMesh(p[0]);

const normPairs = c => JSON.stringify(c.map(pr => [...pr].sort((a, b) => a - b)).sort());

let pass = 0, fail = 0;
for (const f of F.fixtures) {
  const list = f.parts.map(p => ({p: PART_ID_ALIAS[p[0]] || p[0], x: p[1], y: p[2], z: p[3], r: p[4]}));
  const r = kit.validateParts(list);
  const exp = f.expect;
  const expBalance = exp.balance === "none" ? "fail" : exp.balance;
  const ok = r.studConnections === exp.stud_connections &&
             r.pinConnections === exp.pin_connections &&
             JSON.stringify(r.floating) === JSON.stringify(exp.floating) &&
             normPairs(r.collisions) === normPairs(exp.collisions) &&
             (exp.balance === "none" ? r.balance === "none" : r.balance === expBalance);
  console.log((ok ? "  ✓ " : "  ✗ ") + f.name);
  if (!ok) {
    console.log("      got: " + JSON.stringify({studConnections: r.studConnections, pinConnections: r.pinConnections,
      floating: r.floating, collisions: r.collisions, balance: r.balance}));
    console.log("      exp: " + JSON.stringify(exp));
  }
  ok ? pass++ : fail++;
}
console.log(`${pass}/${pass + fail} fixtures pass`);
if (fail) process.exit(1);
