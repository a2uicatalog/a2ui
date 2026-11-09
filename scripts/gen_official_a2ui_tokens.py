#!/usr/bin/env python3
"""Write atoms/official_a2ui_tokens.json: the --a2ui-* custom properties the OFFICIAL A2UI default
theme defines, read from an installed @a2ui/web_core (the theme that @a2ui/lit, react and angular
share: src/universal/basic_catalog/styles/default.js).

Refresh:  python3 scripts/gen_official_a2ui_tokens.py [path/to/node_modules/@a2ui]
Default path: $A2UI_NODE_MODULES or /mnt/hdd2/work/a2ui-renderer-suite/node_modules/@a2ui.
Run after upgrading the @a2ui packages, commit the JSON; tests/test_official_token_clash.py then
checks that none of OUR --a2ui-* names is in it (a clash silently kills our values inside the
official theme: --a2ui-border there is a border shorthand, ours a colour).
"""
import json, os, re, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "atoms" / "official_a2ui_tokens.json"
THEME = "web_core/src/universal/basic_catalog/styles/default.js"


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "A2UI_NODE_MODULES", "/mnt/hdd2/work/a2ui-renderer-suite/node_modules/@a2ui"))
    src = (root / THEME).read_text()
    names = sorted(set(re.findall(r"(--a2ui-[a-zA-Z0-9-]+)\s*:", src)))
    ver = json.loads((root / "lit" / "package.json").read_text()).get("version")
    OUT.write_text(json.dumps({"source": THEME, "a2ui_lit_version": ver, "count": len(names),
                               "tokens": names}, indent=1) + "\n")
    print("wrote", OUT, len(names), "tokens")


if __name__ == "__main__":
    main()
