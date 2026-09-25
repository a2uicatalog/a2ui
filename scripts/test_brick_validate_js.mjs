// brick_build_3d parity — evals the ACTUAL JS out of
// apps-script-surface/gas-wired-renderer/atoms_brick.gs (no reimplementation) and replays
// tests/fixtures/bricks/parity_cases.json: the validator/normaliser the browser runs must reproduce
// every recorded number and detail string, the same fixtures renderers/brick_validate.py is held to
// (tests/test_brick_validate.py). Also checks the renderer's prop handling and its serialised script.
import { readFileSync } from "fs";
import vm from "vm";

const root = new URL("..", import.meta.url);
const gs = readFileSync(new URL("apps-script-surface/gas-wired-renderer/atoms_brick.gs", root), "utf8");
const ctx = { _RENDERERS: {}, console };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const kit = vm.runInContext("_brickKit()", ctx);
const cases = JSON.parse(readFileSync(new URL("tests/fixtures/bricks/parity_cases.json", root), "utf8")).cases;

let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => {
  console.log((cond ? "  ✓ " : "  ✗ ") + name + (cond ? "" : "  " + extra));
  cond ? pass++ : fail++;
};
const near = (a, b) => Math.abs(a - b) < 1e-9;

for (const c of cases) {
  const exp = c.expected;
  const M = kit.normalise(c.bricks.map(([x, y, z, w, d, h, col]) => ({ x, y, z, w, d, h, c: col })));
  const r = kit.validate(M.bricks);
  const checks = r.checks.map(k => ({ id: k.id, label: k.label, status: k.status, detail: k.detail }));
  ok(`${c.name}: checks (status + detail text)`, JSON.stringify(checks) === JSON.stringify(exp.checks),
     JSON.stringify(checks));
  ok(`${c.name}: counts`, r.connections === exp.connections && r.overlaps === exp.overlaps && r.floating === exp.floating);
  ok(`${c.name}: centre of mass`, near(r.com.x, exp.com.x) && near(r.com.z, exp.com.z) && near(r.com.margin, exp.com.margin));
  ok(`${c.name}: cost`, near(r.cost, exp.cost));
  ok(`${c.name}: steps`, M.steps === exp.steps);
}

// stock shapes: tiling + trim must give a model the validator passes (what the atom shows by default)
for (const name of Object.keys(kit.SHAPES)) {
  const M = kit.normalise(kit.voxelBricks(kit.SHAPES[name].fn, kit.SHAPES[name].b));
  const r = kit.validate(M.bricks);
  ok(`shape ${name}: every check passes`, r.ok && r.checks.every(k => k.status !== "fail"), JSON.stringify(r.checks));
}

// an empty model fails loudly rather than yielding NaN
let threw = false; try { kit.validate([]); } catch (e) { threw = true; }
ok("validate([]) throws", threw);
threw = false; try { kit.normalise([]); } catch (e) { threw = true; }
ok("normalise([]) throws", threw);

// renderer: junk props degrade to defaults, hostile data cannot break out of the inline script
const R = ctx._RENDERERS.brick_build_3d;
const junk = R({ bricks: "", shape: "nope", bg: "red;x", height: "9999", speed: "abc" });
ok("junk props clamp/fall back", junk.includes("height:900px") && !junk.includes("red;x") && junk.includes('"shape":"heart"'));
const evil = R({ bricks: [{ x: 0, y: 0, z: 0, w: 2, d: 2, h: 1, c: "</script><b>" }, { x: "1e9", y: -5, z: 0 }] });
const scripts = evil.match(/<\/script>/g) || [];
ok("hostile colour cannot close the script", scripts.length === 1 && !evil.includes("<b>"));
ok("hostile coordinates are clamped", evil.includes('"x":255') && evil.includes('"y":0'));
const html = R({ shape: "house", parts: true });
const js = html.slice(html.indexOf("<script>") + 8, html.lastIndexOf("</script>"));
let parses = true; try { new Function(js); } catch (e) { parses = false; }
ok("serialised inline script parses", parses);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
