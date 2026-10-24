"""sankey_scene: the 3D Sankey cinema scene (I122), composed from existing atoms, no new renderer.

Concept credit: Cornelius van Heerden (the idea of a Sankey that becomes a lit 3D scene with particles flowing along its links).
Only the idea is credited; nothing of any visual design or branding is copied.

The film (a motion_timeline) is a composition:
  * `sk`        a motion_transition from a choropleth_map (the exporting countries, keyed by ISO 3166-1 alpha-3 code) to a
                keyed sankey_flow whose first column carries the same codes: p 0 -> 1 hands the map over to the flow, element by element.
                At p = 1 the page is the flat, readable Sankey with its text table.
  * camera      tilts and orbits the world on the film dial (rx, ry, zoom), then returns flat.
  * particles   one motion_shape dot per flow rides that flow's curve (a motion_timeline path track, with a fading trail). The curve is
                the Sankey's own link path, laid out server-side by sankey_flow's d3-sankey port (`wa._sk_model`) and mapped into
                stage percent here, so the dots stay on the ribbons wherever the camera is.
  * hud         captions and the concept credit stay on screen.
Reduced motion and the poster frame are the settled state: flat Sankey, no particles. The particle count is capped (PARTICLE_CAP).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from renderers import web_article as wa  # noqa: E402

PARTICLE_CAP = 200                      # elements on screen (heads + trail copies); below the ~300 where a Chromebook drops to 20-30 fps
TRAIL_N, TRAIL_LAG = 5, 0.07
STAGE_W, STAGE_H = 1280, 720
CARD = {"x": 6.0, "y": 12.0, "w": 88.0}  # the Sankey card, percent of the stage
TITLE_H = 64.6                          # height of the sankey_flow title row (measured in Chromium at stage scale 1)
SVG_DX = 1.0                            # measured: the SVG sits 1 px right of border + padding
DOT = 1.0                               # particle diameter, percent of stage width
DURATION = 16.0

# Illustrative figures (not statistics): exporter -> cargo -> destination region, in millions of tonnes.
COUNTRIES = [("CHN", "China"), ("USA", "United States"), ("DEU", "Germany"), ("IND", "India"), ("JPN", "Japan"), ("BRA", "Brazil")]
CARGO = [("ELE", "Electronics"), ("MAC", "Machinery"), ("FOD", "Food and farm"), ("ENG", "Energy")]
REGIONS = [("EUR", "Europe"), ("AME", "Americas"), ("APC", "Asia-Pacific")]
FLOWS = [("CHN", "ELE", 38), ("CHN", "MAC", 22), ("USA", "ELE", 12), ("USA", "FOD", 16), ("USA", "ENG", 14), ("DEU", "MAC", 26),
         ("IND", "FOD", 9), ("JPN", "ELE", 14), ("JPN", "MAC", 10), ("BRA", "FOD", 18),
         ("ELE", "EUR", 22), ("ELE", "AME", 20), ("ELE", "APC", 22), ("MAC", "EUR", 28), ("MAC", "APC", 30),
         ("FOD", "AME", 20), ("FOD", "APC", 23), ("ENG", "EUR", 14)]
PALETTE = {"CHN": "#f87171", "USA": "#60a5fa", "DEU": "#fbbf24", "IND": "#34d399", "JPN": "#f472b6", "BRA": "#a3e635",
           "ELE": "#38bdf8", "MAC": "#a78bfa", "FOD": "#10b981", "ENG": "#f59e0b", "EUR": "#e2e8f0", "AME": "#e2e8f0", "APC": "#e2e8f0"}


def sankey_block(keyed: bool = True) -> dict:
    nodes = ([{"id": i, "label": n, "column": 0, "color": PALETTE[i]} for i, n in COUNTRIES]
             + [{"id": i, "label": n, "column": 1, "color": PALETTE[i]} for i, n in CARGO]
             + [{"id": i, "label": n, "column": 2, "color": PALETTE[i]} for i, n in REGIONS])
    b = {"type": "sankey_flow", "title": "Cargo flow, exporter to destination (illustrative, Mt)", "nodes": nodes,
         "links": [{"source": s, "target": t, "value": v, "color": PALETTE[s]} for s, t, v in FLOWS]}
    if keyed:
        b["keyed"] = True
    return b


def map_block() -> dict:
    """The exporters on the world map: the same ISO codes the Sankey's first column carries (total tonnes out of each)."""
    tot = {}
    for s, _, v in FLOWS:
        if s in dict(COUNTRIES):
            tot[s] = tot.get(s, 0) + v
    return {"type": "choropleth_map", "region_set": "world-countries", "title": "Exports by country (illustrative, Mt)",
            "values": [{"id": k, "value": v} for k, v in tot.items()], "legend_title": "Million tonnes"}


