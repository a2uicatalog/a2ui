"""film_to_vtt (I88): WebVTT captions from a film's timed text."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import film_vtt as fv  # noqa: E402

FILMS = ["landing/film-wide-dark.json", "landing/film-tall-light.json", "content/what-is-a2ui.film.json"]
TS = r"\d\d:\d\d:\d\d\.\d{3}"


def cues(vtt):
    out = []
    for blk in vtt.strip().split("\n\n")[1:]:
        lines = blk.split("\n")
        m = re.fullmatch(r"(" + TS + r") --> (" + TS + ")", lines[1])
        assert m, blk
        out.append((m.group(1), m.group(2), "\n".join(lines[2:])))
    return out


def secs(s):
    h, m, r = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(r)


def test_timestamp_format():
    assert fv.ts(0) == "00:00:00.000" and fv.ts(3725.5) == "01:02:05.500" and fv.ts(0.9996) == "00:00:01.000"


def test_real_films_give_valid_ordered_cues():
    for p in FILMS:
        film = json.loads((ROOT / p).read_text())
        v = fv.film_to_vtt(film)
        assert v.startswith("WEBVTT\n\n")
        cs = cues(v)
        assert cs, p
        starts = [secs(a) for a, _, _ in cs]
        assert starts == sorted(starts), p
        dur = film["blocks"][0]["duration"]
        for a, z, text in cs:
            assert 0 <= secs(a) < secs(z) <= dur + 0.001 and text.strip() and "-->" not in text
        assert "*" not in v


def test_cues_follow_the_timeline_not_the_scene_list():
    v = fv.film_to_vtt(json.loads((ROOT / "landing/film-wide-dark.json").read_text()))
    by = {t: (secs(a), secs(z)) for a, z, t in cues(v)}
    a, z = by["Useful for humans."]                    # scene s2 starts 4.6, hands over by 10.2 + 0.9
    assert 4.6 <= a < 6 and 10 < z <= 11.2
    assert "Try it today." in by and by["Try it today."][1] == 33


def test_text_is_escaped_and_hidden_text_gets_no_cue():
    f = {"type": "motion_timeline", "duration": 6, "blocks": [
        {"type": "motion_text", "id": "a", "text": "R&D <b>x</b> -->", "place": {"x": 5, "y": 5, "w": 60}},
        {"type": "motion_text", "id": "never", "text": "Invisible", "place": {"x": 5, "y": 30, "w": 60}}],
        "tracks": [{"target": "a", "keys": [{"t": 1, "opacity": 0}, {"t": 1.2, "opacity": 1}, {"t": 4, "opacity": 1}, {"t": 4.2, "opacity": 0}]},
                   {"target": "never", "keys": [{"t": 0, "opacity": 0}, {"t": 6, "opacity": 0}]}]}
    v = fv.film_to_vtt(f)
    cs = cues(v)
    assert len(cs) == 1
    a, z, text = cs[0]
    assert text == "R&amp;D &lt;b&gt;x&lt;/b&gt; --&gt;"
    assert 1.1 <= secs(a) <= 1.3 and 4.0 <= secs(z) <= 4.2
    assert "Invisible" not in v


def test_demo_caption_lines_become_voiced_cues_in_step_order():
    f = {"type": "motion_timeline", "duration": 6, "blocks": [
        {"type": "demo_caption", "id": "c", "lines": [{"who": "user", "text": "Hi"}, {"who": "agent", "text": "Hello & welcome"}],
         "place": {"x": 5, "y": 5, "w": 60}}],
        "tracks": [{"target": "c", "keys": [{"t": 0, "step": 0}, {"t": 2, "step": 0, "ease": "hold"}, {"t": 2.1, "step": 1}, {"t": 6, "step": 1}]}]}
    cs = cues(fv.film_to_vtt(f))
    assert [c[2] for c in cs] == ["<v user>Hi</v>", "<v agent>Hello &amp; welcome</v>"]
    assert secs(cs[0][1]) <= secs(cs[1][0]) + 0.2


def test_deterministic_and_payload_wrapper():
    d = json.loads((ROOT / "landing/film-wide-dark.json").read_text())
    assert fv.film_to_vtt(d) == fv.film_to_vtt(d["blocks"][0])
