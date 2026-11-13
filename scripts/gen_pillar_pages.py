#!/usr/bin/env python3
"""gen_pillar_pages.py — evergreen guide ("pillar") pages: content/<slug>.md -> public/<slug>/index.html.

A pillar page answers one big search question (first: "What is A2UI?") as a standing, on-brand
site page, not a dated blog post. Same shared chrome as every other page (site header, brand
tokens, theme JS from generate_atom_pages), same honest footer as the trust pages.

Content lives in this repo (content/<slug>.md, front matter: title, summary, date, read_minutes).
`<!-- FILM -->` in the markdown marks where content/<slug>.film.json (an A2UI payload, rendered
by renderers.web_article like every atom page) is spliced. A marker, not byte offsets, so editing
the text can never misplace the film. The film itself is built in a2ui-private
(motion-demos/protocol-film/build_protocol.mjs writes the .film.json here).

Structured data: Article + BreadcrumbList, plus FAQPage when the page has a "## FAQ" section
written as **Question?** lines each followed by an answer paragraph.

Numbers and code samples come from data at build time, never typed into the markdown: an
`@@NAME@@` token is filled from facts() (the published catalogue document and the vendored v1.0
Basic Catalog), and the build fails if a token is unknown or left over. A slug may be nested
("what-is-a2ui/custom-catalog"): content/what-is-a2ui/custom-catalog.md ->
public/what-is-a2ui/custom-catalog/index.html, with the parent page in the breadcrumb.

Run in deploy.yml after gen_public_catalog.py (it reads public/catalogue/a2ui-atoms-v1.json).
"""
import html
import json
import os
import re
import sys

import markdown
import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, ROOT)
import generate_atom_pages as _site  # the site's shared chrome: header, tokens, theme JS (one definition)
from renderers.web_article import render as wa_render

CONTENT = os.path.join(ROOT, "content")
PUBLIC = os.path.join(ROOT, "public")
BASE = "https://a2uicatalog.ai"
LINKEDIN = "https://www.linkedin.com/in/curtiskrygier"
FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
PILLARS = ["what-is-a2ui", "what-is-a2ui/custom-catalog"]
CATALOG = os.path.join(PUBLIC, "catalogue", "a2ui-atoms-v1.json")
BASIC_CATALOG = os.path.join(ROOT, "tests", "fixtures", "a2ui_v1_0_spec", "catalogs", "basic", "catalog.json")
TOKEN_RE = re.compile(r"@@([A-Z0-9_]+)@@")
# Web renderers whose x-renderers status "drawn" is quoted on the custom-catalog page. Flutter and
# Compose are left out: their native counts have their own definition (renderer-matrix-v1.json).
WEB_RENDERERS = [("react", "React"), ("angular", "Angular"), ("lit", "Lit"),
                 ("copilotkit", "CopilotKit"), ("a2ui-vue", "a2ui-vue")]
