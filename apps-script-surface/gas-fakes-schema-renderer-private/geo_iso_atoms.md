# geo_iso_takeoff & geo_iso_rocket_launch — GAS Atom Source

Deployed @ `AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg` @126  
Source: `atoms_canvas.gs` — takeoff ~L1181, rocket ~L1625, heli ~L1782

---

## geo_iso_takeoff

**Schema**
```json
{
  "type": "geo_iso_takeoff",
  "title": "LFBO RWY 32L — A321neo DEPARTURE",
  "airline": "EZY",
  "aircraft_type": "A21N"
}
```

| Field | Default | Notes |
|---|---|---|
| `title` | `LFBO RWY 32L — A321neo DEPARTURE` | HUD headline |
| `airline` | `AIB` | Sets initial livery. Runtime dropdown overrides without server round-trip: `AIB`=Airbus factory, `EZY`=easyJet orange, `AFR`=Air France blue, `BAW`=BA navy, `DLH`=Lufthansa, `RYR`=Ryanair |
| `aircraft_type` | `A21N` | A21N applies 1.25× fuselage / 1.10× wingspan scale |

**Live URL**
```
https://script.google.com/macros/s/AKfycbyVKvt_.../exec?p=W3sidHlwZSI6Imdlb19pc29fdGFrZW9mZiIsInRpdGxlIjoiQUlSQlVTIEEzMjFuZW8g4oCUIExGQk8gUlVOV0FZIDMyTCBERVBBUlRVUkUiLCJhaXJsaW5lIjoiRVpZIiwiYWlyY3JhZnRfdHlwZSI6IkEyMU4ifV0
```

**Architecture**
- Fullscreen canvas via `AirspaceFullscreen.html` — registered in `Code.js` `needsFullscreen` check
- Isometric projection: `proj(lateral, up, depth)` — `+x` right, `+y` up, `-z` away
- LIVE RADAR button uses server-side URL generation (`ScriptApp.getService().getUrl()` + `Utilities.base64EncodeWebSafe`) to bypass GAS sandbox navigation restrictions

**Animation phases**
1. Ground roll `t 0→90`: `speed` ramps to 38u/s, `posY=0`, no pitch
2. Rotation `t 90→130`: pitch ramps to 0.24 rad (≈14°), aircraft lifts
3. Climb `t 130→230`: `posY` increases, `speed` to 46u/s
4. Reset → loop

**A321neo unified mesh — 49 nodes, 66 lines — @115**

Node coordinate system: `x=forward (+nose)`, `y=up`, `z=lateral (+starboard)`  
Mapped to `proj()` via pitch rotation then: `proj(v.z, ry+posY, posZ-rx)`

Key changes from @114: nodes 47/48 added as mid-wing pylon anchors at `{x:6, y:-2.1, z:±16}` — nacelle barrel loops now route through these anchors instead of back to wing root (`z=±6`), eliminating the inward-slanting bracket geometry. Pylon anchors at `|z|>5.5 && idx≥29` are automatically caught by the wing flex loop. Rocket `drawRing`/`drawStrings` upgraded to segment-by-segment depth opacity (`rgba(0,242,255,alpha)`) matching the aircraft visual language.

