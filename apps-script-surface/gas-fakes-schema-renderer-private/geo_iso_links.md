# geo_iso Atom — Live Links & Schema Reference

Deployment ID: `AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg`  
Base URL: `https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec`  
Current version: **@130**

---

## Live URLs

| Atom | Schema | Live URL |
|---|---|---|
| `geo_iso_takeoff` | `{"type":"geo_iso_takeoff","title":"AIRBUS A321neo — LFBO RUNWAY 32L DEPARTURE","airline":"EZY","aircraft_type":"A21N"}` | [Open](https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec?p=W3sidHlwZSI6Imdlb19pc29fdGFrZW9mZiIsInRpdGxlIjoiQUlSQlVTIEEzMjFuZW8g4oCUIExGQk8gUlVOV0FZIDMyTCBERVBBUlRVUkUiLCJhaXJsaW5lIjoiRVpZIiwiYWlyY3JhZnRfdHlwZSI6IkEyMU4ifV0) |
| `geo_iso_rocket_launch` | `{"type":"geo_iso_rocket_launch","title":"KOUROU ELA-4 — ARIANE 6 HEAVY LIFT","vehicle":"ARIANE_6"}` | [Open](https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec?p=W3sidHlwZSI6Imdlb19pc29fcm9ja2V0X2xhdW5jaCIsInRpdGxlIjoiS09VUk9VIEVMQS00IOKAlCBBUklBTkUgNiBIRUFWWSBMSUZUIiwidmVoaWNsZSI6IkFSSUFORV82In1d) |
| `geo_iso_fleet` | `{"type":"geo_iso_fleet","airline":"EZY","rocket":"ESA","livery":"SAR"}` | [Open](https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec?p=W3sidHlwZSI6Imdlb19pc29fZmxlZXQiLCJ0aXRsZSI6IkFJUkJVUyBGTEVFVCBERUNLIiwiYWlybGluZSI6IkFJQiIsInJvY2tldCI6IkVTQSIsImxpdmVyeSI6IkFJQiJ9XQ) |

---

## Schema Fields

### geo_iso_takeoff

| Field | Type | Default | Notes |
|---|---|---|---|
| `type` | string | — | `"geo_iso_takeoff"` |
| `title` | string | `"LFBO RWY 32L — A321neo DEPARTURE"` | HUD headline |
| `airline` | string | `"AIB"` | Sets initial livery: `AIB`=Airbus factory white/navy/cyan, `EZY`=orange, `AFR`=blue, `BAW`=navy, `DLH`=Lufthansa navy, `RYR`=Ryanair blue. Dropdown overrides at runtime with no server round-trip. |
| `aircraft_type` | string | `"A21N"` | `A21N` applies 1.25× fuselage / 1.10× wingspan scale |

### geo_iso_fleet

| Field | Type | Default | Notes |
|---|---|---|---|
| `type` | string | — | `"geo_iso_fleet"` |
| `airline` | string | `"AIB"` | Initial A321neo livery (same 6 options as `geo_iso_takeoff`) |
| `rocket` | string | `"ESA"` | Initial Ariane 6 config: `ESA`=white/cyan, `ARIA`=silver/orange, `DARK`=matte black/red |
| `livery` | string | `"AIB"` | Initial H160 livery (same 3 options as `geo_iso_heli_hover`) |
| `tab` | string | `"ac"` | Initial active tab: `ac`=A321neo, `rk`=Ariane 6, `hh`=H160 |

---

### geo_iso_rocket_launch

| Field | Type | Default | Notes |
|---|---|---|---|
| `type` | string | — | `"geo_iso_rocket_launch"` |
| `title` | string | `"KOUROU ELA-4 — HEAVY LIFT INJECTION PROFILE"` | HUD headline |
| `vehicle` | string | `"ARIANE_6"` | `ARIANE_6` = cyan `#38bdf8`, anything else = purple `#a78bfa` |

---

## Version History

