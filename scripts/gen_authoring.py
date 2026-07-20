#!/usr/bin/env python3
"""
Generate the gated Authoring section (full.a2uicatalog.ai only) as three
real, independently-linkable pages — not one file with JS-only tabs (the
original design; couldn't be bookmarked or deep-linked at all):

  /authoring/              hub: playbook doc + nav cards to the two tools
  /authoring/promptbuilder/  paste a rough draft, pick an archetype, copy
                              the assembled prompt or run it live via Vertex AI
  /authoring/whatscooking/   pick a type, fill in frontmatter fields, write
                              the body directly, save as a draft — no LLM
                              call at all, for planning/organizing ideas
                              before they're ready to lift. Also shows
                              what's currently in progress (launch-src/drafts/).

REAL BOUNDARY, same pattern as scripts/merge_private_schema.py and
_PRIVATE_EXAMPLE_BLOCKS in generate_atom_pages.py: all source content
(playbook prose, archetype/prompt-template data, current drafts) lives in
a2ui-private, never in this (public) repo. This script only emits code —
it produces nothing without the private source present, and refuses to
write anywhere under public/ (only public-full/).

Run (from catalog-rebuild-full, AFTER `cp -r public public-full`):
  A2UI_CATALOG_FULL=1 python3 scripts/gen_authoring.py
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("pip install markdown", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "public-full" / "authoring"
SPEC_JSON = ROOT / "public-full" / "spec.json"
SCHEMA_YAML = ROOT / "atoms" / "schema.yaml"

PRIVATE_SPEC = Path.home() / "a2ui-private" / "spec"
PLAYBOOK_MD = PRIVATE_SPEC / "article-writing-playbook-v0.1.md"
RUNBOOK_MD = PRIVATE_SPEC / "article-formats-runbook-v0.1.md"
ARCHETYPES_JSON = PRIVATE_SPEC / "prompt-builder-archetypes.json"
# Optional: the "run it here (Vertex AI)" pane. Calls the blog-worker Worker's
# /authoring/api/{lift,dispatch} routes (a2ui-private/blog-worker/src/authoring.js)
# — that's operational plumbing (Vertex AI auth, GitHub PR dispatch), a
# different boundary than the content-only files above, so its markup/JS
# lives in a2ui-private too and is spliced in here, never authored in this
# repo. Genuinely optional: the promptbuilder page renders fine without it
# (no lift pane, copy-to-clipboard still works).
LIFT_PANE_HTML = PRIVATE_SPEC / "authoring-lift-pane.html"
LIFT_PANE_JS = PRIVATE_SPEC / "authoring-lift-pane.js"
# What's Cooking's board of in-progress drafts — read-only, best-effort (a
# malformed draft is skipped with a stderr warning, never crashes this build;
# create_draft.py already validates YAML at creation time, but this is a
# second, independent safety net for anything hand-edited afterward).
DRAFTS_DIR = Path.home() / "a2ui-private" / "blog-worker" / "launch-src" / "drafts"


def _guard():
    """Refuse to run unless we are in a full-catalogue build. This script must
    never write into public/ — only public-full/, which does not ship via the
    public deploy.yml pipeline (see .github/workflows/deploy.yml)."""
    if os.environ.get("A2UI_CATALOG_FULL") != "1":
        print("gen_authoring: A2UI_CATALOG_FULL != 1, refusing to run "
              "(this generator only ever writes to public-full/)", file=sys.stderr)
        sys.exit(1)
    if not PRIVATE_SPEC.exists():
        print("gen_authoring: a2ui-private/spec not found — public-only checkout, "
              "skipping (Authoring section is gated-only, has no public form)",
              file=sys.stderr)
        sys.exit(0)
    for p in (PLAYBOOK_MD, ARCHETYPES_JSON):
        if not p.exists():
            print(f"gen_authoring: missing {p}, skipping", file=sys.stderr)
            sys.exit(0)


def _load_spec_atoms():
    """type -> compact_description, from the FULL spec.json already copied
    into public-full/ by the catalog-rebuild-full process. Used to wire each
    archetype's slot list to REAL, live atom docs — a slot name that doesn't
    exactly match a real atom type is left as plain text, never guessed."""
    if not SPEC_JSON.exists():
        return {}
    data = json.loads(SPEC_JSON.read_text(encoding="utf-8"))
    atoms = data.get("atoms", data if isinstance(data, list) else [])
    return {a["type"]: a.get("compact_description", "") for a in atoms if isinstance(a, dict) and a.get("type")}


def _load_schema_children():
    """type -> its declared `children:` dict (or None), from atoms/schema.yaml.
    spec.json carries NO ComponentId structure at all (flattened out at
    compact_description level) — this is the only ground truth for which
    atoms are actually ComponentId-addressable parents. Read directly from
    schema.yaml rather than spec.json because at the point this script runs
    in catalog-rebuild-full, schema.yaml is mid-pipeline in its FULL merged
    state (private blocks spliced in by merge_private_schema.py --merge,
    not yet restored) — so private ComponentId parents like article_journey
    are visible here even though they never reach the public schema."""
    if not SCHEMA_YAML.exists():
        return {}
    import yaml
    data = yaml.safe_load(SCHEMA_YAML.read_text(encoding="utf-8"))
    return {b["type"]: b.get("children") for b in data["blocks"]
            if isinstance(b, dict) and b.get("type")}


def _verify_componentid_maps(archetypes, schema_children):
    """An archetype's componentid_map is a claim about real schema structure
    (which atom is the ComponentId parent, which field holds its children).
    Verify it against the live schema at generation time rather than trusting
    hand-written JSON — if the schema drifts (field renamed, children:
    removed), this must fail loudly, not silently keep showing a stale
    diagram. Mirrors this repo's "ground truth over docs" convention (see
    generate_atom_pages.py's _EXAMPLE_BLOCKS comments on renderer drift)."""
    errors = []
    for arch_key, a in archetypes.items():
        for parent_type, spec in (a.get("componentid_map") or {}).items():
            children = schema_children.get(parent_type)
            if children is None:
                errors.append(f"{arch_key}: componentid_map claims '{parent_type}' has "
                               f"children:, but it's absent from atoms/schema.yaml "
                               f"(atom missing or no longer ComponentId-addressable)")
                continue
            field = spec.get("children_field")
            if field not in children:
                errors.append(f"{arch_key}: componentid_map claims '{parent_type}' has "
                               f"children.{field}, but schema declares children.{list(children.keys())}")
    if errors:
        print("gen_authoring: componentid_map verification FAILED against live schema:",
              file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


def _load_current_drafts():
    """title/series/date for each launch-src/drafts/*.md, for What's
    Cooking's board of in-progress work. Best-effort: a draft with no
    frontmatter or invalid YAML is skipped with a stderr warning rather than
    crashing this whole build — a bad OTHER draft shouldn't block generating
    the Authoring pages."""
    if not DRAFTS_DIR.exists():
        return []
    import yaml
    frontmatter_re = re.compile(r"^---\n(.*?)\n---\n", re.S)
    drafts = []
    for path in sorted(DRAFTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = frontmatter_re.match(text)
        if not m:
            print(f"gen_authoring: {path.name} has no frontmatter block, "
                  f"skipping from What's Cooking board", file=sys.stderr)
            continue
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            print(f"gen_authoring: {path.name} frontmatter invalid ({e}), "
                  f"skipping from What's Cooking board", file=sys.stderr)
            continue
        drafts.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem),
            "series": meta.get("series", ""),
            "date": str(meta.get("date", "")),
        })
    return drafts