```javascript
var nodes = [
  {x:54,  y:-1.5, z:0},    // 0  nose tip
  // Nose taper ring
  {x:44,  y:2,    z:2.5},  // 1
  {x:44,  y:0.5,  z:3.5},  // 2
  {x:44,  y:-2,   z:2.5},  // 3
  {x:44,  y:-2,   z:-2.5}, // 4
  {x:44,  y:0.5,  z:-3.5}, // 5
  {x:44,  y:2,    z:-2.5}, // 6
  // Cockpit hex ring
  {x:34,  y:5,    z:4.5},  // 7
  {x:34,  y:1.5,  z:6},    // 8
  {x:34,  y:-4,   z:4.5},  // 9
  {x:34,  y:-4,   z:-4.5}, // 10
  {x:34,  y:1.5,  z:-6},   // 11
  {x:34,  y:5,    z:-4.5}, // 12
  // Mid-cabin hex ring
  {x:-20, y:5.5,  z:4.5},  // 13
  {x:-20, y:1.5,  z:6},    // 14
  {x:-20, y:-4,   z:4.5},  // 15
  {x:-20, y:-4,   z:-4.5}, // 16
  {x:-20, y:1.5,  z:-6},   // 17
  {x:-20, y:5.5,  z:-4.5}, // 18
  // Aft hex ring
  {x:-65, y:3.5,  z:2},    // 19
  {x:-65, y:1,    z:3.5},  // 20
  {x:-65, y:-2,   z:2},    // 21
  {x:-65, y:-2,   z:-2},   // 22
  {x:-65, y:1,    z:-3.5}, // 23
  {x:-65, y:3.5,  z:-2},   // 24
  {x:-78, y:0.5,  z:0},    // 25 APU
  // Empennage
  {x:-74, y:24,   z:0},    // 26 v-stab apex
  {x:-74, y:1.5,  z:18},   // 27 stbd tailplane
  {x:-74, y:1.5,  z:-18},  // 28 port tailplane
  // L wing
  {x:12,  y:-2.5, z:-6},   // 29 L root LE
  {x:-12, y:-2.5, z:-6},   // 30 L root TE
  {x:-24, y:-0.5, z:-52},  // 31 L tip TE
  {x:-18, y:-0.5, z:-52},  // 32 L tip LE
  {x:-18, y:7,    z:-52},  // 33 L sharklet
  // R wing
  {x:12,  y:-2.5, z:6},    // 34 R root LE
  {x:-12, y:-2.5, z:6},    // 35 R root TE
  {x:-24, y:-0.5, z:52},   // 36 R tip TE
  {x:-18, y:-0.5, z:52},   // 37 R tip LE
  {x:-18, y:7,    z:52},   // 38 R sharklet
  // LEAP-1A nacelles — top rail
  {x:16,  y:-6.5, z:-16},  // 39 L intake top
  {x:2,   y:-5.5, z:-16},  // 40 L exhaust top
  {x:16,  y:-6.5, z:16},   // 41 R intake top
  {x:2,   y:-5.5, z:16},   // 42 R exhaust top
  // LEAP-1A nacelles — bottom rail
  {x:16,  y:-9.5, z:-16},  // 43 L intake bottom
  {x:2,   y:-8.5, z:-16},  // 44 L exhaust bottom
  {x:16,  y:-9.5, z:16},   // 45 R intake bottom
  {x:2,   y:-8.5, z:16},   // 46 R exhaust bottom
  // Pylon anchors — hang engines straight down at z=±16
  {x:6,   y:-2.1, z:-16},  // 47 L mid-wing pylon
  {x:6,   y:-2.1, z:16}    // 48 R mid-wing pylon
];

var lines = [
  // Rib loops
  [1,2],[2,3],[3,4],[4,5],[5,6],[6,1],
  [7,8],[8,9],[9,10],[10,11],[11,12],[12,7],
  [13,14],[14,15],[15,16],[16,17],[17,18],[18,13],
  [19,20],[20,21],[21,22],[22,23],[23,24],[24,19],
  // Outer silhouette ridges
  [0,1],[0,4],[0,2],[0,5],
  [1,7],[7,13],[13,19],[19,25],
  [4,10],[10,16],[16,22],[22,25],
  [2,8],[8,14],[14,20],
  [5,11],[11,17],[17,23],
  // Empennage
  [19,26],[24,26],[25,26],
  [20,27],[25,27],
  [23,28],[25,28],
  // Wings + sharklets
  [29,30],[30,31],[31,32],[32,29],[32,33],[31,33],
  [34,35],[35,36],[36,37],[37,34],[37,38],[36,38],
  // LEAP-1A volumetric cages via pylon anchors 47/48
  [47,39],[39,40],[40,47],   // L top barrel
  [47,43],[43,44],[44,47],   // L bottom barrel
  [39,43],[40,44],           // L cowling rings
  [48,41],[41,42],[42,48],   // R top barrel
  [48,45],[45,46],[46,48],   // R bottom barrel
  [41,45],[42,46]            // R cowling rings
];
```

**A2UI Livery Selector + drawAC — @117**

Client-side `AL` (Airline Livery) database drives all face colours — server no longer injects RGB. A `<select>` dropdown in the top-right corner switches `activeLivery` at runtime with no page reload or server round-trip. Each frame `drawAC` dispatches face type → `activeLivery` property:

