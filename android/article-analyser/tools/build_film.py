#!/usr/bin/env python3
"""Builds docs/architecture-film.html: the article analyser's architecture as an animated film, drawn with the
catalog's own motion_arch atom and rendered by the public web renderer (renderers/web_article.py).

    python3 android/article-analyser/tools/build_film.py

The page is self-contained (no network): open it in a browser, press play or drag the bar.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]                       # the repo root
sys.path.insert(0, str(ROOT))
from renderers.web_article import render     # noqa: E402

BG, PANEL, INK, MUTE, A1, A2 = "#1e2733", "#2d3642", "#eaeff5", "#9ca5b1", "#8d98ff", "#2ac4ce"
DUR = 24.0

DIAGRAM = {
    "type": "motion_arch", "id": "arch", "label": "Article analyser, step by step", "size": 17,
    "accent": A1, "accent2": A2, "color": INK, "mute": MUTE, "fill": PANEL, "background": BG,
    "groups": [{"label": "Your phone", "x": 1.5, "y": 3, "w": 30, "h": 94, "at": 0.0},
               {"label": "Cloudflare", "x": 36, "y": 3, "w": 33, "h": 94, "at": 0.14}],
    "nodes": [
        {"id": "share", "kind": "user", "label": "Share sheet", "sub": "1 · link and lens", "x": 16.5, "y": 18, "w": 26, "at": 0.02},
        {"id": "fq", "kind": "device", "label": "Fetch and queue", "sub": "2-3 · Jsoup, WorkManager", "x": 16.5, "y": 41, "w": 26, "at": 0.08},
        {"id": "lib", "kind": "store", "label": "Offline library", "sub": "7 · files, sync", "x": 16.5, "y": 64, "w": 26, "at": 0.58},
        {"id": "reader", "kind": "surface", "label": "Native reader", "sub": "8-11 · Compose ladder", "x": 16.5, "y": 87, "w": 26, "at": 0.72},
        {"id": "mcp", "kind": "server", "label": "read_article", "sub": "4-6 · closed tool list", "x": 52.5, "y": 41, "w": 27, "at": 0.16},
        {"id": "store", "kind": "store", "label": "Durable Object", "sub": "your readings", "x": 52.5, "y": 64, "w": 27, "at": 0.48},
        {"id": "llm", "kind": "model", "label": "Gemini", "sub": "reads the article", "x": 87.5, "y": 41, "w": 22, "at": 0.26}],
    "edges": [
        {"from": "share", "to": "fq", "label": "shared link", "at": 0.06},
        {"from": "fq", "to": "mcp", "label": "tools/call", "at": 0.18},
        {"from": "mcp", "to": "llm", "label": "read", "style": "dashed", "both": True, "curve": -45, "at": 0.28},
        {"from": "mcp", "to": "store", "label": "save reading", "at": 0.50},
        {"from": "fq", "to": "lib", "label": "keep offline", "at": 0.60},
        {"from": "lib", "to": "reader", "label": "draw natively", "at": 0.74},
        {"from": "store", "to": "lib", "label": "sync", "style": "dashed", "at": 0.88}],
    "messages": [
        {"edge": 0, "text": "{url}", "at": 0.08, "dur": 0.07},
        {"edge": 1, "text": "{url, text, lens}", "at": 0.20, "dur": 0.09},
        {"edge": 2, "text": "article text", "at": 0.31, "dur": 0.07},
        {"edge": 2, "text": "claim, grounds, warrant", "back": True, "at": 0.40, "dur": 0.08, "color": "#f0b45a"},
        {"edge": 3, "text": "payload", "at": 0.52, "dur": 0.07, "color": "#81c995"},
        {"edge": 1, "text": "A2UI payload", "back": True, "at": 0.54, "dur": 0.09, "color": A2},
        {"edge": 4, "text": "payload", "at": 0.62, "dur": 0.08, "color": A2},
        {"edge": 5, "text": "concept_ladder", "at": 0.76, "dur": 0.08, "color": A2},
        {"edge": 6, "text": "new readings", "at": 0.90, "dur": 0.07, "color": "#81c995"}]}


def film() -> dict:
    head = {"font": "sans", "weight": "black", "reveal": "mask", "line_height": 0.98, "tracking": -0.03, "color": INK, "accent": A1}
    return {"type": "motion_timeline", "title": "Article analyser, step by step", "aspect": "16:9", "duration": DUR, "loop": False,
            "accent": A1, "background": BG, "backdrop": "flat", "theme": "dark", "controls": True, "poster": DUR - 0.5,
            "blocks": [
                {"type": "motion_text", "id": "eb", "text": "ARCHITECTURE · ARTICLE ANALYSER", "place": {"x": 3.5, "y": 4, "w": 60},
                 "size": 16, "weight": "bold", "tracking": 0.16, "reveal": "fade", "mode": "words", "color": A2},
                {"type": "motion_text", "id": "hd", "text": "From *share sheet* to native reader.", "place": {"x": 3.5, "y": 8.5, "w": 90},
                 "size": 40, **head},
                {**DIAGRAM, "place": {"x": 11, "y": 19, "w": 78}},
                {"type": "motion_finish", "id": "fin", "grain_amount": 0.05, "leak": "cool", "leak_amount": 0.12, "layer": "hud",
                 "place": {"x": 0, "y": 0, "w": 100, "h": 100, "z": 90}},
            ],
            "tracks": [{"target": "hd", "keys": [{"t": 0.2, "p": 0}, {"t": 1.4, "p": 1, "ease": "expo-out"}]},
                       {"target": "arch", "keys": [{"t": 0.8, "p": 0}, {"t": DUR - 1.5, "p": 1, "ease": "linear"}]}]}


if __name__ == "__main__":
    body = render([film()])
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Article analyser architecture</title><body style="margin:0;background:{BG}">{body}</body></html>')
    out = HERE.parent / "docs" / "architecture-film.html"
    out.write_text(page)
    print("wrote", out.relative_to(ROOT), len(page), "bytes")
