#!/usr/bin/env python3
"""Renderer dimension: the site fragments (library, no side effects; imported by generate_atom_pages.py and
by check_renderer_matrix.py).

The data is public/catalogue/renderer-matrix-v1.json (scripts/gen_renderer_matrix.py, committed). This module
turns it into HTML/Markdown strings and nothing else; no clock, no path, no network. The page chrome (header,
footer, base CSS) stays in generate_atom_pages.py, which writes:

  public/atoms/<atom>/index.html   gets atom_block(m, atom) inside its "Surfaces" column (+ ATOM_CSS in <head>)
  public/renderers/index.html      hub_body(m)            (+ public/renderers.md   from hub_md(m))
  public/renderers/<id>/index.html renderer_body(m, id)   (+ public/renderers/<id>.md from renderer_md(m, id))
  public/renderers/logos/*.svg     copied from atoms/renderer-logos/

The row, chip and note logic is shared with the approved draft pages (gen_renderer_draft_pages.py).
"""
import html
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MATRIX_PATH = os.path.join(ROOT, "public", "catalogue", "renderer-matrix-v1.json")
LOGO_SRC = os.path.join(ROOT, "atoms", "renderer-logos")
LOGO_SRC_DIR = __import__("pathlib").Path(LOGO_SRC)
BASE = "https://a2uicatalog.ai"
E = html.escape


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dp = _load("gen_renderer_draft_pages")


def load_matrix():
    """The committed matrix, or None when it is absent (a checkout without the renderer dimension)."""
    if not os.path.isfile(MATRIX_PATH):
        return None
    with open(MATRIX_PATH, encoding="utf8") as f:
        return json.load(f)


# ------------------------------------------------------------------ CSS (site tokens only, light and dark through them)

# Atom pages: the draft's block CSS (scoped to .rd), without the <style> wrapper (the page puts it in <head>).
ATOM_CSS = dp.CSS_BLOCK.strip().removeprefix("<style>").removesuffix("</style>").replace(
    "/* renderer dimension (draft): scoped to .rd, uses the page's own tokens */", "/* renderer dimension: scoped to .rd, uses the page's own tokens */").strip("\n")

# Hub and renderer pages: scoped to .rdp. Reuses the .rd-chip rules of ATOM_CSS.
PAGE_CSS = """/* renderer dimension pages: scoped to .rdp */
.rdp a{color:var(--accent-2-text)}
.rdp .nm a{color:var(--text)}
.rdp .lead{color:var(--muted);max-width:70ch;font-size:1.05rem;line-height:1.65;margin:0 0 24px}
.rdp h2{font-size:1.15rem;margin:2em 0 .6em}
.rdp table{margin:8px 0 12px}
.rdp td:first-child{font-family:inherit;font-weight:inherit;color:inherit}
.rdp td{color:var(--text)}
.rdp .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px 16px}
.rdp .scroll{overflow-x:auto}
.rdp .nm{display:flex;gap:8px;align-items:center;font-weight:650;white-space:nowrap}
.rdp .nm a{color:var(--text);text-decoration:none}
.rdp .nm a:hover{text-decoration:underline}
.rdp h1 .nm{font-size:inherit;gap:12px}
.rdp .lg{display:inline-block;width:20px;height:20px;flex:none;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat;vertical-align:middle}
.rdp h1 .lg,.rdp h1 .lg0{width:32px;height:32px}
.rdp .lg0{display:inline-block;width:20px;height:20px;flex:none}
.rdp td.n{font-variant-numeric:tabular-nums}
.rdp .bar{display:flex;height:14px;border-radius:7px;overflow:hidden;border:1px solid var(--border-strong);margin:8px 0}
.rdp .bar span{display:block;height:100%}
.rdp .bar .drawn,.rdp .bar .native{background:var(--positive)}
.rdp .bar .drawn_with_differences,.rdp .bar .degraded{background:var(--warn)}
.rdp .bar .not_verified{background:repeating-linear-gradient(45deg,var(--warn),var(--warn) 3px,var(--surface-2) 3px,var(--surface-2) 6px)}
.rdp .bar .not_supported{background:var(--negative)}
.rdp .bar .not_measured{background:var(--border-strong)}
.rdp dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:0;font-size:14px}
.rdp dl.facts dt{color:var(--muted)}
.rdp dl.facts dd{margin:0;overflow-wrap:anywhere}
.rdp details{border:1px solid var(--border);border-radius:10px;background:var(--surface);margin:8px 0;padding:6px 12px}
.rdp summary{cursor:pointer;font-weight:650;padding:4px 0}
.rdp ul.atoms{columns:3 180px;column-gap:18px;list-style:none;padding:0;margin:8px 0;font-size:13px;font-family:ui-monospace,'SF Mono',Monaco,monospace}
.rdp ul.atoms li{break-inside:avoid;padding:1px 0}
.rdp ul.atoms a,.rdp ul.why a{color:var(--accent-2-text)}
.rdp ul.why{list-style:none;padding:0;margin:8px 0;font-size:13px}
.rdp ul.why li{padding:3px 0;border-bottom:1px solid var(--border)}
.rdp ul.why code{font-weight:650}
.rdp .note{font-size:13px;color:var(--muted);max-width:75ch}
.rdp .pre{font-size:13px;border:1px solid color-mix(in srgb,var(--warn) 50%,var(--surface));background:color-mix(in srgb,var(--warn) 12%,var(--surface));border-radius:8px;padding:8px 12px;margin:12px 0;max-width:80ch}
.rdp .tm{font-size:12px;color:var(--muted);margin-top:28px;max-width:80ch}
.rdp .two{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 16px}
.rdp .card ul{margin:0;padding-left:20px}
.rdp .card li{margin:6px 0;font-size:14px;color:var(--text-2)}
.rdp pre{margin:8px 0 12px;font-size:12.5px}
@media(max-width:640px){
 .rdp .two{grid-template-columns:1fr}
 .rdp dl.facts{grid-template-columns:1fr;gap:0}
 .rdp dl.facts dt{margin-top:8px}
 .rdp ul.atoms{columns:2 140px}
 .rdp h1 .nm{white-space:normal}
}"""


