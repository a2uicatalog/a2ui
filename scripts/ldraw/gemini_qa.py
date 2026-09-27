#!/usr/bin/env python3
"""Gemini visual QA of baked LEGO parts (catalogue-expansion helper, hard-capped on spend).

For each part in public/parts/: render the baked triangle mesh (flat-shaded isometric, PIL), fetch the part's
Rebrickable photo, and ask Gemini whether they match and what looks wrong. Gemini only FLAGS; nothing here changes
public/parts -- results go to a review file a human/agent reads before any re-bake.

Safety:
  * the API key is fetched at runtime from the artful-patrol GCP project via gcloud, held in memory only, never
    printed or written, and scrubbed from any error text;
  * every call goes through a cost meter with a HARD stop (default USD 15, ledger persisted across runs at
    ~/.cache/a2ui/gemini_catalog_spend.json) so a re-run can never exceed the total budget.

  python3 scripts/ldraw/gemini_qa.py --limit 5            # trial
  python3 scripts/ldraw/gemini_qa.py                      # all baked parts
"""
import argparse
import base64
import io
import json
import math
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "public" / "parts"
OUT = ROOT / "scripts" / "ldraw" / "qa"
LEDGER = Path.home() / ".cache" / "a2ui" / "gemini_catalog_spend.json"
PROJECT = "artful-patrol-502116-b7"
PRICES = {"gemini-3.7-flash": (0.75, 3.75),       # USD per million tokens (3.7 is an introductory rate through 2026-12-31)
          "gemini-3.5-flash-lite": (0.30, 2.50), "gemini-2.5-flash-lite": (0.10, 0.40)}
MODEL = "gemini-3.7-flash"
PRICE_IN, PRICE_OUT = PRICES[MODEL]
ENDPOINT = "https://aiplatform.googleapis.com/v1beta1/publishers/google/models/%s:generateContent"
MAX_CALL_USD = 0.02                        # conservative per-call ceiling used before the call is made


class Meter:
    def __init__(self, cap):
        self.cap, self.lock = cap, threading.Lock()
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        self.spent = json.loads(LEDGER.read_text())["usd"] if LEDGER.exists() else 0.0

    def reserve(self, n=1):
        with self.lock:
            if self.spent + MAX_CALL_USD * n > self.cap:
                raise SystemExit("budget cap reached: $%.4f of $%.2f spent -- stopping" % (self.spent, self.cap))

    def add(self, tin, tout):
        with self.lock:
            self.spent += (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
            LEDGER.write_text(json.dumps({"usd": self.spent}))
            return self.spent


def _gcloud(args):
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}   # gcloud runs its own Python
    return subprocess.run(['gcloud'] + args, capture_output=True, text=True, check=True, env=env).stdout


def get_key():
    """Pick the key restricted to the API this file actually calls (ENDPOINT's host), not just the first key
    returned -- the project holds more than one API key for different features (e.g. a generativelanguage.
    googleapis.com key for an unrelated Voice feature), and list order is not a service match."""
    host = ENDPOINT.split("/")[2]
    names = _gcloud(["services", "api-keys", "list", "--project", PROJECT, "--format=value(name)"]).split()
    for name in names:
        restriction = _gcloud(["services", "api-keys", "describe", name, "--project", PROJECT,
                               "--format=value(restrictions.apiTargets[0].service)"]).strip()
        if restriction == host:
            return _gcloud(["services", "api-keys", "get-key-string", name, "--format=value(keyString)"]).strip()
    raise RuntimeError("no API key in project %s is restricted to %s" % (PROJECT, host))