def site_header():
    # Mirrors scripts/generate_atom_pages.py's site_header() nav — kept in
    # sync by hand (small, stable nav; not worth a shared-import coupling).
    return """<header class="site-header"><div class="hdr-in">
    <a class="wordmark" href="/"><svg class="logo-atom" viewBox="0 0 24 24" aria-hidden="true"><ellipse class="o1" cx="12" cy="12" rx="10" ry="4.4" transform="rotate(-32 12 12)"/><ellipse class="o2" cx="12" cy="12" rx="10" ry="4.4" transform="rotate(32 12 12)"/><ellipse class="o3" cx="12" cy="12" rx="10" ry="4.4" transform="rotate(90 12 12)"/><circle class="nuc" cx="12" cy="12" r="2.7"/><circle class="el" cx="3.21" cy="15.98" r="1.25"/></svg><span><span class="grad">A2UI</span> Catalog</span></a>
    <nav class="site-nav">
      <a href="/">Atoms</a>
      <a href="/templates">Templates</a>
      <a href="/surfaces/mcp-apps">MCP Playground</a>
      <a href="/renderer">Apps Script Renderer</a>
      <a href="/blog/drafts">Blog</a>
      <a href="/authoring" aria-current="page">Authoring</a>
    </nav>
    <button class="theme-btn" type="button" aria-label="Toggle light/dark theme">◐</button>
    <a class="gh-pill" href="https://github.com/a2uicatalog/a2ui">GitHub ↗</a>
  </div></header>"""


THEME_TOGGLE_JS = """document.querySelector('.theme-btn').addEventListener('click', function(){
  var r = document.documentElement, t = r.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  r.setAttribute('data-theme', t);
});"""


