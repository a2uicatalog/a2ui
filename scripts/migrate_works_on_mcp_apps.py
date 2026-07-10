#!/usr/bin/env python3
"""One-shot migration: tag atoms `works_on: mcp-apps` in atoms/schema.yaml.

Text-surgical by design — NOT a yaml round-trip. pyyaml would destroy the
&id006 anchor (aliased by 81 atoms) and ruamel rewraps long folded strings,
burying the real diff in noise. This script only INSERTS lines, then proves
equivalence: it pyyaml-loads the file before and after and asserts the only
semantic delta per atom is the intended works_on/degraded_on addition.

Classification source: the 2026-07-10 renderer scan (all 22 .gs files),
recorded in a2ui-private/spec/mcp-apps-surface-v0.1.md v0.3.
- Class C (excluded — unguarded render-time server fetch; the browser bundle
  overrides these with a degraded card): the 6 atoms in EXCLUDE.
- Class B (tagged + degraded_on note — `typeof X !== 'undefined'` guards fall
  through to mock/sample output in a browser): the 21 atoms in DEGRADED.
- Everything else: tagged, portable as-is.

Run once: python3 scripts/migrate_works_on_mcp_apps.py
Idempotent: atoms already tagged are skipped.
"""
import copy
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "atoms" / "schema.yaml"

SURFACE = "mcp-apps"

EXCLUDE = {
    "doc_ai_summary", "multi_doc_ai_brief", "gemini_handoff",   # atoms_ai.gs
    "adsb_feed", "metar_feed", "firestore_read",                # atoms_data.gs
}

WORKSPACE_NOTE = ("renders sample data — live Google Workspace data "
                  "requires an Apps Script deployment")
LMS_NOTE = ("renders fully but without persistence — progress and live "
            "data need an Apps Script deployment")

DEGRADED = {
    # atom.gs Workspace-native cluster
    "drive_file_list": WORKSPACE_NOTE, "sheet_preview": WORKSPACE_NOTE,
    "gmail_summary": WORKSPACE_NOTE, "calendar_upcoming": WORKSPACE_NOTE,
    "user_greeting": WORKSPACE_NOTE,
    # atoms_workspace.gs
    "calendar_today": WORKSPACE_NOTE, "sheet_stats": WORKSPACE_NOTE,
    "gmail_unread_count": WORKSPACE_NOTE, "user_profile_card": WORKSPACE_NOTE,
    "drive_storage_usage": WORKSPACE_NOTE, "sheet_form_submit": WORKSPACE_NOTE,
    "gmail_inbox": WORKSPACE_NOTE, "drive_recent_files": WORKSPACE_NOTE,
    "drive_folder_contents": WORKSPACE_NOTE, "drive_file_card": WORKSPACE_NOTE,
    # atoms_lms.gs / atoms_lms2.gs
    "progress_store": LMS_NOTE, "module_map": LMS_NOTE,
    "certification_card": LMS_NOTE, "learning_path_selector": LMS_NOTE,
    "video_checkpoint": LMS_NOTE, "leaderboard_card": LMS_NOTE,
}

TYPE_RE = re.compile(r"^- type: (\S+)$")
WORKS_ON_RE = re.compile(r"^    works_on:(?: (&\S+|\*\S+))?\s*$")
ITEM_RE = re.compile(r"^    - (\S+)\s*$")


def migrate(lines):
    out = []
    stats = {"tagged": 0, "already": 0, "excluded": 0, "alias": 0,
             "anchor_tagged": None, "degraded_added": 0}
    i, n = 0, len(lines)
    atom = None
    while i < n:
        line = lines[i]
        m = TYPE_RE.match(line)
        if m:
            atom = m.group(1)
        wm = WORKS_ON_RE.match(line)
        if not (wm and atom):
            out.append(line)
            i += 1
            continue

        marker = wm.group(1)
        if marker and marker.startswith("*"):
            stats["alias"] += 1          # inherits from the anchor edit
            out.append(line)
            i += 1
            continue

        # literal list or anchor definition — collect items
        out.append(line)
        i += 1
        items = []
        while i < n and ITEM_RE.match(lines[i]):
            items.append(ITEM_RE.match(lines[i]).group(1))
            out.append(lines[i])
            i += 1

        is_anchor = bool(marker)         # &id006 — edit tags all 81 aliases
        if atom in EXCLUDE and not is_anchor:
            stats["excluded"] += 1
        elif SURFACE in items:
            stats["already"] += 1
        else:
            out.append(f"    - {SURFACE}\n")
            if is_anchor:
                stats["anchor_tagged"] = marker
            else:
                stats["tagged"] += 1

        # degraded_on for class B — insert or extend, right after works_on
        if atom in DEGRADED:
            note = DEGRADED[atom]
            entry = [f"    - surface: {SURFACE}\n", f"      note: {note}\n"]
            if i < n and lines[i].rstrip() == "    degraded_on:":
                out.append(lines[i]); i += 1
                while i < n and (lines[i].startswith("    - ") or
                                 lines[i].startswith("      ")):
                    out.append(lines[i]); i += 1
                out.extend(entry)
            else:
                out.append("    degraded_on:\n")
                out.extend(entry)
            stats["degraded_added"] += 1
    return out, stats


def verify(old_text, new_text):
    """The proof: pyyaml both versions; the only per-atom delta allowed is
    the intended works_on append and (class B) degraded_on entry."""
    old = {a["type"]: a for a in yaml.safe_load(old_text)["blocks"]}
    new = {a["type"]: a for a in yaml.safe_load(new_text)["blocks"]}
    assert old.keys() == new.keys(), "atom set changed!"
    for t, oa in old.items():
        na = copy.deepcopy(new[t])
        ow = (oa.get("surfaces") or {}).get("works_on") or []
        nw = (na.get("surfaces") or {}).get("works_on") or []
        if t in EXCLUDE:
            assert nw == ow, f"{t}: excluded atom was modified: {nw}"
        elif SURFACE in ow:
            assert nw == ow, f"{t}: already-tagged atom changed: {nw}"
        else:
            assert nw == ow + [SURFACE], f"{t}: works_on wrong: {ow} -> {nw}"
        od = (oa.get("surfaces") or {}).get("degraded_on") or []
        nd = (na.get("surfaces") or {}).get("degraded_on") or []
        if t in DEGRADED:
            assert nd == od + [{"surface": SURFACE, "note": DEGRADED[t]}], \
                f"{t}: degraded_on wrong"
        else:
            assert nd == od, f"{t}: degraded_on changed unexpectedly"
        # everything else must be untouched
        oa2, na2 = copy.deepcopy(oa), na
        for d in (oa2, na2):
            d.pop("surfaces", None)
        assert oa2 == na2, f"{t}: non-surface fields changed!"
    return len(old)


def main():
    old_text = SCHEMA.read_text()
    lines = old_text.splitlines(keepends=True)
    out, stats = migrate(lines)
    new_text = "".join(out)
    total = verify(old_text, new_text)
    SCHEMA.write_text(new_text)
    print(f"✓ verified equivalence across {total} atoms")
    print(f"  tagged (literal): {stats['tagged']}")
    print(f"  tagged via anchor {stats['anchor_tagged']}: +{stats['alias']} aliases")
    print(f"  already tagged:   {stats['already']}")
    print(f"  excluded (class C): {stats['excluded']}")
    print(f"  degraded_on added:  {stats['degraded_added']}")


if __name__ == "__main__":
    main()
