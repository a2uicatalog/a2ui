#!/usr/bin/env python3
"""Renderer-dimension DRAFT pages, built from public/catalogue/renderer-matrix-v1.json (deterministic,
stdlib only, offline, no wall clock).

Two modes:
  default            writes the committed pages (hub + one page per renderer) to docs/renderer-draft/.
                     These are a pure function of the matrix, so scripts/check_renderer_matrix.py can
                     re-generate them and compare byte for byte.
  --out DIR          write somewhere else (for example the local review folder), together with
  --atom-pages       modified copies of the built public/atoms/<atom>/index.html pages for a few sample
                     atoms, with a Renderers section (reads public/atoms, never changes it), and
  --logos DIR        copies the *.svg renderer logos from DIR into <out>/logos (default: atoms/renderer-logos,
                     committed with their credit and trademark notes in its README), and
  --file-links       links the matrix JSON and README next to the pages.

Status words: Drawn, Drawn with differences, Not verified (web); Native, Degraded (Flutter);
Not supported; Not measured. The "what was measured" text is computed from the data.
"""
import argparse
import html
import json
import os
import shutil

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(WT, "public/catalogue/renderer-matrix-v1.json")
DEFAULT_OUT = os.path.join(WT, "docs/renderer-draft")
SAMPLES = ["stat_card", "key_value", "badge_group", "table", "callout", "bullet_list", "pull_stat", "progress_bar", "sparkline", "shimmer_text"]
E = html.escape
LABEL = {
    "drawn": "Drawn", "drawn_with_differences": "Drawn with differences", "not_verified": "Not verified",
    "native": "Native", "degraded": "Degraded", "not_supported": "Not supported", "not_measured": "Not measured",
}
GLYPH = {"drawn": "✓", "native": "✓", "drawn_with_differences": "≠", "degraded": "~", "not_verified": "?",
         "not_supported": "✕", "not_measured": "–"}
HELP = {
    "drawn": "drawn by the renderer; every check passed",
    "drawn_with_differences": "drawn, but at least one check differs from React (pixels, overflow at 360, contrast or behaviour)",
    "not_verified": "no difference found, but the atom could not be verified (no visible text, blank on both sides, or an unstable check)",
    "native": "drawn by the renderer's own implementation of the atom",
    "degraded": "drawn through Basic components, not the atom's own implementation",
    "not_supported": "draws nothing or errors",
    "not_measured": "no per-atom data (no example, or the example is invalid)",
}
ENV = {"light480": "light 480", "dark480": "dark 480", "light360": "light 360", "dark360": "dark 360"}
ENV_SHORT = {"light480": "L480", "dark480": "D480", "light360": "L360", "dark360": "D360"}
REASON = {
    "no_visible_text": "no visible text in the example",
    "unstable_text": "text changes between runs (time or animation)",
    "overflow_360": "overflows at 360 px",
    "behaviour_differs": "behaviour probe differs from React",
    "painted_fail_error": "painting raised an error",
    "painted_fail_broken": "painted but flagged broken",
    "no_example": "no example payload in the gate data",
    "invalid_example": "example payload invalid, atom untested",
    "lane_painted_own_type": "painted with its own type",
    "lowered_to_basic": "lowered to Basic components",
    "unknown_component_type": "component type unknown to the renderer",
    "nested_type_unknown": "a nested atom type is unknown",
    "renderer_not_measured": "renderer not measured",
    "text_differs": "visible text differs from React",
    "basic_component_rendered": "rendered by a Basic component (the atom's root type)",
    "custom_component_rendered": "rendered by a native custom Compose component registered for this atom",
}
HELP_COMPOSE = {
    "native": "the atom's root type is a Basic component and it rendered through the Basic catalog; Compose has no implementation of our atoms",
    "not_supported": "no implementation of this atom: the type is not in the Basic catalog, so the surface shows an error chip",
    "not_measured": "no per-atom data (no example payload)",
}
PRE = "Measured on a pre-merge build, re-measurement pending."
BUILD_NOTE = {
    "preview-unmerged": PRE,
    "private-build": "Measured on a private, unpublished build of the renderer; it cannot be reproduced from a public commit.",
    "release-package": "",
    "unrecorded": "Build provenance was not recorded for this run.",
    "shipped": "",
}


def reason_text(code):
    if code in REASON:
        return REASON[code]
    for pre, tpl in (("pixel_fail_", "pixels differ from React (%s)"), ("blank_both_", "blank on both sides (%s)"),
                     ("unstable_pixel_", "pixel check unstable (%s)"), ("contrast_worse_", "contrast worse than React (%s)")):
        if code.startswith(pre):
            return tpl % ENV.get(code[len(pre):], code[len(pre):])
    return code


