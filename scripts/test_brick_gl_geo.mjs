// brick_build_3d WebGL geometry and shaders — evals the ACTUAL atoms_brick.gs (no copies).
// Every triangle of the unit box and stud must face outward (backface culling and the front-face-culled shadow pass
// depend on it), the box must be closed, and the shader sources must be well-formed GLSL ES 1.0 at the text level.
// usage: node scripts/test_brick_gl_geo.mjs
import { readFileSync } from "fs";
import vm from "vm";

const gs = readFileSync(new URL("../apps-script-surface/gas-wired-renderer/atoms_brick.gs", import.meta.url), "utf8");
const ctx = { _RENDERERS: {} };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const K = vm.runInContext("_brickKit()", ctx);
let pass = 0, fail = 0;
const check = (name, ok, detail = "") => { ok ? pass++ : fail++; console.log(`  ${ok ? "✓" : "✗"} ${name}${ok ? "" : " — " + detail}`); };

function outward(g, centre) {
  let bad = 0;
  for (let t = 0; t < g.i.length; t += 3) {
    const P = [0, 1, 2].map((k) => g.v.slice(g.i[t + k] * 6, g.i[t + k] * 6 + 3));
    const u = P[1].map((x, k) => x - P[0][k]), w = P[2].map((x, k) => x - P[0][k]);
    const n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]];
    const c = [0, 1, 2].map((k) => (P[0][k] + P[1][k] + P[2][k]) / 3 - centre[k]);
    if (n[0] * c[0] + n[1] * c[1] + n[2] * c[2] <= 0) bad++;
  }
  return bad;
}
const box = K.geo.box(), stud = K.geo.stud();
check("box has 6 faces, 12 triangles", box.i.length === 36, String(box.i.length / 3));
check("every box triangle faces outward", outward(box, [0.5, 0.5, 0.5]) === 0, outward(box, [0.5, 0.5, 0.5]) + " inward");
const edges = new Map();
for (let t = 0; t < box.i.length; t += 3) for (let k = 0; k < 3; k++) {
  const a = box.v.slice(box.i[t + k] * 6, box.i[t + k] * 6 + 3).join(), b = box.v.slice(box.i[t + (k + 1) % 3] * 6, box.i[t + (k + 1) % 3] * 6 + 3).join();
  const key = a < b ? a + "|" + b : b + "|" + a;
  edges.set(key, (edges.get(key) || 0) + 1);
}
check("box is closed (every edge shared by exactly two triangles)", [...edges.values()].every((n) => n === 2));
check("box vertex normals are unit axis vectors", box.v.every((x, i) => i % 6 < 3 || [-1, 0, 1].includes(x)));
check("every stud triangle faces outward", outward(stud, [0, 0.09, 0]) === 0, outward(stud, [0, 0.09, 0]) + " inward");
check("stud stays inside its 0.3 radius and 0.18 height", stud.v.every((x, i) => (i % 6 === 1 ? x >= 0 && x <= 0.18 + 1e-9 : i % 6 === 0 || i % 6 === 2 ? Math.abs(x) <= 0.3 + 1e-9 : true)));
check("stud index count fits Uint16", Math.max(...stud.i) < 65536 && Math.max(...box.i) < 65536);
const vs = K.geo.vs(), fs = K.geo.fs(true), fs0 = K.geo.fs(false);
for (const [name, src] of [["vertex", vs], ["fragment (derivatives)", fs], ["fragment (no derivatives)", fs0], ["depth", K.geo.fsDepth]]) {
  const body = src.replace(/#[^\n]*\n/g, "");
  let depth = 0, ok = true;
  for (const ch of body) { if ("({".includes(ch)) depth++; if (")}".includes(ch)) depth--; if (depth < 0) ok = false; }
  check(`${name} shader braces and parentheses balance`, ok && depth === 0);
  check(`${name} shader has no JS 'undefined'/'NaN' leaked into it`, !/undefined|NaN/.test(src));
}
check("derivative extension is declared first when used", fs.startsWith("#extension GL_OES_standard_derivatives"));
check("float literals carry a decimal point (GLSL ES 1.0 has no int->float promotion)", !/vec3\((\d+)\)/.test(vs + fs));
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
