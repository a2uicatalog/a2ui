#!/usr/bin/env python3
"""gen_threejs_demo_page.py -- public/bricksdemo/threejs-demo/index.html, the Three.js render-appearance
proof-of-concept (see /home/ck/.claude/plans/cozy-forging-newt.md, Track B "Render appearance" schema gap).

Standalone and additive: it renders real baked LDraw part geometry (public/parts/3005.json) through vendored
Three.js (public/vendors/threejs/, fetched+verified by scripts/fetch_threejs.py -- see THIRD-PARTY-NOTICES.md
for provenance) to prove a render-appearance axis the live production renderer (atoms_brick.gs's hand-rolled
WebGL/Canvas-2D shader) has no concept of at all. Does NOT touch, load, or replace any part of that renderer.

Was first committed as a hand-written static HTML file, then converted to a generator (this file) the same day
after tests/test_brand.py::test_pages_without_the_site_chrome_are_declared_and_only_shrink caught it missing the
shared site header/brand tokens -- same fix gen_renderer_page.py applied for the same reason (2026-09-26). Follows
that script's exact pattern: shared chrome (SITE_BASE_CSS/site_header/theme JS) from generate_atom_pages.py, only
this page's own content (the canvas panel + the three.js module script) stays here.

Run:  python3 scripts/brick_models/gen_threejs_demo_page.py     # after generate_atom_pages.py (imports its chrome)
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "public" / "bricksdemo" / "threejs-demo" / "index.html"

sys.path.insert(0, str(ROOT / "scripts"))
import generate_atom_pages as _site  # noqa: E402  the site's shared chrome -- one definition

PAGE_CSS = """
.wrap{max-width:900px}
#stage{width:100%;height:480px;border:1px solid var(--border);border-radius:var(--radius);display:block;background:#1a1f26}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;display:flex;flex-direction:column;gap:10px;margin-bottom:20px}
.note{font-size:12px;color:var(--muted)}
#status{font-size:12px;color:var(--muted)}
.wrap footer{border-top:1px solid var(--border);padding-top:12px;margin-top:0;display:block}
.wrap footer p{font-size:12px;color:var(--muted)}
.wrap code{background:var(--surface-2);border-radius:3px;padding:1px 5px;font-size:12px}
"""

BODY = """
  <div>
    <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:8px;">Three.js render-appearance proof-of-concept</h1>
    <p style="color:var(--muted);font-size:13px;max-width:70ch;margin-bottom:20px;">This is a standalone demo, additive to the catalogue -- it does not touch, replace, or get loaded by the live Brick Design Lab or its production WebGL renderer. It exists to prove one thing: the same real LDraw brick geometry, rendered with two genuinely different material finishes side by side. The live renderer's hand-rolled shader has no material-appearance concept at all today (flat hex colour, simple Lambert shading) -- it cannot do this.</p>
  </div>
  <section class="panel">
    <canvas id="stage"></canvas>
    <p id="status" role="status">Loading real part geometry (public/parts/3005.json)&hellip;</p>
    <p class="note">Left: <b>opaque matte ABS</b> (<code>MeshStandardMaterial</code>, high roughness, near-zero metalness) -- how every brick renders in the live catalogue today. Right: <b>trans-clear plastic</b> (<code>MeshPhysicalMaterial</code>, low opacity, clearcoat) -- like a real LEGO windscreen or trans-clear part, a finish that exists in the real LEGO catalogue but has no representation in the current shader. Both instances share the exact same baked mesh (LDraw part 3005, a real 1&times;1 brick, from <code>public/parts/3005.json</code>) -- drag to orbit, scroll to zoom.</p>
  </section>
  <footer>
    <p>Rendered with <a href="https://threejs.org/">three.js</a> (MIT License, &copy; 2010-2026 three.js authors), vendored at <code>/vendors/threejs/</code> (see <a href="/THIRD-PARTY-NOTICES.md">THIRD-PARTY-NOTICES.md</a> for full provenance, version pin and license text) -- fetched and verified by <code>scripts/fetch_threejs.py</code>, never loaded from a CDN. Part geometry from the LDraw parts library (CC BY 4.0). Fan-made, not affiliated with or endorsed by the LEGO Group. LEGO&reg; is a trademark of the LEGO Group, which does not sponsor, authorize or endorse this content.</p>
  </footer>
"""

DEMO_SCRIPT = """
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const statusEl = document.getElementById('status');
const canvas = document.getElementById('stage');
window.addEventListener('error', (e) => {
  statusEl.textContent = 'Script error: ' + (e.message || e.error);
});