def render(mesh, size=384):
    q = mesh["quant"]
    tris = []
    for g in mesh["triangles"]:
        p = np.array(g["pos"], dtype=float) / q
        tris.append(p.reshape(-1, 3, 3))
    for st in mesh["connectors"]["studs"]:             # studs are connectors in the bake (drawn as instances), so draw them here
        c = np.array(st["pos"], dtype=float) / q
        d = np.array(st["dir"], dtype=float)
        d /= max(np.linalg.norm(d), 1e-9)
        u = np.cross(d, [1.0, 0.0, 0.0] if abs(d[0]) < 0.9 else [0.0, 1.0, 0.0])
        u /= np.linalg.norm(u)
        w = np.cross(d, u)
        ring = [c + 6 * (math.cos(t) * u + math.sin(t) * w) for t in np.linspace(0, 2 * math.pi, 9)[:-1]]
        top = [r + 4 * d for r in ring]
        for i in range(8):
            j = (i + 1) % 8
            tris.append(np.array([[ring[i], ring[j], top[j]], [ring[i], top[j], top[i]], [c + 4 * d, top[i], top[j]]]))
    T = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
    T[:, :, 1] *= -1                                   # LDraw y is down -> flip so studs point up
    ay, ax = math.radians(35), math.radians(28)
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    V = T @ Ry.T @ Rx.T
    n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    shade = np.clip(0.35 + 0.65 * np.abs(n @ np.array([0.3, 0.6, 0.75]) / np.linalg.norm([0.3, 0.6, 0.75])), 0, 1)
    depth = V[:, :, 2].mean(axis=1)
    lo, hi = V[:, :, :2].reshape(-1, 2).min(0), V[:, :, :2].reshape(-1, 2).max(0)
    scale = 0.86 * size / max(hi - lo)
    off = size / 2 - (lo + hi) / 2 * scale
    S = size * 2                                                        # 2x supersample, then downsample
    zb = np.full((S, S), -1e18)
    rgb = np.empty((S, S, 3), dtype=np.uint8)
    rgb[:] = (238, 241, 245)
    P = np.empty((len(V), 3, 3))
    P[:, :, 0] = V[:, :, 0] * scale * 2 + off[0] * 2
    P[:, :, 1] = S - (V[:, :, 1] * scale * 2 + off[1] * 2)
    P[:, :, 2] = V[:, :, 2]
    for i in range(len(P)):
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = P[i]
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        xmin, xmax = int(max(0, math.floor(min(x0, x1, x2)))), int(min(S - 1, math.ceil(max(x0, x1, x2))))
        ymin, ymax = int(max(0, math.floor(min(y0, y1, y2)))), int(min(S - 1, math.ceil(max(y0, y1, y2))))
        if xmin > xmax or ymin > ymax:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any():
            continue
        z = l0 * z0 + l1 * z1 + l2 * z2
        sub = zb[ymin:ymax + 1, xmin:xmax + 1]
        upd = m & (z > sub)
        sub[upd] = z[upd]
        c = int(60 + 170 * shade[i])
        rgb[ymin:ymax + 1, xmin:xmax + 1][upd] = (c, int(c * 0.55), int(c * 0.5))
    img = Image.fromarray(rgb).resize((size, size), Image.LANCZOS)
    return img


def png_b64(img):
    b = io.BytesIO()
    img.save(b, "PNG")
    return base64.b64encode(b.getvalue()).decode()


_rb_lock, _rb_last = threading.Lock(), [0.0]


def rebrickable_image(part_id, rb_key):
    cache = OUT / "refs" / (part_id + ".png")
    if cache.exists():
        return Image.open(cache).convert("RGB")
    img = _fetch_ref(part_id, rb_key)
    if img is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        img.save(cache)
    return img


def _fetch_ref(part_id, rb_key):
    with _rb_lock:                                     # free key: ~1 request/second
        time.sleep(max(0.0, 1.1 - (time.time() - _rb_last[0])))
        _rb_last[0] = time.time()
    base = part_id
    for cand in (base, base.rstrip("abcdefghijklmnopqrstuvwxyz")):
        try:
            req = urllib.request.Request("https://rebrickable.com/api/v3/lego/parts/%s/" % cand,
                                         headers={"Authorization": "key " + rb_key})
            url = json.load(urllib.request.urlopen(req, timeout=30)).get("part_img_url")
            if url:
                data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "a2ui-qa"}), timeout=30).read()
                return Image.open(io.BytesIO(data)).convert("RGB").resize((384, 384))
        except Exception:
            continue
        finally:
            time.sleep(1.1)
    return None