CSS_BLOCK = """
<style>
/* renderer dimension (draft): scoped to .rd, uses the page's own tokens */
.rd{margin:0 0 8px}
.rd-lead{font-size:13px;color:var(--muted);margin:0 0 10px;max-width:70ch}
.rd table{width:100%;border-collapse:collapse;font-size:13px}
.rd th,.rd td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--border)}
.rd th{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.rd-name{display:flex;align-items:center;gap:8px;font-weight:650;white-space:nowrap}
.rd-name a{color:var(--text);text-decoration:none;font-family:inherit;font-size:13.5px}
.rd-name a:hover{text-decoration:underline}
.rd .lg{display:inline-block;width:18px;height:18px;flex:none;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.rd .lg0{display:inline-block;width:18px;height:18px;flex:none}
.rd-chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;border:1px solid var(--c-line);background:var(--c-bg);color:var(--c-ink);white-space:nowrap}
.rd-chip.drawn,.rd-chip.native{--c-bg:color-mix(in srgb,var(--positive) 16%,var(--surface));--c-line:color-mix(in srgb,var(--positive) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--positive) 55%,var(--text))}
.rd-chip.drawn_with_differences,.rd-chip.degraded{--c-bg:color-mix(in srgb,var(--warn) 18%,var(--surface));--c-line:color-mix(in srgb,var(--warn) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--warn) 45%,var(--text))}
.rd-chip.not_verified{--c-bg:var(--surface-2);--c-line:color-mix(in srgb,var(--warn) 45%,var(--surface));--c-ink:color-mix(in srgb,var(--warn) 40%,var(--text))}
.rd-chip.not_supported{--c-bg:color-mix(in srgb,var(--negative) 14%,var(--surface));--c-line:color-mix(in srgb,var(--negative) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--negative) 55%,var(--text))}
.rd-chip.not_measured{--c-bg:var(--surface-2);--c-line:var(--border-strong);--c-ink:var(--text-muted)}
.rd-ev{color:var(--muted);font-size:12.5px;line-height:1.45}
.rd-ck{display:flex;flex-wrap:wrap;gap:3px 6px}
.rd-ck span{font-size:11.5px;padding:0 6px;border-radius:5px;border:1px solid var(--border);white-space:nowrap}
.rd-ck .bad{border-color:color-mix(in srgb,var(--negative) 55%,var(--surface));color:color-mix(in srgb,var(--negative) 55%,var(--text))}
.rd-ck .unk{border-color:color-mix(in srgb,var(--warn) 55%,var(--surface));color:color-mix(in srgb,var(--warn) 45%,var(--text))}
.rd-why{margin:4px 0 0;font-size:12px}
.rd-date{white-space:nowrap;color:var(--muted);font-size:12px}
.rd-pre{font-size:12px;border:1px solid color-mix(in srgb,var(--warn) 50%,var(--surface));background:color-mix(in srgb,var(--warn) 12%,var(--surface));border-radius:8px;padding:6px 10px;margin:10px 0 0;max-width:80ch}
.rd-tm{font-size:11.5px;color:var(--muted);margin:10px 0 28px;max-width:80ch;line-height:1.45}
@media(max-width:600px){
 .rd table,.rd tbody,.rd tr,.rd td{display:block;width:100%;box-sizing:border-box}
 .rd thead{display:none}
 .rd tr{border:1px solid var(--border);border-radius:10px;padding:8px 10px;margin-bottom:8px;background:var(--surface)}
 .rd td{border:0;padding:3px 0}
 .rd-name{white-space:normal}
}
</style>
"""


def chip(status):
    return '<span class="rd-chip %s" title="%s"><span aria-hidden="true">%s</span>%s</span>' % (status, E(HELP[status]), GLYPH[status], LABEL[status])


def logo(reg, prefix):
    if reg.get("logo"):
        return '<span class="lg" style="--m:url(%slogos/%s)" aria-hidden="true"></span>' % (prefix, reg["logo"])
    return '<span class="lg0" aria-hidden="true"></span>'


def mark(v):
    """-> (symbol, css class)"""
    return {"pass": ("✓", ""), "reference": ("ref", ""), "fail": ("✕", "bad"), "unstable": ("~ unstable", "unk"),
            "blank_both": ("blank", "unk"), "no_visible_text": ("no text", "unk"), "n/a": ("–", ""),
            "inherited": ("same as React", ""), "worse": ("worse", "bad"), "not_compared": ("n/c", ""),
            "INERT": ("inert", "unk"), "not_run": ("not run", "unk"), "excluded_random": ("excluded (seeded random)", "unk"), "SAME": ("same", ""), "n/a (no probe)": ("no probe", "")}.get(v, (str(v), "bad"))


def span(label, v):
    sym, cls = mark(v)
    return '<span class="%s">%s %s</span>' % (cls, E(label), E(sym))