PAGE_CSS = """
<style>
:root{
  color-scheme:light;
  --bg:oklch(98% 0.006 255);--surface:oklch(100% 0 0);--surface-2:oklch(96.5% 0.008 255);
  --border:oklch(90% 0.01 255);--border-strong:oklch(82% 0.02 255);
  --text:oklch(22% 0.02 255);--text-muted:oklch(46% 0.02 255);--text-faint:oklch(62% 0.02 255);
  --accent:oklch(58% 0.19 277);--accent-contrast:oklch(100% 0 0);--accent-soft-bg:oklch(94% 0.03 277);
  --accent-2:oklch(62% 0.13 202);--positive:oklch(58% 0.15 146);--warn:oklch(58% 0.17 55);
  --code-bg:oklch(96% 0.01 255);--radius:12px;
  --shadow:0 1px 2px oklch(0% 0 0 / .05),0 8px 24px oklch(0% 0 0 / .05);
  --mono:ui-monospace,'SF Mono',Monaco,monospace;
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:oklch(27% 0.025 255);--surface:oklch(33% 0.025 255);--surface-2:oklch(30% 0.02 255);
  --border:oklch(42% 0.02 255);--border-strong:oklch(50% 0.02 255);
  --text:oklch(95% 0.01 255);--text-muted:oklch(72% 0.02 255);--text-faint:oklch(58% 0.02 255);
  --accent:oklch(72% 0.16 277);--accent-contrast:oklch(15% 0.02 255);--accent-soft-bg:oklch(38% 0.06 277);
  --accent-2:oklch(75% 0.12 202);--positive:oklch(72% 0.15 146);--warn:oklch(78% 0.15 55);
  --code-bg:oklch(23% 0.02 255);
  --shadow:0 1px 2px oklch(0% 0 0 / .3),0 8px 24px oklch(0% 0 0 / .28);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:oklch(27% 0.025 255);--surface:oklch(33% 0.025 255);--surface-2:oklch(30% 0.02 255);
    --border:oklch(42% 0.02 255);--border-strong:oklch(50% 0.02 255);
    --text:oklch(95% 0.01 255);--text-muted:oklch(72% 0.02 255);--text-faint:oklch(58% 0.02 255);
    --accent:oklch(72% 0.16 277);--accent-contrast:oklch(15% 0.02 255);--accent-soft-bg:oklch(38% 0.06 277);
    --accent-2:oklch(75% 0.12 202);--positive:oklch(72% 0.15 146);--warn:oklch(78% 0.15 55);
    --code-bg:oklch(23% 0.02 255);
    --shadow:0 1px 2px oklch(0% 0 0 / .3),0 8px 24px oklch(0% 0 0 / .28);
  }
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:15.5px;line-height:1.6;margin:0}
a{color:var(--accent-2)}
code{font-family:var(--mono);font-size:.86em;background:var(--code-bg);padding:1px 5px;border-radius:4px}
pre code{background:none;padding:0}
pre{background:var(--code-bg);border:1px solid var(--border);border-radius:8px;padding:14px 16px;overflow:auto;font-size:13px}

.site-header{position:sticky;top:0;z-index:60;background:var(--surface);border-bottom:1px solid var(--border);backdrop-filter:blur(8px)}
.hdr-in{max-width:1360px;margin:0 auto;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.wordmark{display:flex;align-items:center;gap:8px;font-weight:800;color:var(--text);text-decoration:none;font-size:14px}
.logo-atom{width:22px;height:22px;flex-shrink:0}
.logo-atom .nuc{fill:var(--accent)}
.logo-atom .o1{stroke:var(--accent);fill:none;stroke-width:1.5}
.logo-atom .o2{stroke:var(--accent-2);fill:none;stroke-width:1.5}
.logo-atom .o3{stroke:var(--accent);fill:none;stroke-width:1.1;opacity:.35}
.logo-atom .el{fill:var(--accent-2)}
.grad{background:linear-gradient(120deg,var(--accent),var(--accent-2));-webkit-background-clip:text;background-clip:text;color:transparent}
.site-nav{display:flex;gap:20px;font-size:13.5px}
.site-nav a{color:var(--text-muted);text-decoration:none;font-weight:600}
.site-nav a[aria-current="page"]{color:var(--accent)}
.site-nav a:hover{color:var(--text)}
.theme-btn{font:inherit;font-size:14px;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:6px 10px;cursor:pointer;color:var(--text)}
.gh-pill{font-size:12px;font-weight:700;color:var(--text-muted);text-decoration:none;border:1px solid var(--border);border-radius:99px;padding:5px 12px}

.authoring-top{padding:20px 24px 0;max-width:1360px;margin:0 auto}
.authoring-top h1{font-size:1.6rem;font-weight:800;letter-spacing:-.5px;margin:0 0 4px}
.authoring-top .sub{color:var(--text-muted);font-size:13.5px;margin:0 0 18px}
.gate-note{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--warn);border:1px solid color-mix(in oklch, var(--warn) 40%, transparent);background:color-mix(in oklch, var(--warn) 8%, transparent);padding:3px 9px;border-radius:99px;margin-bottom:18px}

.section{max-width:1360px;margin:0 auto;padding:24px}

/* hub landing page (/authoring/) */
.authoring-hub-cards{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px}
@media(max-width:760px){.authoring-hub-cards{grid-template-columns:1fr}}
.hub-card{display:block;background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:20px 22px;text-decoration:none;box-shadow:var(--shadow);transition:border-color .12s}
.hub-card:hover{border-color:var(--accent)}
.hub-card-title{font-weight:800;font-size:1.05rem;color:var(--text);margin-bottom:6px}
.hub-card-desc{font-size:13px;color:var(--text-muted);line-height:1.5}

/* what's-cooking board */
.cooking-board{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.cooking-card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-decoration:none}
.cooking-card:hover{border-color:var(--accent)}
.cooking-card-title{font-weight:700;font-size:13.5px;color:var(--text);margin-bottom:3px}
.cooking-card-meta{font-family:var(--mono);font-size:11px;color:var(--text-faint)}

/* what's-cooking frontmatter form */
.fm-fields{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:16px}
.fm-fields label{display:flex;flex-direction:column;gap:5px;font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}
.fm-fields input,.fm-fields textarea{font:inherit;font-size:13.5px;font-weight:400;text-transform:none;letter-spacing:normal;color:var(--text);background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px 10px}
.fm-fields textarea{resize:vertical}

/* playbook doc */
.playbook-doc{max-width:820px}
.playbook-doc h1{font-size:1.8rem;margin:0 0 6px}
.playbook-doc h2{font-size:1.25rem;margin:34px 0 12px;padding-top:14px;border-top:1px solid var(--border)}
.playbook-doc h3{font-size:1rem;color:var(--accent);margin:22px 0 8px}
.playbook-doc p{margin:0 0 14px;color:var(--text)}
.playbook-doc strong{color:var(--text)}
.playbook-doc ul,.playbook-doc ol{margin:0 0 14px;padding-left:22px}
.playbook-doc li{margin-bottom:4px}
.playbook-doc blockquote{border-left:3px solid var(--accent);margin:0 0 14px;padding:2px 0 2px 14px;color:var(--text-muted)}

/* archetype picker (promptbuilder + whatscooking) */
.picker{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:22px}
@media(max-width:980px){.picker{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.picker{grid-template-columns:1fr}}
.arch-card{text-align:left;background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:14px 16px;cursor:pointer;font:inherit;color:var(--text);transition:border-color .12s,box-shadow .12s}
.arch-card:hover{border-color:var(--border-strong)}
.arch-card.active{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft-bg)}
.arch-card .name{font-family:var(--mono);font-weight:800;font-size:13px;color:var(--accent);margin-bottom:5px}
.arch-card .spine{font-size:12.5px;color:var(--text-muted);line-height:1.45}
.arch-card .proof-tag{display:inline-block;margin-top:7px;font-size:10px;font-family:var(--mono);text-transform:uppercase;letter-spacing:.05em;padding:1px 7px;border-radius:99px}
.arch-card .proof-tag.proven{background:var(--accent-soft-bg);color:var(--accent)}
.arch-card .proof-tag.draft{background:var(--surface-2);color:var(--text-faint);border:1px solid var(--border)}

.workspace{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
@media(max-width:980px){.workspace{grid-template-columns:1fr}}
.pane{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden}
.pane-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--surface-2);border-bottom:1px solid var(--border)}
.pane-bar span{font-family:var(--mono);font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em}
.pane-bar .count{font-family:var(--mono);font-size:11px;color:var(--text-faint)}
textarea#draftInput,textarea#cookingBody{width:100%;height:480px;border:none;resize:vertical;padding:16px;font-family:var(--mono);font-size:13px;line-height:1.6;background:transparent;color:var(--text);outline:none}
textarea#draftInput::placeholder,textarea#cookingBody::placeholder{color:var(--text-faint)}
.copy-btn{background:var(--accent-soft-bg);border:1px solid transparent;border-radius:6px;color:var(--accent);font-size:11.5px;font-weight:700;padding:6px 14px;cursor:pointer;letter-spacing:.03em;font-family:var(--mono)}
.copy-btn:hover{border-color:var(--accent)}
.copy-btn.copied{color:var(--positive)}
.copy-btn.copy-failed{color:var(--warn);background:transparent;border-color:var(--warn)}
#promptOutput{margin:0;padding:16px;overflow:auto;height:480px;font-family:var(--mono);font-size:12px;line-height:1.6;white-space:pre-wrap;color:var(--text);border:none}
.childlist-strip{padding:12px 16px;border-top:1px solid var(--border);background:var(--code-bg);font-family:var(--mono);font-size:11.5px;color:var(--text-muted);line-height:1.9}
.childlist-strip b{color:var(--accent);display:block;margin-bottom:4px;font-size:10px;text-transform:uppercase;letter-spacing:.06em}
.slot-chip{display:inline-flex;align-items:center;gap:4px;background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:2px 8px;margin:2px 4px 2px 0;font-size:11px}
.slot-chip.wired{border-color:var(--accent-2);color:var(--accent-2);text-decoration:none}
.slot-chip.wired:hover{background:var(--accent-soft-bg)}
.slot-chip.parent{border-color:var(--accent);color:var(--accent);font-weight:700}
.slot-chip.child{border-style:dashed}
.slot-chip.unwired{color:var(--text-faint)}
.componentid-strip{padding:10px 16px;border-top:1px solid var(--border);font-family:var(--mono);font-size:11.5px;color:var(--text-muted)}
.componentid-strip b{color:var(--accent);display:block;margin-bottom:4px;font-size:10px;text-transform:uppercase;letter-spacing:.06em}
.hint{font-size:12.5px;color:var(--text-faint);margin:14px 0 24px;max-width:80ch}
</style>
"""


