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

// Axle-through-hole mated pair exemption test (2026-09-28)
loadMesh('3700');
loadMesh('3704');
const rAxle = kit.validateParts([
  {p: '3700', x: 0, y: -24, z: 0, r: 0},
  {p: '3704', x: 0, y: -14, z: 0, r: 1}
]);
if (rAxle.axleConnections !== 1 || rAxle.overlaps !== 0 || rAxle.collisions.length !== 0) {
  console.error("Axle-through-hole test failed:", rAxle);
  process.exit(1);
}
console.log("  ✓ axle_through_hole_mating_and_exemption");

// Clip-around-bar mated pair exemption test (2026-09-28)
loadMesh('2921');
loadMesh('4085c');
const rClip = kit.validateParts([
  {p: '2921', x: 0, y: -24, z: 0, r: 0},
  {p: '4085c', x: 0, y: -24, z: 0, r: 0}
]);
if (rClip.clipConnections !== 1 || rClip.overlaps !== 0 || rClip.collisions.length !== 0) {
  console.error("Clip-around-bar test failed:", rClip);
  process.exit(1);
}
console.log("  ✓ clip_around_bar_mating_and_exemption");

// Continuous (non-preset) rotation OBB/SAT cross-check (2026-09-29) -- the JS twin of the Python OBB/SAT core
// (rot_ldu/_world_boxes/_boxes_overlap in renderers/brick_parts_validate.py). Same real matrices and same
// expected outcomes as tests/test_brick_parts_validate.py's test_real_cited_matrix_hinge_no_false_collision /
// test_rotated_boxes_deliberate_collision_detected, replayed here through the ACTUAL JS validateParts() so a
// translation bug in rotLDU/worldBoxes/boxesOverlap's matrix branch would be caught on this side too, not just
// trusted because the Python side passes.
const M_HINGE_29 = [-0.868, 0.0, 0.496, 0.0, 1.0, 0.0, -0.496, 0.0, -0.868];
const M_METRO_30 = [0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866];
const M_METRO_60 = [0.5, 0.0, 0.866, 0.0, 1.0, 0.0, -0.866, 0.0, 0.5];
const M_METRO_150 = [-0.866, 0.0, 0.5, 0.0, 1.0, 0.0, -0.5, 0.0, -0.866];
const M_PANTOGRAPH_16_5 = [1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0];
const M_TECHNIC_33_9 = [0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0];

// Real 2429/2430 mated hinge at ~29.7 degrees (8880-1 Super Car) -- must NOT false-collide under OBB/SAT.
loadMesh('2429');
loadMesh('2430');
const rHinge = kit.validateParts([
  {p: '2429', x: 0, y: 0, z: 0, r: 0},
  {p: '2430', x: 0, y: 0, z: 0, r: M_HINGE_29}
]);
if (rHinge.overlaps !== 0 || rHinge.collisions.some(c => c[0] === 0 && c[1] === 1)) {
  console.error("Real hinge matrix (M_HINGE_29) false-collision test failed:", rHinge);
  process.exit(1);
}
console.log("  ✓ continuous_rotation_real_hinge_no_false_collision");

// Deliberate overlap under the SAME M_HINGE_29 matrix (offset into collision range) -- must BE detected, not
// silently missed by the matrix branch.
const rHingeColl = kit.validateParts([
  {p: '2429', x: 0, y: 0, z: 0, r: 0},
  {p: '2430', x: -6.28, y: 0, z: 23.64, r: M_HINGE_29}
]);
if (rHingeColl.overlaps < 1 || !rHingeColl.collisions.some(c => c[0] === 0 && c[1] === 1)) {
  console.error("Deliberate rotated-box collision test failed:", rHingeColl);
  process.exit(1);
}
console.log("  ✓ continuous_rotation_deliberate_collision_detected");

// Metroliner (10001-1) cab matrices + Technic 33.9deg diagonal brace (8880-1) -- a second instance of the
// same part, offset and rotated by each matrix, must not false-collide with the un-rotated instance.
loadMesh('3023');
for (const [name, m] of [['metro_30', M_METRO_30], ['metro_60', M_METRO_60], ['metro_150', M_METRO_150],
                          ['pantograph_16_5', M_PANTOGRAPH_16_5], ['technic_33_9', M_TECHNIC_33_9]]) {
  const r = kit.validateParts([
    {p: '3023', x: 0, y: 0, z: 0, r: 0},
    {p: '3023', x: 50, y: 0, z: 50, r: m}
  ]);
  if (r.overlaps !== 0 || r.collisions.some(c => c[0] === 0 && c[1] === 1)) {
    console.error("Real matrix (" + name + ") false-collision test failed:", r);
    process.exit(1);
  }
  console.log("  ✓ continuous_rotation_" + name + "_no_false_collision");
}

// Towball<->ball-socket mated pair exemption test (2026-09-29) -- real baked parts, same positions/tolerance
// as tests/test_brick_parts_validate.py's Python-side towball tests.
loadMesh('3184');
loadMesh('3730');
const rTowball = kit.validateParts([
  {p: '3184', x: 0, y: 0, z: 0, r: 0},
  {p: '3730', x: 0, y: 0, z: 0, r: 0}
]);
// overlaps is the real part-vs-part collision count; collisions may legitimately also carry floor-
// penetration entries ([-1, i]) unrelated to the mated-pair exemption being tested here (twin of the
// Python test's `assert report['overlaps'] == 0; assert [0, 1] not in report['collisions']` pattern).
if (rTowball.towballConnections !== 1 || rTowball.overlaps !== 0 ||
    rTowball.collisions.some(c => (c[0] === 0 && c[1] === 1) || (c[0] === 1 && c[1] === 0))) {
  console.error("Towball mating test failed:", rTowball);
  process.exit(1);
}
console.log("  ✓ towball_mating_and_exemption");

const rTowballFar = kit.validateParts([
  {p: '3184', x: 0, y: 0, z: 0, r: 0},
  {p: '3730', x: 200, y: 0, z: 0, r: 0}
]);
if (rTowballFar.towballConnections !== 0) {
  console.error("Towball far-apart false-mate test failed:", rTowballFar);
  process.exit(1);
}
console.log("  ✓ towball_far_apart_no_false_mate");