# Where the Sankey's SVG sits on the stage: the card is CARD x%, padded 24 px with a 1 px border, margin 24 px above; the SVG fills the
# card's content width and keeps its aspect. Verified against the browser (tests/test_sankey_scene.py measures a rect).
def svg_frame(model: dict) -> tuple[float, float, float]:
    card_px = CARD["w"] / 100 * STAGE_W
    sw = card_px - 2 * 24 - 2
    sc = sw / model["w"]
    ox = CARD["x"] / 100 * STAGE_W + 1 + 24 + SVG_DX
    oy = CARD["y"] / 100 * STAGE_H + 1 + 24 + TITLE_H
    return ox, oy, sc


def link_paths() -> list[dict]:
    """Every drawable flow's curve in stage percent, from the server-side layout (the d3-sankey port behind sankey_flow)."""
    m = wa._sk_model(sankey_block(False))
    ox, oy, sc = svg_frame(m)
    out = []
    for l in m["links"]:
        a, c = l["source"]["x1"], l["target"]["x0"]
        mx = (a + c) / 2
        pts = [(a, l["y0"]), (mx, l["y0"]), (mx, l["y1"]), (c, l["y1"])]
        pc = [((ox + x * sc) / STAGE_W * 100, (oy + y * sc) / STAGE_H * 100) for x, y in pts]
        f = lambda v: ("%.2f" % v).rstrip("0").rstrip(".")
        d = "M%s,%s C%s,%s %s,%s %s,%s" % tuple(f(v) for p in pc for v in p)
        out.append({"s": l["source"]["id"], "t": l["target"]["id"], "d": d, "color": PALETTE[l["source"]["id"]], "col": l["source"]["layer"]})
    return out


