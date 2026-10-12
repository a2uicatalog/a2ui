#!/usr/bin/env python3
"""motion_lint: check a motion_timeline film against evidence-based limits for animated text.

An atom runs on normalised progress (p 0 to 1); the TIME it takes lives in the film's keyframes. So the limits that depend on time (how fast units arrive,
how long the finished text is held, how often something flashes) cannot be clamps on the atom: they are checked here, on the whole film.

    python3 scripts/motion_lint.py film.json          # prints findings, exit 1 if there is any error
    from motion_lint import lint; lint(film_dict)      # list of findings

Each finding: {level: error | warn | info, rule, target, message}. Errors are safety (flashing). Warnings are legibility and timing. Info is advice.

Evidence behind every number: a2ui-private/briefs/text-motion-evidence.md (Deep Research 2026-10-12, with corrections). In short:
  characters    20-60 ms apart (below 20 reads as a glitch, above 60 as slow typing; 30-50 is comfortable)
  words         40-120 ms apart when they stay on screen (a cascade); a replaced word needs a hold of about 300 ms (reading speed ~200 wpm)
  hold          after the text has finished arriving: at least 500 ms (the eye needs about 150-200 ms to settle after motion) and, for reading, words x 300 ms + 200 ms
  flashing      WCAG 2.3.1: no more than 3 flashes in any second, unless the flashing area is under about 21,824 px2 (a quarter of a 341 x 256 px field at 1024 x 768)
  tracking      reading-size text: -0.05em to +0.2em (wider spacing cuts reading speed; very tight crowds letters)
  rotation      text that must be read: within 30 degrees (10-15% slower to 45, 40-60% slower at 90)
  looping       moving text that runs longer than 5 s needs a way to pause it (WCAG 2.2.2)
"""
from __future__ import annotations

import json
import re
import sys

FLASH_AREA_PX2 = 21824      # WCAG 2.3.1: a quarter of a 341 x 256 field
FLASH_RATE_HZ = 3
SPACE = re.compile(r"\s+")


def _t(key, bpm):
    if isinstance(key.get("t"), (int, float)):
        return float(key["t"])
    if isinstance(key.get("beat"), (int, float)) and bpm:
        return key["beat"] * 60.0 / bpm
    return None


def _blocks(film):
    """Every block in the film by id, with the layer it lives in."""
    out = {}

    def walk(bs, layer):
        for b in bs or []:
            if not isinstance(b, dict):
                continue
            lay = b.get("id") if b.get("type") == "motion_layer" else layer
            if b.get("id"):
                out[b["id"]] = (b, lay)
            walk(b.get("blocks"), lay)
    walk(film.get("blocks"), None)
    return out


def _units(b):
    """How many units a motion_text or motion_capsule reveals, and how many words it holds."""
    if b.get("type") == "motion_capsule":
        w = [x for x in SPACE.split(str(b.get("text") or "Text")[:120]) if x][:12]
        return max(len(w), 1), max(len(w), 1), "words"
    text = b.get("text") if isinstance(b.get("text"), str) else "Text"
    lines = [ln.strip()[:60] for ln in text.split("\n") if ln.strip()][:4] or ["Text"]
    mode = b.get("mode") if b.get("mode") in ("block", "words", "chars") else "lines"
    words = sum(len(ln.split()) for ln in lines)
    if mode == "chars":
        n = sum(len(ln.replace(" ", "")) for ln in lines)
    elif mode == "words":
        n = words
    elif mode == "lines":
        n = len(lines)
    else:
        n = 1
    if n > 120:
        n, mode = 1, "block"
    return max(n, 1), max(words, 1), mode


def _reveal(keys, bpm):
    """(start, end) seconds of the first time p runs from below 1 up to 1, or None."""
    pk = [(_t(k, bpm), k["p"]) for k in keys if isinstance(k.get("p"), (int, float)) and _t(k, bpm) is not None]
    pk.sort()
    for i, (t, p) in enumerate(pk):
        if p >= 0.999 and i > 0 and pk[i - 1][1] < 0.999:
            j = i - 1
            while j > 0 and pk[j - 1][1] < pk[j][1]:
                j -= 1
            return pk[j][0], t
    return None


def _drop_after(keys, bpm, t_end):
    for k in sorted((k for k in keys if isinstance(k.get("p"), (int, float)) and _t(k, bpm) is not None), key=lambda k: _t(k, bpm)):
        if _t(k, bpm) > t_end and k["p"] < 0.999:
            return _t(k, bpm)
    return None