SCHEMA = {"type": "OBJECT", "properties": {
    "verdict": {"type": "STRING", "enum": ["pass", "warn", "fail"]},
    "matches_reference": {"type": "STRING", "enum": ["yes", "partly", "no", "no_reference"]},
    "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
    "visible_studs": {"type": "INTEGER"},
    "notes": {"type": "STRING"}}, "required": ["verdict", "matches_reference", "issues"]}


def _part_prompt_block(i, mesh, ref_img):
    c = mesh["connectors"]
    b = mesh["bounds"]
    span = [round((b["max"][i2] - b["min"][i2]) / mesh["quant"] / 20, 2) for i2 in range(3)]
    return ("PART %d: id %s \"%s\". %s Baked data: %d top studs, %d bottom sockets, %d holes, %d pins, %d occupancy "
            "boxes; size in studs (x,y,z) = %s." % (i, mesh["id"], mesh["title"],
            "Its reference photo follows its render." if ref_img else "No reference photo is available.",
            len(c["studs"]), len(c["sockets"]), len(c["holes"]), len(c["pins"]), len(mesh["occupancy"] or []), span))


def ask_batch(key, meter, items):
    """items: [(mesh, render_img, ref_img), ...]. One Gemini call judges all of them, returning a JSON array in the
    same order -- batching amortises the fixed system-instruction overhead across parts (images, the dominant cost,
    don't get cheaper by batching, so the saving is real but modest: roughly the fixed-prompt fraction of a call).
    Returns a list of result dicts, same length and order as `items` -- an item Gemini dropped or added spuriously
    is never silently mis-attributed: a short response is padded with verdict="error" (never a fabricated pass),
    a long one is truncated and flagged in every result's "notes"."""
    intro = ("You are QA-ing %d baked 3D models of LEGO parts (LDraw geometry), one after another. For each part, "
             "its render image comes first (isometric, studs up, flat-shaded), then its reference photo of the real "
             "part if one is available. Judge whether each render is a correct, complete model of the real part "
             "(shape, proportions, studs present, nothing inverted/mirrored/missing or with stray geometry) -- "
             "independently of the others. Respond with a JSON array of exactly %d objects, one per part IN ORDER, "
             "each: verdict pass|warn|fail, matches_reference, issues (short strings, empty if none), visible_studs, "
             "notes." % (len(items), len(items)))
    content = [{"text": intro}]
    for i, (mesh, render_img, ref_img) in enumerate(items, 1):
        content.append({"text": _part_prompt_block(i, mesh, ref_img)})
        content.append({"inline_data": {"mime_type": "image/png", "data": png_b64(render_img)}})
        if ref_img:
            content.append({"inline_data": {"mime_type": "image/png", "data": png_b64(ref_img)}})
    schema = {"type": "ARRAY", "minItems": len(items), "maxItems": len(items), "items": SCHEMA}
    body = {"contents": [{"role": "user", "parts": content}],
            "generationConfig": {"maxOutputTokens": 1024 * len(items), "temperature": 0.1,
                                 "thinkingConfig": {"thinkingBudget": 0}, "responseMimeType": "application/json",
                                 "responseSchema": schema}}
    meter.reserve(len(items))
    req = urllib.request.Request(ENDPOINT % MODEL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    for attempt in range(5):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=120))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(4 * 2 ** attempt)
                continue
            raise RuntimeError("gemini HTTP %d" % e.code)
    u = data.get("usageMetadata", {})
    meter.add(u.get("promptTokenCount", 0), (u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)))
    text_out = data["candidates"][0]["content"]["parts"][0]["text"]
    results = json.loads(text_out)
    if not isinstance(results, list):
        results = [results]
    note = "" if len(results) == len(items) else " [batch response had %d entries for %d parts -- misaligned, requeue]" % (len(results), len(items))
    results = (results + [{"verdict": "error", "issues": ["missing from batch response"]}] * len(items))[:len(items)]
    if note:
        for r in results:
            r["notes"] = (r.get("notes") or "") + note
    return results


