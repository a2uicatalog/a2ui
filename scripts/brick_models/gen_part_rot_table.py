#!/usr/bin/env python3
"""Regenerates blender_view_math.py's PART_ROT block from renderers/brick_parts_validate.py's own PART_ROT --
the existing, already-Python, already-documented twin of the 24-entry LDraw rotation table
(atoms_brick.gs/brick_parts_validate.py/threejs_view_math.js/mcp-worker's omr-import.js already hand-keep in
sync). Generating the 5th (Blender) twin from this one, rather than hand-typing a sixth copy, means an edit to
the source table that isn't followed by re-running this script is caught by tests/test_blender_view_math.py's
drift check, instead of silently becoming a hand-kept copy that can diverge unnoticed.

Usage: python3 scripts/brick_models/gen_part_rot_table.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from renderers.brick_parts_validate import PART_ROT  # noqa: E402

TARGET = Path(__file__).resolve().parent / "blender_view_math.py"
BEGIN = "# BEGIN GENERATED PART_ROT -- do not hand-edit; run gen_part_rot_table.py to refresh from\n" \
        "# renderers/brick_parts_validate.py's PART_ROT.\n"
END = "# END GENERATED PART_ROT\n"


def render_block():
    lines = [BEGIN, "PART_ROT = [\n"]
    for m in PART_ROT:
        lines.append("    (%s),\n" % ", ".join(repr(v) for v in m))
    lines.append("]\n")
    lines.append(END)
    return "".join(lines)


def main():
    src = TARGET.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if not pattern.search(src):
        sys.exit("gen_part_rot_table: BEGIN/END sentinels not found in %s -- was the file restructured?" % TARGET)
    new_src = pattern.sub(render_block().rstrip("\n") + "\n", src)
    if new_src == src:
        print("blender_view_math.py's PART_ROT already matches renderers/brick_parts_validate.py -- no change")
        return
    TARGET.write_text(new_src, encoding="utf-8")
    print("regenerated PART_ROT in %s from renderers/brick_parts_validate.py" % TARGET)


if __name__ == "__main__":
    main()
