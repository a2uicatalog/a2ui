#!/usr/bin/env python3
"""Builds the ranked "browse real sets by coverage" gallery manifest for the Brick Design Lab.

Reads a real_set_coverage.py --out JSON (real OMR-vs-catalogue diff, see that script's own docstring),
keeps sets at >= MIN_FRACTION (below that the render is more holes than model -- not honest to list as
"browsable"), and enriches each with its real title + reference image from the Rebrickable API (same auth
pattern as gemini_qa.py's rebrickable_image / scripts/ldraw/pipeline.py). Output is sorted by coverage
descending -- ranked, not gated at a single yes/no threshold, so the honest gradient is visible rather
than hidden behind a pass/fail cutoff.

Usage:
    python3 scripts/ldraw/gen_set_gallery.py --coverage /tmp/set_coverage_now.json --out public/bricksdemo/set_gallery.json

Rebrickable calls are rate-limited to ~1/sec (same real constraint as gemini_qa.py's _fetch_ref) and
cached to a local dir so a re-run only fetches new/changed sets.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

MIN_FRACTION = 0.50
PROJECT = "artful-patrol-502116-b7"


def rb_key():
    return subprocess.check_output(
        ["gcloud", "secrets", "versions", "access", "latest", "--secret=rebrickable", "--project", PROJECT]
    ).decode().strip()


def fetch_set_meta(set_num, key, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (set_num + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    req = urllib.request.Request(
        "https://rebrickable.com/api/v3/lego/sets/%s/" % set_num,
        headers={"Authorization": "key " + key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        meta = {"name": d.get("name"), "img_url": d.get("set_img_url"), "num_parts": d.get("num_parts"),
                "year": d.get("year")}
    except Exception as e:
        meta = {"name": None, "img_url": None, "num_parts": None, "year": None, "error": str(e)}
    cache_file.write_text(json.dumps(meta))
    time.sleep(1.1)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", required=True, help="real_set_coverage.py --out JSON")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache-dir", default=str(Path(__file__).resolve().parent / "_ldraw_cache" / "rb_set_meta"))
    ap.add_argument("--min-fraction", type=float, default=MIN_FRACTION)
    ap.add_argument("--limit", type=int, default=None, help="stop after N sets (smoke test)")
    a = ap.parse_args()

    cov = json.load(open(a.coverage))
    results = [r for r in cov["results"] if "fraction" in r and r["fraction"] >= a.min_fraction]
    results.sort(key=lambda r: -r["fraction"])
    if a.limit:
        results = results[: a.limit]

    key = rb_key()
    cache_dir = Path(a.cache_dir)
    out = []
    for i, r in enumerate(results):
        set_num = r["set"]
        meta = fetch_set_meta(set_num, key, cache_dir)
        out.append({
            "set": set_num,
            "title": meta.get("name") or set_num,
            "img_url": meta.get("img_url"),
            "coverage_pct": round(r["fraction"] * 100, 1),
            "instances": r["parts"],
            "renderable_instances": r.get("renderable", r.get("baked")),
            "rebrickable_url": "https://rebrickable.com/sets/%s/" % set_num,
        })
        print("%3d/%d  %-12s %5.1f%%  %s" % (i + 1, len(results), set_num, r["fraction"] * 100, meta.get("name")),
              file=sys.stderr)

    Path(a.out).write_text(json.dumps({
        "generatedAt": cov.get("generatedAt"),
        "min_fraction": a.min_fraction,
        "sets": out,
    }, indent=1))
    print("wrote %s (%d sets, >= %.0f%% coverage)" % (a.out, len(out), a.min_fraction * 100), file=sys.stderr)


if __name__ == "__main__":
    main()