def ask(key, meter, mesh, render_img, ref_img):
    c = mesh["connectors"]
    b = mesh["bounds"]
    span = [round((b["max"][i] - b["min"][i]) / mesh["quant"] / 20, 2) for i in range(3)]
    text = ("You are QA-ing a baked 3D model of a LEGO part (LDraw geometry). Image 1 is our flat-shaded render "
            "(isometric, studs up) of part %s \"%s\". %s\nBaked data: %d top studs, %d bottom sockets, %d holes, %d pins, "
            "%d occupancy boxes; size in studs (x,y,z) = %s.\nJudge whether the render is a correct, complete model of the "
            "real part (shape, proportions, studs present, nothing inverted/mirrored/missing or with stray geometry). "
            "Respond as JSON: verdict pass|warn|fail, matches_reference, issues (short strings, empty if none), "
            "visible_studs (count you can see in the render), notes."
            % (mesh["id"], mesh["title"], "Image 2 is a photo of the real part." if ref_img else "No reference photo is available.",
               len(c["studs"]), len(c["sockets"]), len(c["holes"]), len(c["pins"]), len(mesh["occupancy"] or []), span))
    parts = [{"text": text}, {"inline_data": {"mime_type": "image/png", "data": png_b64(render_img)}}]
    if ref_img:
        parts.append({"inline_data": {"mime_type": "image/png", "data": png_b64(ref_img)}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.1, "thinkingConfig": {"thinkingBudget": 0},
                                 "responseMimeType": "application/json", "responseSchema": SCHEMA}}
    meter.reserve()
    req = urllib.request.Request(ENDPOINT % MODEL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    for attempt in range(5):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=90))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(4 * 2 ** attempt)
                continue
            raise RuntimeError("gemini HTTP %d" % e.code)  # never echo the body: it can quote request details
    u = data.get("usageMetadata", {})
    meter.add(u.get("promptTokenCount", 0), (u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)))
    text_out = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text_out)


def main():
    global MODEL, PRICE_IN, PRICE_OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cap", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--model", default=MODEL, choices=sorted(PRICES))
    a = ap.parse_args()
    MODEL = a.model
    PRICE_IN, PRICE_OUT = PRICES[MODEL]
    meter = Meter(a.cap)
    key = get_key()
    rb_key = _gcloud(["secrets", "versions", "access", "latest", "--secret=rebrickable", "--project", PROJECT]).strip()
    ids = a.only or sorted(json.loads((PARTS / "index.json").read_text())["parts"])
    if a.limit:
        ids = ids[:a.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "renders").mkdir(exist_ok=True)
    results = {}
    lock = threading.Lock()

    def work(pid):
        mesh = json.loads((PARTS / (pid + ".json")).read_text())
        img = render(mesh)
        img.save(OUT / "renders" / (pid + ".png"))
        ref = rebrickable_image(pid, rb_key)
        try:
            r = ask(key, meter, mesh, img, ref)
        except SystemExit:
            raise
        except Exception as e:
            r = {"verdict": "error", "issues": [str(e).replace(key, "[redacted]")[:120]]}
        r["title"] = mesh["title"]
        with lock:
            results[pid] = r
            print("%-8s %-5s ref=%-12s %s  ($%.3f)" % (pid, r["verdict"], r.get("matches_reference", "-"),
                  "; ".join(r.get("issues", []))[:90], meter.spent), flush=True)

    try:
        with ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(work, ids))
    finally:
        (OUT / ("gemini_qa_results_%s.json" % MODEL)).write_text(json.dumps(results, indent=1, sort_keys=True))
    tally = {}
    for r in results.values():
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("done", tally, "spent $%.4f of $%.2f" % (meter.spent, a.cap))


if __name__ == "__main__":
    main()
