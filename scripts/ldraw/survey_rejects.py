#!/usr/bin/env python3
"""Surveys every real LDraw part NOT already in the curated set, resolves occupancy/sockets exactly like
bake_parts.py does, and buckets the ones that come back needs_occupancy=True by LDraw category -- so a new
per-family occupancy function (see parts.py's ROUND_PARTS/CORNER_L_PARTS/TECHNIC_HOLES_PARTS for the pattern)
can be prioritised by how many rejected parts it would actually unlock, instead of guessing.

A prior session ran this same survey as a throwaway `python3 - <<EOF` heredoc and never saved it --
BRICK_CATALOGUE_STATUS.md section 6 notes it was lost. This is that script, saved for real.

Category comes from each part's own `0 !CATEGORY <name>` header line when present (~25% of files); otherwise
falls back to the LDraw convention of the description's leading word(s) (stripped of a leading size/count like
"6 x 3" or a "~"/"_" prefix marker). Approximate, not authoritative -- good enough to rank families by size.

Usage:
    LDRAW_DIR=.../ldraw python3 scripts/ldraw/survey_rejects.py [--limit N] [--out FILE] [--workers N]

Each part's resolve+classify is independent and CPU-bound (no shared state, no network), so --workers > 1 fans
out over a ProcessPoolExecutor -- this is a local-cores problem, not a Cloud-Run-fan-out problem: the ~13k part
.dat files already live on disk here, and shipping them into a container plus cold-start would cost more than
the whole run takes on this box's 4 cores. Defaults to os.cpu_count().
"""
import argparse
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
from resolve import Library, ColourTable, resolve_part  # noqa: E402
from parts import resolve_occupancy_and_sockets  # noqa: E402

_lib = None
_colours = None


def _init_worker():
    global _lib, _colours
    _lib = Library()
    _colours = ColourTable(_lib)


def _classify_one(pid):
    try:
        part = resolve_part(_lib, _colours, pid + ".dat")
    except Exception as e:
        return (pid, "error", None, "%s: %s" % (pid, e))
    if part.missing:
        return (pid, "error", None, "%s: missing %s" % (pid, sorted(part.missing)))
    title = part.title or pid
    occ, sockets, needs_occ = resolve_occupancy_and_sockets(pid, title, part.min, part.max, part.holes,
                                                              part.studs, part.tris, part.cylinders)
    if not needs_occ:
        return (pid, "accepted", None, None)
    path = _lib.find(pid + ".dat")
    text = open(path, encoding="utf-8", errors="ignore").read() if path else ""
    cat = explicit_category(text) or guessed_category(title)
    return (pid, "rejected", cat, None)

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CURATED = os.path.join(ROOT, "..", "a2ui-private", "spec", "brick-parts", "curated-parts-v1.json")
PARTS_DIR = os.path.join(os.environ.get("LDRAW_DIR") or os.path.join(os.path.dirname(__file__), "_ldraw_cache", "ldraw"), "parts")

PRINTED_RE = re.compile(r"^[a-z0-9]+p[a-z0-9]{2,5}\.dat$", re.I)   # e.g. 3068p01.dat, 2440p02.dat
LEADING_COUNT_RE = re.compile(r"^[~=_]*\s*(\d+\s*[xX]\s*\d+(\.\d+)?\s*)+")


def explicit_category(text):
    m = re.search(r"^0\s+!CATEGORY\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def guessed_category(title):
    t = LEADING_COUNT_RE.sub("", title).strip()
    words = t.split()
    if not words:
        return "(unknown)"
    # LDraw convention: a compound leading word ("Minifig", "Technic", "Plant", "Duplo", "Electric", "Sticker")
    # combines with the next word into a two-word category; otherwise it's just the first word.
    compound = {"minifig", "technic", "duplo", "plant", "electric", "sticker", "container", "baseplate",
                "train", "tile", "wedge", "slope", "panel", "support", "bracket", "arch", "cylinder"}
    if words[0].lower() in compound and len(words) > 1:
        return words[0] + " " + words[1]
    return words[0]


def candidates():
    curated_ids = {e["id"] for e in json.load(open(CURATED))}
    for fn in sorted(os.listdir(PARTS_DIR)):
        if not fn.lower().endswith(".dat"):
            continue
        pid = fn[:-4]
        if pid in curated_ids or PRINTED_RE.match(fn):
            continue
        yield pid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="stop after N candidates (smoke-test the script)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "qa", "reject_survey.json"))
    ap.add_argument("--workers", type=int, default=os.cpu_count(),
                     help="process-pool fan-out (this box's cores, not Cloud Run -- see module docstring); 1 = serial")
    a = ap.parse_args()

    ids = list(candidates())
    if a.limit:
        ids = ids[:a.limit]

    buckets = {}       # category -> [ids]
    errors = []
    accepted = 0
    n = len(ids)
    if a.workers > 1:
        with ProcessPoolExecutor(max_workers=a.workers, initializer=_init_worker) as ex:
            for i, (pid, status, cat, err) in enumerate(ex.map(_classify_one, ids, chunksize=32)):
                if status == "error":
                    errors.append(err)
                elif status == "accepted":
                    accepted += 1
                else:
                    buckets.setdefault(cat, []).append(pid)
                if (i + 1) % 500 == 0:
                    print("...%d/%d scanned, %d accepted, %d rejected so far" % (i + 1, n, accepted,
                          sum(len(v) for v in buckets.values())), file=sys.stderr, flush=True)
    else:
        _init_worker()
        for i, pid in enumerate(ids):
            _, status, cat, err = _classify_one(pid)
            if status == "error":
                errors.append(err)
            elif status == "accepted":
                accepted += 1
            else:
                buckets.setdefault(cat, []).append(pid)
            if (i + 1) % 500 == 0:
                print("...%d/%d scanned, %d accepted, %d rejected so far" % (i + 1, n, accepted,
                      sum(len(v) for v in buckets.values())), file=sys.stderr, flush=True)

    total_rejected = sum(len(v) for v in buckets.values())
    ranked = sorted(buckets.items(), key=lambda kv: -len(kv[1]))
    out = {"scanned": len(ids), "accepted": accepted, "rejected": total_rejected, "errors": len(errors),
           "buckets": {k: v for k, v in ranked}}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(json.dumps(out, indent=1))

    print("\nscanned %d, accepted %d, rejected %d, errors %d" % (len(ids), accepted, total_rejected, len(errors)))
    print("wrote", a.out)
    print("\ntop categories among rejected parts:")
    for cat, pids in ranked[:30]:
        print("  %5d  %s" % (len(pids), cat))
    if errors:
        print("\n%d resolution errors (see script output above / rerun with fewer parts to debug)" % len(errors))


if __name__ == "__main__":
    main()