def checks_html(kind, e):
    ck = e.get("checks")
    if not ck:
        return ""
    if kind == "web":
        parts = [span("paint", ck["painted"]), span("text", ck["text_visible"])]
        parts.append("<span>pixel %s</span>" % " ".join(
            "%s %s" % (ENV_SHORT[k], E(mark(ck["pixel"][k])[0])) for k in ENV if k in ck["pixel"]))
        parts += [span("overflow 360", ck["overflow_360"]),
                  "<span>contrast %s</span>" % " ".join("%s %s" % (ENV_SHORT[k], E(mark(v)[0])) for k, v in ck["contrast"].items()),
                  span("behaviour", ck["behaviour"])]
        if ck.get("text_parity", "n/a") != "n/a":
            parts.insert(2, span("text vs React", ck["text_parity"]))
        if ck.get("stability") != "stable":
            parts.append('<span class="unk">on the unstable allowance list</span>')
        return '<div class="rd-ck">%s</div>' % "".join(parts)
    parts = ['<span>lane %s</span>' % E(ck["painted"].replace("_", " ")), "<span>own type %s</span>" % ("yes" if ck["own_type_present"] else "no")]
    if kind == "compose":
        bl = ck.get("basic_lane") or {}
        parts = ['<span>Basic catalog lane %s</span>' % E(ck["painted"].replace("_", " "))]
        if bl:
            parts.append("<span>Basic-lane text same as React %s</span>" % ("yes" if bl.get("text_sha_equal") else "no"))
        return '<div class="rd-ck">%s</div>' % "".join(parts)
    p = ck.get("parity_text")
    if p:
        parts.append("<span>web words missing %d of %d</span>" % (p["missing_in_flutter"], p["web_words"]))
    return '<div class="rd-ck">%s</div>' % "".join(parts)


NOTE_TEXT = {"vertical_offset_1px_cause_not_isolated": "content sits 1 px lower than in React (and than 1.85.0), stable between passes; cause not isolated. A real difference, not hidden",
             "seeded_random_order_differs": "seeded-random order differs per renderer: pixel and text parity with React are excluded for this atom, not counted as a failure"}


def why_html(e):
    r = [x for x in e.get("reasons", []) if x not in ("lane_painted_own_type",)]
    notes = "".join('<p class="rd-why">%s</p>' % E(NOTE_TEXT.get(n, n)) for n in e.get("notes", []))
    if not r or e["status"] in ("drawn", "native"):
        return notes
    return '<p class="rd-why">%s</p>' % E("; ".join(reason_text(x) for x in r)) + notes


def build_note(reg):
    m = reg.get("measurement")
    return BUILD_NOTE.get(m["measured_on"], "") if m else ""


def tm_text(m):
    return "%s %s %s" % (m["independence_note"], m["trademark_note"], m["trademark_note_extra"])


def atom_block(m, atom, prefix):
    rows = []
    notes = set()
    for rid, reg in m["renderers"].items():
        v = m["atoms"][atom][rid]
        if v["status"] in ("not_measured",) and not reg["measured"]:
            ev = '<span class="rd-ev">%s</span>' % E("renderer not measured")
        else:
            ev = checks_html(reg["kind"], v) + why_html(v)
            if not ev:
                ev = '<span class="rd-ev">%s</span>' % E("; ".join(reason_text(x) for x in v["reasons"]))
        if reg["measured"] and build_note(reg):
            notes.add(build_note(reg))
        rows.append(
            '<tr><td><span class="rd-name">%s<a href="%srenderers/%s.html">%s</a></span></td><td>%s</td><td class="rd-ev">%s</td><td class="rd-date">%s</td></tr>'
            % (logo(reg, prefix), prefix, rid, E(reg["name"]), chip(v["status"]), ev, E(v["measured"] or "n/a"))
        )
    note = "".join('<p class="rd-pre">%s</p>' % E(n) for n in sorted(notes))
    return (
        '\n  <div class="section rd" id="renderers">\n    <div class="label">Renderers</div>\n'
        '    <p class="rd-lead">What draws this atom, separate from the surfaces above. Draft data from the renderer gates. '
        '<a href="%sindex.html">About this dimension</a></p>\n'
        '    <table><thead><tr><th>Renderer</th><th>Status</th><th>Checks</th><th>Measured</th></tr></thead><tbody>%s</tbody></table>\n'
        '    %s<p class="rd-tm">%s</p>\n  </div>\n' % (prefix, "".join(rows), note, E(tm_text(m)))
    )