| Face type | Maps to | Notes |
|---|---|---|
| `"f"` fuselage / `"n"` nose | `activeLivery.body` | Main livery colour |
| `"fin"` vertical fin | `activeLivery.tail` | Airline tail colour |
| `"sk"` sharklet tips | `activeLivery.sk` | Accent colour (distinct on AIB: Airbus cyan) |
| `"w"` wing / `"s"` stabiliser | `{r:160,g:168,b:175}` | Airbus structural grey |
| `"e"` engine nacelle | `{r:240,g:242,b:245}` | Nacelle off-white |

AL database entries: `AIB` (Airbus factory: white body, `#0a2254` tail, `#009ace` sharklets), `EZY` (all-orange), `AFR` (white/`#002395` tail), `BAW` (white/`#075aaa` tail), `DLH` (white/`#1a3c8f` tail), `RYR` (all `#073590`).

**geo_iso_rocket_launch — solid surface @121**

`drawRing`/`drawStrings` replaced by `drawSolidRocketCylinder(h1, r1, h2, r2, segs, dx, dy, dz, type)`. Generates quad panel faces between two rings, sorts back-to-front per cylinder, computes cross-product normals, Lambertian dot against same sun vector as aircraft `(-0.1, 0.8, +0.6)`, ambient floor `0.42`.

Material palette: `"core"` = white `245,247,250`; `"booster"` = ESA cyan `56,189,248`; `"payload"` = fairing grey `90,98,105`. Nose cone uses `drawSolidRocketCylinder(55, 7, 75, 0.2, ...)` — taper to near-zero radius.

Draw order: SRBs → core → payload fairing (ascending depth order in isometric).

`ring(h, r, segs)` helper retained (used internally by `drawSolidRocketCylinder`).

---

## geo_iso_rocket_launch

**Schema**
```json
{
  "type": "geo_iso_rocket_launch",
  "title": "KOUROU ELA-4 — ARIANE 6 HEAVY LIFT",
  "vehicle": "ARIANE_6"
}
```

| Field | Default | Notes |
|---|---|---|
| `title` | `KOUROU ELA-4 — HEAVY LIFT INJECTION PROFILE` | HUD headline |
| `vehicle` | `ARIANE_6` | `ARIANE_6` = cyan accent, anything else = purple |

**Live URL**
```
https://script.google.com/macros/s/AKfycbyVKvt_.../exec?p=W3sidHlwZSI6Imdlb19pc29fcm9ja2V0X2xhdW5jaCIsInRpdGxlIjoiS09VUk9VIEVMQS00IOKAlCBBUklBTkUgNiBIRUFWWSBMSUZUIiwidmVoaWNsZSI6IkFSSUFORV82In1d
```

**Architecture**
- Fullscreen canvas — registered in `Code.js` `needsFullscreen` check
- Same `proj(x, y, z)` isometric function as takeoff atom
- No server-side URL needed (no nav button)

**Animation phases**
1. Core ascent `t 0→120`: `velY` accumulates at `acc=0.04`, both SRBs attached, triple flame (core + 2 boosters)
2. Stage sep `t 120→220`: `boostOff` grows, SRBs drift laterally + drop, core-only flame
3. Reset → loop

**Geometry — procedural rings**

The rocket body and SRBs are generated from `ring(height, radius, segments)` returning a polygon of points, then drawn with `drawRing` / `drawStrings`. No static node list.

```javascript
function ring(h, r, segs) {
  var pts = [];
  for (var i = 0; i < segs; i++) {
    var a = i / segs * Math.PI * 2;
    pts.push({ x: Math.cos(a) * r, y: h, z: Math.sin(a) * r });
  }
  return pts;
}

// Main core: segs=6, radius=7, base→h55, nose from ring to apex
var rBase = ring(0, 7, 6);
var rMid  = ring(55, 7, 6);

// SRBs: segs=6, radius=2.5, base→h35
// boostOff causes lateral drift + vertical drop after stage sep
var b1x = -10 - boostOff;
var b1y = posY - (boostOff * .5);
```

**Flame particles**
- Core: random spread ±2, `vy=-1.5`, pink/orange `rgba(244, 63+100*life, 94)`
- Boosters: same but from `x=±12`, only spawned while `t < 120`
- `life -= 0.04` per frame, radius = `sz * life`