def lint(film: dict) -> list[dict]:
    f: list[dict] = []
    if not isinstance(film, dict):
        return f
    bpm = film.get("bpm") if isinstance(film.get("bpm"), (int, float)) else None
    dur = float(film["duration"]) if isinstance(film.get("duration"), (int, float)) else None
    blocks = _blocks(film)
    scenes = sorted(((_t(s, bpm), s.get("layer")) for s in (film.get("scenes") or []) if isinstance(s, dict) and _t(s, bpm) is not None and s.get("layer")), key=lambda x: x[0])
    overlap = float(film["overlap"]) if isinstance(film.get("overlap"), (int, float)) else 0.6

    def add(level, rule, target, msg):
        f.append({"level": level, "rule": rule, "target": target, "message": msg})

    # looping text that never stops (WCAG 2.2.2)
    if film.get("loop") is True and film.get("controls") is False and (dur or 0) > 5:
        add("warn", "pause-control", "film", "a looping film longer than 5 s with no controls: moving text must be pausable (WCAG 2.2.2); keep controls on, or stop looping")

    for tr in film.get("tracks") or []:
        if not isinstance(tr, dict) or tr.get("target") not in blocks:
            continue
        b, layer = blocks[tr["target"]]
        typ, tid, keys = b.get("type"), tr["target"], [k for k in (tr.get("keys") or []) if isinstance(k, dict)]
        if typ not in ("motion_text", "motion_capsule"):
            continue
        rv = _reveal(keys, bpm)
        if not rv:
            continue
        t0, t1 = rv
        d = t1 - t0
        n, words, mode = _units(b)
        reveal = b.get("reveal") if typ == "motion_text" else (b.get("resolve") or "blur")
        S = b.get("overlap") if isinstance(b.get("overlap"), int) and 1 <= b.get("overlap") <= 8 else 3
        gap_ms = d * 1000.0 / (n + (S if typ == "motion_text" else 1))      # time between one unit starting and the next
        if mode == "chars":
            if gap_ms < 20:
                add("warn", "chars-too-fast", tid, f"characters arrive {gap_ms:.0f} ms apart: under 20 ms reads as a glitch, not as typing (30-50 ms is comfortable)")
            elif gap_ms > 60:
                add("warn", "chars-too-slow", tid, f"characters arrive {gap_ms:.0f} ms apart: over 60 ms feels like slow typing (30-50 ms is comfortable)")
        elif mode == "words" and n > 1:
            if gap_ms < 20:
                add("warn", "words-too-fast", tid, f"words arrive {gap_ms:.0f} ms apart: too fast to see the order (40-120 ms for a cascade)")
            elif gap_ms > 600:
                add("info", "words-slow", tid, f"words arrive {gap_ms:.0f} ms apart: slower than reading speed (about 300 ms a word), so readers wait for the text")
        if mode == "chars" and d > 2.5:
            add("info", "long-cascade", tid, f"a character cascade of {d:.1f} s: cascades over about 0.8 s feel unresponsive in a UI; long is fine in a film if it is the point")
        # hold after the text has arrived
        ends = [x for x in (_drop_after(keys, bpm, t1), dur) if x is not None]
        lay_scene = [t for t, l in scenes if l == layer]
        if lay_scene:
            nxt = [t for t, _l in scenes if t > lay_scene[0]]
            ends.append((min(nxt) + overlap) if nxt else (dur if dur else 1e9))
        if ends:
            hold_ms = (min(ends) - t1) * 1000.0
            budget = words * 300 + 200
            if hold_ms < 500:
                add("warn", "hold-short", tid, f"the finished text is held {max(hold_ms, 0):.0f} ms: at least 500 ms is needed for the eye to settle, and about {budget} ms to read {words} word(s)")
            elif hold_ms < budget:
                add("info", "hold-below-reading", tid, f"held {hold_ms:.0f} ms; reading {words} word(s) at subtitle pace takes about {budget} ms")
        # flashing: noisy reveals that change glyphs quickly over a large area
        if reveal in ("flap", "decode", "scramble") or (isinstance(b.get("split"), int) and b.get("split") > 0):
            size = b.get("size") if isinstance(b.get("size"), (int, float)) else (22 if typ == "motion_capsule" else 64)
            rate = (n + S) / (S * d) if d > 0 else 99      # a place flashes once per unit transition, which lasts S/(n+S) of the reveal
            conc_area = (S if mode == "chars" else 1) * size * size * (0.6 if mode == "chars" else max(len(str(b.get("text") or "Text")), 1) * 0.55)
            if rate > FLASH_RATE_HZ and conc_area > FLASH_AREA_PX2:
                add("error", "flash-risk", tid, f"{reveal or 'split'} flashes each place about {rate:.1f} times a second, over roughly {conc_area:,.0f} px2: above 3 a second and over {FLASH_AREA_PX2:,} px2 can breach WCAG 2.3.1 (three flashes)")
            elif rate > FLASH_RATE_HZ:
                add("info", "flash-rate", tid, f"{reveal or 'split'} flashes each place about {rate:.1f} times a second; the area is under the {FLASH_AREA_PX2:,} px2 exception, but check it at your real size")

    # per-block rules that do not depend on time
    for bid, (b, _l) in blocks.items():
        typ = b.get("type")
        if typ == "motion_text":
            tk = b.get("tracking")
            size = b.get("size") if isinstance(b.get("size"), (int, float)) else 64
            if isinstance(tk, (int, float)) and size < 48 and not -0.05 <= tk <= 0.2:
                add("warn", "tracking-range", bid, f"letter-spacing {tk} em at {size}px: for reading-size text keep it between -0.05 and 0.2 em (wide spacing cuts reading speed about 25% at double)")
            ss = b.get("start_scale")
            if isinstance(ss, (int, float)) and ss > 3:
                add("info", "vestibular-zoom", bid, f"start_scale {ss}: a large zoom can trigger vestibular discomfort; the end state (p = 1) is what a reduced-motion viewer sees")
            if b.get("prism"):
                add("info", "vestibular-spin", bid, "prism turns the words in 3D on the step dial: a spinning motion; the end state is what a reduced-motion viewer sees")
        elif typ == "motion_pattern":
            ang = b.get("angle")
            if isinstance(ang, (int, float)) and abs(ang) > 30:
                add("info", "rotated-text", bid, f"text at {ang} degrees: reading slows about 10-15% to 45 degrees and 40-60% at 90; fine for decoration, not for a message")
    return f


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    film = json.load(open(argv[1]))
    out = lint(film)
    for x in out:
        print(f"{x['level'].upper():5} {x['rule']:20} {x['target']:12} {x['message']}")
    print(f"{len(out)} finding(s): {sum(x['level'] == 'error' for x in out)} error, {sum(x['level'] == 'warn' for x in out)} warn, {sum(x['level'] == 'info' for x in out)} info")
    return 1 if any(x["level"] == "error" for x in out) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
