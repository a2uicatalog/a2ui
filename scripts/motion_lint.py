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
  flashing      WCAG 2.3.1: no more than 3 flashes in any second, unless the flashing area is under about 21,824 px2 (a quarter of a 341 x 256 px field at 1024 x 768).
                Two checks: noisy text reveals (flash-risk), and a static flash-rate analysis of the film's tracks (flash-general, flash-red; see _flash_lint)
  tracking      reading-size text: -0.05em to +0.2em (wider spacing cuts reading speed; very tight crowds letters)
  rotation      text that must be read: within 30 degrees (10-15% slower to 45, 40-60% slower at 90)
  looping       moving text that runs longer than 5 s needs a way to pause it (WCAG 2.2.2)
"""
from __future__ import annotations

import bisect
import json
import re
import sys

FLASH_AREA_PX2 = 21824      # WCAG 2.3.1: a quarter of a 341 x 256 field
FLASH_RATE_HZ = 3
FLASH_DELTA = 0.10          # WCAG 2.3.1: a general flash is a pair of opposing changes in relative luminance of 10% or more ...
FLASH_DARK_LIMIT = 0.80     # ... where the darker state is below 0.80
RED_DELTA = 20              # WCAG 2.3.1 red flash: opposing changes of 20 or more in (R - G - B) * 320, where a state is saturated red when R / (R + G + B) >= 0.8
SAMPLE_HZ = 240
STAGE_PX = {"16:9": (1280, 720), "4:3": (1200, 900), "1:1": (1000, 1000), "9:16": (720, 1280)}
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


def _reveal(keys, bpm, dial="p"):
    """(start, end) seconds of the first time the dial (p, or s) runs from below 1 up to 1, or None."""
    pk = [(_t(k, bpm), k[dial]) for k in keys if isinstance(k.get(dial), (int, float)) and _t(k, bpm) is not None]
    if dial == "s" and not pk:      # the timeline's key for the step dial is "step"
        pk = [(_t(k, bpm), k["step"]) for k in keys if isinstance(k.get("step"), (int, float)) and _t(k, bpm) is not None]
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


_SHOWPIECE = ("motion_foil", "motion_wrap", "motion_drop", "motion_flag", "motion_disperse", "motion_reveal", "motion_streak")


def _showpiece(add, b, tid, keys, bpm):
    """The showpiece text atoms: how fast their dials may run. Spins and waves are vestibular and flicker risks; a fast wipe of a big area is a sudden change."""
    typ = b["type"]
    p, sv = _reveal(keys, bpm, "p"), _reveal(keys, bpm, "s")
    dp, ds = (p[1] - p[0]) if p else None, (sv[1] - sv[0]) if sv else None
    text = b.get("text") if isinstance(b.get("text"), str) else "Text"
    n = max(len(text.strip()[:48]), 1)
    S = b.get("overlap") if isinstance(b.get("overlap"), int) and 1 <= b.get("overlap") <= 8 else 3
    if typ == "motion_streak" and dp is not None and dp < 0.3:
        add("warn", "streak-fast", tid, f"the line whips in over {dp * 1000:.0f} ms: a big sudden movement; run p over at least 300 ms")
    if typ == "motion_drop" and dp is not None and dp * 1000.0 / (n + S) < 20:
        add("warn", "drop-too-fast", tid, f"letters land {dp * 1000.0 / (n + S):.0f} ms apart: under 20 ms the order cannot be seen; slow the p run")
    if typ == "motion_reveal" and dp is not None:
        if dp < 0.4:
            add("warn", "reveal-fast", tid, f"the mask opens over {dp * 1000:.0f} ms: a large area changes suddenly; run p over at least 400 ms")
        elif b.get("mode") in ("halftone", "blinds", "slats", "diagonal") and dp < 1:
            add("info", "reveal-busy", tid, f"{b.get('mode')} opens many small shapes in {dp:.1f} s; a second or more reads calmer")
    if typ == "motion_wrap":
        turns = b.get("turns") if isinstance(b.get("turns"), int) and not isinstance(b.get("turns"), bool) else 1
        if turns:
            add("info", "vestibular-spin", tid, "wrap turns the words in 3D on the step dial: a spinning motion; the end state is what a reduced-motion viewer sees")
            if ds and abs(turns) * 360.0 / ds > 720:
                add("warn", "spin-fast", tid, f"the form turns {abs(turns) * 360.0 / ds:.0f} degrees a second: over 720 can cause discomfort; slow the s run or use fewer turns")
    if typ == "motion_flag" and ds:
        cyc = b.get("cycles") if isinstance(b.get("cycles"), int) and 1 <= b.get("cycles") <= 6 else 2
        if cyc / ds > 3:
            add("warn", "wave-fast", tid, f"the wave oscillates {cyc / ds:.1f} times a second: over 3 a second reads as flicker (WCAG 2.3.1); lengthen the s run")
    if typ == "motion_foil" and ds is not None and ds < 0.25:
        add("info", "foil-fast", tid, f"the light band crosses in {ds * 1000:.0f} ms; a quick glint is fine, a repeated one over a large area is a flash risk")
    if typ == "motion_disperse" and ds is not None and ds < 0.3:
        add("info", "disperse-fast", tid, f"the exit takes {ds * 1000:.0f} ms; 400 ms or more reads as an intentional exit")


# ── flash rate (WCAG 2.3.1), from the film's tracks ────────────────────────────────────────────────────────────────────────────────
# What can flash in a film: (1) any block's opacity track (a blink, a strobe); (2) motion_flash, a full-frame pop driven by p; (3) motion_lightning
# with flash: true (a pale wash driven by p; its bolt flicker is a thin stroke well under the area limit, and a strike makes at most 2 flashes per
# p pass); (4) motion_beats with the cut transition, whose colour fields swap on the step dial; (5) a brightness or invert filter track (the block's colour scaled and inverted); (6) the noisy text reveals (checked by flash-risk).
# The glitch tear is bounded by construction (under 1.5 swings over p 0 to 1) and is not modelled. Each source is turned into a colour-over-time
# signal sampled at SAMPLE_HZ (keys are read linearly: easing changes when the middle of a move happens, not where it turns), then the signal is
# reduced to its opposing changes. Static analysis of the payload only: no video is rendered.

def _hex(v):
    if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", v):
        h = v[1:]
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return None


def _lum(c):
    lin = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _red(c):
    """(R - G - B) * 320 for a saturated red (R / (R + G + B) >= 0.8), else 0."""
    tot = c[0] + c[1] + c[2]
    return (c[0] - c[1] - c[2]) * 320.0 if tot > 0 and c[0] / tot >= 0.8 else 0.0


def _mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def _clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def _curve(keys, bpm, *props):
    """f(t) for a dial from a track's keys (linear between keys, a hold key jumps on arrival), or None when no key carries the dial."""
    pts = []
    for k in keys:
        tt = _t(k, bpm)
        for pr in props:
            if tt is not None and isinstance(k.get(pr), (int, float)) and not isinstance(k.get(pr), bool):
                pts.append((tt, float(k[pr]), k.get("ease") == "hold"))
                break
    if not pts:
        return None
    pts.sort(key=lambda x: x[0])
    xs = [x[0] for x in pts]

    def f(t):
        if t <= xs[0]:
            return pts[0][1]
        if t >= xs[-1]:
            return pts[-1][1]
        i = bisect.bisect_right(xs, t) - 1
        (t0, v0, _h0), (t1, v1, h1) = pts[i], pts[i + 1]
        if h1:
            return v0
        return v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 1.0)
    return f


