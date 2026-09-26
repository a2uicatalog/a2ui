// One-off generator (run manually, not part of the test suite): dumps the REAL JS validateParts() output for
// every fixture in tests/fixtures/bricks/parts_fixtures-v0.1.json into
// tests/fixtures/bricks/parts_parity_cases.json, the same way tests/fixtures/bricks/parity_cases.json was
// captured from the procedural validator's JS output. The Python twin (renderers/brick_parts_validate.py) is
// checked against this file, not against the fixtures' own hand-computed `expect` block, so parity means
// "byte-identical to what the browser's validator actually produces" (including exact detail strings), the
// same guarantee tests/test_brick_validate.py already gives the procedural validator.
import { readFileSync, writeFileSync } from "fs";
import vm from "vm";

const root = new URL("../", import.meta.url);
const gs = readFileSync(new URL("apps-script-surface/gas-wired-renderer/atoms_brick.gs", root), "utf8");
const ctx = { _RENDERERS: {}, console };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const kit = vm.runInContext("_brickKit()", ctx);

const F = JSON.parse(readFileSync(new URL("tests/fixtures/bricks/parts_fixtures-v0.1.json", root), "utf8"));
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

const cases = F.fixtures.map(f => {
  const list = f.parts.map(p => ({p: PART_ID_ALIAS[p[0]] || p[0], x: p[1], y: p[2], z: p[3], r: p[4], c: "#c91a09"}));
  const r = kit.validateParts(list);
  return {
    name: f.name,
    parts: list,
    expected: {
      ok: r.ok, checks: r.checks, connections: r.connections, studConnections: r.studConnections,
      pinConnections: r.pinConnections, collisions: r.collisions, overlaps: r.overlaps,
      floating: r.floating, balance: r.balance, com: r.com,
    },
  };
});
writeFileSync(new URL("tests/fixtures/bricks/parts_parity_cases.json", root), JSON.stringify({cases}, null, 1) + "\n");
console.log("wrote", cases.length, "cases");
