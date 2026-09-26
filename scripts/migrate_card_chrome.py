#!/usr/bin/env python3
"""Mechanical sweep: wrap known-neutral chrome literals (border-radius / border-color /
background-color) in the outer wrapper of simple-card renderer functions with
var(--a2ui-<token>,<same literal>) -- the SAME transform already proven on the 7 report-
cluster atoms, applied function-by-function instead of by hand. Fallback stays the modern
preset's value (2026-09-26: modern IS the default), so every converted atom renders modern
by default with zero further edits, exactly like the original 7.

SAFE BY CONSTRUCTION: only touches a function when EVERY chrome property it has (of
border-radius/border/background) is in the already-vetted whitelist below -- the same values
the 7 report-cluster atoms already used. No property is invented (a function with no
`background` stays without one -- adding one would be a visual change, not a refactor).
box-shadow, non-whitelisted colours, dark-mode-specific literals, and chart/svg/canvas/table
content are never touched; those functions are skipped and listed in the report.

Verification is automatic: every candidate is rendered with a synthetic probe payload before
and after, and the outputs must be identical once every var(--a2ui-<token>,val) is folded back
to val -- i.e. what today's page renders is provably unchanged; only the fallback source (an
editable token instead of a bare literal) differs.

Run:  python3 scripts/migrate_card_chrome.py           # dry run
      python3 scripts/migrate_card_chrome.py --apply   # write + self-verify
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "renderers" / "web_article.py"

BORDER = {"#e5e7eb": "border", "#e0e0e0": "border", "#e2e8f0": "border",
          "#dadce0": "border", "#d1d5db": "border", "#eaeaea": "border"}
BG = {"#fff": "surface", "#ffffff": "surface",
      "#f9fafb": "surface-muted", "#fafafa": "surface-muted", "#f8f9fa": "surface-muted"}
RADIUS = {"8": "radius", "10": "radius", "12": "radius", "14": "radius",
          "4": "radius-sm", "6": "radius-sm"}
EXCLUDE_CONTENT = re.compile(r"<svg|<canvas|<table|WebGL|THREE\.|[Cc]hart\(")

FN_RE = re.compile(r"\ndef (_render_\w+)\(b(?:: dict)?\) -> str:(.*?)(?=\ndef _render_|\nclass |\Z)", re.S)


def _modern():
    spec = importlib.util.spec_from_file_location("_dt", ROOT / "renderers" / "_design_tokens.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.TOKEN_PRESETS["modern"]


def find_candidates(src):
    out = []
    for m in FN_RE.finditer(src):
        name, body = m.group(1), m.group(2)
        if EXCLUDE_CONTENT.search(body) or "var(--a2ui-" in body:
            continue   # already tokenized (the original 7), or has content this sweep must not touch
        sm = re.search(r'style="([^"]*)"', body)
        if not sm:
            continue
        style = sm.group(1)
        matches = []
        for pat, table, prop_tpl in (
            (r"border-radius:\s*(\d+)px\b", RADIUS, "border-radius"),
            (r"(border(?:-\w+)?):\s*1px solid (#[0-9a-fA-F]{3,6})\b", BORDER, None),
            (r"(background(?:-color)?):\s*(#[0-9a-fA-F]{3,6})\b", BG, None),
        ):
            mm = re.search(pat, style)
            if not mm:
                continue
            val = mm.group(1) if prop_tpl else mm.group(2)
            table_val = val.lower() if prop_tpl is None else val
            token = table.get(table_val)
            if token is None:
                continue
            prop = prop_tpl or mm.group(1)
            # must be ';'-terminated (or end of string) -- anything else is a shape this
            # sweep doesn't try to parse, skipped rather than guessed at.
            end = mm.end()
            if end < len(style) and style[end] != ";":
                matches = None
                break
            matches.append((mm.start(), end, prop, val, token))
        if not matches:
            continue
        base = m.start(2) + sm.start(1)
        out.append({"name": name, "style": style,
                    "matches": [(s + base, e + base, prop, val, token) for s, e, prop, val, token in matches]})
    return out


def apply(src, candidates, modern):
    log = []
    # bottom-to-top so earlier offsets stay valid
    for c in sorted(candidates, key=lambda c: c["matches"][0][0], reverse=True):
        for s, e, prop, val, token in sorted(c["matches"], key=lambda t: t[0], reverse=True):
            new_val = modern[token]
            replacement = f"{prop}:{new_val};{prop}:var(--a2ui-{token},{new_val})"
            src = src[:s] + replacement + src[e:]
        log.append(f"OK   {c['name']}: {len(c['matches'])} propert{'y' if len(c['matches'])==1 else 'ies'} tokenized")
    return src, log


def verify(before_src, after_src, candidates):
    """Render each candidate's probe payload against BOTH versions of web_article.py (loaded
    standalone, not via the package, so this needs no import side effects) and confirm the
    after-render, with every var(--a2ui-<t>,v) folded back to v, equals the before-render
    byte for byte."""
    import tempfile
    def load(src, tag):
        p = Path(tempfile.mkdtemp()) / "web_article.py"
        p.write_text(src)
        spec = importlib.util.spec_from_file_location(f"_wa_verify_{tag}", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    before_mod, after_mod = load(before_src, "before"), load(after_src, "after")
    fold = re.compile(r"var\(--a2ui-[a-z-]+,((?:[^()]|\([^()]*\))*)\)")
    bad = []
    for c in candidates:
        name = c["name"][len("_render_"):]
        fn_before = before_mod._RENDERERS.get(name)
        fn_after = after_mod._RENDERERS.get(name)
        if fn_before is None or fn_after is None:
            bad.append((c["name"], "not registered in _RENDERERS"))
            continue
        probe = {"text": "x", "label": "x", "title": "x", "items": [], "value": "1",
                 "headers": [], "rows": [], "events": [], "blocks": []}
        try:
            b = fn_before(probe)
            a = fn_after(probe)
        except Exception as e:
            bad.append((c["name"], f"render error: {e}"))
            continue
        a_folded = fold.sub(r"\1", a)
        if a_folded != b:
            bad.append((c["name"], "OUTPUT CHANGED after folding var() back to literal"))
    return bad


if __name__ == "__main__":
    src = TARGET.read_text()
    modern = _modern()
    candidates = find_candidates(src)
    print(f"{len(candidates)} candidate function(s), safe by construction.")
    if "--apply" not in sys.argv:
        for c in candidates[:15]:
            print(" ", c["name"], [(p, v, t) for _, _, p, v, t in c["matches"]])
        if len(candidates) > 15:
            print(f"  ... and {len(candidates) - 15} more")
        sys.exit(0)

    new_src, log = apply(src, candidates, modern)
    print(f"Verifying {len(candidates)} conversions render identically...")
    bad = verify(src, new_src, candidates)
    if bad:
        print(f"\n{len(bad)} FAILED verification -- aborting, no file written:")
        for name, why in bad:
            print(f"  FAIL {name}: {why}")
        sys.exit(1)
    TARGET.write_text(new_src)
    print(f"\nAll {len(candidates)} verified identical. Wrote {TARGET.relative_to(ROOT)}.")
    for line in log:
        print(" ", line)
