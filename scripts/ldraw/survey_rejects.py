#!/usr/bin/env python3
"""Surveys the pinned LDraw parts library for parts that currently lack occupancy (needs_occupancy=True).
Groups rejected parts by category (from 0 !CATEGORY header or first word of title).

Usage:
    LDRAW_DIR=scripts/ldraw/_ldraw_cache/ldraw python3 scripts/ldraw/survey_rejects.py --out /tmp/reject_survey.json
"""
import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from resolve import Library, ColourTable, resolve_part  # noqa: E402
import parts as P  # noqa: E402

LDRAW_DEFAULT = str(HERE / "_ldraw_cache" / "ldraw")
STUD_SUBFILE = re.compile(r"\bstud(2a?|10|15)?\.dat\b", re.I)
HOLE_SUBFILE = re.compile(r"\bpeghole\.dat\b", re.I)


def _worker_init(ldraw_dir):
    global _LIB, _COLOURS
    _LIB = Library(ldraw_dir)
    _COLOURS = ColourTable(_LIB)


def _check_part(args):
    filename, title, cat = args
    pid = filename[:-4]
    try:
        part = resolve_part(_LIB, _COLOURS, filename)
        occ, sockets, needs = P.resolve_occupancy_and_sockets(
            pid, title, part.min, part.max, part.holes, part.studs, part.tris
        )
        return pid, cat, needs
    except Exception:
        return pid, cat, True


def survey(ldraw_dir, out_path, workers=5):
    parts_dir = Path(ldraw_dir) / "parts"
    if not parts_dir.is_dir():
        sys.exit(f"Parts directory not found: {parts_dir}")

    files = sorted(os.listdir(parts_dir))
    print(f"Scanning {len(files)} files under {parts_dir}...")

    candidates = []
    scanned_count = 0
    fast_clean = 0
    rejects_by_cat = {}

    tyre_parts = getattr(P, "TYRE_PARTS", set())

    for f in files:
        if not f.endswith(".dat") or f.startswith("~"):
            continue
        path = parts_dir / f
        with open(path, "r", encoding="utf-8", errors="replace") as fp:
            lines = fp.readlines()
        if not lines:
            continue
        l0 = lines[0].strip()
        if not l0.startswith("0 ") or l0.startswith("0 ~"):
            continue
        title = l0[2:].strip()
        if title.startswith("~") or "Moved to" in title:
            continue

        cat = None
        is_shortcut = False
        has_connector_ref = False
        for line in lines:
            raw = line.strip()
            if not raw:
                continue
            if raw.startswith("0 !CATEGORY"):
                cat = raw.split("0 !CATEGORY", 1)[1].strip()
            elif raw.startswith("0 !LDRAW_ORG") and "Shortcut" in raw:
                is_shortcut = True
                break
            elif raw.startswith("1 "):
                if STUD_SUBFILE.search(raw) or HOLE_SUBFILE.search(raw):
                    has_connector_ref = True

        if is_shortcut:
            continue
        if not cat:
            cat = title.split()[0] if title.split() else "Unknown"

        pid = f[:-4]
        scanned_count += 1

        # Fast path 1: plain rectangular box
        if P.classify_box(title) is not None:
            fast_clean += 1
            continue

        # Fast path 2: known families that always have occupancy
        if (
            pid in P.OVERRIDES
            or pid in P.ROUND_PARTS
            or pid in P.DISH_PARTS
            or pid in tyre_parts
        ):
            candidates.append((f, title, cat))
            continue

        # If it has no connectors and is not in named families, it cannot have occupancy
        if not has_connector_ref and pid not in P.CORNER_L_PARTS and pid not in P.SLOPE_BACK_WALL_PARTS and pid not in P.TECHNIC_HOLES_PARTS:
            rejects_by_cat.setdefault(cat, []).append(pid)
            continue

        candidates.append((f, title, cat))

    print(f"Scanned {scanned_count} parts: {fast_clean} fast-clean, {len(candidates)} candidates for full check...")

    t0 = time.time()
    done = 0
    total_cand = len(candidates)
    with ProcessPoolExecutor(max_workers=workers, initializer=_worker_init, initargs=(ldraw_dir,)) as pool:
        futures = {pool.submit(_check_part, item): item for item in candidates}
        for fut in as_completed(futures):
            pid, cat, needs = fut.result()
            if needs:
                rejects_by_cat.setdefault(cat, []).append(pid)
            done += 1
            if done % 100 == 0 or done == total_cand:
                print(f"Checked {done}/{total_cand} candidates ({time.time() - t0:.1f}s)...", flush=True)

    total_rejected = sum(len(v) for v in rejects_by_cat.values())
    dt = time.time() - t0
    print(f"Candidate check completed in {dt:.1f}s. Total rejected: {total_rejected}")

    # Build output
    category_counts = {k: len(v) for k, v in sorted(rejects_by_cat.items(), key=lambda x: -len(x[1]))}
    output = {
        "summary": {
            "total_scanned": scanned_count,
            "total_rejected": total_rejected,
            "category_counts": category_counts,
        },
        "categories": {k: sorted(v) for k, v in rejects_by_cat.items()},
        "Tyre": sorted(rejects_by_cat.get("Tyre", [])),
    }

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(output, indent=2))
    print(f"Wrote reject survey to {out_file}")

    print("\nTop 15 Reject Categories:")
    for cat, count in list(category_counts.items())[:15]:
        print(f"  {cat:25s}: {count:5d}")
    print(f"  {'Tyre':25s}: {category_counts.get('Tyre', 0):5d}")


def main():
    ap = argparse.ArgumentParser(description="Survey LDraw parts library for rejected parts")
    ap.add_argument("--out", default="/tmp/reject_survey.json", help="Path to output JSON")
    ap.add_argument("--workers", type=int, default=5, help="Number of worker processes")
    args = ap.parse_args()

    ldraw_dir = os.environ.get("LDRAW_DIR", LDRAW_DEFAULT)
    survey(ldraw_dir, args.out, workers=args.workers)


if __name__ == "__main__":
    main()