def atom_pages(m, src_dir, samples):
    out = {}
    for atom in samples:
        p = os.path.join(src_dir, atom, "index.html")
        if not os.path.exists(p) or atom not in m["atoms"]:
            continue
        s = open(p, encoding="utf8").read()
        i = s.index('<div class="label">Surfaces</div>')
        j = s.index("</div>", i + 40)
        j = s.index("</div>", j + 1) if s[i:j].count("<div") > 1 else j
        end = j + len("</div>")
        s = s[:end] + "\n" + atom_block(m, atom, "../") + s[end:]
        s = s.replace("</head>", CSS_BLOCK + "</head>", 1)
        s = s.replace("<title>", "<title>[DRAFT renderers] ", 1)
        out["atoms/" + atom + ".html"] = s
    return out


PAGE_CSS = """
:root{color-scheme:light;--bg:#f7f9fc;--card:#fff;--sunk:#f1f4f9;--ink:#1a1b25;--mut:#5b6070;--line:#e2e6ef;--line2:#cfd5e2;--acc:#4f46e5;--ok:#1b7f3b;--bad:#b3261e;--warn:#8a6100;--sh:0 1px 2px rgba(20,27,36,.05),0 6px 20px rgba(20,27,36,.06)}
@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#0f1117;--card:#171a23;--sunk:#12151c;--ink:#eceef5;--mut:#9aa1b5;--line:#2a2f3d;--line2:#3a4152;--acc:#8d98ff;--ok:#7fd99a;--bad:#ffb4ab;--warn:#f2d27a;--sh:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.25)}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:20px 16px 56px}
h1{font-size:1.7rem;margin:.2em 0 .3em;line-height:1.2}
h2{font-size:1.1rem;margin:1.8em 0 .5em}
a{color:var(--acc)}
.draft{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line2);border-radius:6px;padding:2px 8px;color:var(--mut)}
.lead{color:var(--mut);max-width:70ch}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh);padding:14px 16px}
.crumb{font-size:13px;margin:0 0 10px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
th{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
td.n{font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
.lg{display:inline-block;width:20px;height:20px;flex:none;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat;vertical-align:middle}
.lg0{display:inline-block;width:20px;height:20px;flex:none;vertical-align:middle}
.nm{display:flex;gap:8px;align-items:center;font-weight:650;white-space:nowrap}
.rd-chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;border:1px solid var(--c-line);background:var(--c-bg);color:var(--c-ink);white-space:nowrap}
.rd-chip.drawn,.rd-chip.native{--c-bg:color-mix(in srgb,var(--ok) 15%,var(--card));--c-line:color-mix(in srgb,var(--ok) 50%,var(--card));--c-ink:var(--ok)}
.rd-chip.drawn_with_differences,.rd-chip.degraded{--c-bg:color-mix(in srgb,var(--warn) 16%,var(--card));--c-line:color-mix(in srgb,var(--warn) 50%,var(--card));--c-ink:var(--warn)}
.rd-chip.not_verified{--c-bg:var(--sunk);--c-line:color-mix(in srgb,var(--warn) 45%,var(--card));--c-ink:var(--warn)}
.rd-chip.not_supported{--c-bg:color-mix(in srgb,var(--bad) 13%,var(--card));--c-line:color-mix(in srgb,var(--bad) 50%,var(--card));--c-ink:var(--bad)}
.rd-chip.not_measured{--c-bg:var(--sunk);--c-line:var(--line2);--c-ink:var(--mut)}
.bar{display:flex;height:14px;border-radius:7px;overflow:hidden;border:1px solid var(--line2);margin:8px 0}
.bar span{display:block;height:100%}
.bar .drawn,.bar .native{background:var(--ok)}.bar .drawn_with_differences,.bar .degraded{background:var(--warn)}.bar .not_verified{background:repeating-linear-gradient(45deg,var(--warn),var(--warn) 3px,var(--sunk) 3px,var(--sunk) 6px)}.bar .not_supported{background:var(--bad)}.bar .not_measured{background:var(--line2)}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:0;font-size:14px}
dl.facts dt{color:var(--mut)}dl.facts dd{margin:0}
details{border:1px solid var(--line);border-radius:10px;background:var(--card);margin:8px 0;padding:6px 12px}
summary{cursor:pointer;font-weight:650;padding:4px 0}
ul.atoms{columns:3 180px;column-gap:18px;list-style:none;padding:0;margin:8px 0;font-size:13px;font-family:ui-monospace,Menlo,monospace}
ul.atoms li{break-inside:avoid;padding:1px 0}
ul.why{list-style:none;padding:0;margin:8px 0;font-size:13px}
ul.why li{padding:3px 0;border-bottom:1px solid var(--line)}
ul.why code{font-weight:650}
.note{font-size:13px;color:var(--mut);max-width:75ch}
.pre{font-size:13px;border:1px solid var(--warn);border-radius:8px;padding:8px 12px;margin:12px 0;max-width:80ch}
.tm{font-size:12px;color:var(--mut);margin-top:28px;max-width:80ch}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){
 .two{grid-template-columns:1fr}
 dl.facts{grid-template-columns:1fr;gap:0}dl.facts dt{margin-top:8px}
 ul.atoms{columns:2 140px}
}
"""


