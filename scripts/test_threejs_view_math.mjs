// Brick Design Lab's "View in Three.js" viewer -- evals the ACTUAL threejs_view_math.js (no copies), the
// same file build_design_page.py embeds verbatim into the live page. Locks in the rotation/placement/camera-
// fit math directly, rather than relying on eyeballing a headless-Chromium screenshot each time (how the two
// real bugs in this math were originally found, 2026-09-29).
// usage: node scripts/test_threejs_view_math.mjs
import { readFileSync } from "fs";
import vm from "vm";

const src = readFileSync(new URL("brick_models/threejs_view_math.js", import.meta.url), "utf8");
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src, ctx);

let pass = 0, fail = 0;
const EPS = 1e-9;
const close = (a, b, eps = EPS) => Math.abs(a - b) <= eps;
const closeVec = (a, b, eps = EPS) => a.length === b.length && a.every((v, i) => close(v, b[i], eps));
const check = (name, ok, detail = "") => { ok ? pass++ : fail++; console.log(`  ${ok ? "✓" : "✗"} ${name}${ok ? "" : " — " + detail}`); };

// tjsRot: identity (index 0) is a no-op.
const identityOut = ctx.tjsRot(0, [3, -2, 7]);
check("tjsRot index 0 (identity) leaves a point unchanged", closeVec(identityOut, [3, -2, 7]), JSON.stringify(identityOut));

// tjsRot: index 1 ([0,0,1, 0,1,0, -1,0,0]) rotates (1,0,0) -> (0,0,-1) -- hand-computed from the real matrix.
const rot1Out = ctx.tjsRot(1, [1, 0, 0]);
check("tjsRot index 1 matches its own matrix, hand-computed", closeVec(rot1Out, [0, 0, -1]), JSON.stringify(rot1Out));

// tjsToWorld: a real quant=16 vertex one stud away on X, at a properly-floored instance position (r=0, no
// rotation) -- hand-computed: local=[1,0,0], world=[(1+0)/20, -(0-24)/20, 0/20] = [0.05, 1.2, 0].
const worldOut = ctx.tjsToWorld([16, 0, 0], 16, 0, [0, -24, 0]);
check("tjsToWorld: LDraw Y-down floored offset becomes three.js Y-up correctly",
  closeVec(worldOut, [0.05, 1.2, 0], 1e-6), JSON.stringify(worldOut));

// tjsFitCamera: a 2x2x2 cube centred at the origin, viewed straight down -Z (dir=[0,0,1], i.e. camera sits
// on +Z looking toward -Z), 90-degree vertical FOV, square aspect -- every quantity hand-computable exactly
// (tan(45deg)=1), so this checks the corner-projection distance formula end to end, not just its inputs.
const fit = ctx.tjsFitCamera([-1, -1, -1], [1, 1, 1], [0, 0, 1], 90, 1, 1.15);
check("tjsFitCamera: target is the box centre", closeVec(fit.target, [0, 0, 0]));
check("tjsFitCamera: distance is margin * halfExtent / tan(45deg) = 1.15 * 1 / 1", close(fit.distance, 1.15, 1e-9), String(fit.distance));
check("tjsFitCamera: camera position sits along dir at that distance from centre",
  closeVec(fit.position, [0, 0, 1.15], 1e-9), JSON.stringify(fit.position));
check("tjsFitCamera: near/far bracket the object without clipping it",
  fit.near < fit.distance - 1 && fit.far > fit.distance + 1, `near=${fit.near} far=${fit.far} dist=${fit.distance}`);

// tjsFitCamera: a box that's much WIDER than tall must need MORE distance than a square box of the same
// height -- the real bug this function was written to fix (a scalar heuristic gave the same, too-small
// distance regardless of the box's actual proportions).
const wideFit = ctx.tjsFitCamera([-5, -1, -1], [5, 1, 1], [0, 0, 1], 90, 1, 1.15);
const squareFit = ctx.tjsFitCamera([-1, -1, -1], [1, 1, 1], [0, 0, 1], 90, 1, 1.15);
check("tjsFitCamera: a wide box needs more distance than a square box of the same height",
  wideFit.distance > squareFit.distance, `wide=${wideFit.distance} square=${squareFit.distance}`);

