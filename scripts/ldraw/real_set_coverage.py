#!/usr/bin/env python3
"""Measures real-world catalogue coverage against a sample of real LDraw Official Model Repository sets --
"how many actual LEGO sets can this engine render, not just how many parts are in the catalogue". Fetches
real .mpd files live from library.ldraw.org (requires a User-Agent header -- see fetch_library.py's
UA_HEADERS for the same real fix), flattens each with omr_import.py, and reports coverage() per set plus a
summary: how many sets are fully renderable (fraction >= threshold), and the real reject-instance count by
category (cross-referenced against parts.py's resolve_occupancy_and_sockets so "missing entirely from the
catalogue" and "in the catalogue but needs_occupancy" are both counted).

This is the exact real methodology used live in the 2026-09-27 catalogue-completion session to measure the
before/after impact of each family's occupancy work (tyres, wheel-rims, etc.) -- committed here as reusable
tooling instead of living only in a throwaway scratchpad script, since "how many real sets does this unlock"
is the real question every family task should be measured against, not just its own reject-count delta.

Usage:
    LDRAW_DIR=scripts/ldraw/_ldraw_cache/ldraw python3 scripts/ldraw/real_set_coverage.py \
        [--pages N] [--out FILE] [--workers N] [--compare-to OLD_RESULT.json]

--compare-to lets a later run report a real delta against an earlier run's saved JSON (e.g. "before this
session's tile-family task landed" vs "after") -- both files are the --out of a previous run.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import omr_import as om  # noqa: E402

UA_HEADERS = {"User-Agent": "a2ui-catalogue-real-set-coverage (https://github.com/a2uicatalog/a2ui)"}


def get(url, limit=None, timeout=30):
    req = urllib.request.Request(url, headers=UA_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if limit and int(r.headers.get("content-length") or 0) > limit:
            return None
        return r.read().decode("utf-8", "replace")


def collect_set_numbers(pages):
    nums = []
    for n in range(1, pages + 1):
        try:
            body = get("https://library.ldraw.org/omr/sets?page=%d" % n)
        except Exception as e:
            print("page %d: %s" % (n, e), file=sys.stderr)
            break
        found = re.findall(r"\b(\d{3,6}-\d{1,2})\b", body)
        new = [x for x in dict.fromkeys(found) if x not in nums]
        if not new:
            break
        nums += new
    return nums


def fetch_and_score(num, baked):
    try:
        t = get("https://library.ldraw.org/library/omr/%s.mpd" % num, limit=800_000, timeout=45)
    except Exception as e:
        return {"set": num, "err": str(e)[:60]}
    if t is None:
        return {"set": num, "skipped": "too large"}
    try:
        leaves = om.flatten(t)
        c = om.coverage(leaves, baked)
    except Exception as e:
        return {"set": num, "err": "parse: %s" % str(e)[:60]}
    c["set"] = num
    return c


def summarize(results, threshold=0.999, min_parts=5):
    ok = [r for r in results if "fraction" in r]
    complete = [r for r in ok if r["fraction"] >= threshold and r["parts"] >= min_parts]
    total_parts = sum(r["parts"] for r in ok)
    total_renderable = sum(r["renderable"] for r in ok)
    return {
        "sets_scored": len(ok),
        "sets_skipped": sum("skipped" in r for r in results),
        "sets_errored": sum("err" in r for r in results),
        "sets_fully_renderable": len(complete),
        "fully_renderable_set_ids": sorted(r["set"] for r in complete),
        "total_part_instances": total_parts,
        "total_renderable_instances": total_renderable,
        "instance_fraction": (total_renderable / total_parts) if total_parts else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=8, help="OMR set-list pages to fetch (each ~25 sets)")
    ap.add_argument("--out", default=str(HERE / "qa" / "real_set_coverage.json"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--compare-to", default=None, help="an earlier run's --out JSON, to report a real delta")
    a = ap.parse_args()

    nums = collect_set_numbers(a.pages)
    print("Collected %d real set numbers" % len(nums), file=sys.stderr)
    baked = om.baked_ids()

    results = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(fetch_and_score, num, baked): num for num in nums}
        for i, fut in enumerate(cf.as_completed(futs)):
            results.append(fut.result())
            if (i + 1) % 25 == 0:
                print("...%d/%d sets fetched" % (i + 1, len(nums)), file=sys.stderr)

    summary = summarize(results)
    out = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "summary": summary, "results": results}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)

    print("\n=== real set coverage ===")
    print("sets scored: %d (skipped %d, errored %d)" % (
        summary["sets_scored"], summary["sets_skipped"], summary["sets_errored"]))
    print("sets FULLY renderable: %d / %d" % (summary["sets_fully_renderable"], summary["sets_scored"]))
    print("part instances renderable: %d / %d (%.1f%%)" % (
        summary["total_renderable_instances"], summary["total_part_instances"],
        100 * summary["instance_fraction"]))
    print("wrote", a.out)

    if a.compare_to:
        old = json.load(open(a.compare_to))["summary"]
        print("\n=== delta vs %s ===" % a.compare_to)
        print("sets fully renderable: %d -> %d (%+d)" % (
            old["sets_fully_renderable"], summary["sets_fully_renderable"],
            summary["sets_fully_renderable"] - old["sets_fully_renderable"]))
        print("renderable part instances: %d -> %d (%+d)" % (
            old["total_renderable_instances"], summary["total_renderable_instances"],
            summary["total_renderable_instances"] - old["total_renderable_instances"]))


if __name__ == "__main__":
    main()