# The mixed-catalog example: Basic Catalog layout and text, one component from this catalogue.
# Emitted by renderers.a2ui_v1 (the code that serves real surfaces), so the page shows what we send.
MIXED_EXAMPLE = {"title": "Weekly sales", "blocks": [
    {"type": "heading", "level": 1, "text": "Weekly sales"},
    {"type": "stat_card", "value": "1,234", "label": "Orders this week", "delta": "+12%", "is_up": True}]}

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}/brand/og-card.png">
<meta name="twitter:card" content="summary_large_image">
{jsonld}
{site_head_js}
<style>{site_css}
.pillar{{max-width:820px;margin:0 auto;padding:44px 24px 80px}}
.pillar-hero{{position:relative;padding:8px 0 28px;margin-bottom:8px;border-bottom:1px solid var(--border)}}
.pillar-kicker{{display:inline-block;font-size:.74rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);background:var(--accent-soft-bg);border:1px solid var(--border);border-radius:999px;padding:4px 12px;margin-bottom:18px}}
a.pillar-kicker{{text-decoration:none}}a.pillar-kicker::before{{content:"← "}}
.pillar-hero h1{{margin:0;font-size:clamp(2.2rem,5.4vw,3.4rem);line-height:1.05;font-weight:850;letter-spacing:-.03em;color:var(--text)}}
.pillar-hero h1 .grad{{background:linear-gradient(90deg,var(--accent),var(--accent-2));-webkit-background-clip:text;background-clip:text;color:transparent}}
.pillar-hero .sub{{margin:10px 0 0;font-size:clamp(1.15rem,2.4vw,1.4rem);font-weight:650;color:var(--text-muted)}}
.pillar-hero .lede{{margin:18px 0 0;font-size:1.08rem;line-height:1.6;color:var(--text);max-width:68ch}}
.pillar-meta{{margin-top:16px;font-size:.84rem;color:var(--text-muted)}}
.pillar-body{{font-size:1.04rem;line-height:1.72;color:var(--text)}}
.pillar-body h2{{font-size:1.45rem;letter-spacing:-.01em;margin:2.4rem 0 .6rem;scroll-margin-top:84px}}
.pillar-body p,.pillar-body li{{color:var(--text)}}
.pillar-body p{{margin:0 0 1.1rem}}
.pillar-body ul,.pillar-body ol{{margin:0 0 1.2rem;padding-left:1.4rem}}
.pillar-body li{{margin:.3rem 0}}
.pillar-body strong{{color:var(--text)}}
.pillar-body a{{color:var(--accent);text-underline-offset:2px}}
.pillar-body code{{background:var(--code-bg);padding:2px 6px;border-radius:5px;font-size:.9em;font-family:ui-monospace,'SF Mono',Monaco,monospace}}
.pillar-body pre{{background:var(--code-bg);padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:.86rem;line-height:1.5;margin:0 0 1.1rem}}
.pillar-body pre code{{background:none;padding:0;font-size:inherit}}
.pillar-body table{{width:100%;border-collapse:collapse;margin:1.2rem 0;font-size:.95rem}}
.pillar-body th,.pillar-body td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}}
.pillar-body th{{font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--text-muted)}}
.pillar-film{{margin:2rem -48px;padding:0}}
.pillar-film figcaption{{margin:10px 48px 0;font-size:.86rem;color:var(--text-muted);text-align:center}}
.pillar-foot{{margin-top:44px;padding-top:18px;border-top:1px solid var(--border);font-size:.8rem;color:var(--text-muted)}}
.pillar-foot a{{color:var(--accent)}}
@media(max-width:900px){{.pillar-film{{margin:2rem 0}}.pillar-film figcaption{{margin:10px 0 0}}}}
@media(max-width:640px){{.pillar{{padding:28px 16px 64px}}}}
</style>
</head>
<body>
{site_header}
<main class="pillar">
<header class="pillar-hero">
{kicker}
<h1>{h1}</h1>
<p class="sub">{h1_sub}</p>
<p class="lede">{lede}</p>
<p class="pillar-meta">{read_minutes} min read &middot; Updated {date_human}</p>
</header>
<article class="pillar-body">
{body}
</article>
<p class="pillar-foot">Independent, unofficial catalog: not affiliated with, endorsed by, or sponsored by Google or Anthropic.
A2UI is Google's protocol; MCP is Anthropic's. Maintained by <a href="{li}">Curtis Krygier</a>. MIT License.</p>
</main>
{site_foot_js}
</body>
</html>
"""


def _faq(body_md):
    """**Question?** line or ### Question? heading + following paragraph(s) under '## FAQ' -> [(q, a_plain)]."""
    m = re.search(r"^## FAQ\s*\n(.*?)(?=^## |\Z)", body_md, re.S | re.M)
    if not m:
        return []
    out = []
    # a question is a "**Question?**" line or a "### Question?" heading; its answer runs to the next one
    for q1, q2, a in re.findall(r"^(?:\*\*(.+?)\*\*|#{3,4}[ \t]+(.+?))[ \t]*\n(.*?)(?=^\*\*|^#{3,4}[ \t]|\Z)", m.group(1), re.S | re.M):
        q = q1 or q2
        plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a)         # links -> their text
        plain = re.sub(r"[`*_]", "", " ".join(plain.split()))
        if plain:
            out.append((q.strip(), plain))
    return out


def _json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def mixed_example():
    from renderers.a2ui_v1 import emit_surface
    return emit_surface(MIXED_EXAMPLE, surface_id="sales")


def facts():
    """Every @@TOKEN@@ a pillar page may use, read from the published catalogue and the vendored spec."""
    cat = json.load(open(CATALOG, encoding="utf-8"))
    basic = json.load(open(BASIC_CATALOG, encoding="utf-8"))
    comps = cat["components"]
    head = {k: cat[k] for k in ("$schema", "$id", "protocolVersion", "catalogId", "title")}
    head["description"] = cat["description"].split(". ")[0] + "."
    head["components"] = {"intro": "{ ... }", "body": "{ ... }", "…": f"{len(comps)} components in all"}
    head["functions"] = cat.get("functions", {})
    f = {"ATOMS": str(len(comps)), "BASIC_N": str(len(basic["components"])),
         "CATALOG_ID": cat["catalogId"], "BASIC_ID": basic["catalogId"], "PROTOCOL": cat["protocolVersion"],
         "JSON_CATALOG_HEAD": _json(head), "JSON_STAT_CARD": _json({"stat_card": {k: v for k, v in comps["stat_card"].items()
                                                 if k not in ("x-routing-text", "x-intent-phrases")}}),
         "JSON_MIXED_EXAMPLE": _json(mixed_example())}
    rows = []
    for key, name in WEB_RENDERERS:
        n = sum(1 for c in comps.values() if c.get("x-renderers", {}).get(key) == "drawn")
        if not n:  # an empty x-renderers dimension means the catalogue build lost it: fail, never print "0 of"
            raise SystemExit(f"{CATALOG}: no component has x-renderers.{key} == 'drawn'")
        f[f"DRAWN_{key.upper().replace('-', '_')}"] = str(n)
        rows.append(f"| {name} | {n} of {len(comps)} |")
    f["WEB_RENDERER_TABLE"] = "| Renderer | Components it draws |\n|---|---|\n" + "\n".join(rows)
    return f