| Version | Date | Changes |
|---|---|---|
| @109 | 2026-06-17 | Initial `geo_iso_takeoff` + `geo_iso_rocket_launch` — old V-object mesh |
| @110 | 2026-06-17 | Upgraded to index-based nodes/lines mesh (29 nodes); rocket atom added |
| @111 | 2026-06-17 | Hex bulkhead rings (37 nodes), LEAP-1A nacelles, horizontal stabilisers |
| @112 | 2026-06-18 | Layered back-to-front rendering with occlusion masks (43 nodes); nose taper ring; `drawLG` helper |
| @113 | 2026-06-18 | Structural pruning — interior stringers removed; circumferential rings + outer silhouette only; single-pass draw, no masks |
| @114 | 2026-06-19 | Volumetric LEAP-1A nacelle cages (47 nodes, 66 lines); quadratic wing flex tied to altitude; per-line depth opacity replaces flat colour |
| @115 | 2026-06-19 | Pylon anchor nodes 47/48 at `z=±16` — engine barrels route through anchors, eliminating inward bracket slant; rocket `drawRing`/`drawStrings` upgraded to segment depth opacity |
| @116 | 2026-06-19 | **Solid surface rendering** — `lines` replaced by `faces` polygon matrix; Painter's Algorithm (back-to-front depth sort per frame); Lambertian flat shading with cross-product surface normals + virtual sun vector; airline livery RGB injected server-side as `BR/BG/BB` |
| @117 | 2026-06-19 | **A2UI livery selector** — client-side `AL` database replaces static `BR/BG/BB`; 6 airlines (AIB/EZY/AFR/BAW/DLH/RYR); glassmorphic dropdown with real-time livery switch, no server round-trip; sharklets split to `"sk"` face type for per-airline accent colour; Airbus Factory House (`AIB`) is new default |
| @118 | 2026-06-19 | **Lighting fix** — sun vector flipped to `(-0.1, 0.8, +0.6)` (key light behind camera); ambient floor `0.15→0.46` for luminous shadow sides; stroke reduced to `0.18` alpha; wing grey `168,174,182`, engine white `245,247,250` |
| @119 | 2026-06-19 | **Wing topology fix** — wing winding reversed to `[root-LE→tip-LE→tip-TE→root-TE]` so cross-product normals point upward and catch direct light; engine faces detached from wing roots (29/30, 34/35) and anchored strictly to pylon nodes 47/48 — eliminates giant solid wedge across right wing |
| @120 | 2026-06-19 | **Background rocket** — Ariane 6 launch embedded into `geo_iso_takeoff` scene; `drawRocketBg()` reuses scene `proj()`, positioned at `ox=62, oz=130, sc=0.4`; independent 290-frame cycle (`rT/rky/rVY/rBoff`); SRB stage separation at t=200; gradient flame glow; drawn before runway so aircraft always in foreground |
| @121 | 2026-06-19 | **Rocket solid surface** — `geo_iso_rocket_launch`: `drawRing`/`drawStrings` replaced by `drawSolidRocketCylinder(h1,r1,h2,r2,segs,dx,dy,dz,type)`; Painter's Algorithm per cylinder + Lambertian shading with shared sun vector `(-0.1, 0.8, +0.6)`; palette: core=white, boosters=ESA cyan `56,189,248`, fairing=dark grey `90,98,105`; nose cone = tapered cylinder to r=0.2 |
| @122 | 2026-06-19 | **Global face sort** — `drawSolidRocketCylinder` split into `buildCylFaces` (returns array) + `paintRocketFaces` (global sort+paint); all cylinder faces collected then sorted in one pass before painting — eliminates cross-cylinder see-through caused by per-cylinder Painter's sort |
| @123 | 2026-06-19 | **Winding fix** — `buildCylFaces` quad order corrected to `[base_i→top_i→top_n→base_n]` giving outward-facing cross-product normals; `pj` helper moved outside for loop (was: closure-inside-loop risk); previous inverted normals caused all faces to clamp to ambient, making solid fills invisible against background |
| @124 | 2026-06-19 | **Rocket solid-surface rewrite** — `buildCylFaces` + `paintRocketFaces` global-sort pattern replaced by self-contained `drawSolidRocketCylinder`; retains corrected `[base_i→top_i→top_n→base_n]` winding (outward normals); depth metric upgraded from `wZ` to `(wx+wz)/4` per face (true isometric depth); Painter's sort ascending on isometric depth; Lambertian + ambient 0.42 per cylinder; cleaner code structure |
| @125 | 2026-06-19 | **Background rocket solid-surface** — `drawRocketBg()` inside `geo_iso_takeoff` upgraded from wireframe `ra`/`rs` loops to `drawSolidBgSeg` Lambertian quads; same `[base_i→top_i→top_n→base_n]` winding and `(wx+wz)` isometric depth sort; SRBs=ESA cyan `56,189,248`, core=white `245,247,250`, fairing=grey `90,98,105`; flame glows preserved; stars no longer clip through hull |
| @126 | 2026-06-19 | **`geo_iso_heli_hover`** — Airbus H160 third flagship atom; 31-node volumetric mesh; solid Lambertian face shading with corrected outward-normal winding (`[a,d,c,b]` quads, `[a,c,b]` tris); Painter's sort on `wz` (forward axis); 5-bladed main rotor pitch-synced to hull transform; fenestron blur disc on node 26; 4-phase flight loop (spool-up → liftoff → torque transition → cruise); 3-livery client-side dropdown (AIB=factory white, VIP=carbon/gold, SAR=rescue red); registered in `Code.js` `needsFullscreen` |
| @127 | 2026-06-19 | **H160 mesh correction** — node coords calibrated; nose fan tris restored to original CCW winding (reversed tris in @126 were wrong); quads remain reversed for outward normals; duplicate roof face removed (was Z-fighting every frame); semantic `f.type` dispatch: `canopy`=glass `30,45,70`, `belly`=structural grey `145,152,162` (fixed, not livery-scaled), `engine`/`fin`=accent, `body`/`nose`=livery body |
| @128 | 2026-06-19 | **H160 rotor disc blur** — stick blades replaced by procedural 3D disc engine; 12-segment ellipse projected through pitch matrix (tilts forward with fuselage in cruise); `rgba(0,242,255,0.04)` filled disc + `rgba(140,148,158,0.15)` boundary ring; 5 blades × 4 motion-trail ghost arcs with fading alpha `(1-trail/4)*0.45` and tapering lineWidth `1.6-trail*0.3`; cyan tip caps on leading edge only; blade radius 46 units |
| @129 | 2026-06-19 | **Rotor concentric blur** — solid polygon fill removed (was masking canopy and hull); 16-seg outer tip-vortex ring `rgba(0,242,255,0.08)` + 75%-chord inner ring `rgba(140,148,158,0.04)` (stroke-only, fully transparent background); 8-pass quadratic `Math.pow(1-tr/8,2)*0.38` decay fan at 0.035 rad lag per step; rotor mast anchor cap `rgba(10,34,84,0.95)` at hub |
| @130 | 2026-06-19 | **`geo_iso_fleet`** — Combined Fleet Deck with all three atoms on one fullscreen canvas; tab bar (A321neo / ARIANE 6 / H160) switches active aircraft with state reset on each switch; three simultaneous livery dropdowns always visible in right panel (A321neo: 6 airlines, Ariane 6: 3 configs — ESA/ARIA/DARK, H160: 3 liveries); shared `proj()` with per-draw SC + OY override (A321neo: 3.5/0.8H, Ariane 6: 3.2/0.82H, H160: 4.2/0.72H); shared `paintFaces()` Lambertian helper eliminates code duplication; pre-normalised sun constant `(-0.0995, 0.796, 0.597)`; tab defaults to `"ac"`, overridable via `b.tab` schema field |

---

## Generate a URL

```javascript
// Node.js / browser
var payload = [{ type: 'geo_iso_takeoff', title: 'MY TITLE', airline: 'EZY', aircraft_type: 'A21N' }];
var b64 = btoa(unescape(encodeURIComponent(JSON.stringify(payload))))
            .replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
var url = 'https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec?p=' + b64;
```
