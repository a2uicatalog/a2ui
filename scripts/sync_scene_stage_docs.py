#!/usr/bin/env python3
"""Keep the scene_stage atom's enumerated lists (presets, backdrops, grounds, actor motions, the preset count) equal to the kit.

The lists in atoms/schema.yaml used to be typed by hand and drifted (45 presets long after there were 53, no `airfield`, no `interior-home`).
The source of truth is public/catalogue/scene-spec.schema.json (generated from the kit's SPEC_VOCAB, layouts and registry). This rewrites only those
substrings, as text (schema.yaml carries YAML anchors and comments, so it is never round-tripped).

  python3 scripts/sync_scene_stage_docs.py            rewrite atoms/schema.yaml
  python3 scripts/sync_scene_stage_docs.py --check    exit 1 if it is out of date (used by tests/test_scene_stage.py)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "atoms" / "schema.yaml"
SPEC = ROOT / "public" / "catalogue" / "scene-spec.schema.json"


def synced(text: str) -> str:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))["properties"]
    presets, backdrops, grounds = spec["preset"]["enum"], spec["backdrop"]["enum"], spec["ground"]["enum"]
    motions = spec["actors"]["items"]["properties"]["motion"]["enum"]
    i = text.index("- type: scene_stage")
    j = text.index("\n- type: clipart", i)
    block = text[i:j]

    def sub(pattern: str, repl: str, what: str) -> None:
        nonlocal block
        new, n = re.subn(pattern, lambda m: repl, block, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"sync_scene_stage_docs: could not find {what} in the scene_stage block")
        block = new

    sub(r"\(\d+ ready presets\)", f"({len(presets)} ready presets)", "the preset count")
    sub(r"One of: [a-z0-9, -]+\.", "One of: " + ", ".join(sorted(presets)) + ".", "the preset list")
    sub(r'"sky-city"\|[^\n]*?"interior-dark"', "|".join(f'"{b}"' for b in backdrops), "the backdrop list")
    sub(r'"grass"\|[^\n]*?"none"', "|".join(f'"{g}"' for g in grounds), "the ground list")
    sub(r'"walk"\|"ride"[^,\n]*?"land"', "|".join(f'"{m}"' for m in motions), "the motion list")
    return text[:i] + block + text[j:]


def main() -> int:
    current = SCHEMA.read_text(encoding="utf-8")
    new = synced(current)
    if "--check" in sys.argv:
        if new != current:
            print("atoms/schema.yaml scene_stage lists are out of date: run python3 scripts/sync_scene_stage_docs.py")
            return 1
        print("ok: scene_stage lists match the kit")
        return 0
    SCHEMA.write_text(new, encoding="utf-8")
    print("scene_stage lists synced" if new != current else "already in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
