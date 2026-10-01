#!/usr/bin/env python3
"""Advisory motion-style lint for A2UI payloads.

Reads a payload (a JSON file holding a block list, or {"blocks": [...]}) and reports where its motion departs from the
style benchmark recorded in a2ui-private/briefs/motion-style-benchmark.md: what reads as DESIGNED rather than generated
in motion-design output by current frontier models (Opus 5.5 benchmark, researched 2026-09-30).

It NEVER fails a build (exit 0 unless --strict). Like check_koans.py, it surfaces candidates for a human to read in
context: a 0.8 s page swap is fine if it is the scene's one hero move, and the lint cannot know that.

Checks (level in brackets):
  [warn] overshoot / anticipate / pop used more than once           "use once, sparingly": bounce on UI is the tell
  [warn] linear easing on position, scale or opacity                 linear is for progress bars and loops only
  [warn] an entrance (opacity rising to ~1) slower than 600 ms       the benchmark caps entrances near 600 ms on expo-out
  [warn] camera shake: rz changing direction more than twice
  [warn] keys off the beat grid when bpm is set (t not on a half beat, tolerance 20 ms)
  [info] a property's first key is after t=0                         it holds that value from t=0 (hidden until its key)
  [info] no bpm                                                      benchmark pieces sit on a beat grid
  [info] duration over 40 s                                          typical pieces are 15-40 s
  [info] no `ease` on a key and no timeline default                  falls back to "standard": fine, but unnamed

Usage:
  python3 scripts/check_motion_style.py payload.json [more.json ...] [--strict] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BOUNCY = {"overshoot", "anticipate"}
LINEAR_OK = {"p", "step"}
ENTRANCE_CAP_S = 0.6
BEAT_TOL_S = 0.02


def _blocks(payload):
    if isinstance(payload, dict) and isinstance(payload.get("blocks"), list):
        return payload["blocks"]
    return payload if isinstance(payload, list) else []


def _walk(blocks):
    for b in blocks:
        if isinstance(b, dict):
            yield b
            for k in ("blocks", "children"):
                if isinstance(b.get(k), list):
                    yield from _walk(b[k])


def _ease_name(e, default):
    if e is None:
        return default
    return e if isinstance(e, str) else "custom"


def lint_timeline(tl: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    default = tl.get("ease") if isinstance(tl.get("ease"), str) else "standard"
    bpm = tl.get("bpm") if isinstance(tl.get("bpm"), (int, float)) and tl.get("bpm") else 0
    dur = tl.get("duration") if isinstance(tl.get("duration"), (int, float)) else 12
    if not bpm:
        out.append(("info", "no bpm: the benchmark sits on a beat grid (set bpm and key with `beat`)"))
    if dur > 40:
        out.append(("info", f"duration {dur:g}s: typical motion pieces are 15-40 s"))
    bouncy, unnamed = 0, 0
    tracks = [(t.get("target", "?"), t.get("keys") or []) for t in tl.get("tracks") or [] if isinstance(t, dict)]
    cam = tl.get("camera") if isinstance(tl.get("camera"), dict) else None
    if cam:
        tracks.append(("camera", cam.get("keys") or []))
    for target, keys in tracks:
        keys = [k for k in keys if isinstance(k, dict)]
        def tm(k):
            if isinstance(k.get("t"), (int, float)):
                return float(k["t"])
            if isinstance(k.get("beat"), (int, float)) and bpm:
                return k["beat"] * 60.0 / bpm
            return None
        keys = sorted((k for k in keys if tm(k) is not None), key=tm)
        props = {p for k in keys for p in k if p not in ("t", "beat", "ease")}
        for p in sorted(props):
            pk = [k for k in keys if isinstance(k.get(p), (int, float))]
            if not pk:
                continue
            if tm(pk[0]) > 0.001:
                out.append(("info", f"{target}.{p}: first key at {tm(pk[0]):.2f}s, so it holds that value from t=0 (fine if it should be hidden until then)"))
            for prev, k in zip(pk, pk[1:]):
                e = _ease_name(k.get("ease"), default)
                if e in BOUNCY:
                    bouncy += 1
                if e == "linear" and p not in LINEAR_OK and target != "camera":
                    out.append(("warn", f"{target}.{p} at {tm(k):.2f}s: linear easing on {p} (linear is for progress and loops)"))
                span = tm(k) - tm(prev)
                if p == "opacity" and prev[p] <= 0.05 and k[p] >= 0.95 and span > ENTRANCE_CAP_S + 1e-6 and e not in ("linear",):
                    out.append(("warn", f"{target} enters over {span * 1000:.0f} ms ({e}): the benchmark caps entrances near {int(ENTRANCE_CAP_S * 1000)} ms"))
        for k in keys:
            if "ease" not in k and not isinstance(tl.get("ease"), str) and k is keys[0]:
                unnamed += 1
            if bpm and isinstance(k.get("t"), (int, float)):
                beats = k["t"] * bpm / 60.0
                off = abs(beats * 2 - round(beats * 2)) * 30.0 / bpm
                if off > BEAT_TOL_S:
                    out.append(("warn", f"{target}: key at t={k['t']:g}s is off the {bpm} BPM grid (nearest half beat is {off * 1000:.0f} ms away)"))
    if cam:
        rz = [k["rz"] for k in (cam.get("keys") or []) if isinstance(k, dict) and isinstance(k.get("rz"), (int, float))]
        turns = sum(1 for a, b, c in zip(rz, rz[1:], rz[2:]) if (b - a) * (c - b) < 0)
        if turns > 2:
            out.append(("warn", f"camera rz changes direction {turns} times: reads as shake"))
    if bouncy > 1:
        out.append(("warn", f"{bouncy} overshoot/anticipate segments: use once, sparingly"))
    if unnamed:
        out.append(("info", "some keys name no ease and there is no timeline default: they use \"standard\""))
    return out


def lint_enter(b: dict) -> list[tuple[str, str]]:
    e = b.get("enter") if b.get("type") != "motion_group" else {k: b.get(k) for k in ("effect", "ease", "duration")}
    if isinstance(e, str):
        e = {"effect": e}
    if not isinstance(e, dict):
        return []
    out = []
    eff = e.get("effect")
    tokens = {"instant": 120, "quick": 240, "base": 400, "slow": 640, "cinematic": 1000}
    dur = e.get("duration")
    ms = tokens.get(dur) if isinstance(dur, str) else dur
    if isinstance(ms, (int, float)) and ms > ENTRANCE_CAP_S * 1000 and eff not in ("wipe",):
        out.append(("warn", f"enter {eff or 'rise'} lasts {ms:g} ms: the benchmark caps entrances near 600 ms"))
    if eff == "pop" or (isinstance(e.get("ease"), str) and e["ease"] in BOUNCY):
        out.append(("warn", f"enter uses a bouncy curve ({eff or e.get('ease')}): use once, sparingly"))
    return out


def lint(payload) -> list[dict]:
    findings, pops = [], 0
    for b in _walk(_blocks(payload)):
        if b.get("type") == "motion_timeline":
            for lvl, msg in lint_timeline(b):
                findings.append({"level": lvl, "where": f"motion_timeline[{b.get('title', '')[:30]}]", "message": msg})
        if b.get("enter") or b.get("type") == "motion_group":
            for lvl, msg in lint_enter(b):
                findings.append({"level": lvl, "where": b.get("type", "?"), "message": msg})
            if (b.get("enter") in ("pop",) or (isinstance(b.get("enter"), dict) and (b["enter"].get("effect") == "pop" or b["enter"].get("ease") in BOUNCY))
                    or b.get("effect") == "pop"):
                pops += 1
    if pops > 1:
        findings.append({"level": "warn", "where": "page", "message": f"{pops} bouncy entrances on one page: use once, sparingly"})
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any warn-level finding")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    worst = 0
    allf = {}
    for f in args.files:
        fs = lint(json.loads(Path(f).read_text()))
        allf[f] = fs
        worst = max(worst, sum(1 for x in fs if x["level"] == "warn"))
        if not args.json:
            print(f"{f}: {sum(1 for x in fs if x['level'] == 'warn')} warn, {sum(1 for x in fs if x['level'] == 'info')} info")
            for x in fs:
                print(f"  [{x['level']}] {x['where']}: {x['message']}")
    if args.json:
        print(json.dumps(allf, indent=2))
    return 1 if (args.strict and worst) else 0


if __name__ == "__main__":
    sys.exit(main())