// tjsFitCamera: ortho.halfW/halfH (item 4, OrthographicCamera framing) -- FOV/aspect-independent, so the
// SAME 2x2x2 cube (half-extent 1 on every axis) viewed along Z must report margin*1 on both axes exactly,
// regardless of the 90-degree FOV those perspective checks above used (a real bug an ortho fit would need
// to NOT reproduce: baking any FOV dependency into halfW/halfH would defeat the point of parallel projection).
check("tjsFitCamera: ortho.halfW is margin * half-extent along the view's right axis (cube: 1.15 * 1)",
  close(fit.ortho.halfW, 1.15, 1e-9), String(fit.ortho.halfW));
check("tjsFitCamera: ortho.halfH is margin * half-extent along the view's up axis (cube: 1.15 * 1)",
  close(fit.ortho.halfH, 1.15, 1e-9), String(fit.ortho.halfH));
// The wide box (half-extent 5 on X, 1 on Y, viewed along Z so right=X/up=Y) must report an asymmetric
// ortho frustum matching that shape exactly -- not a single scalar collapsing both axes together.
check("tjsFitCamera: ortho.halfW/halfH track a non-square box's real X/Y half-extents independently",
  close(wideFit.ortho.halfW, 5.75, 1e-9) && close(wideFit.ortho.halfH, 1.15, 1e-9),
  JSON.stringify(wideFit.ortho));

// TJS_PART_ROT: exactly 24 real, proper (determinant +1) rotation matrices -- twinned by hand across four
// files (atoms_brick.gs, brick_parts_validate.py, omr-import.js, here); a wrong or missing entry would
// silently mis-rotate any part using that index.
check("TJS_PART_ROT has exactly 24 entries", ctx.TJS_PART_ROT.length === 24, String(ctx.TJS_PART_ROT.length));
const det3 = (m) => m[0] * (m[4] * m[8] - m[5] * m[7]) - m[1] * (m[3] * m[8] - m[5] * m[6]) + m[2] * (m[3] * m[7] - m[4] * m[6]);
check("every TJS_PART_ROT matrix is a proper rotation (determinant +1)",
  ctx.TJS_PART_ROT.every((m) => close(det3(m), 1, 1e-9)),
  JSON.stringify(ctx.TJS_PART_ROT.map(det3).filter((d) => !close(d, 1, 1e-9))));

// tjsInstanceMatrixRowMajor: deliberately does NOT include tjsToWorld's D=diag(1/20,-1/20,1/20) scale/flip --
// that belongs on the InstancedMesh's own object-level .scale in render() instead (see the function's own
// comment for why: three.js decides front-face winding/normal-flip from object.matrixWorld's determinant
// alone, with no visibility into a per-instance instanceMatrix, so baking a mirror into every instance broke
// real rendering live 2026-09-30). Composing this function's output with D EXACTLY the way render() does
// (object scale applied after the instance matrix) must still reproduce tjsToWorld's own point-by-point
// result exactly -- checked across several rotation indices, instance positions and quant values, not just
// re-derived by eye a second time.
function applyMatrixRowMajor(els, p) {
  return [
    els[0] * p[0] + els[1] * p[1] + els[2] * p[2] + els[3],
    els[4] * p[0] + els[5] * p[1] + els[6] * p[2] + els[7],
    els[8] * p[0] + els[9] * p[1] + els[10] * p[2] + els[11],
  ];
}
const applyD = (p) => [p[0] / 20, -p[1] / 20, p[2] / 20];
const instanceCases = [
  { r: 0, instPos: [0, -24, 0], q: 16, p: [16, 0, 0] },
  { r: 1, instPos: [40, -24, -40], q: 16, p: [8, -12, 4] },
  { r: 5, instPos: [-80, 0, 120], q: 20, p: [-3, 7, 11] },
  { r: 13, instPos: [0, 0, 0], q: 1, p: [1, 2, 3] },
  { r: 23, instPos: [200, -48, -200], q: 8, p: [-5, 0, 17] },
];
for (const { r, instPos, q, p } of instanceCases) {
  const viaMatrix = applyD(applyMatrixRowMajor(ctx.tjsInstanceMatrixRowMajor(r, instPos, q), p));
  const viaToWorld = ctx.tjsToWorld(p, q, r, instPos);
  check(`tjsInstanceMatrixRowMajor (composed with D) matches tjsToWorld for r=${r} instPos=${JSON.stringify(instPos)} q=${q}`,
    closeVec(viaMatrix, viaToWorld, 1e-9), `matrix=${JSON.stringify(viaMatrix)} toWorld=${JSON.stringify(viaToWorld)}`);
}

console.log(fail ? `${fail} failure(s)` : `all ok (${pass} checks)`);
process.exit(fail ? 1 : 0);