def _changes(ts, vals, thr, dark_limit=None):
    """Times of the opposing changes in a signal: each swing of at least thr between turning points (and, for luminance, with the darker end under dark_limit)."""
    out = []
    if not vals:
        return out
    pv, rv, rt, d = vals[0], vals[0], ts[0], 0

    def commit(a, b, tt):
        if abs(b - a) >= thr and (dark_limit is None or min(a, b) < dark_limit):
            out.append(tt)
    for t, v in zip(ts, vals):
        if d == 0:
            if v - pv >= thr:
                d, rv, rt = 1, v, t
            elif pv - v >= thr:
                d, rv, rt = -1, v, t
        elif d == 1:
            if v > rv:
                rv, rt = v, t
            elif rv - v >= thr:
                commit(pv, rv, rt)
                pv, d, rv, rt = rv, -1, v, t
        else:
            if v < rv:
                rv, rt = v, t
            elif v - rv >= thr:
                commit(pv, rv, rt)
                pv, d, rv, rt = rv, 1, v, t
    if d:
        commit(pv, rv, rt)
    return out


def _worst_second(times):
    """(flashes, start, end) of the busiest one-second window: two opposing changes make one flash."""
    best = (0, 0.0, 0.0)
    for i, t0 in enumerate(times):
        j = bisect.bisect_left(times, t0 + 1.0 - 1e-6)
        n = (j - i) // 2
        if n > best[0]:
            best = (n, t0, times[j - 1])
    return best


