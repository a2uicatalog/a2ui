#!/usr/bin/env python3
"""Build the DRAFT renderer-dimension pages (local only) from renderer-matrix-v1.json.

Writes ONLY new files under the draft folder; it reads the built live atom pages and
writes modified copies, it never changes them. Stdlib only, deterministic.
"""
import html
import json
import os
import re
import shutil

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = "/mnt/hdd2/work/launch-piece/20-renderer-dimension-draft"
LOGOS = "/mnt/hdd2/work/launch-piece/13-try-it-draft/logos"
MATRIX = os.path.join(WT, "public/catalogue/renderer-matrix-v1.json")
SAMPLES = ["stat_card", "key_value", "badge_group", "table", "callout", "bullet_list", "pull_stat", "progress_bar", "sparkline", "shimmer_text"]
E = html.escape
LABEL = {"native": "Native", "degraded": "Degraded", "not_supported": "Not supported", "not_measured": "Not measured"}
GLYPH = {"native": "✓", "degraded": "~", "not_supported": "✕", "not_measured": "?"}
HELP = {
    "native": "drawn by the renderer's own implementation of the atom",
    "degraded": "drawn through Basic components",
    "not_supported": "draws nothing or errors",
    "not_measured": "no per-atom data",
}

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
.rd-chip.native{--c-bg:color-mix(in srgb,var(--positive) 16%,var(--surface));--c-line:color-mix(in srgb,var(--positive) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--positive) 55%,var(--text))}
.rd-chip.degraded{--c-bg:color-mix(in srgb,var(--warn) 18%,var(--surface));--c-line:color-mix(in srgb,var(--warn) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--warn) 45%,var(--text))}
.rd-chip.not_supported{--c-bg:color-mix(in srgb,var(--negative) 14%,var(--surface));--c-line:color-mix(in srgb,var(--negative) 50%,var(--surface));--c-ink:color-mix(in srgb,var(--negative) 55%,var(--text))}
.rd-chip.not_measured{--c-bg:var(--surface-2);--c-line:var(--border-strong);--c-ink:var(--text-muted)}
.rd-ev{color:var(--muted);font-size:12.5px;line-height:1.45}
.rd-date{white-space:nowrap;color:var(--muted);font-size:12px}
.rd-tm{font-size:11.5px;color:var(--muted);margin:10px 0 0;max-width:80ch;line-height:1.45}
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


def short_date(d):
    return d or "n/a"


def block(m, atom, prefix):
    rows = []
    for rid, reg in m["renderers"].items():
        v = m["atoms"][atom][rid]
        rows.append(
            '<tr><td><span class="rd-name">%s<a href="%srenderers/%s.html">%s</a></span></td><td>%s</td><td class="rd-ev">%s</td><td class="rd-date">%s</td></tr>'
            % (logo(reg, prefix), prefix, rid, E(reg["name"]), chip(v["status"]), E(v["evidence"]), E(short_date(v["measured"])))
        )
    return (
        '\n  <div class="section rd" id="renderers">\n    <div class="label">Renderers</div>\n'
        '    <p class="rd-lead">What draws this atom, separate from the surfaces above. Draft data from the renderer gates, 10 to 12 Nov 2026. '
        '<a href="%sindex.html">About this dimension</a></p>\n'
        '    <table><thead><tr><th>Renderer</th><th>Status</th><th>Evidence</th><th>Measured</th></tr></thead><tbody>%s</tbody></table>\n'
        '    <p class="rd-tm">%s %s %s</p>\n  </div>\n'
        % (prefix, "".join(rows), E(m["independence_note"]), E(m["trademark_note"]), E(m["trademark_note_extra"]))
    )


