#!/usr/bin/env python3
"""GAS/JS twin of migrate_card_chrome.py -- same transform, same safety discipline, same
modern-default intent, adapted for JS string syntax (single/double quoted, string
concatenation) across atom.gs and atoms_charts.gs. See that script's docstring for the full
rationale; only the JS-specific mechanics are re-explained here.

_RENDERERS is one shared object built by concatenating every atoms_*.gs file in a fixed
order (scripts/gen_mcp_apps_bundle.py); a later file's assignment to the same key overwrites
an earlier one, same "last wins" semantics as Python's duplicate defs, just across files. Not
observed as an actual problem in this codebase (no duplicate keys found), but guarded anyway.

Verification renders each candidate through the REAL MCP Apps bundle in Node (not a mock),
individually, then as the combined batch -- same two-pass pattern as the Python script.

Run:  python3 scripts/migrate_card_chrome_gas.py           # dry run
      python3 scripts/migrate_card_chrome_gas.py --apply   # write + self-verify
"""
import collections
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAS_DIR = ROOT / "apps-script-surface" / "gas-wired-renderer"
# Every renderer source the bundle actually ships (scripts/gen_mcp_apps_bundle.py's own
# NON_RENDERER_GS list, mirrored here) -- the first version of this script only scanned 2 of
# 41 files, found retroactively while reconciling web/GAS token coverage (2026-09-26).
_NON_RENDERER_GS = {"PackMap.gs", "atoms_v1_decode.gs", "atoms_wired_expand.gs",
                    "atoms_wired_render.gs", "atoms_scene_data.gs", "atoms_tokens.gs",
                    "atoms_schema_snapshot.gs"}
FILES = [GAS_DIR / "atom.gs"] + sorted(
    f for f in GAS_DIR.glob("atoms_*.gs") if f.name not in _NON_RENDERER_GS)

BORDER = {"#e5e7eb": "border", "#e0e0e0": "border", "#e2e8f0": "border",
          "#dadce0": "border", "#d1d5db": "border", "#eaeaea": "border",
          "#f3f4f6": "border-soft", "#f1f5f9": "border-soft", "#f0f0f0": "border"}
BG = {"#fff": "surface", "#ffffff": "surface",
      "#f9fafb": "surface-muted", "#fafafa": "surface-muted", "#f8f9fa": "surface-muted",
      "#f3f4f6": "surface-muted", "#e5e7eb": "surface-muted"}
RADIUS = {"8": "radius", "10": "radius", "12": "radius", "14": "radius",
          "4": "radius-sm", "6": "radius-sm"}
_BORDER_PROPS = {"border", "border-top", "border-bottom", "border-left", "border-right"}
EXCLUDE_CONTENT = re.compile(r"<svg|<canvas|<table|WebGL|THREE\.|Chart\(")
# Atoms with a DELIBERATE byte-for-byte Python/GAS parity contract (tests/test_computed_type.py) --
# found the hard way 2026-09-26: tokenizing ONE side's radius/border independently broke that
# contract for type_scale and contrast_audit (each side's ORIGINAL literal happened to already
# match the other; the sweep is not aware of this class of cross-file test and must never touch
# these). If a new byte-parity contract is added elsewhere, add its atoms here too.
_BYTE_PARITY_CONTRACT = {"type_scale", "readability_card", "drop_cap", "contrast_audit"}
FN_RE = re.compile(r"\n_RENDERERS\['(\w+)'\] = function\(b\) \{(.*?)\n\};", re.S)
# One style="..." (or style='...') per candidate, the SAME literal-quote style it already
# uses -- never rewritten to the other quote convention, to keep the diff minimal.
STYLE_RE = re.compile(r"style=(['\"])((?:(?!\1).)*)\1")