def film() -> dict:
    paths = link_paths()
    blocks = [{"type": "motion_transition", "id": "sk", "place": {"x": CARD["x"], "y": CARD["y"], "w": CARD["w"]},
               "from": map_block(), "to": sankey_block(True), "match": "exact"}]
    tracks = [{"target": "sk", "keys": [{"t": 0, "p": 0, "opacity": 0}, {"t": 0.8, "opacity": 1, "ease": "expo-out"}, {"t": 3.6, "p": 0},
                                        {"t": 6.6, "p": 1, "ease": "quart-in-out"}]}]
    n = len(paths)
    dur_pass = 1.6
    for i, p in enumerate(paths):
        t0 = 8.6 + (i % 6) * 0.25 + (0.5 if p["col"] == 1 else 0)
        keys = [{"t": 0, "opacity": 0, "scale": 0}, {"t": t0, "opacity": 0, "scale": 0, "a": 0, "ease": "hold"}, {"t": t0 + 0.4, "opacity": 0.95, "scale": 1, "a": 0.08}]
        t = t0
        passes = int((14.4 - t0) // dur_pass)
        assert passes >= 2
        for k in range(passes):
            keys.append({"t": round(t + dur_pass, 3), "a": 1, "ease": "linear"})
            if k < passes - 1:
                keys.append({"t": round(t + dur_pass + 0.01, 3), "a": 0, "ease": "hold"})
            t += dur_pass
        keys.append({"t": round(t + 0.4, 3), "opacity": 0, "scale": 0, "a": 1})
        blocks.append({"type": "motion_shape", "id": "d%d" % i, "shape": "circle", "draw": "none", "fill": p["color"], "glow": 0,
                       "place": {"x": 0, "y": 0, "w": DOT, "h": round(DOT * STAGE_W / STAGE_H, 2)},
                       "w": 12, "h": 12})
        tracks.append({"target": "d%d" % i, "path": p["d"], "trail": {"n": TRAIL_N, "lag": TRAIL_LAG}, "keys": keys})
    assert n * (1 + TRAIL_N) <= PARTICLE_CAP, "particle cap"
    hud = [
        ("cap1", "Where it starts: *six exporters*", 0.6, 3.4, 4.5),
        ("cap2", "The countries become the first column of a *flow*", 3.8, 7.0, 4.5),
        ("cap3", "Cargo moves from origin to destination", 8.2, 14.6, 4.5),
        ("cred", "Concept: Cornelius van Heerden. Figures are illustrative.", 0.0, DURATION, 95.0),
    ]
    for hid, text, a, b, y in hud:
        small = hid == "cred"
        blocks.append({"type": "motion_text", "id": hid, "text": text, "size": 16 if small else 30, "layer": "hud", "font": "sans", "reveal": "fade",
                       "weight": "regular" if small else "bold", "color": "#475569" if small else "#0f172a", "place": {"x": 4, "y": y if not small else 94, "w": 92, "h": 6 if small else 8}})
        if small:
            tracks.append({"target": hid, "keys": [{"t": 0, "opacity": 0.55}]})
        else:
            tracks.append({"target": hid, "keys": [{"t": 0, "opacity": 0, "p": 0}, {"t": a, "opacity": 0, "p": 0, "ease": "hold"}, {"t": a + 0.5, "opacity": 1, "p": 1},
                                                   {"t": b - 0.4, "opacity": 1}, {"t": b, "opacity": 0}]})
    camera = {"keys": [
        {"t": 0, "x": 50, "y": 50, "zoom": 1.0, "rx": 0, "ry": 0},
        {"t": 3.6, "zoom": 1.06, "ease": "standard"},
        {"t": 6.8, "zoom": 1.0, "rx": 0, "ry": 0, "ease": "quart-in-out"},
        {"t": 9.2, "zoom": 0.92, "rx": 52, "ry": -14, "ease": "quart-in-out"},
        {"t": 12.4, "zoom": 0.96, "rx": 50, "ry": 14, "ease": "standard"},
        {"t": 15.2, "zoom": 1.0, "rx": 0, "ry": 0, "ease": "quart-in-out"},
    ]}
    return {"type": "motion_timeline", "title": "Sankey cinema: exporters on a map become a flow, then a 3D scene", "aspect": "16:9",
            "duration": DURATION, "poster": DURATION, "loop": False, "transcript": True, "backdrop": "grid", "theme": "light",
            "blocks": blocks, "tracks": tracks, "camera": camera}


NOTE = ("Concept: Cornelius van Heerden. This scene is a composition of existing atoms (choropleth_map, sankey_flow with keyed true, "
        "motion_transition, motion_shape particles on motion_path-style tracks, a camera track); no visual design or branding of the concept is copied. "
        "Figures are illustrative, not statistics. Particles are capped at %d on screen (this film draws %d: %d dots, each with a %d-copy trail), "
        "because they get heavy on low-end devices. Reduced motion and the poster frame show the settled state: the flat Sankey, with its text table. "
        "Free drag-orbit and depth-curved lit ribbons need WebGL and are out of scope." % (PARTICLE_CAP, 0, 0, TRAIL_N))


def particle_count(f: dict | None = None) -> tuple[int, int]:
    """(heads, elements on screen at once): every dot block plus its trail copies."""
    f = f or film()
    heads = sum(1 for b in f["blocks"] if str(b.get("id", "")).startswith("d"))
    return heads, heads * (1 + TRAIL_N)


def payload() -> dict:
    f = film()
    heads, els = particle_count(f)
    note = NOTE.replace("(this film draws 0: 0 dots", "(this film draws %d: %d dots" % (els, heads))
    return {"title": "Sankey cinema scene", "theme": "light",
            "blocks": [f, {"type": "callout", "kind": "info", "title": "About this scene", "text": note}]}


def demo_page(lang: str = "en") -> str:
    """A standalone page: the real renderer's output for the payload (wa.render), in a plain document."""
    body = wa.render(payload()["blocks"], "light")
    return ('<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Sankey cinema scene</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:1rem auto;padding:0 1rem;color:#0f172a}'
            'h1{font-size:1.2rem}</style></head><body><main><h1>Sankey cinema scene</h1>'
            '<p>Exporters on a world map become the first column of a Sankey, the Sankey tilts into 3D under a scripted camera, and particles '
            'ride its flows. Open with #t=11 to freeze on a frame.</p>' + body + '</main></body></html>')


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--page"]:
        Path(a[1]).write_text(demo_page())
    else:
        out = a[0] if a else "-"
        s = json.dumps(payload(), indent=1, ensure_ascii=False)
        (sys.stdout.write(s + "\n") if out == "-" else Path(out).write_text(s + "\n"))