def head_css(extra_atom=False):
    """The <style> block for the hub/renderer pages (ATOM_CSS carries the shared .rd-chip rules)."""
    return "<style>\n" + ATOM_CSS + "\n" + PAGE_CSS + "\n</style>"


# ------------------------------------------------------------------ the Renderers block of an atom page

def _row_link(rid):
    return "/renderers/%s/" % rid


def atom_block(m, atom):
    """The `Renderers` section of one atom page, or "" when the matrix does not cover the atom."""
    if not m or atom not in m["atoms"]:
        return ""
    rows = []
    notes = {}
    for rid, reg in m["renderers"].items():
        v = m["atoms"][atom][rid]
        if v["status"] in ("not_measured",) and not reg["measured"]:
            ev = '<span class="rd-ev">%s</span>' % E("renderer not measured")
        else:
            ev = dp.checks_html(reg["kind"], v) + dp.why_html(v)
            if not ev:
                ev = '<span class="rd-ev">%s</span>' % E("; ".join(dp.reason_text(x) for x in v["reasons"]))
        if reg["measured"] and dp.build_note(reg):
            notes.setdefault(dp.build_note(reg), []).append(reg["name"])
        rows.append(
            '<tr><td><span class="rd-name">%s<a href="%s">%s</a></span></td><td>%s</td><td class="rd-ev">%s</td><td class="rd-date">%s</td></tr>'
            % (dp.logo(reg, "/renderers/"), _row_link(rid), E(reg["name"]), dp.chip(v["status"]), ev, E(v["measured"] or "n/a"))
        )
    note = "".join('<p class="rd-pre">%s: %s</p>' % (E(", ".join(v)), E(n)) for n, v in sorted(notes.items()))
    return (
        '\n      <div class="section rd" id="renderers">\n        <div class="label">Renderers</div>\n'
        '        <p class="rd-lead">What draws this atom, separate from the surfaces above: measured per renderer, '
        'each check against React. <a href="/renderers/">About this dimension</a></p>\n'
        '        <table><thead><tr><th>Renderer</th><th>Status</th><th>Checks</th><th>Measured</th></tr></thead><tbody>%s</tbody></table>\n'
        '        %s<p class="rd-tm">%s</p>\n      </div>\n' % ("".join(rows), note, E(dp.tm_text(m)))
    )


# ------------------------------------------------------------------ hub and renderer pages (bodies; the shell is in generate_atom_pages.py)

def atom_link(a):
    return '<a href="/atoms/%s/">%s</a>' % (a, a)