def _fill(text, slug):
    f = facts() if "@@" in text else {}
    def sub(m):
        if m.group(1) not in f:
            raise SystemExit(f"content/{slug}.md: unknown token @@{m.group(1)}@@")
        return f[m.group(1)]
    return TOKEN_RE.sub(sub, text)


def _film(slug):
    path = os.path.join(CONTENT, f"{slug}.film.json")
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    blocks = payload["blocks"] if isinstance(payload, dict) else payload
    title = next((b.get("title") for b in blocks if isinstance(b, dict) and b.get("title")), "")
    return wa_render(blocks, theme="light"), title  # "dark" adds page-wide Meet-stage overrides; the film carries its own dark stage


def build(slug):
    raw = open(os.path.join(CONTENT, f"{slug}.md"), encoding="utf-8").read()
    m = FRONT_MATTER_RE.match(raw)
    if not m:
        raise SystemExit(f"content/{slug}.md: missing front matter")
    fm, body_md = yaml.safe_load(m.group(1)) or {}, _fill(m.group(2), slug)
    title, summary = _fill(fm["title"], slug), _fill(fm["summary"], slug)
    # the markdown's own H1 becomes the hero; its first paragraph becomes the lede
    body_md = re.sub(r"^# .*\n+", "", body_md.lstrip(), count=1)
    first, rest = body_md.split("\n\n", 1)
    url = f"{BASE}/{slug}/"
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"permalink": False}})
    body_html = md.convert(rest)
    lede_html = markdown.markdown(first).removeprefix("<p>").removesuffix("</p>")
    if "@@" in body_html:
        raise SystemExit(f"content/{slug}.md: unfilled @@ token")
    if "<!-- FILM -->" in body_html:
        film_html, film_title = _film(slug)
        cap = f"<figcaption>{html.escape(film_title)}</figcaption>" if film_title else ""
        body_html = body_html.replace("<!-- FILM -->", f'<figure class="pillar-film">{film_html}{cap}</figure>', 1)
    elif os.path.exists(os.path.join(CONTENT, f"{slug}.film.json")):
        raise SystemExit(f"content/{slug}.film.json exists but content/{slug}.md has no <!-- FILM --> marker")

    head, _, tail = title.partition("?")
    h1 = html.escape(head + "?").replace("A2UI", '<span class="grad">A2UI</span>', 1) if tail else html.escape(title)
    h1_sub = html.escape(tail.strip()) if tail else ""
    date = str(fm.get("date", ""))
    parent = slug.rpartition("/")[0]
    crumbs = [{"@type": "ListItem", "position": 1, "name": "A2UI Atomic Catalog", "item": f"{BASE}/"}]
    if parent:
        ptitle = yaml.safe_load(FRONT_MATTER_RE.match(open(os.path.join(CONTENT, f"{parent}.md"), encoding="utf-8").read()).group(1))["title"]
        crumbs.append({"@type": "ListItem", "position": 2, "name": ptitle.partition("?")[0] + "?" if "?" in ptitle else ptitle,
                       "item": f"{BASE}/{parent}/"})
    kicker = '<span class="pillar-kicker">Guide</span>'
    if parent:
        kicker = (f'<a class="pillar-kicker" href="/{parent}/">{html.escape(crumbs[-1]["name"])}</a>')
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": head + "?" if tail else title, "item": url})
    graph = [
        {"@type": "Article", "@id": url + "#article", "headline": title, "description": summary, "url": url,
         "mainEntityOfPage": url, "datePublished": date, "dateModified": date, "inLanguage": "en",
         "author": {"@type": "Person", "name": "Curtis Krygier", "url": LINKEDIN},
         "publisher": {"@id": f"{BASE}/#org"}, "image": f"{BASE}/brand/og-card.png"},
        {"@type": "BreadcrumbList", "itemListElement": crumbs},
    ]
    faq = _faq(body_md)
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    jsonld = ('<script type="application/ld+json">\n'
              + json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=1, ensure_ascii=False).replace("</", "<\\/")
              + "\n</script>")
    import datetime
    try:
        date_human = datetime.date.fromisoformat(date).strftime("%-d %B %Y")
    except ValueError:
        date_human = date
    out = PAGE.format(title=html.escape(title), desc=html.escape(summary, quote=True), url=url, base=BASE, li=LINKEDIN,
                      jsonld=jsonld, h1=h1, h1_sub=h1_sub, lede=lede_html, read_minutes=fm.get("read_minutes", 5),
                      date_human=date_human, body=body_html, kicker=kicker,
                      site_head_js=_site.SITE_HEAD_JS, site_css=_site.SITE_BASE_CSS,
                      site_header=_site.site_header("guide"), site_foot_js=_site.SITE_FOOT_JS)
    d = os.path.join(PUBLIC, slug)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"wrote public/{slug}/index.html ({len(faq)} FAQ entries)")


def main():
    for slug in PILLARS:
        build(slug)


if __name__ == "__main__":
    main()