def _page_shell(title, body_html, extra_script=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title} — A2UI Catalog (full)</title>
{PAGE_CSS}
</head>
<body>
{site_header()}
{body_html}
<script>
{THEME_TOGGLE_JS}
{extra_script}
</script>
</body>
</html>
"""


def _slots_html(archetype, spec_atoms):
    """Render each slot as a chip: a real atom type in spec.json gets a live
    link + its actual compact_description; anything else stays plain text —
    mechanical, no guessed mapping. Slots that are the parent or child side of
    a verified componentid_map get a distinct style (solid accent = ComponentId
    parent, dashed = its declared child) so the real nesting is visible, not
    just a flat list of atom names."""
    cmap = archetype.get("componentid_map") or {}
    parents = set(cmap.keys())
    children = {spec["child_type"] for spec in cmap.values()}
    chips = []
    for slot in archetype["slots"]:
        extra = " parent" if slot in parents else " child" if slot in children else ""
        if slot in spec_atoms:
            desc = spec_atoms[slot].replace('"', "&quot;")
            chips.append(f'<a class="slot-chip wired{extra}" href="/atoms/{slot}" title="{desc}">{slot} ↗</a>')
        else:
            chips.append(f'<span class="slot-chip unwired{extra}">{slot}</span>')
    return "".join(chips)


def _componentid_structure_html(archetype):
    """A plain-language line for each verified componentid_map entry, e.g.
    'article_journey.steps[] -> journey_step (each independently addressable
    by ComponentId)'. Only rendered when the archetype declares one — absence
    is an honest fact (most archetypes don't have a ComponentId target yet),
    not an error."""
    cmap = archetype.get("componentid_map") or {}
    if not cmap:
        return ""
    lines = [f"{parent}.{spec['children_field']}[] → {spec['child_type']} "
             "(each independently addressable by ComponentId)"
             for parent, spec in cmap.items()]
    return ('<div class="componentid-strip"><b>ComponentId structure (verified against atoms/schema.yaml)</b>'
            + "<br>".join(lines) + "</div>")


def _cooking_board_html(drafts):
    if not drafts:
        return '<p class="hint">Nothing in progress right now.</p>'
    cards = "".join(
        f'<a class="cooking-card" href="https://full.a2uicatalog.ai/blog/drafts/{d["slug"]}/">'
        f'<div class="cooking-card-title">{d["title"]}</div>'
        f'<div class="cooking-card-meta">{d["series"]} · {d["date"]}</div>'
        f'</a>'
        for d in drafts
    )
    return f'<div class="cooking-board">{cards}</div>'


def build_landing_page(playbook_html):
    body = f"""<div class="authoring-top">
  <div class="gate-note">🔒 full.a2uicatalog.ai only</div>
  <h1>Authoring</h1>
  <p class="sub">Plan, draft, and lift articles for the blog.</p>
</div>
<div class="section">
  <div class="authoring-hub-cards">
    <a class="hub-card" href="/authoring/whatscooking/">
      <div class="hub-card-title">What's Cooking</div>
      <div class="hub-card-desc">Pick an article type, fill in the frontmatter, and write the body directly — no LLM call, for organizing ideas before they're ready to lift. Also shows what's already in progress.</div>
    </a>
    <a class="hub-card" href="/authoring/promptbuilder/">
      <div class="hub-card-title">Prompt Builder</div>
      <div class="hub-card-desc">Paste a rough draft, pick an archetype, and either copy the assembled prompt into any LLM or run it live here via Vertex AI.</div>
    </a>
    <a class="hub-card" href="/authoring/posts/">
      <div class="hub-card-title">LinkedIn Posts</div>
      <div class="hub-card-desc">Draft posts, review them against your own tone via Gemini, link them to articles, and track posted engagement — all through the same registry the stats pipe reads.</div>
    </a>
  </div>
  <div class="playbook-doc" style="margin-top:36px">{playbook_html}</div>
</div>"""
    return _page_shell("Authoring", body)


def build_promptbuilder_page(archetypes, spec_atoms, lift_pane_html, lift_pane_js):
    archetypes_json = json.dumps(archetypes)
    slots_by_key = {key: _slots_html(a, spec_atoms) for key, a in archetypes.items()}
    slots_json = json.dumps(slots_by_key)
    componentid_by_key = {key: _componentid_structure_html(a) for key, a in archetypes.items()}
    componentid_json = json.dumps(componentid_by_key)
    wired_count = sum(1 for a in archetypes.values() for s in a["slots"] if s in spec_atoms)
    total_slots = sum(len(a["slots"]) for a in archetypes.values())

    body = f"""<div class="authoring-top">
  <div class="gate-note">🔒 full.a2uicatalog.ai only</div>
  <h1>Prompt Builder</h1>
  <p class="sub">Paste a rough draft, pick an archetype — {wired_count}/{total_slots} template slots wired to live atom docs via spec.json.</p>
</div>
<div class="section">
  <div class="picker" id="picker"></div>
  <p class="hint" id="archDetail"></p>
  <div class="workspace">
    <div class="pane">
      <div class="pane-bar"><span>Your draft</span><span class="count" id="draftCount">0 words</span></div>
      <textarea id="draftInput" placeholder="Paste your rough draft here — freeform is fine, don't pre-structure it. The prompt on the right adapts to whichever layout you pick above."></textarea>
    </div>
    <div class="pane">
      <div class="pane-bar"><span>Assembled prompt — copy into your LLM</span><button class="copy-btn" id="copyBtn" type="button">COPY</button></div>
      <pre id="promptOutput"></pre>
      <div class="childlist-strip"><b>ChildList slots (solid = ComponentId parent, dashed = its child, wired = real atom linked to its live doc)</b><span id="slotChips"></span></div>
      <div id="componentidStrip"></div>
    </div>
  </div>
{lift_pane_html}</div>"""

    script = f"""
var ARCHETYPES = {archetypes_json};
var SLOT_CHIPS = {slots_json};
var COMPONENTID_STRIPS = {componentid_json};
var current = 'build_log';

function wordCount(s){{ return (s.trim().match(/\\S+/g) || []).length; }}

function buildPrompt(a, draft){{
  var slotList = a.slots.map(function(s){{ return '  <!-- slot: ' + s + ' -->'; }}).join('\\n');
  return (
"You are formatting a rough draft into this blog's exact parser conventions\\n" +
"AND annotating it for future graduation to a live A2UI ComponentId/ChildList\\n" +
"template. Output ONLY the final markdown file (frontmatter + body). No\\n" +
"commentary, no fences around the whole thing, no explanation outside the\\n" +
"Phase 4 report. Invent nothing not present in the draft - sparseness in the\\n" +
"draft stays sparse in the output; never fabricate a section, quote, caveat,\\n" +
"or number to fill a template slot.\\n" +
"\\n" +
"PHASE 0 - Frontmatter\\n" +
"Emit: title, series, date, summary, read_minutes (volume is resolved in\\n" +
"Phase 0.5, not here). All are required by the parser or the build fails.\\n" +
"Infer read_minutes from word count (~200 wpm) if not given. If this post\\n" +
"is one part of a named multi-part arc, say so as plain text in the title\\n" +
"itself (e.g. \\\"... (Part 2)\\\") - there is no separate part-number field.\\n" +
"\\n" +
"PHASE 0.5 - Filename & volume\\n" +
"State this on its own line, before the formatted output:\\n" +
"  Proposed filename: NNN-<slug>.md\\n" +
"<slug> is lowercase, hyphenated, short, derived from the title - you have\\n" +
"full context by now, propose one. NNN is the post's position across ALL\\n" +
"posts ever published (never per-series) - you cannot see the current\\n" +
"launch-src/ directory, so always ASK for NNN rather than guessing a\\n" +
"number. volume is the SAME integer as NNN, always (NNN=004 -> volume: 4)\\n" +
"- once NNN is confirmed, set volume to match it exactly; do not compute\\n" +
"it separately or guess a per-series count.\\n" +
"\\n" +
"PHASE 1 - Archetype (fixed for this run)\\n" +
"Archetype: " + a.label + "\\n" +
"Spine: " + a.spine + "\\n" +
"Signals this archetype fits: " + a.signals + "\\n" +
"If the draft clearly does NOT fit this spine, say so in Phase 4 instead of\\n" +
"forcing it - don't silently reshape content into a spine it doesn't have.\\n" +
"\\n" +
"PHASE 2 - Structure into H2 sections matching the spine\\n" +
a.phase2 + "\\n" +
"Every heading gets {{label=\\"Short\\"}} if the natural heading is longer than\\n" +
"~3 words or doesn't front-load its distinctive word.\\n" +
"\\n" +
"PHASE 2.5 - Template alignment (for future ComponentId/ChildList graduation)\\n" +
"This archetype's target composition (article-formats-runbook-v0.1.md):\\n" +
"  " + a.childlist + "\\n" +
"Immediately before each section that corresponds to one of these slots,\\n" +
"insert an HTML comment naming it, e.g.:\\n" +
slotList + "\\n" +
"Comments are invisible in the rendered post today - they're forward\\n" +
"compatibility for the day this graduates from markdown to a live\\n" +
"ComponentId/ChildList payload. Skip slots the draft doesn't support rather\\n" +
"than inventing content to fill them - an absent slot is a true fact about\\n" +
"this draft, not an error.\\n" +
"\\n" +
"PHASE 3 - Marks\\n" +
"- The single most quotable line (if one exists) becomes `> [!QUOTE] <line>`.\\n" +
"  Zero or one per major section; two is the ceiling for the whole post.\\n" +
"- Fenced code blocks stay ordinary triple-backtick.\\n" +
"- Real markdown tables where the draft has tabular data.\\n" +
"\\n" +
"PHASE 4 - Report\\n" +
"After the output, list on separate lines:\\n" +
"- Whether the draft actually fit the " + a.label + " spine, or where it strained\\n" +
"- Any heading you added an explicit {{label=...}} to, and why\\n" +
"- Which ComponentId slots got skipped (no content for them) vs used\\n" +
"- Anything you could NOT confidently structure - flag it, don't paper over it\\n" +
"\\n" +
"---\\n" +
"DRAFT TO FORMAT:\\n" +
(draft && draft.trim() ? draft : "[paste your rough draft here]")
  );
}}

function render(){{
  var a = ARCHETYPES[current];
  var draft = document.getElementById('draftInput').value;
  document.getElementById('draftCount').textContent = wordCount(draft) + ' words';
  document.getElementById('promptOutput').textContent = buildPrompt(a, draft);
  document.getElementById('archDetail').innerHTML =
    '<b style="color:var(--accent)">' + a.label + '</b> — ' + a.spine +
    (a.proven ? '' : ' <span style="color:var(--warn)">(unproven — no live fixture yet)</span>');
  document.getElementById('slotChips').innerHTML = SLOT_CHIPS[current];
  document.getElementById('componentidStrip').innerHTML = COMPONENTID_STRIPS[current];
}}

function buildPicker(){{
  var host = document.getElementById('picker');
  Object.keys(ARCHETYPES).forEach(function(key){{
    var a = ARCHETYPES[key];
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'arch-card' + (key === current ? ' active' : '');
    btn.dataset.key = key;
    btn.innerHTML =
      '<div class="name">' + a.label + '</div>' +
      '<div class="spine">' + a.spine + '</div>' +
      '<span class="proof-tag ' + (a.proven ? 'proven' : 'draft') + '">' + (a.proven ? 'proven' : 'unproven') + '</span>';
    btn.addEventListener('click', function(){{
      current = key;
      document.querySelectorAll('.arch-card').forEach(function(c){{ c.classList.remove('active'); }});
      btn.classList.add('active');
      render();
    }});
    host.appendChild(btn);
  }});
}}

function copyPromptToClipboard(){{
  var srcEl = document.getElementById('promptOutput');
  var text = srcEl.textContent;
  var btn = document.getElementById('copyBtn');
  function showOk(){{
    btn.textContent = 'COPIED'; btn.classList.add('copied'); btn.classList.remove('copy-failed');
    setTimeout(function(){{ btn.textContent = 'COPY'; btn.classList.remove('copied'); }}, 2000);
  }}
  function showManualFallback(){{
    try{{
      var range = document.createRange();
      range.selectNodeContents(srcEl);
      var sel = window.getSelection();
      sel.removeAllRanges(); sel.addRange(range);
    }}catch(e){{}}
    btn.textContent = 'SELECTED — PRESS ⌘/CTRL+C'; btn.classList.add('copy-failed'); btn.classList.remove('copied');
    setTimeout(function(){{ btn.textContent = 'COPY'; btn.classList.remove('copy-failed'); }}, 4000);
  }}
  function tryExecCommand(){{
    try{{
      var range = document.createRange();
      range.selectNodeContents(srcEl);
      var sel = window.getSelection();
      sel.removeAllRanges(); sel.addRange(range);
      var ok = document.execCommand('copy');
      sel.removeAllRanges();
      if (ok) {{ showOk(); return true; }}
    }}catch(e){{}}
    return false;
  }}
  if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext){{
    navigator.clipboard.writeText(text).then(showOk, function(){{
      if (!tryExecCommand()) showManualFallback();
    }});
  }} else {{
    if (!tryExecCommand()) showManualFallback();
  }}
}}
document.getElementById('copyBtn').addEventListener('click', copyPromptToClipboard);
document.getElementById('draftInput').addEventListener('input', render);