def page(title, body):
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%s</title><style>%s</style></head><body><main>%s</main></body></html>\n" % (E(title), PAGE_CSS, body)
    )


def counts_bar(cov, statuses):
    t = cov["total"]
    return '<div class="bar" role="img" aria-label="%s">%s</div>' % (
        E(", ".join("%s %d" % (LABEL[s], cov[s]) for s in statuses)),
        "".join('<span class="%s" style="width:%.3f%%"></span>' % (s, 100.0 * cov[s] / t) for s in statuses if cov[s]),
    )


def tm_block(m):
    return '<p class="tm">%s</p>' % E(tm_text(m))


def atom_link(a, samples):
    return '<a href="../atoms/%s.html">%s</a>' % (a, a) if a in samples else a


def reason_counts(m, rid):
    c = {}
    for atom in m["atoms"]:
        for r in m["atoms"][atom][rid]["reasons"]:
            c[r] = c.get(r, 0) + 1
    return c


def measured_text(m, rid):
    """Honest M-level text computed from the data (never a free-text 'M4 complete')."""
    reg = m["renderers"][rid]
    cov = reg["coverage"]
    T = cov["total"]
    if not reg["measured"]:
        return "Not measured; skipped by the completeness check."
    n_case = T - cov.get("not_measured", 0)
    if reg["kind"] == "web":
        probes = sum(1 for a in m["atoms"] if (m["atoms"][a][rid].get("checks") or {}).get("behaviour") not in (None, "n/a (no probe)", "not_run"))
        no_beh = n_case > 0 and all((m["atoms"][a][rid].get("checks") or {}).get("behaviour") == "not_run" for a in m["atoms"] if m["atoms"][a][rid].get("checks"))
        ref = reg["measurement"].get("reference_renderer")
        txt = "%d of %d atoms have a gate example. Checks recorded per atom: painting, visible text, blank on both sides, pixel parity %s in the lanes the gate has, overflow at 360 px, contrast, and behaviour %s." % (
            n_case, T, "with " + ref.capitalize() if ref else "(React is the reference: parity is recorded against its own frozen shots)", "(the behaviour lane was not run for this measurement)" if no_beh else "for the %d atoms that have an interaction probe" % probes)
    elif reg["kind"] == "compose":
        txt = ("%d of %d atoms have a gate example, tried through the Basic catalog only (Compose has no implementation of our atoms). "
               "Also measured: the Basic lane (670 Basic cases) and 48 Basic behaviour probes against React; pixel parity is recorded but not meaningful across Compose Desktop and Chromium.") % (n_case, T)
    else:
        par = sum(1 for a in m["atoms"] if ((m["atoms"][a][rid].get("checks") or {}).get("parity_text")))
        txt = "%d of %d atoms have a lane example, drawn in the headless Flutter widget-test engine. Text parity with the web painter was checked on %d atoms; no pixel parity, no Basic-lane measurement by us and no device run." % (n_case, T, par)
    return txt + " Weekly gate (M5) not claimed."


