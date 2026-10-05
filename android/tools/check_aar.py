#!/usr/bin/env python3
"""Verify a built a2ui-atoms AAR against this checkout (android-build's verify step).

Fails unless the AAR:
  * registers exactly the STABLE atoms in atoms/schema.yaml. A missing one would throw on a
    device (androidx.a2ui rejects unregistered types); an extra preview atom would be
    published to Maven Central, where a release can never be withdrawn;
  * carries a renderer-bundle.html byte-identical to public/surfaces/mcp-apps/
    renderer-bundle.html (the web and Android surfaces must run the same renderer);
  * contains the public entry point, ai.a2uicatalog.android.A2uiAtomicCatalog.

Usage: python3 android/tools/check_aar.py [path/to/a2ui-atoms-release.aar]
"""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AAR = ROOT / "android" / "a2ui-atoms" / "build" / "outputs" / "aar" / "a2ui-atoms-release.aar"


def main(aar_path: Path) -> int:
    if not aar_path.exists():
        print(f"❌ no AAR at {aar_path}: run the android-build step first", file=sys.stderr)
        return 1
    problems = []
    with zipfile.ZipFile(aar_path) as aar:
        names = set(aar.namelist())
        atoms = json.loads(aar.read("assets/atoms.json")) if "assets/atoms.json" in names else None
        bundle = aar.read("assets/renderer-bundle.html") if "assets/renderer-bundle.html" in names else None
        classes = zipfile.ZipFile(io.BytesIO(aar.read("classes.jar"))).namelist() if "classes.jar" in names else []

    # The release AAR is the published one: stable atoms only (preview atoms are repo-only).
    schema_atoms = {b["type"] for b in yaml.safe_load(open(ROOT / "atoms" / "schema.yaml"))["blocks"]
                    if b.get("stage") != "preview"}
    if atoms is None:
        problems.append("assets/atoms.json missing")
    else:
        aar_atoms = {a["name"] for a in atoms}
        if aar_atoms != schema_atoms:
            missing, extra = sorted(schema_atoms - aar_atoms), sorted(aar_atoms - schema_atoms)
            problems.append(f"atoms differ from schema.yaml's stable atoms: missing {missing[:8]}, "
                            f"extra (a preview atom here would be published) {extra[:8]}")

    web = (ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html").read_bytes()
    if bundle is None:
        problems.append("assets/renderer-bundle.html missing")
    elif bundle != web:
        problems.append("renderer-bundle.html differs from public/surfaces/mcp-apps/renderer-bundle.html "
                        f"(aar {hashlib.sha256(bundle).hexdigest()[:12]}, web {hashlib.sha256(web).hexdigest()[:12]})")

    if "ai/a2uicatalog/android/A2uiAtomicCatalog.class" not in classes:
        problems.append("public entry point ai.a2uicatalog.android.A2uiAtomicCatalog missing from classes.jar")

    if problems:
        for p in problems:
            print(f"❌ {p}", file=sys.stderr)
        return 1
    print(f"✅ {aar_path.name}: {len(schema_atoms)} atoms match schema.yaml's stable atoms, renderer bundle "
          f"byte-identical to the web bundle ({hashlib.sha256(web).hexdigest()[:12]}), entry point present")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_AAR))