{lift_pane_js}
buildPicker();
render();
"""
    return _page_shell("Prompt Builder", body, script)


def build_whatscooking_page(archetypes, spec_atoms, current_drafts):
    archetypes_json = json.dumps(archetypes)
    slots_by_key = {key: _slots_html(a, spec_atoms) for key, a in archetypes.items()}
    slots_json = json.dumps(slots_by_key)

    body = f"""<div class="authoring-top">
  <div class="gate-note">🔒 full.a2uicatalog.ai only</div>
  <h1>What's Cooking</h1>
  <p class="sub">Pick a type, fill in the frontmatter, write the body directly — saves straight to launch-src/drafts/, lands on full.a2uicatalog.ai/blog/drafts for review, exactly like a Vertex-lifted draft.</p>
</div>
<div class="section">
  <h2 style="font-size:1.05rem;margin:0 0 12px">Currently cooking ({len(current_drafts)})</h2>
  {_cooking_board_html(current_drafts)}
</div>
<div class="section" style="padding-top:0">
  <h2 style="font-size:1.05rem;margin:24px 0 12px">Start a new draft</h2>
  <div class="picker" id="picker"></div>
  <div class="workspace">
    <div class="pane" style="grid-column:1 / -1">
      <div class="pane-bar"><span>Frontmatter</span></div>
      <div class="fm-fields">
        <label>Title <input id="fmTitle" type="text" placeholder="Article title"></label>
        <label>Series <input id="fmSeries" type="text" list="seriesOptions" placeholder="e.g. essay"></label>
        <datalist id="seriesOptions">
          <option value="Problems Nobody Asked Me to Solve">
          <option value="a2uicatalog">
          <option value="Building AI agents in Google Cloud">
        </datalist>
        <label>Date <input id="fmDate" type="date"></label>
        <label>Read minutes <input id="fmReadMinutes" type="number" min="1"></label>
        <label style="grid-column:1/-1">Summary <textarea id="fmSummary" rows="2" placeholder="One or two sentences"></textarea></label>
      </div>
    </div>
  </div>
  <div class="workspace" style="margin-top:16px">
    <div class="pane">
      <div class="pane-bar"><span>Body</span><button class="copy-btn" id="insertTemplateBtn" type="button">INSERT SLOT TEMPLATE</button></div>
      <textarea id="cookingBody" placeholder="Write here — the slot comments (INSERT SLOT TEMPLATE, or type your own) are forward-compatibility markers for future ComponentId graduation, not required structure."></textarea>
    </div>
    <div class="pane">
      <div class="pane-bar"><span>Archetype reference</span></div>
      <div style="padding:16px;font-size:13px;color:var(--text-muted)" id="archRef"></div>
      <div class="childlist-strip"><b>Slots</b><span id="slotChips"></span></div>
    </div>
  </div>
  <div class="childlist-strip" style="display:flex;align-items:center;gap:10px;margin-top:16px;border-top:1px solid var(--border)">
    <button class="copy-btn" id="saveDraftBtn" type="button">SAVE DRAFT</button>
    <span id="saveDraftStatus" style="color:var(--text-faint)"></span>
  </div>