def renderer_parts(m, rid, link):
    """Shared by the draft pages and the real site pages (scripts/renderer_site.py): the sections of a
    renderer page as HTML strings. `link(atom)` renders an atom name (a link or plain text)."""
    reg = m["renderers"][rid]
    cov = reg["coverage"]
    atoms = m["atoms"]
    statuses = reg["statuses"]
    byst = {s: [a for a in sorted(atoms) if atoms[a][rid]["status"] == s] for s in statuses}
    ms = reg.get("measurement") or {}
    facts = [("Package", reg["package"]), ("Version measured", ms.get("renderer_version") or "n/a"), ("Protocol dialect", reg["protocol"]),
             ("Platform", reg["platform"]), ("Measured", ms.get("measured") or "n/a"),
             ("Run", ms.get("run_id") or "n/a"), ("What was measured", measured_text(m, rid))]
    if reg.get("environment"):
        facts.insert(4, ("Environment", reg["environment"]))
    if ms.get("commit"):
        facts.append(("Measured on commit", ms["commit"][:9]))
    if ms.get("core_sha256"):
        facts.append(("Core build (sha256, first 12)", ms["core_sha256"][:12]))
    if ms.get("renderer_bundle_sha256"):
        facts.append(("Shipped renderer bundle (sha256, first 12)", ms["renderer_bundle_sha256"][:12]))
    src = sorted({v for a in atoms for v in ((atoms[a][rid].get("checks") or {}).get("sources") or {}).values() if v not in ("n/a",)}) if reg["kind"] == "web" else []
    if src:
        facts.append(("Evidence sources", "per-check provenance in the data: " + ", ".join(
            {"det-ab": "det-ab (deterministic two-pass gate: pixel parity vs React, overflow, contrast, text parity, stability)",
             "f111": "f111 (gate run on the shipped commit: painting, visible text, behaviour)",
             "ck187": "ck187 (one non-deterministic CopilotKit 1.87.0 run: painting and visible text; the behaviour lane was not run)"}.get(x, x) for x in src)))
    if reg.get("earlier_measurement"):
        facts.append(("Earlier measurement", reg["earlier_measurement"]))
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % (E(k), E(v)) for k, v in facts)
    hp = HELP_COMPOSE if reg["kind"] == "compose" else HELP
    chips = "".join('<tr><td>%s</td><td class="n">%d</td><td class="note">%s</td></tr>' % (chip(s), cov[s], E(hp[s])) for s in statuses)
    pre = build_note(reg)
    pre_html = '<div class="pre">%s</div>' % E(pre) if pre else ""
    items = ["<li>%s</li>" % E(reg["note"])]
    if reg["kind"] == "web":
        rc = reason_counts(m, rid)
        pxf = ", ".join("%s %d" % (ENV[e], rc.get("pixel_fail_" + e, 0)) for e in ENV)
        items += [
            "<li>Status is derived from per-check results with rules version %d: any difference from React wins over a verification gap; the worst case wins for atoms with several cases.</li>" % m["rules_version"],
            "<li>Atoms with a pixel difference from React, by environment: %s. Overflow at 360 px: %d. Contrast worse than React: %d. Behaviour differs: %d.</li>" % (
                pxf, rc.get("overflow_360", 0), sum(v for k, v in rc.items() if k.startswith("contrast_worse_")), rc.get("behaviour_differs", 0)),
            "<li>%d atoms are not verified because the example paints no visible text, %d because they are blank on both sides in at least one environment and %d because a check is unstable (time or animation dependent; non-deterministic measurements only: they sit on the allowance list and record unstable, never pass).</li>" % (
                rc.get("no_visible_text", 0), len({a for a in atoms if any(r.startswith("blank_both_") for r in atoms[a][rid]["reasons"])}),
                len({a for a in atoms if any(r.startswith("unstable_") for r in atoms[a][rid]["reasons"])})),
            "<li>%d atoms have no example in the gate data and are not measured.</li>" % cov.get("not_measured", 0),
        ]
        n4 = len([a for a in atoms if all("pixel_fail_" + e in atoms[a][rid]["reasons"] for e in ENV)])
        if n4:
            items.append("<li>%d atoms fail the pixel rule in all four environments (light and dark, 480 and 360 px).</li>" % n4)
    elif reg["kind"] == "flutter":
        chk = [a for a in atoms if (atoms[a][rid].get("checks") or {}).get("parity_text")]
        mism = [a for a in chk if atoms[a][rid]["checks"]["parity_text"]["missing_in_flutter"] > 0]
        inval = sum(1 for a in atoms if "invalid_example" in atoms[a][rid]["reasons"])
        items += [
            "<li>Partial coverage: %d of %d atoms draw natively; %d draw only through Basic components; %d draw nothing; %d are not measured (%d with an invalid example, the rest without an example).</li>" % (
                cov["native"], cov["total"], cov["degraded"], cov["not_supported"], cov["not_measured"], inval),
            "<li>Text parity with the web painter was checked on %d atoms; %d of those miss at least one web word in Flutter. The check compares visible words, not layout or pixels. For atoms with several cases the worst case counts.</li>" % (len(chk), len(mism)),
            "<li>No device run: everything ran in the headless widget-test engine. An independent 12 Nov audit of 40 ported atoms found visible drift in about 16, so Native here means the port draws the lane example, not that it matches the web look.</li>",
        ]
    elif reg["kind"] == "compose":
        f = ms.get("facts") or {}
        bl, bb = f.get("basic_lane"), f.get("basic_behaviour")
        items += [
            "<li>Compose has no custom-atom implementations. %d of the %d stable atoms with an example are not supported; %d draw natively only because their root is a Basic component. Say it plainly: this renderer is not a target for our atoms today.</li>" % (
                cov["not_supported"], cov["total"] - cov["not_measured"], cov["native"]),
        ]
        if bl:
            items.append("<li>Basic lane (the Basic catalog on its own): %d of %d cases render without error or crash; visible text is identical to React on %d of %d (%d of %d among the stable atoms).</li>" % (
                bl["rendered"], bl["cases"], bl["text_identical_to_react"], bl["cases"], bl["stable_text_identical"], bl["stable_atoms"]))
        if bb:
            items.append("<li>Behaviour, %d Basic probes against React: same %d, different %d, same rejection %d, error %d, not runnable %d. Custom-atom behaviour probes were not run (the atoms are not registered).</li>" % (
                bb["probes"], bb["same"], bb["different"], bb["same_reject"], bb["error"], bb["not_runnable"]))
        items.append("<li>Not run: dark mode, 360 px, an Android device or emulator, spec v1.0.</li>")
    dt = (ms.get("facts") or {}).get("determinism")
    if dt:
        items.append("<li>Deterministic mode: every shot was taken twice on the shipped build (frozen Date, virtual clock, seeded random, fixed raster settings). %d of %d renderer-and-environment cells are byte-identical; the other %d differ in one atom by at most %d pixels of dither (channel-sum delta at most %d of 765) and pass the pixel rule. So pixel results are plain pass or fail with no allowance list. The custom-text check is also deterministic (two identical passes). This holds only for a fixed id order and %d-case chunking (chunk 1 against chunk 12 differs for %d of %d test atoms), on the slicer image that took the baselines; the old local custom runner is not deterministic. Painting and visible text (and behaviour where it was run) still come from one earlier, non-deterministic run.</li>" % (
            dt["byte_identical_cells"], dt["cells"], dt["cells"] - dt["byte_identical_cells"], dt["dither_max_pixels"], dt["dither_max_delta_of_765"], dt["chunk_size"], dt["chunk_1_vs_12_differs_atoms"], dt["chunk_test_atoms"]))
        nr = [a for a in atoms if "seeded_random_order_differs" in atoms[a][rid].get("notes", [])]
        if nr:
            items.append("<li>%s: %s are drawn with a note: their random draws are consumed per renderer, so parity with React is excluded for them. Open item: reseed per case in the slicer.</li>" % (
                "Seeded-random atoms", ", ".join(sorted(nr))))
    for n in reg.get("notes_extra", []):
        items.append("<li>%s</li>" % E(n))
    extra = '<h2>Honest notes</h2><div class="card"><ul>%s</ul></div>' % "".join(items)
    lists = ""
    for s in statuses:
        if not byst[s]:
            continue
        if s in ("drawn", "native", "not_measured") or len(byst[s]) > 80:
            li = []
            for a in byst[s]:
                suffix = ""
                p = (atoms[a][rid].get("checks") or {}).get("parity_text") if s == "native" and reg["kind"] == "flutter" else None
                if p and p["missing_in_flutter"]:
                    suffix = ' <span class="note">(%d of %d web words missing)</span>' % (p["missing_in_flutter"], p["web_words"])
                li.append("<li>%s%s</li>" % (link(a), suffix))
            body = '<ul class="atoms">%s</ul>' % "".join(li)
        else:
            body = '<ul class="why">%s</ul>' % "".join(
                "<li><code>%s</code> <span class=\"note\">%s</span></li>" % (link(a), E("; ".join(reason_text(r) for r in atoms[a][rid]["reasons"])))
                for a in byst[s])
        open_attr = " open" if len(byst[s]) <= 12 else ""
        lists += '<details%s><summary>%s: %d atoms</summary>%s</details>' % (open_attr, chip(s), len(byst[s]), body)
    return {"reg": reg, "pre_html": pre_html, "dl": dl, "total": cov["total"], "bar": counts_bar(cov, statuses),
            "chips": chips, "extra": extra, "lists": lists}


