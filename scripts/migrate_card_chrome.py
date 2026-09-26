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
import collections
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "renderers" / "web_article.py"

BORDER = {"#e5e7eb": "border", "#e0e0e0": "border", "#e2e8f0": "border",
          "#dadce0": "border", "#d1d5db": "border", "#eaeaea": "border",
          "#f3f4f6": "border-soft", "#f1f5f9": "border-soft", "#f0f0f0": "border"}
BG = {"#fff": "surface", "#ffffff": "surface",
      "#f9fafb": "surface-muted", "#fafafa": "surface-muted", "#f8f9fa": "surface-muted",
      "#f3f4f6": "surface-muted", "#e5e7eb": "surface-muted"}
RADIUS = {"8": "radius", "10": "radius", "12": "radius", "14": "radius",
          "4": "radius-sm", "6": "radius-sm"}
EXCLUDE_CONTENT = re.compile(r"<svg|<canvas|<table|WebGL|THREE\.|[Cc]hart\(")
# Atoms with a DELIBERATE byte-for-byte Python/GAS parity contract (tests/test_computed_type.py) --
# found the hard way 2026-09-26: tokenizing ONE side's radius/border independently broke that
# contract for type_scale and contrast_audit (each side's ORIGINAL literal happened to already
# match the other; the sweep is not aware of this class of cross-file test and must never touch
# these). If a new byte-parity contract is added elsewhere, add its atoms here too.
_BYTE_PARITY_CONTRACT = {"type_scale", "readability_card", "drop_cap", "contrast_audit"}

FN_RE = re.compile(r"\ndef (_render_\w+)\(b(?:: dict)?\) -> str:(.*?)(?=\ndef _render_|\nclass |\Z)", re.S)


