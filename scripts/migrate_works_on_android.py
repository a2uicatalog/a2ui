#!/usr/bin/env python3
"""One-shot migration: tag atoms `works_on: android` in atoms/schema.yaml.

Same mechanics as migrate_works_on_mcp_apps.py, for the same reasons: text-surgical
(only INSERTS lines, so the shared &idNNN works_on anchors and folded strings stay
byte-identical), then proves equivalence by loading the file before and after.

Rule (Curtis, 2026-10-04: list android on every bridge-capable atom): an atom works
on android if and only if it works on mcp-apps. The Android library
(android/a2ui-atoms) draws every catalogue atom by running the SAME MCP Apps renderer
bundle in a WebView, so the two surfaces support exactly the same atoms, and every
mcp-apps degraded_on note (sample data instead of live Workspace data, no
persistence) applies to android unchanged and is copied across.

Anchors: a shared works_on list carries mcp-apps for all of its aliases or none, so
tagging the anchor tags exactly the aliases the rule wants; verify() checks that.

Run once: python3 scripts/migrate_works_on_android.py
Idempotent: atoms already tagged are skipped.
"""
import copy
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "atoms" / "schema.yaml"

SURFACE = "android"
SOURCE = "mcp-apps"

TYPE_RE = re.compile(r"^- type: (\S+)$")
WORKS_ON_RE = re.compile(r"^    works_on:(?: (&\S+|\*\S+))?\s*$")
ITEM_RE = re.compile(r"^    - (\S+)\s*$")
DEGRADED_RE = re.compile(r"^    degraded_on:\s*$")
ENTRY_RE = re.compile(r"^    - surface: (\S+)\s*$")


def _atom_chunks(lines):
    """Split into [preamble, atom1, atom2, ...] at each top-level `- type:` line."""
    chunks, cur = [], []
    for line in lines:
        if TYPE_RE.match(line) and cur:
            chunks.append(cur)
            cur = []
        cur.append(line)
    chunks.append(cur)
    return chunks


def _migrate_atom(chunk, stats):
    m = TYPE_RE.match(chunk[0])
    if not m:
        return chunk
    out, i, n = [], 0, len(chunk)
    tag = False
    while i < n:
        line = chunk[i]
        wm = WORKS_ON_RE.match(line)
        if wm:
            marker = wm.group(1)
            out.append(line)
            i += 1
            if marker and marker.startswith("*"):
                stats["alias"] += 1           # inherits from its anchor's edit
                continue
            items = []
            while i < n and ITEM_RE.match(chunk[i]):
                items.append(ITEM_RE.match(chunk[i]).group(1))
                out.append(chunk[i])
                i += 1
            if SURFACE in items:
                stats["already"] += 1
            elif SOURCE in items:
                out.append(f"    - {SURFACE}\n")
                if marker:
                    stats["anchors"].append(marker)
                else:
                    stats["tagged"] += 1
            continue
        if DEGRADED_RE.match(line):
            out.append(line)
            i += 1
            entries = []                      # (surface, [lines])
            while i < n and (chunk[i].startswith("    - ") or chunk[i].startswith("      ")):
                em = ENTRY_RE.match(chunk[i])
                if em:
                    entries.append((em.group(1), [chunk[i]]))
                elif entries:
                    entries[-1][1].append(chunk[i])
                out.append(chunk[i])
                i += 1
            have = {s for s, _ in entries}
            if SURFACE not in have:
                for s, elines in entries:
                    if s == SOURCE:
                        out.append(f"    - surface: {SURFACE}\n")
                        out.extend(elines[1:])
                        stats["degraded"] += 1
            continue
        out.append(line)
        i += 1
    return out


def migrate(lines):
    stats = {"tagged": 0, "already": 0, "alias": 0, "anchors": [], "degraded": 0}
    out = []
    for chunk in _atom_chunks(lines):
        out.extend(_migrate_atom(chunk, stats))
    return out, stats


def _surfaces(a):
    s = a.get("surfaces") or {}
    return list(s.get("works_on") or []), list(s.get("degraded_on") or [])


def verify(old_text, new_text):
    """The proof: the only per-atom change is android appended to works_on exactly
    where mcp-apps is listed, plus an android copy of each mcp-apps degraded_on note."""
    old = {a["type"]: a for a in yaml.safe_load(old_text)["blocks"]}
    new = {a["type"]: a for a in yaml.safe_load(new_text)["blocks"]}
    assert old.keys() == new.keys(), "atom set changed!"
    tagged = 0
    for t, oa in old.items():
        na = new[t]
        ow, od = _surfaces(oa)
        nw, nd = _surfaces(na)
        if SURFACE in ow:
            assert nw == ow, f"{t}: already-tagged atom changed"
        elif SOURCE in ow:
            assert nw == ow + [SURFACE], f"{t}: works_on wrong: {ow} -> {nw}"
            tagged += 1
        else:
            assert nw == ow, f"{t}: non-{SOURCE} atom was tagged: {nw}"
        want_d = list(od)
        if not any(d.get("surface") == SURFACE for d in od):
            want_d += [dict(d, surface=SURFACE) for d in od if d.get("surface") == SOURCE]
        assert nd == want_d, f"{t}: degraded_on wrong: {nd}"
        oa2, na2 = copy.deepcopy(oa), copy.deepcopy(na)
        for d in (oa2, na2):
            d.pop("surfaces", None)
        assert oa2 == na2, f"{t}: non-surface fields changed!"
        osur = {k: v for k, v in (oa.get("surfaces") or {}).items() if k not in ("works_on", "degraded_on")}
        nsur = {k: v for k, v in (na.get("surfaces") or {}).items() if k not in ("works_on", "degraded_on")}
        assert osur == nsur, f"{t}: other surfaces keys changed!"
    return len(old), tagged


def main():
    old_text = SCHEMA.read_text()
    out, stats = migrate(old_text.splitlines(keepends=True))
    new_text = "".join(out)
    total, tagged = verify(old_text, new_text)
    SCHEMA.write_text(new_text)
    print(f"✓ verified equivalence across {total} atoms; {tagged} now list {SURFACE}")
    print(f"  tagged (literal): {stats['tagged']}")
    print(f"  tagged via anchors {stats['anchors']}: +{stats['alias']} aliases")
    print(f"  already tagged:   {stats['already']}")
    print(f"  degraded_on copied from {SOURCE}: {stats['degraded']}")


if __name__ == "__main__":
    main()