def _flash_sources(film, bpm, blocks):
    """Yield (block id, type, area in px2, colour function of t) for every block whose tracks can make it flash."""
    asp = STAGE_PX.get(film.get("aspect"), STAGE_PX["16:9"])
    bgc = _hex(film.get("background")) or ((0.96, 0.97, 0.98) if film.get("theme") == "light" else (0.04, 0.06, 0.12))
    keys_of = {}
    for tr in film.get("tracks") or []:
        if isinstance(tr, dict) and isinstance(tr.get("target"), str):
            keys_of.setdefault(tr["target"], []).extend(k for k in (tr.get("keys") or []) if isinstance(k, dict))
    parent = {}

    def walk(bs, par):
        for b in bs or []:
            if isinstance(b, dict):
                if b.get("id"):
                    parent[b["id"]] = par
                walk(b.get("blocks"), b.get("id") or par)
    walk(film.get("blocks"), None)
    op_cache = {}

    def opacity(bid):
        if bid not in op_cache:
            op_cache[bid] = _curve(keys_of.get(bid, []), bpm, "opacity")
        return op_cache[bid]

    def alpha(bid):
        fs, cur = [], bid
        while cur is not None:
            f = opacity(cur)
            if f:
                fs.append(f)
            cur = parent.get(cur)

        def a(t):
            r = 1.0
            for f in fs:
                r *= _clamp(f(t))
            return r
        return a, bool(fs)

    def area(bid):
        w = h = None
        cur = bid
        while cur is not None and (w is None or h is None):
            pl = (blocks.get(cur, ({}, None))[0].get("place") or {})
            pl = pl if isinstance(pl, dict) else {}
            w = pl.get("w") if w is None and isinstance(pl.get("w"), (int, float)) else w
            h = pl.get("h") if h is None and isinstance(pl.get("h"), (int, float)) else h
            cur = parent.get(cur)
        return asp[0] * asp[1] * _clamp((w if w is not None else 100) / 100.0) * _clamp((h if h is not None else 100) / 100.0)

    for bid, (b, _layer) in blocks.items():
        typ = b.get("type")
        keys = keys_of.get(bid, [])
        if not keys:
            continue
        al, has_op = alpha(bid)
        if typ == "motion_flash":
            pf = _curve(keys, bpm, "p")
            if not pf:
                continue
            col = _hex(b.get("color")) or (1.0, 1.0, 1.0)
            st = b.get("strength") if isinstance(b.get("strength"), (int, float)) else 0.8
            st = _clamp(st, 0.1, 1.0)

            def fl(t, pf=pf, al=al, col=col, st=st):
                p = _clamp(pf(t), -0.5, 1.5)
                return _mix(bgc, col, al(t) * _clamp(p * 10) * (1 - _clamp(p)) * st)
            yield bid, typ, area(bid), fl
        elif typ == "motion_lightning" and b.get("flash") is True:
            pf = _curve(keys, bpm, "p")
            if not pf:
                continue
            col = _mix(_hex(b.get("color")) or (0.90, 0.94, 1.0), (1.0, 1.0, 1.0), 0.85)
            under = (0.5, 0.5, 0.5) if b.get("blocks") else bgc      # over child blocks the backdrop is unknown: assume a mid grey

            def fl(t, pf=pf, al=al, col=col, under=under):
                p = _clamp(pf(t), -0.5, 1.5)
                return _mix(under, col, al(t) * 0.3 * _clamp(min((p - 0.04) * 12, (0.2 - p) * 12)))
            yield bid, typ, area(bid), fl
        elif typ == "motion_beats":
            sf = _curve(keys, bpm, "step", "s")
            if not sf:
                continue
            items = b.get("items") if isinstance(b.get("items"), list) else []
            bgs = [(_hex(it.get("bg")) if isinstance(it, dict) else None) or (0.15, 0.20, 0.42) for it in items[:12]]
            while len(bgs) < 2:
                bgs.append((0.15, 0.20, 0.42))
            n, w = len(bgs), (0.2 if b.get("transition") == "fade" else 0.001)

            def fl(t, sf=sf, al=al, bgs=bgs, n=n, w=w):
                u = _clamp(sf(t), 0, 40) * n
                c = bgs[0]
                for j in range(1, n):
                    c = _mix(c, bgs[j], _clamp((u - j) / w))
                return _mix(bgc, c, al(t))
            yield bid, typ, area(bid), fl
        elif typ != "motion_beats" and (_curve(keys, bpm, "brightness") or _curve(keys, bpm, "invert")):
            br_f = _curve(keys, bpm, "brightness")
            inv_f = _curve(keys, bpm, "invert")
            fg = next((c for c in (_hex(b.get(k)) for k in ("bg", "fill", "color", "colour", "accent")) if c), (1.0, 1.0, 1.0))

            def fl(t, al=al, fg=fg, br_f=br_f, inv_f=inv_f):
                br = br_f(t) if br_f else 1.0
                inv = inv_f(t) if inv_f else 0.0
                c = tuple(_clamp(ch * br, 0.0, 1.0) for ch in fg)
                c = tuple(_clamp(ch * (1.0 - inv) + (1.0 - ch) * inv, 0.0, 1.0) for ch in c)
                return _mix(bgc, c, al(t))

            yield bid, typ, area(bid), fl
        elif has_op and opacity(bid):
            fg = next((c for c in (_hex(b.get(k)) for k in ("bg", "fill", "color", "colour", "accent")) if c), (1.0, 1.0, 1.0))
            yield bid, typ, area(bid), (lambda t, al=al, fg=fg: _mix(bgc, fg, al(t)))


