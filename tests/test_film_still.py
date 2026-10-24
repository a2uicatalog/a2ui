"""film_still (I91): a film's poster = its settled frame as static HTML for PDF, email and Chat."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import film_still as fs  # noqa: E402

FILMS = ["landing/film-wide-dark.json", "landing/film-wide-light.json", "landing/film-tall-dark.json",
         "landing/film-tall-light.json", "content/what-is-a2ui.film.json"]


def load(p):
    d = json.loads((ROOT / p).read_text())
    return d["blocks"][0]


def small(extra=None):
    f = {"type": "motion_timeline", "duration": 6, "poster": 5, "blocks": [
        {"type": "motion_text", "id": "a", "text": "Hello *world*", "place": {"x": 5, "y": 5, "w": 60}},
        {"type": "motion_text", "id": "b", "text": "Gone by then", "place": {"x": 5, "y": 40, "w": 60}}],
        "tracks": [{"target": "a", "keys": [{"t": 0, "opacity": 0}, {"t": 1, "opacity": 1}]},
                   {"target": "b", "keys": [{"t": 0, "opacity": 1}, {"t": 2, "opacity": 0}]}]}
    f.update(extra or {})
    return f


def test_poster_has_no_script_animation_or_controls():
    for p in FILMS:
        h = fs.film_poster_html(load(p))
        assert "<script" not in h, p
        assert "animation" not in h.lower() and "@keyframes" not in h, p
        assert "mt-play" not in h and "mt-rng" not in h, p
        assert h.count("<div") == h.count("</div>"), p


def test_poster_is_deterministic():
    for p in FILMS:
        assert fs.film_poster_html(load(p)) == fs.film_poster_html(load(p))


def test_poster_carries_the_final_text_and_hides_what_has_left():
    h = fs.film_poster_html(load("landing/film-wide-dark.json"))   # declared poster 32.5 of 33 s: the call to action
    assert "Try it" in h and "Browse the" in h
    m = re.search(r'data-mt-id="s1"[^>]*style="([^"]*)"', h)       # the first scene has been handed over
    assert "opacity:0.000" in m.group(1)
    h2 = fs.film_poster_html(load("content/what-is-a2ui.film.json"))
    assert "Write the letter once. Every surface can draw it." in h2


def test_time_argument_and_declared_poster_pick_the_frame():
    f = small()
    at5 = fs.film_poster_html(f)                       # declared poster 5 s
    at0 = fs.film_poster_html(f, t=0)
    assert re.search(r'data-mt-id="a"[^>]*opacity:1\.000', at5)
    assert re.search(r'data-mt-id="a"[^>]*opacity:0\.000', at0)
    assert re.search(r'data-mt-id="b"[^>]*opacity:0\.000', at5)
    assert re.search(r'data-mt-id="b"[^>]*opacity:1\.000', at0)
    f2 = small()
    del f2["poster"]                                   # the renderer's default: 60% of duration
    assert fs.film_poster_html(f2) == fs.film_poster_html(f2, t=3.6)


def test_progress_settles_and_width_scales_the_stage():
    f = {"type": "motion_timeline", "duration": 6, "poster": 5, "blocks": [
        {"type": "stat_card", "id": "k", "label": "Atoms", "value": "1,000", "place": {"x": 5, "y": 5, "w": 40}}],
        "tracks": [{"target": "k", "keys": [{"t": 0, "p": 0}, {"t": 2, "p": 1}]}]}
    h = fs.film_poster_html(f, width=640)
    assert "--p:1.0000" in h
    assert "scale(0.50000)" in h and "width:640px" in h


def test_forwards_animation_is_replaced_by_its_end_state():
    f = {"type": "motion_timeline", "duration": 4, "blocks": [
        {"type": "progress_ring", "id": "r", "value": 70, "place": {"x": 5, "y": 5, "w": 20}}], "tracks": []}
    h = fs.film_poster_html(f)
    assert "stroke-dasharray" in h and "animation" not in h


def test_payload_wrapper_and_document():
    d = json.loads((ROOT / "landing/film-wide-dark.json").read_text())
    assert "Try it" in fs.film_poster_html(d)
    doc = fs.film_poster_document(d)
    assert doc.startswith("<!doctype html>") and "<script" not in doc