def _modern():
    spec = importlib.util.spec_from_file_location("_dt", ROOT / "renderers" / "_design_tokens.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.TOKEN_PRESETS["modern"]


def find_candidates():
    texts = {f: f.read_text() for f in FILES}
    last_start = {}
    for f, t in texts.items():
        for m in FN_RE.finditer(t):
            last_start[(f, m.group(1))] = m.start()   # later file/position wins if repeated

    out = []
    for f, t in texts.items():
        for m in FN_RE.finditer(t):
            name, body = m.group(1), m.group(2)
            if last_start[(f, name)] != m.start():
                continue
            if name in _BYTE_PARITY_CONTRACT:
                continue   # has a cross-file Python/GAS byte-identity test; never touch independently
            if EXCLUDE_CONTENT.search(body) or "var(--a2ui-" in body:
                continue
            # Same fix as migrate_card_chrome.py: several style=/'...'/ attrs can exist per
            # function; take the one that actually looks like a card wrapper (radius+border
            # together), not just the first textually.
            wrapper_pat = re.compile(r"border-radius:\s*\d+px\b.{0,200}?border(?:-\w+)?:\s*1px solid|"
                                     r"border(?:-\w+)?:\s*1px solid.{0,200}?border-radius:\s*\d+px\b", re.S)
            sm = None
            for cand in STYLE_RE.finditer(body):
                if wrapper_pat.search(cand.group(2)):
                    sm = cand
                    break
            if not sm:
                continue
            quote, style = sm.group(1), sm.group(2)
            matches = []
            ok = True
            for pat, table, prop_tpl in (
                (r"border-radius:\s*(\d+)px\b", RADIUS, "border-radius"),
                (r"(border(?:-\w+)?):\s*1px solid (#[0-9a-fA-F]{3,6})\b", BORDER, None),
                (r"(background(?:-color)?):\s*(#[0-9a-fA-F]{3,6})\b", BG, None),
            ):
                mm = re.search(pat, style)
                if not mm:
                    continue
                val = mm.group(1) if prop_tpl else mm.group(2)
                token = table.get(val)
                if token is None:
                    continue
                prop = prop_tpl or mm.group(1)
                end = mm.end()
                if end < len(style) and style[end] != ";":
                    ok = False
                    break
                matches.append((mm.start(), end, prop, val, token))
            if not ok or not matches:
                continue
            base = m.start(2) + sm.start(2)
            out.append({"file": f, "name": name, "quote": quote,
                        "matches": [(s + base, e + base, p, v, tok) for s, e, p, v, tok in matches]})
    return out


def apply_batch(texts, candidates, modern):
    """texts: {file: current_text}. Applies EVERY candidate's edits in ONE bottom-to-top pass
    PER FILE -- never per-candidate separately. Each candidate's match offsets were computed
    once, against the ORIGINAL text; applying them one candidate at a time in separate calls
    (tried first, wrong) shifts bytes for every edit still pending in the same file, silently
    corrupting position calculations for anything after the first edit applied. Caught by the
    verify step's own render check (a Node SyntaxError, not a silent bad render) before
    anything was written -- but the bug was in this script, not the target files: `finally`
    in render_via_bundle already restores the real files on any exception, confirmed (atom.gs
    parses, single definition) before this fix."""
    out = dict(texts)
    by_file = collections.defaultdict(list)
    for c in candidates:
        by_file[c["file"]].extend(c["matches"])
    for f, matches in by_file.items():
        t = out[f]
        for s, e, prop, val, token in sorted(matches, key=lambda m: m[0], reverse=True):
            new_val = modern[token]
            prefix = "1px solid " if prop in _BORDER_PROPS else ""
            repl = f"{prop}:{prefix}{new_val};{prop}:{prefix}var(--a2ui-{token},{new_val})"
            t = t[:s] + repl + t[e:]
        out[f] = t
    return out


_STYLE_ATTR_ANY = re.compile(r"style=(['\"])(?:(?!\1).)*\1")
# Captures the border-shorthand prefix ("1px solid ", or "") SEPARATELY on each side: it sits
# OUTSIDE var(...) in the generated CSS ("border:1px solid X;border:1px solid var(...,X)"), so
# comparing the raw "plain" text (prefix included) against the raw var()-fallback text (prefix
# excluded, since it's outside the parens) is comparing different shapes of the same correct
# value, not a real mismatch -- reconstruct prefix+fallback on both sides before comparing.
_VAR_PAIR = re.compile(r"([a-z-]+):(1px solid )?([^;]+);\1:(?:1px solid )?var\(--a2ui-[a-z-]+,((?:[^()]|\([^()]*\))*)\);?")


def render_via_bundle(texts_override, probes):
    """Build the real MCP Apps bundle (scripts/gen_mcp_apps_bundle.py) with FILES' content
    swapped for texts_override, render each probe through it in Node, return {name: html}."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_mcp_apps_bundle as gen
    real = {f: f.read_text() for f in FILES}
    try:
        for f, t in texts_override.items():
            f.write_text(t)
        bundle = gen.build_bundle()
    finally:
        for f, t in real.items():
            f.write_text(t)
    core = [x for x in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in x[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        # Some renderers roll Math.random() into a uid (e.g. split_pane's CSS class name) --
        # a real, deliberate design choice in the shipped renderer, but it means two
        # INDEPENDENT render calls of the same unmodified function legitimately produce
        # different output, which looks like "content changed" to a before/after diff that
        # isn't actually comparing the transform. Fixed to a constant ONLY inside this
        # throwaway verification process (never touches the real renderer source) so both
        # calls roll identically and the comparison is meaningful again.
        d.write_text("global.window=global;\nMath.random=function(){return 0.42;};\n" + core + "\nvar cs=" + json.dumps(probes) +
                     ";var r={};cs.forEach(function(c){try{r[c.component]=renderAtoms([c],{theme:'light'});}"
                     "catch(e){r[c.component]='THREW: '+e.message;}});console.log(JSON.stringify(r));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-1000:])
    return json.loads(p.stdout)


def verify(candidates, modern, real_texts):
    probes = [{"component": c["name"], "b": "x"} for c in candidates]  # placeholder, replaced below
    # A minimal, generic probe per candidate -- same spirit as the Python script's probe dict.
    probes = [dict({"component": c["name"], "text": "x", "label": "x", "title": "x",
                    "items": [], "value": "1", "headers": [], "rows": [], "events": []})
             for c in candidates]
    before = render_via_bundle(real_texts, probes)
    after_texts = apply_batch(real_texts, candidates, modern)
    after = render_via_bundle(after_texts, probes)

    bad = []
    for c in candidates:
        b, a = before.get(c["name"]), after.get(c["name"])
        if b is None or a is None or a.startswith("THREW") or b.startswith("THREW"):
            bad.append((c["name"], f"render error: before={b!r:.80} after={a!r:.80}"))
            continue
        b_bare = _STYLE_ATTR_ANY.sub("style=STYLE", b)
        a_bare = _STYLE_ATTR_ANY.sub("style=STYLE", a)
        if b_bare != a_bare:
            bad.append((c["name"], "content/structure changed outside a style attribute value"))
            continue
        for prop, prefix, plain, var_fallback in _VAR_PAIR.findall(a):
            if plain != var_fallback:
                bad.append((c["name"], f"{prop}: plain {plain!r} != var() fallback {var_fallback!r}"))
    return bad, after_texts


if __name__ == "__main__":
    real_texts = {f: f.read_text() for f in FILES}
    modern = _modern()
    candidates = find_candidates()
    print(f"{len(candidates)} candidate function(s), safe by construction.")
    by_file = collections.Counter(c["file"].name for c in candidates)
    for f, n in by_file.items():
        print(f"  {f}: {n}")
    if "--apply" not in sys.argv:
        for c in candidates[:15]:
            print(" ", c["name"], c["file"].name, [(p, v, t) for _, _, p, v, t in c["matches"]])
        sys.exit(0)

    print("Verifying individually...")
    good, skipped = [], []
    for c in candidates:
        bad, _ = verify([c], modern, real_texts)
        (skipped if bad else good).append((c, bad))
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for c, bad in skipped:
            for name, why in bad:
                print(f"  SKIP {name}: {why}")
    if not good:
        print("\nNothing verified cleanly -- no file written.")
        sys.exit(1)

    print(f"\nVerifying combined batch of {len(good)}...")
    batch_bad, final_texts = verify([c for c, _ in good], modern, real_texts)
    if batch_bad:
        print(f"{len(batch_bad)} FAILED when combined (passed individually -- overlap?):")
        for name, why in batch_bad:
            print(f"  FAIL {name}: {why}")
        sys.exit(1)

    for f, t in final_texts.items():
        f.write_text(t)
    print(f"\n{len(good)} of {len(candidates)} verified and written.")