// Build a THREE.BufferGeometry from this catalogue's own baked-mesh JSON shape (public/parts/<id>.json --
// see renderers/brick_parts_validate.py's module docstring for the full field reference). `triangles` is a
// list of {colour, pos} groups; `pos` is a flat list of [x,y,z] LDU-times-`quant` vertex triples, three per
// triangle, no index buffer -- the same shape the live atoms_brick.gs renderer consumes directly, just
// re-expressed here as a THREE.BufferGeometry instead of raw WebGL calls. LDraw's Y axis points DOWN with 0
// at the part's TOP (confirmed by this part's own connectors: the stud sits at y=0, the socket -- i.e. the
// flat underside that rests on the thing below it -- at y=bounds.max[1]). three.js is Y-up, and a part should
// sit with its underside (LDraw max Y) on the floor at world Y=0 and its top (LDraw y=0) up at world
// Y=(max-min)/quant -- so this flips AND re-origins on bounds.max[1], not just negates.
function geometryFromBakedPart(part) {
  const quant = part.quant || 1;
  const floorY = part.bounds.max[1];
  const toWorld = ([x, y, z]) => [x / quant, (floorY - y) / quant, z / quant];
  const positions = [];
  for (const group of part.triangles) {
    const verts = group.pos;
    for (let i = 0; i + 2 < verts.length; i += 3) {
      // Mirroring only the Y axis above (LDraw is Y-down, three.js is Y-up) flips the coordinate system's
      // handedness, which reverses every triangle's winding order -- swap the last two vertices per
      // triangle to restore correct outward-facing winding. Confirmed visually: without this swap,
      // backface culling hid the true outer faces and rendered the hollow interior instead.
      const a = toWorld(verts[i]), b = toWorld(verts[i + 1]), c = toWorld(verts[i + 2]);
      positions.push(...a, ...c, ...b);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.computeVertexNormals();
  return geo;
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1f26);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
camera.position.set(38, 30, 46);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 8, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.4;

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(25, 40, 20);
scene.add(key);
const fill = new THREE.DirectionalLight(0x8fb8ff, 0.6);
fill.position.set(-20, 10, -15);
scene.add(fill);

const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(200, 200),
  new THREE.MeshStandardMaterial({ color: 0x24303b, roughness: 1, metalness: 0 })
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = 0;
scene.add(floor);

function resize() {
  const w = canvas.clientWidth || canvas.parentElement.clientWidth;
  const h = canvas.clientHeight || 480;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

fetch('/parts/3005.json')
  .then((r) => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  })
  .then((part) => {
    const geo = geometryFromBakedPart(part);

    // Opaque matte ABS -- the finish every part in the live catalogue renders as today.
    const matteMat = new THREE.MeshStandardMaterial({
      color: 0xc91a09, roughness: 0.85, metalness: 0.05,
    });
    // Trans-clear plastic -- a real LEGO finish (windscreens, some 1x1 round plates) the current shader
    // cannot represent at all. Opacity + clearcoat, not `transmission`, so it renders correctly with no
    // extra render-target passes or environment map required.
    const transMat = new THREE.MeshPhysicalMaterial({
      color: 0x6fc7ff, transparent: true, opacity: 0.35,
      roughness: 0.05, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.05,
    });

    const left = new THREE.Mesh(geo, matteMat);
    left.position.set(-14, 0, 0);
    scene.add(left);

    const right = new THREE.Mesh(geo, transMat);
    right.position.set(14, 0, 0);
    scene.add(right);

    statusEl.textContent = 'Rendering "' + part.title.trim() + '" (LDraw part ' + part.id +
      ') -- same mesh, two material finishes.';
  })
  .catch((err) => {
    statusEl.textContent = 'Could not load /parts/3005.json (' + err.message +
      ') -- serve this page from the public/ directory root, e.g. `cd public && python3 -m http.server`.';
  });

resize();
(function loop() {
  requestAnimationFrame(loop);
  controls.update();
  renderer.render(scene, camera);
})();
"""


def render():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Three.js render-appearance proof-of-concept</title>
<meta name="description" content="A standalone Three.js demo rendering a real LDraw brick mesh with two different material finishes on the same geometry -- proving a render-appearance axis this catalogue's live renderer doesn't model yet.">
<meta name="robots" content="noindex, nofollow">
{_site.SITE_HEAD_JS}
<style>{_site.SITE_BASE_CSS}
{PAGE_CSS}</style>
</head>
<body>
{_site.site_header("")}
<div class="wrap">
{BODY}
</div>
<script type="importmap">
{{
  "imports": {{
    "three": "/vendors/threejs/three.module.js",
    "three/addons/controls/OrbitControls.js": "/vendors/threejs/addons/controls/OrbitControls.js"
  }}
}}
</script>
<script type="module">{DEMO_SCRIPT}</script>
<script>
{_site.SITE_FOOT_JS.replace("<script>", "").replace("</script>", "")}
</script>
</body>
</html>
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
