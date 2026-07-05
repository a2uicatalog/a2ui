#!/usr/bin/env python3
"""
Compile opted-in training.md sources into knowledge atoms:
public/knowledge/<id>.json (payload + build metadata) and index.json.

Opt-in is declarative: project.yaml `published_knowledge:` lists source
paths. Unlisted sources are never published. The /knowledge/ URL space is
published-but-unannounced: served, but linked from nowhere (not the site
index, not ai-catalog.json, not spec.json) until deliberately called out.
"""
import json
import os
import sys
from datetime import date

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from parse_training_md import parse  # noqa: E402

PUBLIC_KNOWLEDGE = os.path.join(ROOT, "public", "knowledge")


def main():
    with open(os.path.join(ROOT, "project.yaml")) as f:
        manifest = yaml.safe_load(f)
    sources = manifest.get("published_knowledge", []) or []
    os.makedirs(PUBLIC_KNOWLEDGE, exist_ok=True)

    index = []
    expected = {"index.json"}
    failed = False
    for src in sources:
        # Dict entries publish a PRECOMPILED payload (e.g. curriculum-domain
        # decks from the June pipeline) with explicit provenance; string
        # entries are training.md sources parsed deterministically.
        if isinstance(src, dict):
            payload = json.load(open(os.path.join(ROOT, src["payload"])))
            atom = {
                "id": src["id"],
                "title": payload.get("title", src["id"]),
                "domain": src.get("domain", "course"),
                "source": src.get("source", ""),
                "source_url": src.get("source_url"),
                "license": src.get("license", ""),
                "steps": None,
                "coverage": "precompiled",
                "built": str(date.today()),
                "planes": {"learning-interactive": {
                    "surface": payload.get("type", "blocks-page"),
                    "payload": payload}},
            }
            out = f"{src['id']}.json"
            expected.add(out)
            with open(os.path.join(PUBLIC_KNOWLEDGE, out), "w") as f:
                json.dump(atom, f, indent=1, ensure_ascii=False)
                f.write("\n")
            index.append({k: atom[k] for k in
                          ("id", "title", "domain", "source", "license", "steps", "coverage", "built")})
            print(f"  ✅ public/knowledge/{out} (precompiled)")
            continue
        text = open(os.path.join(ROOT, src)).read()
        payload, report = parse(text)
        if payload is None:
            print(f"  ❌ {src}: {report['errors'][0]}", file=sys.stderr)
            failed = True
            continue
        fm = yaml.safe_load(text.split("---")[1])
        atom = {
            "id": fm["id"],
            "title": payload["title"],
            "domain": fm.get("domain"),
            "source": fm.get("source"),
            "source_url": fm.get("source_url"),
            "license": fm.get("license"),
            "steps": report["step_count"],
            "coverage": report["coverage"],
            "built": str(date.today()),
            # The knowledge is the atom; presentations attach as view planes.
            # learning-interactive = the wired training app; future planes
            # (document-static, flashcards, quiz) attach without breaking consumers.
            "planes": {"learning-interactive": {"surface": "a2ui_wired_surface",
                                                 "payload": payload}},
        }
        out = f"{fm['id']}.json"
        expected.add(out)
        with open(os.path.join(PUBLIC_KNOWLEDGE, out), "w") as f:
            json.dump(atom, f, indent=1, ensure_ascii=False)
            f.write("\n")
        index.append({k: atom[k] for k in
                      ("id", "title", "domain", "source", "license", "steps", "coverage", "built")})
        print(f"  ✅ public/knowledge/{out}")

    with open(os.path.join(PUBLIC_KNOWLEDGE, "index.json"), "w") as f:
        json.dump({"knowledgeAtoms": index, "note":
                   "Compiled knowledge artifacts — payload + provenance. Unannounced tier."},
                  f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"  ✅ public/knowledge/index.json ({len(index)} atoms)")

    # prune anything no longer opted in
    for existing in os.listdir(PUBLIC_KNOWLEDGE):
        if existing not in expected:
            os.remove(os.path.join(PUBLIC_KNOWLEDGE, existing))
            print(f"  🧹 pruned public/knowledge/{existing} (no longer opted in)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