</div>"""

    script = f"""
var ARCHETYPES = {archetypes_json};
var SLOT_CHIPS = {slots_json};
var current = 'build_log';

function slugify(s){{ return (s || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }}
function yamlQuote(s){{ return '"' + String(s || '').replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\\\"') + '"'; }}

function renderArchRef(){{
  var a = ARCHETYPES[current];
  document.getElementById('archRef').innerHTML =
    '<b style="color:var(--accent)">' + a.label + '</b><br>' + a.spine +
    (a.proven ? '' : ' <span style="color:var(--warn)">(unproven — no live fixture yet)</span>');
  document.getElementById('slotChips').innerHTML = SLOT_CHIPS[current];
}}

function buildPicker(){{
  var host = document.getElementById('picker');
  Object.keys(ARCHETYPES).forEach(function(key){{
    var a = ARCHETYPES[key];
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'arch-card' + (key === current ? ' active' : '');
    btn.dataset.key = key;
    btn.innerHTML =
      '<div class="name">' + a.label + '</div>' +
      '<div class="spine">' + a.spine + '</div>' +
      '<span class="proof-tag ' + (a.proven ? 'proven' : 'draft') + '">' + (a.proven ? 'proven' : 'unproven') + '</span>';
    btn.addEventListener('click', function(){{
      current = key;
      document.querySelectorAll('.arch-card').forEach(function(c){{ c.classList.remove('active'); }});
      btn.classList.add('active');
      renderArchRef();
    }});
    host.appendChild(btn);
  }});
}}

document.getElementById('insertTemplateBtn').addEventListener('click', function(){{
  var body = document.getElementById('cookingBody');
  var a = ARCHETYPES[current];
  if (body.value.trim() && !confirm('Replace the current body with a fresh slot scaffold for ' + a.label + '?')) return;
  body.value = a.slots.map(function(s){{ return '<!-- slot: ' + s + ' -->\\n\\n'; }}).join('\\n');
}});

document.getElementById('saveDraftBtn').addEventListener('click', function(){{
  var title = document.getElementById('fmTitle').value.trim();
  var series = document.getElementById('fmSeries').value.trim();
  var date = document.getElementById('fmDate').value;
  var readMin = document.getElementById('fmReadMinutes').value;
  var summary = document.getElementById('fmSummary').value.trim();
  var body = document.getElementById('cookingBody').value;
  var status = document.getElementById('saveDraftStatus');
  var btn = document.getElementById('saveDraftBtn');
  if (!title || !series || !date || !readMin || !summary) {{
    status.textContent = 'Fill in all frontmatter fields first.';
    return;
  }}
  var slug = slugify(title);
  if (!slug) {{ status.textContent = 'Title must contain at least one letter or number.'; return; }}
  var markdown =
    'Proposed slug: ' + slug + '\\n\\n' +
    '---\\n' +
    'title: ' + yamlQuote(title) + '\\n' +
    'series: ' + yamlQuote(series) + '\\n' +
    'date: ' + date + '\\n' +
    'summary: ' + yamlQuote(summary) + '\\n' +
    'read_minutes: ' + readMin + '\\n' +
    '---\\n\\n' +
    body;
  btn.disabled = true; btn.textContent = 'SAVING...';
  status.textContent = 'Saving...';
  fetch('/authoring/api/dispatch', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{markdown: markdown}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      if (res.ok && res.data.draftUrl) {{
        status.innerHTML = 'Saved — building the gated preview (full rebuild + deploy takes <b>~5–8 min</b>; this page will tell you when it\\'s live)…';
        pollDraftLive(res.data.draftUrl, status, 0);
      }} else if (res.ok) {{
        status.textContent = 'Saved — check GitHub for the new PR shortly.';
      }} else {{
        status.textContent = 'FAILED: ' + (res.data.error || 'unknown error');
        btn.disabled = false; btn.textContent = 'SAVE DRAFT';
      }}
    }})
    .catch(function(e){{
      status.textContent = 'FAILED: ' + e.message;
      btn.disabled = false; btn.textContent = 'SAVE DRAFT';
    }});
}});