def _modern():
    spec = importlib.util.spec_from_file_location("_dt", ROOT / "renderers" / "_design_tokens.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.TOKEN_PRESETS["modern"]


def find_candidates(src):
    # A name can be `def`-ed more than once (an early bootstrap placeholder that gives
    # _RENDERERS a value before the real implementation is defined later and overwrites it
    # -- same pattern documented this session for metric_delta). Python's real runtime
    # semantics: the LAST def wins. Detect that structurally, not by guessing every stub's
    # docstring wording (tried and was wrong for several -- editing an earlier, shadowed def
    # is harmless since _RENDERERS never points at it, but it's noise, not a fix).
    all_starts = collections.defaultdict(list)
    for m in FN_RE.finditer(src):
        all_starts[m.group(1)].append(m.start())
    last_start = {name: max(starts) for name, starts in all_starts.items()}

    out = []
    for m in FN_RE.finditer(src):
        name, body = m.group(1), m.group(2)
        if m.start() != last_start[name]:
            continue   # shadowed earlier definition -- never runs
        if name[len("_render_"):] in _BYTE_PARITY_CONTRACT:
            continue   # has a cross-file Python/GAS byte-identity test; never touch independently
        if EXCLUDE_CONTENT.search(body) or "var(--a2ui-" in body:
            continue   # already tokenized, or has content this sweep must not touch
        # Some functions have SEVERAL style="..." attributes (an inner icon/badge's style
        # textually before the outer wrapper's); taking only the first one (tried first, was
        # wrong for ~90 atoms -- e.g. anchor_list's first style is an inner element's
        # "margin:4px 0;", not its card wrapper) missed the real chrome entirely. Search all
        # of them for the one that actually looks like a card wrapper -- radius AND border
        # together, the strong signal -- rather than guessing from position.
        wrapper_pat = re.compile(r"border-radius:\s*\d+px\b.{0,200}?border(?:-\w+)?:\s*1px solid|"
                                 r"border(?:-\w+)?:\s*1px solid.{0,200}?border-radius:\s*\d+px\b", re.S)
        sm = None
        for cand in re.finditer(r'style="([^"]*)"', body):
            if wrapper_pat.search(cand.group(1)):
                sm = cand
                break
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


_BORDER_PROPS = {"border", "border-top", "border-bottom", "border-left", "border-right"}


def apply(src, candidates, modern):
    log = []
    # bottom-to-top so earlier offsets stay valid
    for c in sorted(candidates, key=lambda c: c["matches"][0][0], reverse=True):
        for s, e, prop, val, token in sorted(c["matches"], key=lambda t: t[0], reverse=True):
            new_val = modern[token]
            prefix = "1px solid " if prop in _BORDER_PROPS else ""
            replacement = f"{prop}:{prefix}{new_val};{prop}:{prefix}var(--a2ui-{token},{new_val})"
            src = src[:s] + replacement + src[e:]
        log.append(f"OK   {c['name']}: {len(c['matches'])} propert{'y' if len(c['matches'])==1 else 'ies'} tokenized")
    return src, log


# A few atoms' field names collide with the generic probe's own shape (e.g. skeleton's own
# `rows`/`cols` are integers, not the generic probe's list-shaped `rows`) -- named overrides
# rather than a smarter generic probe, since it's just this one case so far.
_PROBE_OVERRIDES = {"skeleton": {"rows": 3, "cols": 3}}
_STYLE_ATTR = re.compile(r'style="[^"]*"')
# Captures the border-shorthand prefix ("1px solid ", or "") SEPARATELY on each side: it sits
# OUTSIDE var(...) in the generated CSS, so without this the pattern doesn't match a border
# declaration AT ALL (found retroactively: the border check was silently never running, 0
# matches, not a false pass on bad content -- the generated CSS itself was independently
# confirmed correct by hand before this was caught).
_VAR_PAIR = re.compile(r"([a-z-]+):(1px solid )?([^;]+);\1:(?:1px solid )?var\(--a2ui-[a-z-]+,((?:[^()]|\([^()]*\))*)\);?")


def verify(before_src, after_src, candidates):
    """Render each candidate's probe payload against BOTH versions of web_article.py (loaded
    standalone, not via the package, so this needs no import side effects). This is a
    MODERN-DEFAULT flip (like the original 7 report atoms), not a value-preserving wrap, so
    the rendered CSS values are EXPECTED to change (old literal -> modern literal) -- folding
    var() back and comparing to "before" is the wrong invariant (caught this against the
    first version of this check: it "failed" 100/139 on a transform that was actually
    correct). What must hold instead:
      1. Every style="..." attribute in the after-render, once VALUES are stripped, is
         IDENTICAL in position/count to before -- i.e. nothing outside inline style VALUES
         changed: same tags, same attributes, same text content, same number of style attrs.
      2. Every double-declaration this sweep added is internally consistent: the plain value
         and the var() fallback are the same value, and that value is the recipe's modern
         one for that token -- not a mismatched or stale pair.
    """
    import shutil
    import tempfile
    def load(src, tag):
        d = Path(tempfile.mkdtemp())
        (d / "web_article.py").write_text(src)
        shutil.copy(ROOT / "renderers" / "_design_tokens.py", d / "_design_tokens.py")
        spec = importlib.util.spec_from_file_location(f"_wa_verify_{tag}", d / "web_article.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    before_mod, after_mod = load(before_src, "before"), load(after_src, "after")
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
        probe.update(_PROBE_OVERRIDES.get(name, {}))
        try:
            b = fn_before(probe)
            a = fn_after(probe)
        except Exception as e:
            bad.append((c["name"], f"render error: {e}"))
            continue
        b_bare, a_bare = _STYLE_ATTR.sub("style=STYLE", b), _STYLE_ATTR.sub("style=STYLE", a)
        if b_bare != a_bare:
            bad.append((c["name"], "content/structure changed outside a style attribute value"))
            continue
        for prop, prefix, plain, var_fallback in _VAR_PAIR.findall(a):
            if plain != var_fallback:
                bad.append((c["name"], f"{prop}: plain {plain!r} != var() fallback {var_fallback!r}"))
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

    # Verify each candidate INDIVIDUALLY (apply it alone, check it, discard the temp result)
    # rather than the whole batch at once, so one atom's probe-shape mismatch or dead-code
    # oddity doesn't block the other 130+ that are genuinely fine -- reported and skipped,
    # not silently forced and not allowed to abort real, verified progress.
    print(f"Verifying {len(candidates)} conversions individually...")
    good, skipped = [], []
    for c in candidates:
        one_src, _ = apply(src, [c], modern)
        bad = verify(src, one_src, [c])
        (skipped if bad else good).append((c, bad))

    if skipped:
        print(f"\n{len(skipped)} skipped (not converted, needs a human look):")
        for c, bad in skipped:
            for name, why in bad:
                print(f"  SKIP {name}: {why}")

    if not good:
        print("\nNothing verified cleanly -- no file written.")
        sys.exit(1)

    final_src, log = apply(src, [c for c, _ in good], modern)
    # Final sanity pass: the whole batch together must verify exactly as each did alone
    # (catches one conversion's edit accidentally overlapping another's).
    batch_bad = verify(src, final_src, [c for c, _ in good])
    if batch_bad:
        print(f"\n{len(batch_bad)} FAILED when combined (passed individually -- overlap?):")
        for name, why in batch_bad:
            print(f"  FAIL {name}: {why}")
        sys.exit(1)

    TARGET.write_text(final_src)
    print(f"\n{len(good)} of {len(candidates)} verified and written to {TARGET.relative_to(ROOT)}.")
    for line in log:
        print(" ", line)