def atom_pages(m):
    src_dir = os.path.join(WT, "public/atoms")
    done = []
    for atom in SAMPLES:
        p = os.path.join(src_dir, atom, "index.html")
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf8").read()
        i = s.index('<div class="label">Surfaces</div>')
        j = s.index("</div>", i + 40)  # first </div> after the label closes the section
        j = s.index("</div>", j + 1) if s[i:j].count("<div") > 1 else j
        end = j + len("</div>")
        s = s[:end] + "\n" + block(m, atom, "../") + s[end:]
        s = s.replace("</head>", CSS_BLOCK + "</head>", 1)
        s = s.replace("<title>", "<title>[DRAFT renderers] ", 1)
        with open(os.path.join(DRAFT, "atoms", atom + ".html"), "w", encoding="utf8") as f:
            f.write(s)
        done.append(atom)
    return done


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
.scroll{overflow-x:auto}
.lg{display:inline-block;width:20px;height:20px;flex:none;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat;vertical-align:middle}
.lg0{display:inline-block;width:20px;height:20px;flex:none;vertical-align:middle}
.nm{display:flex;gap:8px;align-items:center;font-weight:650;white-space:nowrap}
.rd-chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;border:1px solid var(--c-line);background:var(--c-bg);color:var(--c-ink);white-space:nowrap}
.rd-chip.native{--c-bg:color-mix(in srgb,var(--ok) 15%,var(--card));--c-line:color-mix(in srgb,var(--ok) 50%,var(--card));--c-ink:var(--ok)}
.rd-chip.degraded{--c-bg:color-mix(in srgb,var(--warn) 16%,var(--card));--c-line:color-mix(in srgb,var(--warn) 50%,var(--card));--c-ink:var(--warn)}
.rd-chip.not_supported{--c-bg:color-mix(in srgb,var(--bad) 13%,var(--card));--c-line:color-mix(in srgb,var(--bad) 50%,var(--card));--c-ink:var(--bad)}
.rd-chip.not_measured{--c-bg:var(--sunk);--c-line:var(--line2);--c-ink:var(--mut)}
.bar{display:flex;height:14px;border-radius:7px;overflow:hidden;border:1px solid var(--line2);margin:8px 0}
.bar span{display:block;height:100%}
.bar .native{background:var(--ok)}.bar .degraded{background:var(--warn)}.bar .not_supported{background:var(--bad)}.bar .not_measured{background:var(--line2)}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:0;font-size:14px}
dl.facts dt{color:var(--mut)}dl.facts dd{margin:0}
details{border:1px solid var(--line);border-radius:10px;background:var(--card);margin:8px 0;padding:6px 12px}
summary{cursor:pointer;font-weight:650;padding:4px 0}
ul.atoms{columns:3 180px;column-gap:18px;list-style:none;padding:0;margin:8px 0;font-size:13px;font-family:ui-monospace,Menlo,monospace}
ul.atoms li{break-inside:avoid;padding:1px 0}
.note{font-size:13px;color:var(--mut);max-width:75ch}
.tm{font-size:12px;color:var(--mut);margin-top:28px;max-width:80ch}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){
 .two{grid-template-columns:1fr}
 dl.facts{grid-template-columns:1fr;gap:0}dl.facts dt{margin-top:8px}
 ul.atoms{columns:2 140px}
}
"""


def page(title, body, prefix):
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%s</title><style>%s</style></head><body><main>%s</main></body></html>\n" % (E(title), PAGE_CSS, body)
    )


def counts_bar(cov):
    t = cov["total"]
    return '<div class="bar" role="img" aria-label="%s">%s</div>' % (
        E(", ".join("%s %d" % (LABEL[s], cov[s]) for s in LABEL)),
        "".join('<span class="%s" style="width:%.3f%%"></span>' % (s, 100.0 * cov[s] / t) for s in LABEL if cov[s]),
    )


def tm_block(m):
    return '<p class="tm">%s %s %s</p>' % (E(m["independence_note"]), E(m["trademark_note"]), E(m["trademark_note_extra"]))


def atom_link(a, samples):
    if a in samples:
        return '<a href="../atoms/%s.html">%s</a>' % (a, a)
    return a


def renderer_page(m, rid, samples):
    reg = m["renderers"][rid]
    cov = reg["coverage"]
    atoms = m["atoms"]
    byst = {s: [a for a in sorted(atoms) if atoms[a][rid]["status"] == s] for s in LABEL}
    facts = [
        ("Package", reg["package"]), ("Version measured", reg["version"]), ("Protocol dialect", reg["protocol"]),
        ("Platform", reg["platform"]), ("M-level reached", reg["m_level"]), ("Measured", reg["measured"] or "n/a"),
        ("Data source", reg["data_source"]),
    ]
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % (E(k), E(v)) for k, v in facts)
    chips = "".join("<tr><td>%s</td><td>%d</td><td class=\"note\">%s</td></tr>" % (chip(s), cov[s], E(HELP[s])) for s in LABEL)
    extra = ""
    if rid == "flutter":
        nat = byst["native"]
        chk = [a for a in nat if "text parity with the web painter checked" in atoms[a][rid]["evidence"]]
        mism = [a for a in chk if "web words missing" in atoms[a][rid]["evidence"]]
        extra = (
            '<h2>Honest notes</h2><div class="card"><ul>'
            "<li>Partial coverage: %d of %d public atoms draw natively; %d draw only through Basic components; %d draw nothing or are rejected; %d have no lane example.</li>"
            "<li>Text parity with the web painter checked on %d atoms; %d of those miss at least one web word in Flutter. The parity check compares visible words, not layout or pixels.</li>"
            "<li>The Basic lane was not measured by us; this renderer is below M4. No device run: everything ran in the headless widget-test engine.</li>"
            "<li>A 40-atom independent audit (12 Nov) found undocumented visible drift in about 16 of 40 ported atoms, so \"native\" here means the port draws the lane example, not that it matches the web look.</li>"
            "</ul></div>"
        ) % (cov["native"], cov["total"], cov["degraded"], cov["not_supported"], cov["not_measured"], len(chk), len(mism))
    elif rid == "compose":
        extra = '<h2>Honest notes</h2><div class="card">Compose is on hold. No measurement exists, so every atom is not measured. This page is a placeholder for the registry entry.</div>'
    else:
        ev = [atoms[a][rid]["evidence"] for a in byst["native"]]
        n_loose = sum(1 for e in ev if "no visible text found" in e)
        fails = {}
        for lab in ("light 480", "dark 480", "light 360", "dark 360"):
            fails[lab] = sum(1 for e in ev if (lab + " FAIL") in e)
        n_unst = sum(1 for e in ev if "unstable allowance" in e)
        px = ""
        if rid != "react":
            px = "<li>Pixel parity with React (same code, same fixed rule): atoms that FAIL by environment: " + ", ".join("%s %d" % (k, v) for k, v in fails.items() if k != "dark 360" or rid != "lit") + ". %d atoms are on the unstable (time or animation) allowance list.</li>" % n_unst
        extra = (
            '<h2>Honest notes</h2><div class="card"><ul><li>%s</li>'
            "<li>Status comes from the custom lane (our 670 example payloads): an atom is native when it painted without error and was not flagged broken. All %d measured atoms did; the lane cannot show a lower status for them. Pixel parity, behaviour probes and allowance lists are evidence text only.</li>%s"
            "<li>%d atoms painted no visible text in the lane example (loose flag off); most draw canvas or graphics, and some are blank in React as well. They stay native under the rule; a reviewer may want to treat them differently.</li>"
            "<li>M5 (weekly gate, schedule installed, independent recount) is not claimed. 22 public atoms had no example in the lane data and are not measured.</li></ul></div>"
        ) % (E(reg["note"]), cov["native"], px, n_loose)
    lists = ""
    for s in LABEL:
        if not byst[s]:
            continue
        items = []
        for a in byst[s]:
            suffix = ""
            if rid == "flutter" and s == "native":
                mm = re.search(r"(\d+) of (\d+) web words missing", atoms[a][rid]["evidence"])
                if mm:
                    suffix = ' <span class="note">(%s words missing)</span>' % mm.group(1)
            items.append("<li>%s%s</li>" % (atom_link(a, samples), suffix))
        open_attr = " open" if len(byst[s]) <= 12 else ""
        lists += '<details%s><summary>%s %s: %d atoms</summary><ul class="atoms">%s</ul></details>' % (open_attr, chip(s), "", len(byst[s]), "".join(items))
    body = (
        '<p class="crumb"><a href="../index.html">Renderer dimension (draft)</a> / %s</p><span class="draft">Draft, local only</span>'
        '<h1><span class="nm">%s%s</span></h1><p class="lead">%s</p>'
        '<div class="card"><dl class="facts">%s</dl></div>'
        "<h2>Coverage of the %d public atoms</h2>%s%s"
        '<div class="scroll"><table><thead><tr><th>Status</th><th>Atoms</th><th>Meaning</th></tr></thead><tbody>%s</tbody></table></div>'
        "%s<h2>Atoms by status</h2>%s%s"
    ) % (E(reg["name"]), logo(reg, "../"), E(reg["name"]), E(reg["note"]), dl, cov["total"], counts_bar(cov), "", chips, extra, lists, tm_block(m))
    return page("[DRAFT] %s renderer support" % reg["name"], body, "../")


def hub(m, samples):
    rows = []
    for rid, reg in m["renderers"].items():
        cov = reg["coverage"]
        rows.append(
            '<tr><td><span class="nm">%s<a href="renderers/%s.html">%s</a></span></td><td>%s<br><span class="note">%s</span></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (logo(reg, ""), rid, E(reg["name"]), E(reg["package"]), E(reg["version"]), E(reg["protocol"]), E(reg["m_level"]),
               "%d" % cov["native"], "%d / %d" % (cov["degraded"], cov["not_supported"]), "%d" % cov["not_measured"])
        )
    sm = " ".join('<a href="atoms/%s.html">%s</a>' % (a, a) for a in samples)
    body = (
        '<span class="draft">Draft, local only, not published</span><h1>Which renderer draws which atom</h1>'
        '<p class="lead">A new, separate dimension of the catalogue. Every atom already says where it appears; this adds what draws it, measured per renderer. %d public atoms, %d renderers (one on hold).</p>'
        "<h2>Two dimensions, in plain words</h2>"
        '<div class="two"><div class="card"><strong>Surface: where it appears</strong><p class="note">The place a person sees the atom: web page, MCP app, Android, PDF, Google Meet stage, and so on. This is the existing <code>x-surfaces</code> field. It does not change.</p></div>'
        '<div class="card"><strong>Renderer: what draws it</strong><p class="note">The piece of software that turns the atom into pixels: React, Lit, Angular, CopilotKit, a2ui-vue or Flutter. This is the new <code>x-renderers</code> field. One surface (the web) is drawn by several renderers, and one renderer can serve several surfaces.</p></div></div>'
        "<h2>Registry</h2>"
        '<div class="scroll"><table><thead><tr><th>Renderer</th><th>Package, version</th><th>Protocol</th><th>M-level</th><th>Native</th><th>Degraded / not supported</th><th>Not measured</th></tr></thead><tbody>%s</tbody></table></div>'
        '<p class="note">Native: drawn by the renderer\'s own implementation. Degraded: drawn through Basic components. Not supported: draws nothing or errors. Not measured: no per-atom data. CopilotKit and a2ui-vue draw our atoms inside their own wrapper and theme. Flutter coverage is partial and below M4.</p>'
        "<h2>Sample atom pages</h2><p>%s</p>"
        '<h2>Files</h2><p class="note"><a href="README.md">README.md</a> (data model, mapping, ambiguities, what a reviewer should rule on), <a href="data/renderer-matrix-v1.json">renderer-matrix-v1.json</a>.</p>%s'
    ) % (m["atom_count"], len(m["renderers"]), "".join(rows), sm, tm_block(m))
    return page("[DRAFT] Renderer dimension", body, "")


def main():
    m = json.load(open(MATRIX, encoding="utf8"))
    os.makedirs(os.path.join(DRAFT, "atoms"), exist_ok=True)
    os.makedirs(os.path.join(DRAFT, "renderers"), exist_ok=True)
    os.makedirs(os.path.join(DRAFT, "data"), exist_ok=True)
    os.makedirs(os.path.join(DRAFT, "logos"), exist_ok=True)
    for f in sorted(os.listdir(LOGOS)):
        if f.endswith(".svg"):
            shutil.copyfile(os.path.join(LOGOS, f), os.path.join(DRAFT, "logos", f))
    shutil.copyfile(MATRIX, os.path.join(DRAFT, "data/renderer-matrix-v1.json"))
    done = atom_pages(m)
    for rid in m["renderers"]:
        with open(os.path.join(DRAFT, "renderers", rid + ".html"), "w", encoding="utf8") as f:
            f.write(renderer_page(m, rid, done))
    with open(os.path.join(DRAFT, "index.html"), "w", encoding="utf8") as f:
        f.write(hub(m, done))
    print("atom pages:", done)


if __name__ == "__main__":
    main()