// Browser is Access-authenticated, so fetching the draft URL distinguishes
// 404 (deploy not landed) from 200 (live). The real CI cycle is ~5-8 min —
// understating it ("~1-2 min") caused three duplicate re-saves of one
// article on 2026-07-20.
function pollDraftLive(url, statusEl, attempt){{
  if (attempt > 60) {{ statusEl.innerHTML = 'Still not live after 15 min — check the deploy-full-catalog run on GitHub. URL: <a href="' + url + '" target="_blank">' + url + '</a>'; return; }}
  fetch(url, {{method: 'GET', cache: 'no-store'}})
    .then(function(r){{
      if (r.ok) {{
        statusEl.innerHTML = '✅ LIVE — <a href="' + url + '" target="_blank">' + url + '</a>';
      }} else {{
        setTimeout(function(){{ pollDraftLive(url, statusEl, attempt + 1); }}, 15000);
      }}
    }})
    .catch(function(){{ setTimeout(function(){{ pollDraftLive(url, statusEl, attempt + 1); }}, 15000); }});
}}

buildPicker();
renderArchRef();
"""
    return _page_shell("What's Cooking", body, script)


def main():
    _guard()
    playbook_html = markdown.markdown(
        PLAYBOOK_MD.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables"],
    )
    archetypes = json.loads(ARCHETYPES_JSON.read_text(encoding="utf-8"))
    spec_atoms = _load_spec_atoms()
    schema_children = _load_schema_children()
    _verify_componentid_maps(archetypes, schema_children)
    current_drafts = _load_current_drafts()

    lift_pane_html = LIFT_PANE_HTML.read_text(encoding="utf-8") if LIFT_PANE_HTML.exists() else ""
    lift_pane_js = LIFT_PANE_JS.read_text(encoding="utf-8") if LIFT_PANE_JS.exists() else ""
    if not lift_pane_html:
        print("gen_authoring: no authoring-lift-pane.html in a2ui-private/spec — "
              "building promptbuilder without the Vertex AI lift pane", file=sys.stderr)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(build_landing_page(playbook_html), encoding="utf-8")

    promptbuilder_dir = OUTPUT_DIR / "promptbuilder"
    promptbuilder_dir.mkdir(parents=True, exist_ok=True)
    (promptbuilder_dir / "index.html").write_text(
        build_promptbuilder_page(archetypes, spec_atoms, lift_pane_html, lift_pane_js),
        encoding="utf-8",
    )

    whatscooking_dir = OUTPUT_DIR / "whatscooking"
    whatscooking_dir.mkdir(parents=True, exist_ok=True)
    (whatscooking_dir / "index.html").write_text(
        build_whatscooking_page(archetypes, spec_atoms, current_drafts),
        encoding="utf-8",
    )

    wired = sum(1 for a in archetypes.values() for s in a["slots"] if s in spec_atoms)
    total = sum(len(a["slots"]) for a in archetypes.values())
    print(f"gen_authoring: wrote /authoring/, /authoring/promptbuilder/, /authoring/whatscooking/ "
          f"({len(archetypes)} archetypes, {wired}/{total} slots wired to spec.json, "
          f"{len(current_drafts)} draft(s) on the cooking board)")


if __name__ == "__main__":
    main()
