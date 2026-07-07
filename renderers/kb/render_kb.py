#!/usr/bin/env python3
"""render_kb.py — render a KB structure YAML to interactive HTML.

Design language: scope hero · alert callouts · step cards · action buttons ·
terminal tables · CSS-only interactivity via hidden checkbox/radio inputs
(radio = exclusive WHAT/IS decision choices, checkbox = nested CHECK reveals).
One <style> block, zero JavaScript — survives paste into CMS editors.

Input contract: the KCS-shaped structure YAML documented in README.md
(sections issue/environment/cause/cause_test/resolution; blocks body, list,
key_value, steps, table, tabs, callout, code_block, branch).

Usage: python3 render_kb.py article.yaml [--section description|resolution|all] > out.html
"""
import sys, html, re, yaml, itertools

_uid = itertools.count(1)
def uid(p): return f"{p}{next(_uid)}"

def esc(s): return html.escape(str(s), quote=False)
def md(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s

CSS = """
:root{--acc:#4f46e5;--acc-soft:#eef2ff;--ink:#1c2030;--mut:#6b7280;--line:#e5e7eb;
--ok:#059669;--warn:#d97706;--bad:#dc2626;--term:#0d1117;--term-ink:#7ee787;}
.kb{max-width:780px;margin:0 auto;padding:0 24px 72px;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink);line-height:1.6;}
.kb code{background:#f3f4f6;padding:1px 6px;border-radius:4px;font-size:.9em;}
/* scope hero */
.hero{background:linear-gradient(135deg,#312e81,#4f46e5);border-radius:0 0 18px 18px;padding:34px 30px 26px;color:#fff;margin:0 -4px 30px;}
.hero .eyebrow{font-size:.68rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;opacity:.75;margin-bottom:10px;}
.hero h1{margin:0 0 16px;font-size:1.72rem;line-height:1.18;text-wrap:balance;}
.chips{display:flex;flex-wrap:wrap;gap:8px;}
.chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 13px;font-size:.78rem;font-weight:600;}
.chip b{opacity:.7;font-weight:700;margin-right:5px;text-transform:uppercase;font-size:.68rem;letter-spacing:.05em;}
/* sections */
.sec{margin:0 0 30px;}
.sec>.lbl{font-size:.74rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);border-bottom:2px solid var(--line);padding-bottom:6px;margin-bottom:16px;}
/* callouts */
.co{display:flex;gap:12px;border-radius:10px;padding:13px 16px;margin:0 0 16px;font-size:.95rem;}
.co .lead{font-weight:800;flex:0 0 auto;}
.co.info{background:var(--acc-soft);border-left:4px solid var(--acc);}.co.info .lead{color:var(--acc);}
.co.warning{background:#fffbeb;border-left:4px solid var(--warn);}.co.warning .lead{color:var(--warn);}
.co.caution{background:#fef2f2;border-left:4px solid var(--bad);}.co.caution .lead{color:var(--bad);}
.co.tip{background:#ecfdf5;border-left:4px solid var(--ok);}.co.tip .lead{color:var(--ok);}
/* step cards */
.stepcards{display:flex;flex-direction:column;gap:10px;margin:0 0 18px;}
.stepcard{display:flex;gap:15px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04);}
.stepcard .n{flex:0 0 30px;height:30px;border-radius:9px;background:var(--acc-soft);color:var(--acc);font-weight:800;display:flex;align-items:center;justify-content:center;font-size:.92rem;}
.stepcard .t{padding-top:3px;}
/* key/value */
.kv{margin:0 0 16px;}
.kv .row{display:flex;gap:16px;padding:7px 0;border-bottom:1px solid var(--line);}
.kv .k{min-width:110px;font-size:.74rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);padding-top:3px;}
/* hidden-engine branch (radio) */
.branch{background:#f8f7ff;border:1px solid #e4e1fb;border-radius:14px;padding:18px;margin:0 0 22px;}
.branch>input{position:absolute;opacity:0;pointer-events:none;}
.qbar{display:flex;align-items:baseline;gap:10px;margin-bottom:14px;}
.kind{font-size:.66rem;font-weight:800;letter-spacing:.12em;color:var(--acc);background:var(--acc-soft);padding:3px 9px;border-radius:5px;}
.q{font-weight:700;font-size:1.05rem;}
.pills{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:4px;}
.pills label{cursor:pointer;border:1.5px solid #cfd2f6;background:#fff;border-radius:999px;padding:8px 16px;font-size:.88rem;font-weight:600;color:var(--ink);transition:all .12s;}
.pills label:hover{border-color:var(--acc);}
.panel{display:none;margin-top:14px;padding:16px 16px 6px;background:#fff;border:1px solid var(--line);border-radius:12px;}
/* nested check (checkbox) */
.chk{margin:0 0 16px;border:1.5px dashed #cfd2f6;border-radius:11px;padding:12px 15px;background:#fbfbff;}
.chk>input{position:absolute;opacity:0;pointer-events:none;}
.chk .cq{display:flex;align-items:center;gap:10px;}
.chk label{cursor:pointer;font-weight:700;color:var(--acc);text-decoration:underline dotted;}
.chk .cbody{display:none;margin-top:10px;}
/* action buttons */
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0 0;}
.btn{display:inline-block;border-radius:9px;padding:10px 20px;font-weight:700;font-size:.9rem;text-decoration:none;}
.btn.primary{background:var(--acc);color:#fff;}
.btn.ghost{border:1.5px solid var(--acc);color:var(--acc);background:#fff;}
/* terminal table */
.term{background:var(--term);border-radius:12px;padding:6px 0;margin:0 0 16px;overflow-x:auto;}
.term table{border-collapse:collapse;width:100%;font-family:ui-monospace,'Cascadia Code',Menlo,monospace;font-size:.84rem;}
.term th{color:var(--term-ink);text-align:left;padding:9px 16px;border-bottom:1px solid #21262d;font-weight:600;}
.term td{color:#c9d1d9;padding:8px 16px;border-bottom:1px solid #161b22;}
.term tr:nth-child(even) td{background:rgba(255,255,255,.03);}
pre.term-block{background:var(--term);color:#c9d1d9;border-radius:10px;padding:14px 16px;overflow-x:auto;font-size:.85rem;}
"""

def r_body(v): return f'<p style="margin:0 0 13px;">{md(v)}</p>'

def r_list(items):
    lis = "".join(f'<li style="margin:0 0 7px;">{md(i)}</li>' for i in items)
    return f'<ul style="margin:0 0 15px;padding-left:22px;">{lis}</ul>' 

def r_kv(items):
    rows = "".join(f'<div class="row"><div class="k">{esc(i["key"])}</div><div>{md(i["value"])}</div></div>' for i in items)
    return f'<div class="kv">{rows}</div>'

LEAD = {"info":"Note","tip":"Tip","warning":"Warning","caution":"Important"}
def r_callout(v):
    kind = v.get("kind","info")
    return (f'<div class="co {kind}"><span class="lead">{esc(v.get("title") or LEAD.get(kind,"Note"))}</span>'
            f'<span>{md(v.get("text",""))}</span></div>')

def r_steps(items, start=1):
    cards = "".join(f'<div class="stepcard"><div class="n">{i}</div><div class="t">{md(s)}</div></div>'
                    for i, s in enumerate(items, start))
    return f'<div class="stepcards">{cards}</div>'

def r_table(v):
    head = "".join(f"<th>{esc(h)}</th>" for h in v.get("headers", []))
    rows = "".join("<tr>" + "".join(f"<td>{md(c)}</td>" for c in r) + "</tr>" for r in v.get("rows", []))
    return f'<div class="term"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'

def r_tabs(tabs, extra_css):
    g = uid("tab")
    ids = [f"{g}_{i}" for i in range(len(tabs))]
    inputs = "".join(f'<input type="radio" id="{i}" name="{g}" style="position:absolute;opacity:0;pointer-events:none"{" checked" if n==0 else ""}>' for n, i in enumerate(ids))
    labels = "".join(f'<label for="{i}">{esc(t["label"])}</label>' for i, t in zip(ids, tabs))
    panels = "".join(f'<div class="panel p_{i}">{render_blocks(t.get("content",[]), extra_css)}</div>' for i, t in zip(ids, tabs))
    for i in ids:
        extra_css.append(f'#{i}:checked ~ .p_{i}{{display:block}} #{i}:checked ~ .pills label[for={i}]{{background:var(--acc);color:#fff;border-color:var(--acc)}}')
    return f'<div class="branch">{inputs}<div class="pills">{labels}</div>{panels}</div>'

def r_branch(br, extra_css):
    kind = br.get("kind","is")
    if kind == "check":                                     # checkbox engine — nested reveal
        c = uid("chk")
        yes, no = (br.get("choices") + [{}, {}])[:2]
        return (f'<div class="chk"><input type="checkbox" id="{c}" style="position:absolute;opacity:0;pointer-events:none">'
                f'<div class="cq"><span class="kind">CHECK</span><label for="{c}">{md(br.get("question",""))}</label></div>'
                f'<div class="cbody"><div class="co tip"><span class="lead">{esc(yes.get("answer","Yes"))}</span>'
                f'<span>{render_blocks(yes.get("guidance",[]), extra_css)}</span></div>'
                f'<div class="co info"><span class="lead">{esc(no.get("answer","No"))}</span>'
                f'<span>{render_blocks(no.get("guidance",[]), extra_css)}</span></div></div></div>'
                ), extra_css.append(f'#{c}:checked ~ .cbody{{display:block}}') or ""
    g = uid("q")                                            # radio engine — exclusive WHAT/IS
    ids = [f"{g}_{i}" for i in range(len(br.get("choices", [])))]
    inputs = "".join(f'<input type="radio" id="{i}" name="{g}" style="position:absolute;opacity:0;pointer-events:none">' for i in ids)
    labels = "".join(f'<label for="{i}">{md(c["answer"])}</label>' for i, c in zip(ids, br["choices"]))
    panels = "".join(f'<div class="panel p_{i}">{render_blocks(c.get("guidance",[]), extra_css)}</div>' for i, c in zip(ids, br["choices"]))
    for i in ids:
        extra_css.append(f'#{i}:checked ~ .p_{i}{{display:block}} #{i}:checked ~ .pills label[for={i}]{{background:var(--acc);color:#fff;border-color:var(--acc)}}')
    return (f'<div class="branch">{inputs}<div class="qbar"><span class="kind">{kind.upper()}</span>'
            f'<span class="q">{md(br.get("question",""))}</span></div>'
            f'<div class="pills">{labels}</div>{panels}</div>')

def render_blocks(blocks, extra_css):
    out = []
    for b in blocks or []:
        if "body" in b:        out.append(r_body(b["body"]))
        elif "list" in b:      out.append(r_list(b["list"]))
        elif "key_value" in b: out.append(r_kv(b["key_value"]))
        elif "steps" in b:     out.append(r_steps(b["steps"]))
        elif "callout" in b:   out.append(r_callout(b["callout"]))
        elif "table" in b:     out.append(r_table(b["table"]))
        elif "tabs" in b:      out.append(r_tabs(b["tabs"], extra_css))
        elif "branch" in b:
            r = r_branch(b["branch"], extra_css)
            out.append(r[0] if isinstance(r, tuple) else r)
        elif "code_block" in b: out.append(f'<pre class="term-block">{esc(b["code_block"])}</pre>')
    return "".join(out)

SECTIONS = [("issue","Issue"),("environment","Environment"),("cause","Cause"),
            ("cause_test","Confirm this is your issue"),("resolution","Resolution")]

# Two-field compose model: the article ships as TWO payloads → two CMS fields.
FRAGMENTS = {
    "description": ["issue", "environment", "cause", "cause_test"],  # + scope hero
    "resolution":  ["resolution"],                                   # + action buttons
    "all":         [k for k, _ in SECTIONS],
}

def render(a, section="all"):
    extra = []
    # scope hero: title + environment chips
    chips = ""
    env = a.get("environment")
    env_blocks = (env.get("blocks") if isinstance(env, dict) else env) or []
    kv = next((b["key_value"] for b in env_blocks if "key_value" in b), [])
    chips = "".join(f'<span class="chip"><b>{esc(i["key"])}</b>{esc(i["value"])}</span>' for i in kv)
    hero = (f'<div class="hero"><div class="eyebrow">Knowledge · {esc(a.get("layout",""))}</div>'
            f'<h1>{esc(a["title"])}</h1><div class="chips">{chips}</div></div>')
    wanted = FRAGMENTS.get(section, FRAGMENTS["all"])
    if section == "resolution": hero = ""           # resolution payload: no hero
    body = []
    for key, label in SECTIONS:
        if key not in wanted: continue
        sec = a.get(key)
        if not sec: continue
        blocks = (sec.get("blocks") if isinstance(sec, dict) else sec) or []
        if key == "environment":                       # kv went to the hero; keep only non-kv blocks
            blocks = [b for b in blocks if "key_value" not in b]
            if not blocks: continue
        body.append(f'<div class="sec"><div class="lbl">{label}</div>{render_blocks(blocks, extra)}</div>')
    # actions are DATA-DRIVEN (lifted from the source) — never fabricated
    acts = a.get("actions") or []
    actions = ""
    if acts and section != "description":
        btns = "".join(
            f'<a class="btn {"primary" if n == 0 else "ghost"}" href="{esc(x.get("url", "#"))}">{esc(x["label"])}</a>'
            for n, x in enumerate(acts))
        actions = f'<div class="actions">{btns}</div>'
    meta = a.get("meta") or {}
    if meta:
        bits = " · ".join(f'{k.replace("_", " ")}: {v}' for k, v in meta.items())
        actions += f'<div style="margin-top:22px;font-size:.72rem;color:#9ca3af;">Source — {esc(bits)}</div>'
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(a["title"])}</title><style>{CSS}{"".join(extra)}</style></head>'
            f'<body style="margin:0;background:#f4f4f7;"><div class="kb">{hero}{"".join(body)}{actions}</div></body></html>')

if __name__ == "__main__":
    section = "all"
    args = [a for a in sys.argv[1:]]
    if "--section" in args:
        i = args.index("--section"); section = args[i+1]; del args[i:i+2]
    data = yaml.safe_load(open(args[0]))
    print(render(data["article"], section))