def _flash_lint(film, bpm, dur, blocks, add):
    last = max([(_t(k, bpm) or 0) for tr in film.get("tracks") or [] if isinstance(tr, dict) for k in (tr.get("keys") or []) if isinstance(k, dict)] or [0])
    total = min(dur if dur else max(last, 12.0), 120.0)
    n = int(total * SAMPLE_HZ) + 1
    ts = [i / SAMPLE_HZ for i in range(n)]
    for bid, typ, px2, fn in _flash_sources(film, bpm, blocks):
        cols = [fn(t) for t in ts]
        for kind, vals, thr, dl in (("flash-general", [_lum(c) for c in cols], FLASH_DELTA, FLASH_DARK_LIMIT), ("flash-red", [_red(c) for c in cols], RED_DELTA, None)):
            cnt, a, b = _worst_second(_changes(ts, vals, thr, dl))
            if cnt <= FLASH_RATE_HZ:
                continue
            what = "red flashes" if kind == "flash-red" else "flashes"
            if px2 > FLASH_AREA_PX2:
                add("error", kind, bid, f"{typ} '{bid}' makes {cnt} {what} between {a:.2f} s and {b:.2f} s ({cnt} in one second, over roughly {px2:,.0f} px2): more than 3 a second breaches WCAG 2.3.1 (three flashes or below threshold); space the flashes at least a third of a second apart or fade them")
            else:
                add("info", "flash-small-area", bid, f"{typ} '{bid}' makes {cnt} {what} between {a:.2f} s and {b:.2f} s, over roughly {px2:,.0f} px2: under the {FLASH_AREA_PX2:,} px2 exception of WCAG 2.3.1, but check it at your real size")
            break       # one finding per block: the general flash is the one to fix first


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
        if typ in _SHOWPIECE:
            _showpiece(add, b, tid, keys, bpm)
            continue
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

    _flash_lint(film, bpm, dur, blocks, add)

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
