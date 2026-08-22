#!/usr/bin/env python3
"""gen_agent_skills_index.py — compile public/.well-known/agent-skills/index.json.

Agent Skills discovery index (v0.2.0, per orank's agent-readiness audit
2026-08-22: "Agent Skills index conformance"). Lists every SKILL.md under
skills/ with a sha256 digest of its ACTUAL bytes, computed here rather than
hand-typed — a hand-maintained digest silently drifts the moment the skill
content changes, and a stale digest reads as tampering to a strict client,
which is worse than no digest at all.

`url` points at the raw GitHub source, not a a2uicatalog.ai-hosted copy:
skills/ is the single source of truth (also what `npx skills add
a2uicatalog/a2ui` fetches from), and duplicating the same bytes under
public/ would just be a second copy that can drift from the first.

Run:
  python3 scripts/gen_agent_skills_index.py
"""
import hashlib
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILLS_DIR = os.path.join(ROOT, "skills")
OUTPUT = os.path.join(ROOT, "public", ".well-known", "agent-skills", "index.json")
RAW_BASE = "https://raw.githubusercontent.com/a2uicatalog/a2ui/main/skills"


def _frontmatter_field(text: str, field: str) -> str:
    import re
    m = re.search(rf"^---\n.*?^{field}:\s*(.+?)\s*$", text, re.S | re.M)
    if not m:
        raise ValueError(f"SKILL.md missing required frontmatter field: {field}")
    return m.group(1).strip()


def main():
    if not os.path.isdir(SKILLS_DIR):
        raise SystemExit(f"{SKILLS_DIR} missing")

    entries = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8")
        fm_name = _frontmatter_field(text, "name")
        if fm_name != name:
            raise SystemExit(
                f"{skill_md}: frontmatter name '{fm_name}' != directory name '{name}'")
        description = _frontmatter_field(text, "description")
        digest = hashlib.sha256(raw).hexdigest()
        entries.append({
            "name": name,
            "description": description[:200],
            "type": "skill-md",
            "url": f"{RAW_BASE}/{name}/SKILL.md",
            "digest": f"sha256:{digest}",
        })

    index = {
        "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
        "skills": entries,
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {OUTPUT} ({len(entries)} skills)")


if __name__ == "__main__":
    main()