def hub_body(m):
    rows = []
    pre = {}
    for rid, reg in m["renderers"].items():
        cov = reg["coverage"]
        ms = reg.get("measurement") or {}
        web = reg["kind"] == "web"
        if dp.build_note(reg):
            pre.setdefault(dp.build_note(reg), []).append(reg["name"])
        sub = E(ms.get("renderer_version") or "not measured")
        top = cov.get("drawn" if web else "native", 0)
        mid = cov.get("drawn_with_differences" if web else "degraded", 0)
        rows.append(
            '<tr><td><span class="nm">%s<a href="%s">%s</a></span></td><td>%s<br><span class="note">%s</span></td><td>%s</td>'
            '<td class="n">%d</td><td class="n">%d</td><td class="n">%s</td><td class="n">%d</td><td class="n">%d</td></tr>'
            % (dp.logo(reg, "/renderers/"), _row_link(rid), E(reg["name"]), E(reg["package"]), sub, E(reg["protocol"]), top, mid,
               "%d" % cov["not_verified"] if web and reg["measured"] else "–", cov.get("not_supported", 0), cov["not_measured"])
        )
    example = {"x-surfaces": ["web", "mcp-apps"], "x-renderers": {"react": "drawn", "lit": "drawn", "copilotkit": "drawn_with_differences",
                                                                  "flutter": "native", "compose": "not_supported", "...": "one key per renderer"}}
    banners = "".join('<div class="pre">%s: %s</div>' % (E(", ".join(v)), E(n)) for n, v in sorted(pre.items()))
    return (
        '<div class="rdp"><h1>Which renderer draws which atom</h1>'
        '<p class="lead">Every atom already says where it appears; this adds what draws it, measured per renderer. %d public atoms, %d renderers, %d of them measured.</p>%s'
        "<h2>Two dimensions, in plain words</h2>"
        '<div class="two"><div class="card"><strong>Surface: where it appears</strong><p class="note">The place a person sees the atom: web page, MCP app, Android, PDF, Google Meet stage, and so on. This is the <code>x-surfaces</code> field of each atom.</p></div>'
        '<div class="card"><strong>Renderer: what draws it</strong><p class="note">The piece of software that turns the atom into pixels: React, Lit, Angular, CopilotKit, a2ui-vue, Flutter or Compose. This is the <code>x-renderers</code> field. One surface (the web) is drawn by several renderers, and one renderer can serve several surfaces.</p></div></div>'
        "<h2>Renderers</h2>"
        '<div class="scroll"><table><thead><tr><th>Renderer</th><th>Package, version</th><th>Protocol</th><th>Drawn / Native</th><th>With differences / Degraded</th><th>Not verified</th><th>Not supported</th><th>Not measured</th></tr></thead><tbody>%s</tbody></table></div>'
        '<p class="note">Web renderers: Drawn (every check passed), Drawn with differences (a check differs from React), Not verified (no difference found, but the atom could not be verified). Flutter: Native (own implementation), Degraded (drawn through Basic components). Compose: Native only where the atom&rsquo;s root is a Basic component; it has no implementation of our atoms. Not supported: draws nothing or errors. Not measured: no per-atom data. CopilotKit and a2ui-vue draw our atoms inside their own wrapper and theme. Each renderer page says what was measured, computed from the data.</p>'
        "<h2>For agents and tools</h2>"
        '<p class="note">Each component in <a href="/catalogue/a2ui-atoms-v1.json">/catalogue/a2ui-atoms-v1.json</a> and each atom in <a href="/spec.json">/spec.json</a> carries a compact <code>x-renderers</code> map next to <code>x-surfaces</code>: renderer id to status string, one key per renderer. Per-check evidence, dates and notes are only in <a href="/catalogue/renderer-matrix-v1.json">/catalogue/renderer-matrix-v1.json</a>.</p>'
        '<pre tabindex="0"><code>%s</code></pre>'
        '<p class="tm">%s</p></div>'
    ) % (m["atom_count"], len(m["renderers"]), sum(1 for r in m["renderers"].values() if r["measured"]), banners, "".join(rows),
         E(json.dumps(example, indent=2)), E(dp.tm_text(m)))


def renderer_body(m, rid):
    p = dp.renderer_parts(m, rid, atom_link)
    reg = p["reg"]
    return (
        '<div class="rdp"><h1><span class="nm">%s%s</span></h1><p class="lead">%s</p>%s'
        '<div class="card"><dl class="facts">%s</dl></div>'
        "<h2>Coverage of the %d public atoms</h2>%s"
        '<div class="scroll"><table><thead><tr><th>Status</th><th>Atoms</th><th>Meaning</th></tr></thead><tbody>%s</tbody></table></div>'
        "%s<h2>Atoms by status</h2>%s"
        '<p class="tm">%s</p></div>'
    ) % (dp.logo(reg, "/renderers/"), E(reg["name"]), E(reg["note"]), p["pre_html"], p["dl"], p["total"], p["bar"], p["chips"],
         p["extra"], p["lists"], E(dp.tm_text(m)))