def renderer_page(m, rid, samples):
    p = renderer_parts(m, rid, lambda a: atom_link(a, samples))
    reg = p["reg"]
    body = (
        '<p class="crumb"><a href="../index.html">Renderer dimension (draft)</a> / %s</p><span class="draft">Draft, local only</span>'
        '<h1><span class="nm">%s%s</span></h1><p class="lead">%s</p>%s'
        '<div class="card"><dl class="facts">%s</dl></div>'
        "<h2>Coverage of the %d stable atoms</h2>%s"
        '<div class="scroll"><table><thead><tr><th>Status</th><th>Atoms</th><th>Meaning</th></tr></thead><tbody>%s</tbody></table></div>'
        "%s<h2>Atoms by status</h2>%s%s"
    ) % (E(reg["name"]), logo(reg, "../"), E(reg["name"]), E(reg["note"]), p["pre_html"], p["dl"], p["total"], p["bar"], p["chips"], p["extra"], p["lists"], tm_block(m))
    return page("[DRAFT] %s renderer support" % reg["name"], body)


def hub(m, samples, file_links):
    rows = []
    pre = {}
    for rid, reg in m["renderers"].items():
        cov = reg["coverage"]
        ms = reg.get("measurement") or {}
        web = reg["kind"] == "web"
        if build_note(reg):
            pre.setdefault(build_note(reg), []).append(reg["name"])
        sub = E(ms.get("renderer_version") or "not measured")
        top = cov.get("drawn" if web else "native", 0)
        mid = cov.get("drawn_with_differences" if web else "degraded", 0)
        rows.append(
            '<tr><td><span class="nm">%s<a href="renderers/%s.html">%s</a></span></td><td>%s<br><span class="note">%s</span></td><td>%s</td>'
            '<td class="n">%d</td><td class="n">%d</td><td class="n">%s</td><td class="n">%d</td><td class="n">%d</td></tr>'
            % (logo(reg, ""), rid, E(reg["name"]), E(reg["package"]), sub, E(reg["protocol"]), top, mid,
               "%d" % cov["not_verified"] if web and reg["measured"] else "–", cov.get("not_supported", 0), cov["not_measured"])
        )
    sm = " ".join('<a href="atoms/%s.html">%s</a>' % (a, a) for a in samples)
    samples_html = "<h2>Sample atom pages</h2><p>%s</p>" % sm if samples else ""
    files = '<h2>Files</h2><p class="note"><a href="README.md">README.md</a>, <a href="data/renderer-matrix-v1.json">renderer-matrix-v1.json</a>.</p>' if file_links else ""
    body = (
        '<span class="draft">Draft, local only, not published</span><h1>Which renderer draws which atom</h1>'
        '<p class="lead">A new, separate dimension of the catalogue. Every atom already says where it appears; this adds what draws it, measured per renderer. %d stable atoms, %d renderers, %d of them measured.</p>%s'
        "<h2>Two dimensions, in plain words</h2>"
        '<div class="two"><div class="card"><strong>Surface: where it appears</strong><p class="note">The place a person sees the atom: web page, MCP app, Android, PDF, Google Meet stage, and so on. This is the existing <code>x-surfaces</code> field. It does not change.</p></div>'
        '<div class="card"><strong>Renderer: what draws it</strong><p class="note">The piece of software that turns the atom into pixels: React, Lit, Angular, CopilotKit, a2ui-vue, Flutter or Compose. This is the new <code>x-renderers</code> field. One surface (the web) is drawn by several renderers, and one renderer can serve several surfaces.</p></div></div>'
        "<h2>Registry</h2>"
        '<div class="scroll"><table><thead><tr><th>Renderer</th><th>Package, version</th><th>Protocol</th><th>Drawn / Native</th><th>With differences / Degraded</th><th>Not verified</th><th>Not supported</th><th>Not measured</th></tr></thead><tbody>%s</tbody></table></div>'
        '<p class="note">Web renderers: Drawn (every check passed), Drawn with differences (a check differs from React), Not verified (no difference found, but the atom could not be verified). Flutter: Native (own implementation), Degraded (drawn through Basic components). Compose: Native only where the atom&rsquo;s root is a Basic component; it has no implementation of our atoms. Not supported: draws nothing or errors. Not measured: no per-atom data. CopilotKit and a2ui-vue draw our atoms inside their own wrapper and theme. Each renderer page says what was measured, computed from the data.</p>'
        "%s%s%s"
    ) % (m["atom_count"], len(m["renderers"]), sum(1 for r in m["renderers"].values() if r["measured"]), "".join('<div class="pre">%s: %s</div>' % (E(", ".join(v)), E(n)) for n, v in sorted(pre.items())), "".join(rows), samples_html, files, tm_block(m))
    return page("[DRAFT] Renderer dimension", body)


def render_pages(m, registry=None, samples=(), file_links=False):
    """Pure: the committed pages as {path relative to the output dir: text}."""
    out = {"index.html": hub(m, list(samples), file_links)}
    for rid in m["renderers"]:
        out["renderers/%s.html" % rid] = renderer_page(m, rid, list(samples))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--atom-pages", action="store_true", help="also write modified copies of the built public/atoms pages for the samples")
    ap.add_argument("--logos", default=os.path.join(WT, "atoms/renderer-logos"), help="directory with the renderer *.svg logos to copy into <out>/logos")
    ap.add_argument("--file-links", action="store_true", help="link README.md and a copy of the matrix JSON next to the pages")
    a = ap.parse_args()
    with open(MATRIX, encoding="utf8") as f:
        m = json.load(f)
    src = os.path.join(WT, "public/atoms")
    pages = {}
    samples = []
    if a.atom_pages:
        pages = atom_pages(m, src, SAMPLES)
        samples = [k.split("/")[1][:-5] for k in sorted(pages)]
    pages.update(render_pages(m, None, samples, a.file_links))
    for rel, text in pages.items():
        p = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf8") as f:
            f.write(text)
    if a.logos:
        os.makedirs(os.path.join(a.out, "logos"), exist_ok=True)
        for fn in sorted(os.listdir(a.logos)):
            if fn.endswith(".svg"):
                shutil.copyfile(os.path.join(a.logos, fn), os.path.join(a.out, "logos", fn))
    if a.file_links:
        os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
        shutil.copyfile(MATRIX, os.path.join(a.out, "data/renderer-matrix-v1.json"))
    print("pages:", sorted(pages))


if __name__ == "__main__":
    main()