def renderer_title(m, rid):
    return "%s renderer support: which A2UI atoms it draws" % m["renderers"][rid]["name"]


def renderer_desc(m, rid):
    reg = m["renderers"][rid]
    cov = reg["coverage"]
    top = cov.get("drawn" if reg["kind"] == "web" else "native", 0)
    return "%s (%s) against the %d public A2UI atoms: %d %s, %d not measured. Measured per check, no hand-written status." % (
        reg["name"], reg["package"], cov["total"], top, "drawn" if reg["kind"] == "web" else "drawn natively", cov["not_measured"])


# ------------------------------------------------------------------ Markdown twins

def hub_md(m):
    lines = ["# Which renderer draws which atom", "",
             "Every atom says where it appears (`x-surfaces`); `x-renderers` says what draws it, measured per renderer. "
             "%d public atoms, %d renderers, %d of them measured." % (
                 m["atom_count"], len(m["renderers"]), sum(1 for r in m["renderers"].values() if r["measured"])), "",
             "| Renderer | Package | Version measured | Statuses |", "|---|---|---|---|"]
    for rid, reg in m["renderers"].items():
        cov = reg["coverage"]
        ms = reg.get("measurement") or {}
        st = ", ".join("%s %d" % (dp.LABEL[s], cov[s]) for s in reg["statuses"] if cov.get(s))
        lines.append("| [%s](%s/renderers/%s/) | %s | %s | %s |" % (reg["name"], BASE, rid, reg["package"], ms.get("renderer_version") or "not measured", st))
    lines += ["", "Data: %s/catalogue/renderer-matrix-v1.json; per atom in `x-renderers` of %s/catalogue/a2ui-atoms-v1.json and %s/spec.json." % (BASE, BASE, BASE), "",
              dp.tm_text(m), ""]
    return "\n".join(lines)


def renderer_md(m, rid):
    reg = m["renderers"][rid]
    cov = reg["coverage"]
    atoms = m["atoms"]
    ms = reg.get("measurement") or {}
    lines = ["# %s renderer support" % reg["name"], "", reg["note"], "",
             "- Package: %s" % reg["package"], "- Version measured: %s" % (ms.get("renderer_version") or "n/a"),
             "- Protocol: %s" % reg["protocol"], "- Platform: %s" % reg["platform"], "- Measured: %s" % (ms.get("measured") or "n/a"), "",
             "## Coverage of the %d public atoms" % cov["total"], ""]
    for s in reg["statuses"]:
        lines.append("- %s: %d" % (dp.LABEL[s], cov[s]))
    lines.append("")
    skip = ("drawn", "native")
    for s in reg["statuses"]:
        names = [a for a in sorted(atoms) if atoms[a][rid]["status"] == s]
        if not names or (s in skip and len(names) > 80):
            continue
        lines += ["## %s (%d)" % (dp.LABEL[s], len(names)), ""]
        if s in skip or s == "not_measured":
            lines.append(", ".join("`%s`" % a for a in names))
        else:
            lines += ["- `%s`: %s" % (a, "; ".join(dp.reason_text(r) for r in atoms[a][rid]["reasons"]) or "no reason recorded") for a in names]
        lines.append("")
    lines += ["Overview: %s/renderers/" % BASE, "", dp.tm_text(m), ""]
    return "\n".join(lines)


def atom_md(m, atom):
    """Lines for the Markdown twin of an atom page (the `## Renderers` section), [] when not covered."""
    if not m or atom not in m["atoms"]:
        return []
    lines = ["## Renderers", "", "| Renderer | Status | Measured | Notes |", "|---|---|---|---|"]
    for rid, reg in m["renderers"].items():
        v = m["atoms"][atom][rid]
        why = [x for x in v.get("reasons", []) if x != "lane_painted_own_type"]
        notes = [dp.NOTE_TEXT.get(n, n) for n in v.get("notes", [])]
        txt = "; ".join([dp.reason_text(x) for x in why] + notes) if v["status"] not in ("drawn", "native") or notes else ""
        lines.append("| %s | %s | %s | %s |" % (reg["name"], dp.LABEL[v["status"]], v["measured"] or "n/a", txt.replace("|", "/")))
    lines += ["", "What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/", ""]
    return lines
