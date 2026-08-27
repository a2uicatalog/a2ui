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
Also emitted, top-level rather than nested under /authoring/ — it is its own
surface, not a tool inside the authoring suite, even though it shares this
Worker and Access gate (2026-08-04):

  /workspace/                the A2UI Workspace — the SAME per-reader profile
                              and reading history the MCP Apps surface inside
                              Claude uses (same Cloudflare Access `sub`, same
                              Durable Object; confirmed identical 2026-08-04).
                              A browser HOST ADAPTER for the a2ui-catalogue
                              renderer bundle, modeled directly on
                              public/surfaces/mcp-apps/play/'s proven
                              iframe+postMessage pattern — see that file and
                              a2ui-private/blog-worker/src/workspace.js before
                              changing either side. Where Claude drafts a
                              chat message and hands the reading off, this
                              host answers ui/message itself: a bounded
                              Gemini function-calling loop against Vertex,
                              through the SAME article_playbook contract.

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
# Single source of truth for the Workspace's tool allowlist (2026-08-04) —
# see a2uithoughts.md's "workspace verb parity" entry. blog-worker's
# WORKSPACE_TOOLS reads the same file at its own build time (an ordinary
# same-repo import there); this is the cross-repo half of that fix.
WORKSPACE_VERBS_JSON = Path.home() / "a2ui-private" / "mcp-worker" / "src" / "workspace-verbs.json"
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
# Teaser Card Carousel (Authoring suite "template #1") draft storage — a
# JSON file per slug, written by manage-carousel.yml's save_carousel.py
# (mirrors DRAFTS_DIR's role for What's Cooking, just a different content
# shape: {slug, hook, middles, cta} instead of markdown+frontmatter).
CAROUSEL_DRAFTS_DIR = Path.home() / "a2ui-private" / "blog-worker" / "posts" / "carousel-drafts"
SINGLE_POST_DRAFTS_DIR = Path.home() / "a2ui-private" / "blog-worker" / "posts" / "single-post-drafts"


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


def _load_carousel_drafts():
    """slug/hook/middles/cta/card-count for each posts/carousel-drafts/*.json,
    for the Teaser Card Carousel page's own in-progress board AND its
    ?slug=... edit-load path (the full hook/middles/cta content ships to
    the browser, not just a summary, so re-opening a draft actually
    repopulates every field rather than just the slug — see
    build_carousel_page's loader IIFE). Same best-effort shape as
    _load_current_drafts: a malformed draft is skipped with a stderr
    warning, never crashes this build."""
    if not CAROUSEL_DRAFTS_DIR.exists():
        return []
    drafts = []
    for path in sorted(CAROUSEL_DRAFTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"gen_authoring: {path.name} invalid ({e}), "
                  f"skipping from carousel draft board", file=sys.stderr)
            continue
        hook = data.get("hook") or {}
        middles = data.get("middles") or []
        cta = data.get("cta") or {}
        drafts.append({
            "slug": path.stem,
            "headline": hook.get("headline", path.stem),
            "card_count": 2 + len(middles),  # hook + middles + cta
            "hook": hook,
            "middles": middles,
            "cta": cta,
        })
    return drafts


def _carousel_board_html(drafts):
    if not drafts:
        return '<p class="hint">Nothing drafted yet.</p>'
    cards = "".join(
        f'<a class="cooking-card" href="/authoring/templates/teaser-card-carousel/?slug={d["slug"]}">'
        f'<div class="cooking-card-title">{d["headline"]}</div>'
        f'<div class="cooking-card-meta">{d["card_count"]} cards</div>'
        f'</a>'
        for d in drafts
    )
    return f'<div class="cooking-board">{cards}</div>'


def _load_single_post_drafts():
    """Same contract as _load_carousel_drafts, for the Single Post template:
    one card per draft instead of hook/middles/cta. Kept as its own store
    (posts/single-post-drafts/) rather than a zero-middle carousel, because
    the two shapes diverge in the form, in the atom role, and in what a
    board row means -- collapsing them would make every consumer branch on
    a card count."""
    if not SINGLE_POST_DRAFTS_DIR.exists():
        return []
    drafts = []
    for path in sorted(SINGLE_POST_DRAFTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"gen_authoring: {path.name} invalid ({e}), "
                  f"skipping from single-post draft board", file=sys.stderr)
            continue
        card = data.get("card") or {}
        drafts.append({
            "slug": path.stem,
            "headline": card.get("headline", path.stem),
            "eyebrow": card.get("eyebrow", ""),
            "variant": data.get("variant", "field_report"),
            "font": data.get("font", "arimo"),
            "card": card,
        })
    return drafts


def _single_post_board_html(drafts):
    if not drafts:
        return '<p class="hint">Nothing drafted yet.</p>'
    cards = "".join(
        f'<a class="cooking-card" href="/authoring/templates/single-post/?slug={d["slug"]}">'
        f'<div class="cooking-card-title">{d["headline"]}</div>'
        f'<div class="cooking-card-meta">{d["eyebrow"] or "single post"}</div>'
        f'</a>'
        for d in drafts
    )
    return f'<div class="cooking-board">{cards}</div>'


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
      <a href="/workspace/">Workspace</a>
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

/* Teaser Card Carousel (template #1) */
.carousel-card-block{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;margin-bottom:14px}
.carousel-card-block .pane-bar button{margin-left:auto}
.carousel-preview{display:flex;align-items:center;gap:14px;padding:14px 16px;border-top:1px solid var(--border);background:var(--code-bg)}
.car-preview-img{width:120px;aspect-ratio:4/5;object-fit:cover;border-radius:8px;border:1px solid var(--border);background:var(--surface-2)}
.car-preview-status{font-family:var(--mono);font-size:11px;color:var(--text-faint)}
.car-media-radio{display:flex;gap:16px;margin-top:5px}
.car-media-radio label{flex-direction:row;align-items:center;gap:6px;font-weight:400;text-transform:none;letter-spacing:normal;font-size:13px;color:var(--text)}
.car-media-radio input{width:auto;margin:0}
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
    <a class="hub-card" href="/workspace/">
      <div class="hub-card-title">Workspace</div>
      <div class="hub-card-desc">The same profile and reading history the MCP Apps surface uses inside Claude — same Cloudflare Access identity, same store. Run the article playbook here via Vertex Gemini, one click, no chat needed.</div>
    </a>
    <a class="hub-card" href="/authoring/posts/">
      <div class="hub-card-title">LinkedIn Posts</div>
      <div class="hub-card-desc">Draft posts, review them against your own tone via Gemini, link them to articles, and track posted engagement — all through the same registry the stats pipe reads.</div>
    </a>
    <a class="hub-card" href="/authoring/templates/teaser-card-carousel/">
      <div class="hub-card-title">Teaser Card Carousel</div>
      <div class="hub-card-desc">Template #1: hook card, N middle cards (each with an optional media slot), CTA card — real atoms rendered server-side, exported as individual PNGs for a LinkedIn carousel post.</div>
    </a>
    <a class="hub-card" href="/authoring/templates/single-post/">
      <div class="hub-card-title">Single Post</div>
      <div class="hub-card-desc">Template #2: one standalone card in the Field Report treatment — hook-sized headline, optional media, its own call to action. For a post that is a picture, not a swipe.</div>
    </a>
  </div>
  <div class="playbook-doc" style="margin-top:36px">{playbook_html}</div>
</div>"""
    return _page_shell("Authoring", body)


def _bundle_hash():
    """Content hash of the generated renderer bundle, stamped into the iframe
    src as a cache-buster — same function, same reasoning, as
    generate_atom_pages.py's own _bundle_hash() (the americano cache-HIT
    incident, 2026-07-11: an edge cache served a STALE bundle behind a fixed
    URL). Not imported from that module — this script's own guard (_guard(),
    above) makes it runnable stand-alone against a public-only checkout, and
    importing generate_atom_pages.py would pull in its own (much heavier)
    top-level work. Small, pure, worth a second copy rather than a coupling.
    """
    import hashlib
    f = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"
    return hashlib.sha1(f.read_bytes()).hexdigest()[:10] if f.exists() else "0"


# The host-adapter script. Modeled DIRECTLY on
# public/surfaces/mcp-apps/play/index.html's proven iframe+postMessage
# pattern — that page already IS "a browser page acting as an MCP Apps host,"
# proven live; this reuses its exact message-handling shape rather than
# inventing a second one. Differences from /play, and why:
#
#   - APP_TOOLS is the account-bound tool set, substituted in at generation
#     time from mcp-worker/src/workspace-verbs.json (a2ui-private) — the
#     SAME file blog-worker's WORKSPACE_TOOLS reads. Used to be a third
#     hand-typed copy of that list (plus a2ui-catalogue's OWN
#     A2UIState.html MCP_VERBS as a fourth, broader one); one of the four
#     drifted silently (2026-08-04, see a2uithoughts.md's "workspace verb
#     parity" entry) before this consolidation.
#   - tools/call proxies to /authoring/api/workspace-tool, not /mcp — the
#     Access-gated, per-reader endpoint, not the public one.
#   - ui/initialize declares displayMode:'fullscreen' unconditionally: the
#     iframe genuinely occupies the whole viewport here (CSS below), so
#     there is no separate mode to negotiate — and it is answered
#     immediately rather than defaulting to 'inline', which would clamp
#     height the workspace does not need clamped.
#   - ui/message has NO chat to hand a draft to on this host, so it is not
#     proxied at all: it is answered IMMEDIATELY (a fast ack, not a long
#     wait — Gemini's own reading can run past the bundle's internal
#     ui/message timeout, which this host does not control and must not
#     race), then /authoring/api/workspace-read is called asynchronously.
#     Progress and failure show in THIS page's own status chip, not through
#     the wired surface's pending/error state, because by the time an
#     answer exists the ack has already resolved that state to "sent".
#     On success the WHOLE view is repainted with the finished reading via
#     a fresh ui/notifications/tool-result — the same one-document
#     replacement every host already does when a stamped reading is
#     rendered. The #ws-home-btn breadcrumb (host-level, outside the
#     iframe) is this host's way back from that; no equivalent exists on a
#     chat host yet (see articles-as-app-views.md for that follow-up).
WORKSPACE_HOST_JS = """
(function () {
  var iframe = document.getElementById('mcp-view');
  var dot = document.getElementById('mcp-status-dot');
  var text = document.getElementById('mcp-status-text');
  function setStatus(cls, msg) {
    dot.className = 'mcp-status-dot' + (cls ? ' ' + cls : '');
    text.textContent = msg;
  }

  // Same list mcp-worker/src/workspace-verbs.json declares — substituted in
  // at generation time (see build_workspace_page()), not hand-typed here.
  // See a2uithoughts.md's "workspace verb parity" entry (2026-08-04): this
  // used to be a fourth hand-synced copy, and one of the four drifted
  // silently.
  var APP_TOOLS = __WORKSPACE_VERBS_JSON__;

  function send(payload) {
    iframe.contentWindow.postMessage({
      jsonrpc: '2.0',
      method: 'ui/notifications/tool-result',
      params: { content: [{ type: 'text', text: 'Workspace' }], structuredContent: payload }
    }, '*');
  }

  var viewReady = false;

  // Read once, at page load, from the page's OWN url — e.g.
  // /workspace/?view=read bookmarks straight into the Article Reader instead
  // of the tool-selector home. Captured before any navigation happens so the
  // #ws-home-btn breadcrumb below (which always means "go home", not
  // "reload whatever the url says") can stay a plain no-arg call.
  var initialView = new URLSearchParams(window.location.search).get('view');
  // /workspace/?reading=<id> opens ONE saved reading directly, decoded
  // server-side from its stored payload — no GAS ?p= link, no size ceiling,
  // the exact mechanism a history row's one-click reopen already uses
  // (mcp:export_reading). Takes priority over ?view if somehow both are
  // given: naming a specific reading is a strictly more specific request
  // than naming a screen.
  var initialReadingId = new URLSearchParams(window.location.search).get('reading');

  function loadWorkspace(view) {
    setStatus('', 'Opening your workspace…');
    fetch('/authoring/api/workspace-tool', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name: 'open_workspace', arguments: view ? { view: view } : {} })
    })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        if (!resp.ok) { setStatus('err', 'Could not open workspace: ' + resp.error); return; }
        setStatus('live', 'Workspace open');
        send(resp.structuredContent);
      })
      .catch(function (e) { setStatus('err', String(e && e.message || e)); });
  }

  function openReading(id) {
    setStatus('', 'Opening your reading…');
    fetch('/authoring/api/workspace-tool', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name: 'export_reading', arguments: { id: id, format: 'surface' } })
    })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        if (!resp.ok) { setStatus('err', 'Could not open reading: ' + resp.error); return; }
        var sc = resp.structuredContent;
        // 'surface' format spreads the payload at the top level ONLY on
        // success (createSurface/blocks present, same shape paint_result
        // itself checks) — a miss comes back as {available, exported:false,
        // reason} instead. Mirror that check rather than assume the shape.
        if (!sc || (!sc.blocks && !sc.createSurface)) {
          setStatus('err', (sc && sc.reason) || 'That reading is not available.');
          return;
        }
        setStatus('live', 'Reading open');
        send(sc);
      })
      .catch(function (e) { setStatus('err', String(e && e.message || e)); });
  }

  // The one persistent breadcrumb: works from ANY state — a reading, a
  // sub-view, an error — because it lives outside the iframe and just
  // re-runs the same boot call view:'home' defaults to.
  document.getElementById('ws-home-btn').addEventListener('click', function () {
    loadWorkspace();
  });

  window.addEventListener('message', function (ev) {
    if (ev.source !== iframe.contentWindow) return;
    var msg = ev.data;
    if (!msg || msg.jsonrpc !== '2.0') return;

    if (msg.method === 'ui/initialize') {
      iframe.contentWindow.postMessage({
        jsonrpc: '2.0', id: msg.id,
        result: {
          protocolVersion: '2026-01-26',
          hostContext: { theme: 'dark', displayMode: 'fullscreen', availableDisplayModes: ['fullscreen'] },
          capabilities: { serverTools: {}, logging: {} }
        }
      }, '*');
      return;
    }

    if (msg.method === 'ui/notifications/initialized') {
      viewReady = true;
      setStatus('', 'View ready…');
      if (initialReadingId) { openReading(initialReadingId); } else { loadWorkspace(initialView); }
      return;
    }

    // Already fullscreen unconditionally (see header comment) — any request
    // is granted immediately, never negotiated.
    if (msg.method === 'ui/request-display-mode' && msg.id !== undefined) {
      iframe.contentWindow.postMessage({ jsonrpc: '2.0', id: msg.id, result: { mode: 'fullscreen' } }, '*');
      return;
    }

    if (msg.method === 'tools/call' && msg.id !== undefined) {
      var toolName = msg.params && msg.params.name;
      // compose_surface (Composer, 2026-08-05) is NOT a real mcp-worker tool
      // — it has no entry in workspace-verbs.json/APP_TOOLS on purpose, so
      // that allowlist stays scoped to tools that genuinely exist on the
      // other end of the generic proxy below. Its generation step needs
      // Vertex credentials, which only THIS worker (blog-worker) has —
      // mcp-worker has none — so it is handled entirely host-side,
      // special-cased here rather than routed through the generic
      // /authoring/api/workspace-tool proxy.
      //
      // ACK-THEN-NOTIFY, not a plain awaited tools/call (2026-08-06 rewrite).
      // This used to await the whole fetch before answering — relying on the
      // bundle's own client-side tools/call ceiling (raised 15s -> 120s the
      // same day) to outlast a real Gemini generation. It still didn't:
      // found live, repeatedly, that generation (plus a validation-retry
      // round trip) can genuinely exceed even 120s, and there is no fixed
      // ceiling worth picking — any one is eventually wrong. Mirrors
      // ui/message's OWN proven pattern just below instead: ack near-
      // instantly with a stub that is neither an error NOR paintable (so the
      // wired action's own paint_result guard — `r.data.type ===
      // 'a2ui_wired_surface' || r.data.blocks || r.data.createSurface`,
      // A2UIState.html — never fires on it), track progress in THIS page's
      // own status chip instead of the wired surface's pending state (which
      // the ack has already resolved), and replace the WHOLE view via a
      // fresh, independent send() once the real result is ready. Removes the
      // client-side timeout from this path entirely — the only remaining
      // ceiling is however long a reader is willing to watch the status chip.
      if (toolName === 'compose_surface') {
        iframe.contentWindow.postMessage(
          { jsonrpc: '2.0', id: msg.id,
            result: { structuredContent: { ok: true, composing: true } } }, '*');
        setStatus('', 'Composing — this can take a while for a real Gemini call…');
        fetch('/authoring/api/workspace-compose', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify((msg.params && msg.params.arguments) || {})
        })
          .then(function (r) { return r.json(); })
          .then(function (resp) {
            if (!resp.ok) { setStatus('err', 'Compose failed: ' + resp.error); return; }
            setStatus('live', resp.corrected
              ? 'Composed (auto-corrected) — analysed by ' + resp.analysed_by
              : 'Composed — analysed by ' + resp.analysed_by);
            send(resp.payload);
          })
          .catch(function (e) { setStatus('err', String(e && e.message || e)); });
        return;
      }
      if (APP_TOOLS.indexOf(toolName) === -1) {
        iframe.contentWindow.postMessage({
          jsonrpc: '2.0', id: msg.id,
          error: { code: -32601, message: 'tool not app-callable from this host: ' + toolName }
        }, '*');
        return;
      }
      fetch('/authoring/api/workspace-tool', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ name: toolName, arguments: (msg.params && msg.params.arguments) || {} })
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (resp.ok) {
            iframe.contentWindow.postMessage(
              { jsonrpc: '2.0', id: msg.id, result: { structuredContent: resp.structuredContent } }, '*');
          } else {
            iframe.contentWindow.postMessage(
              { jsonrpc: '2.0', id: msg.id, error: { code: -32603, message: resp.error || 'tool call failed' } }, '*');
          }
        })
        .catch(function (e) {
          iframe.contentWindow.postMessage(
            { jsonrpc: '2.0', id: msg.id, error: { code: -32603, message: String(e && e.message || e) } }, '*');
        });
      return;
    }

    if (msg.method === 'ui/message' && msg.id !== undefined) {
      var parts = msg.params && msg.params.content;
      var textMsg = Array.isArray(parts) ? parts.map(function (p) { return p.text || ''; }).join('\\n') : '';
      if (!textMsg.trim()) {
        iframe.contentWindow.postMessage(
          { jsonrpc: '2.0', id: msg.id, error: { code: -32602, message: 'empty message' } }, '*');
        return;
      }
      // ACK IMMEDIATELY. See header comment: this host does not race the
      // bundle's own ui/message timeout with however long Gemini takes.
      iframe.contentWindow.postMessage({ jsonrpc: '2.0', id: msg.id, result: {} }, '*');
      setStatus('', 'Reading via Gemini — this can take a while for a real article…');
      fetch('/authoring/api/workspace-read', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ text: textMsg })
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (!resp.ok) { setStatus('err', 'Reading failed: ' + resp.error); return; }
          setStatus('live', resp.save_reading_error
            ? 'Reading complete (NOT saved to history: ' + resp.save_reading_error + ')'
            : 'Reading complete — analysed by ' + resp.analysed_by);
          send(resp.payload);
        })
        .catch(function (e) { setStatus('err', String(e && e.message || e)); });
      return;
    }
  });

  setTimeout(function () {
    if (!viewReady) setStatus('err', 'No response from view — check console');
  }, 8000);
})();
"""


def build_workspace_page():
    bundle_src = "/surfaces/mcp-apps/renderer-bundle.html?v=" + _bundle_hash()
    workspace_verbs = json.loads(WORKSPACE_VERBS_JSON.read_text(encoding="utf-8"))
    host_js = WORKSPACE_HOST_JS.replace(
        "__WORKSPACE_VERBS_JSON__", json.dumps(workspace_verbs))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Workspace — A2UI Catalog (full)</title>
<style>
:root{{--bg:#0a0e17;--card:#111826;--border:#1f2937;--text:#e6edf3;--muted:#8b949e;--indigo:#7c9cff;--green:#3fb950;--red:#f85149}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:var(--bg);font-family:ui-monospace,SFMono-Regular,Menlo,'JetBrains Mono',monospace}}
#mcp-view{{position:fixed;inset:0;width:100%;height:100%;border:0;background:#fff}}
.ws-bar{{position:fixed;top:12px;left:12px;right:12px;display:flex;gap:10px;align-items:center;z-index:10;pointer-events:none}}
.ws-bar>*{{pointer-events:auto}}
.ws-chip{{display:inline-flex;align-items:center;gap:8px;background:rgba(10,14,23,.9);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:999px;padding:7px 16px;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);text-decoration:none}}
a.ws-chip:hover,button.ws-chip:hover{{border-color:var(--indigo);color:var(--indigo)}}
button.ws-chip{{font:inherit;letter-spacing:inherit;cursor:pointer}}
.mcp-status-dot{{width:8px;height:8px;border-radius:50%;background:var(--muted);flex-shrink:0;transition:background .2s}}
.mcp-status-dot.live{{background:var(--green);box-shadow:0 0 8px rgba(63,185,80,.6)}}
.mcp-status-dot.err{{background:var(--red)}}
</style>
</head>
<body>
  <iframe id="mcp-view" sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation" src="{bundle_src}" title="A2UI Workspace"></iframe>
  <div class="ws-bar">
    <a class="ws-chip" href="/">← A2UI Catalog</a>
    <!-- Lives OUTSIDE the iframe, so it survives no matter what's painted
         inside it — a reading, History, Profile. paint_result only ever
         replaces the iframe's OWN content; nothing inside a reading's v1.0
         surface can navigate the workspace, so a host-level control is the
         only place this can live (Curtis, 2026-08-04: "we did not add
         breadcrumb back to the workspace homepage in a created artifact"). -->
    <button class="ws-chip" id="ws-home-btn" type="button">🏠 Workspace</button>
    <span class="ws-chip"><span class="mcp-status-dot" id="mcp-status-dot"></span><span id="mcp-status-text">Connecting…</span></span>
  </div>
<script>
{host_js}
</script>
</body>
</html>
"""


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


def build_carousel_page(carousel_drafts):
    """Teaser Card Carousel — Authoring suite "template #1". Fixed hook
    card first, fixed cta card last, N variable middle cards in between
    (Curtis's call: card count driven by how much an article has to say,
    not a fixed 5). 100% atom-based: every preview/export image is a real
    promo_carousel_card block rendered through cloud-run-renderer's /render
    (via blog-worker/src/carousel.js), never hand-authored HTML/CSS for the
    cards themselves — this page only collects the fields."""
    drafts_json = json.dumps(carousel_drafts)

    body = f"""<div class="authoring-top">
  <div class="gate-note">🔒 full.a2uicatalog.ai only</div>
  <h1>Teaser Card Carousel</h1>
  <p class="sub">Hook card, N middle cards (each with an optional media slot), CTA card — every card is a real promo_carousel_card atom, rendered server-side, exported as individual PNGs for a LinkedIn carousel post.</p>
</div>
<div class="section">
  <h2 style="font-size:1.05rem;margin:0 0 12px">Drafted ({len(carousel_drafts)})</h2>
  {_carousel_board_html(carousel_drafts)}
</div>
<div class="section" style="padding-top:0">
  <h2 style="font-size:1.05rem;margin:24px 0 12px">Build a carousel</h2>
  <div class="fm-fields" style="grid-template-columns:1fr;margin-bottom:16px">
    <label>Slug (for saving/loading this draft) <input id="carSlug" type="text" placeholder="e.g. ge-print-rendering-workaround"></label>
  </div>
  <div class="fm-fields" style="margin-bottom:16px">
    <label>Card style
      <select id="carVariant">
        <option value="field_report">Field report — amber, blueprint grid, fills the frame</option>
        <option value="glow">Glow — cyan, corner glow, centred</option>
      </select>
    </label>
    <label>Headline font
      <select id="carFont">
        <option value="arimo">Arimo — Arial-metric (default)</option>
        <option value="lato">Lato — chunkiest, true Black 900</option>
        <option value="noto">Noto Sans — humanist</option>
      </select>
    </label>
  </div>

  <div class="carousel-card-block" data-role="hook">
    <div class="pane-bar"><span>Hook card</span></div>
    <div class="fm-fields">
      <label>Eyebrow <input class="car-eyebrow" type="text" placeholder="Series / label"></label>
      <label>Headline <input class="car-headline" type="text" placeholder="The hook line"></label>
      <label style="grid-column:1/-1">Body <textarea class="car-body" rows="2" placeholder="Supporting line (optional)"></textarea></label>
      <label style="grid-column:1/-1">Media on this card?
        <span class="car-media-radio">
          <label><input type="radio" name="media-hook" class="car-has-media" value="yes"> Yes</label>
          <label><input type="radio" name="media-hook" class="car-no-media" value="no" checked> No — text only</label>
        </span>
      </label>
      <label class="car-media-wrap" style="grid-column:1/-1;display:none">Media URL (a site-relative /gallery/... path is fine; an animated GIF stays animated in the GIF export) <input class="car-media" type="text" placeholder="/gallery/ge-primitives/d2-architect-live.gif"></label>
      <label class="car-media-wrap" style="display:none">Trim clip to (seconds) <input class="car-media-secs" type="number" step="0.5" min="0.5" placeholder="whole clip"></label>
      <label>Seconds on screen <input class="car-duration" type="number" step="0.1" min="0.2" max="30" placeholder="3.0 (default)"></label>
    </div>
    <div class="carousel-preview"><img class="car-preview-img" alt="Card preview"><div class="car-preview-status"></div></div>
  </div>

  <div id="carMiddles"></div>
  <button class="copy-btn" id="carAddMiddle" type="button" style="margin:12px 0">+ ADD MIDDLE CARD</button>

  <div class="carousel-card-block" data-role="cta">
    <div class="pane-bar"><span>CTA card</span></div>
    <div class="fm-fields">
      <label>Eyebrow <input class="car-eyebrow" type="text" placeholder="e.g. What this surfaced"></label>
      <label>Headline <input class="car-headline" type="text" placeholder="The closing line"></label>
      <label style="grid-column:1/-1">Body <textarea class="car-body" rows="2" placeholder="Supporting line (optional)"></textarea></label>
      <label style="grid-column:1/-1">Call-to-action button (optional) <input class="car-cta-label" type="text" placeholder="e.g. Read Part 2 →"></label>
      <label style="grid-column:1/-1">Media on this card?
        <span class="car-media-radio">
          <label><input type="radio" name="media-cta" class="car-has-media" value="yes"> Yes</label>
          <label><input type="radio" name="media-cta" class="car-no-media" value="no" checked> No — text only</label>
        </span>
      </label>
      <label class="car-media-wrap" style="grid-column:1/-1;display:none">Media URL (a site-relative /gallery/... path is fine; an animated GIF stays animated in the GIF export) <input class="car-media" type="text" placeholder="/gallery/ge-primitives/d2-architect-live.gif"></label>
      <label class="car-media-wrap" style="display:none">Trim clip to (seconds) <input class="car-media-secs" type="number" step="0.5" min="0.5" placeholder="whole clip"></label>
      <label>Seconds on screen <input class="car-duration" type="number" step="0.1" min="0.2" max="30" placeholder="4.5 (default)"></label>
    </div>
    <div class="carousel-preview"><img class="car-preview-img" alt="Card preview"><div class="car-preview-status"></div></div>
  </div>

  <div class="childlist-strip" style="display:flex;align-items:center;gap:10px;margin-top:16px;border-top:1px solid var(--border)">
    <button class="copy-btn" id="carSaveBtn" type="button">SAVE DRAFT</button>
    <button class="copy-btn" id="carExportBtn" type="button">EXPORT ALL AS PNG</button>
    <button class="copy-btn" id="carExportGifBtn" type="button">EXPORT AS GIF</button>
    <span id="carStatus" style="color:var(--text-faint)"></span>
  </div>
  <p class="hint" id="carCostEstimate" style="margin-top:6px"></p>
</div>"""

    script = f"""
var CAROUSEL_DRAFTS = {drafts_json};
var middleCount = 0;

function carPreviewDebounced(blockEl){{
  clearTimeout(blockEl._previewTimer);
  blockEl._previewTimer = setTimeout(function(){{ carRenderPreview(blockEl); }}, 800);
}}

function carCardFromBlock(blockEl, role, position){{
  var yes = blockEl.querySelector('.car-has-media');
  var card = {{
    type: 'promo_carousel_card',
    role: role,
    // Deck-level look, stamped onto every card: the atom carries variant/font
    // per block (one card is one render), so the deck selects have to be read
    // here or preview and export silently fall back to the atom defaults while
    // the saved draft says otherwise.
    variant: document.getElementById('carVariant').value,
    font: document.getElementById('carFont').value,
    eyebrow: blockEl.querySelector('.car-eyebrow').value,
    position: position,
    headline: blockEl.querySelector('.car-headline').value,
    body: blockEl.querySelector('.car-body').value,
    // Explicit false (not just an empty media_url) is what tells the
    // renderer to omit the slot entirely and centre the text.
    has_media: !!(yes && yes.checked),
    media_url: blockEl.querySelector('.car-media') ? blockEl.querySelector('.car-media').value : ''
  }};
  var msecs = blockEl.querySelector('.car-media-secs');
  if (msecs && msecs.value.trim()) card.media_max_ms = Math.round(parseFloat(msecs.value) * 1000);
  var ctaLabel = blockEl.querySelector('.car-cta-label');
  if (ctaLabel) card.cta_label = ctaLabel.value;
  // Seconds in the UI, milliseconds on the wire. Blank means "use the
  // role default", so only send the field when it's actually set.
  var dur = blockEl.querySelector('.car-duration');
  if (dur && dur.value.trim()) card.duration_ms = Math.round(parseFloat(dur.value) * 1000);
  return card;
}}

function carRenderPreview(blockEl){{
  var role = blockEl.dataset.role;
  var card = carCardFromBlock(blockEl, role, '');
  if (!card.headline.trim()) return;
  var img = blockEl.querySelector('.car-preview-img');
  var status = blockEl.querySelector('.car-preview-status');
  status.textContent = 'Rendering...';
  fetch('/authoring/api/carousel-preview', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{card: card}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      if (res.ok && res.data.png_base64) {{
        img.src = 'data:image/png;base64,' + res.data.png_base64;
        status.textContent = '';
      }} else {{
        status.textContent = 'FAILED: ' + (res.data.error || 'unknown error');
      }}
    }})
    .catch(function(e){{ status.textContent = 'FAILED: ' + e.message; }});
}}

function carWireBlock(blockEl){{
  blockEl.querySelectorAll('.car-eyebrow,.car-headline,.car-body,.car-media,.car-media-secs,.car-cta-label,.car-duration').forEach(function(el){{
    el.addEventListener('input', function(){{ carPreviewDebounced(blockEl); }});
  }});
  blockEl.querySelectorAll('.car-has-media,.car-no-media').forEach(function(el){{
    el.addEventListener('change', function(){{
      var on = blockEl.querySelector('.car-has-media').checked;
      blockEl.querySelectorAll('.car-media-wrap').forEach(function(w){{ w.style.display = on ? '' : 'none'; }});
      carPreviewDebounced(blockEl);
    }});
  }});
}}

function carAddMiddle(prefill){{
  middleCount++;
  var el = document.createElement('div');
  el.className = 'carousel-card-block';
  el.dataset.role = 'middle';
  el.innerHTML =
    '<div class="pane-bar"><span>Middle card ' + middleCount + '</span>' +
    '<button class="copy-btn" type="button" data-remove="1">REMOVE</button></div>' +
    '<div class="fm-fields">' +
    '<label>Eyebrow <input class="car-eyebrow" type="text" placeholder="Section label"></label>' +
    '<label>Headline <input class="car-headline" type="text" placeholder="The point of this card"></label>' +
    '<label style="grid-column:1/-1">Body <textarea class="car-body" rows="2" placeholder="Supporting line (optional)"></textarea></label>' +
    '<label style="grid-column:1/-1">Media on this card?' +
    '<span class="car-media-radio">' +
    '<label><input type="radio" name="media-' + middleCount + '" class="car-has-media" value="yes"> Yes</label>' +
    '<label><input type="radio" name="media-' + middleCount + '" class="car-no-media" value="no" checked> No — centre the text</label>' +
    '</span></label>' +
    '<label>Seconds on screen <input class="car-duration" type="number" step="0.1" min="0.2" max="30" placeholder="2.2 (default)"></label>' +
    '<label class="car-media-wrap" style="grid-column:1/-1;display:none">Media URL (a site-relative /gallery/... path is fine; an animated GIF stays animated in the GIF export) <input class="car-media" type="text" placeholder="/gallery/ge-print-rendering/workspace-status-live.gif"></label>' +
    '<label class="car-media-wrap" style="display:none">Trim clip to (seconds) <input class="car-media-secs" type="number" step="0.5" min="0.5" placeholder="whole clip"></label>' +
    '</div>' +
    '<div class="carousel-preview"><img class="car-preview-img" alt="Card preview"><div class="car-preview-status"></div></div>';
  el.querySelector('[data-remove]').addEventListener('click', function(){{
    el.remove();
    carRenumberMiddles();
    carUpdateCostEstimate();
  }});
  document.getElementById('carMiddles').appendChild(el);
  carWireBlock(el);
  if (prefill) {{
    el.querySelector('.car-eyebrow').value = prefill.eyebrow || '';
    el.querySelector('.car-headline').value = prefill.headline || '';
    el.querySelector('.car-body').value = prefill.body || '';
    el.querySelector('.car-media').value = prefill.media_url || '';
    if (prefill.duration_ms) el.querySelector('.car-duration').value = prefill.duration_ms / 1000;
    if (prefill.media_max_ms) el.querySelector('.car-media-secs').value = prefill.media_max_ms / 1000;
    // Older drafts predate has_media; infer from whether a url was saved,
    // which matches what those drafts actually rendered at the time.
    var wantsMedia = prefill.has_media === undefined
      ? !!prefill.media_url : !!prefill.has_media;
    el.querySelector('.car-has-media').checked = wantsMedia;
    el.querySelector('.car-no-media').checked = !wantsMedia;
    el.querySelector('.car-media-wrap').style.display = wantsMedia ? '' : 'none';
    carRenderPreview(el);
  }}
  carUpdateCostEstimate();
  return el;
}}

function carRenumberMiddles(){{
  var blocks = document.querySelectorAll('#carMiddles .carousel-card-block');
  blocks.forEach(function(el, i){{ el.querySelector('.pane-bar span').textContent = 'Middle card ' + (i + 1); }});
}}

// Real Cloud Run compute cost, not a guess — measured live 2026-07-26
// (3 back-to-back single-card renders at full 1080px export width against
// the actual deployed a2ui-atom-renderer, ~2.9-3.0s each) and combined
// with Cloud Run's published per-second gen2 pricing (1 vCPU + 1GiB
// allocated): $0.000024/vCPU-second + $0.0000025/GiB-second. GIF export
// additionally pays a per-deck stitch overhead (frame diffing, resizing,
// GIF encoding in cloud_run_renderer's _render_deck_gif) estimated at
// ~2s flat on top of the per-frame renders. Both numbers are Cloud Run
// COMPUTE only -- no Vertex AI/LLM call happens on export, and Cloud
// Run's free tier (180,000 vCPU-seconds + 360,000 GiB-seconds/month) is
// far beyond what any realistic personal-authoring usage would reach, so
// this is honest transparency, not a meaningful spend warning.
var CAR_SECONDS_PER_CARD = 3.0;
var CAR_GIF_STITCH_OVERHEAD_SECONDS = 2.0;
var CAR_COST_PER_SECOND = 0.000024 + 0.0000025;  // 1 vCPU + 1 GiB, gen2 rate

function carFormatCost(dollars){{
  return dollars < 0.0001 ? '<$0.0001' : '$' + dollars.toFixed(4);
}}

function carUpdateCostEstimate(){{
  var n = 2 + document.querySelectorAll('#carMiddles .carousel-card-block').length;
  var pngSeconds = n * CAR_SECONDS_PER_CARD;
  var gifSeconds = pngSeconds + CAR_GIF_STITCH_OVERHEAD_SECONDS;
  var pngCost = pngSeconds * CAR_COST_PER_SECOND;
  var gifCost = gifSeconds * CAR_COST_PER_SECOND;
  document.getElementById('carCostEstimate').textContent =
    'Estimated Cloud Run compute cost for ' + n + ' card(s): ' +
    carFormatCost(pngCost) + ' as PNGs, ' + carFormatCost(gifCost) + ' as GIF ' +
    '(real Cloud Run compute pricing; well within the monthly free tier for normal use).';
}}

function carAssembleCards(){{
  var hookEl = document.querySelector('.carousel-card-block[data-role="hook"]');
  var ctaEl = document.querySelector('.carousel-card-block[data-role="cta"]');
  var middleEls = document.querySelectorAll('#carMiddles .carousel-card-block');
  var total = 2 + middleEls.length;
  var cards = [];
  cards.push(carCardFromBlock(hookEl, 'hook', '1 / ' + total));
  middleEls.forEach(function(el, i){{ cards.push(carCardFromBlock(el, 'middle', (i + 2) + ' / ' + total)); }});
  cards.push(carCardFromBlock(ctaEl, 'cta', total + ' / ' + total));
  return cards;
}}

document.getElementById('carAddMiddle').addEventListener('click', function(){{ carAddMiddle(null); }});
carWireBlock(document.querySelector('.carousel-card-block[data-role="hook"]'));
carWireBlock(document.querySelector('.carousel-card-block[data-role="cta"]'));
carUpdateCostEstimate();

['carVariant','carFont'].forEach(function(id){{
  document.getElementById(id).addEventListener('change', function(){{
    document.querySelectorAll('.carousel-card-block').forEach(carRenderPreview);
  }});
}});

document.getElementById('carSaveBtn').addEventListener('click', function(){{
  var slug = document.getElementById('carSlug').value.trim();
  var status = document.getElementById('carStatus');
  if (!slug || !/^[a-z0-9-]+$/.test(slug)) {{ status.textContent = 'Slug must be lowercase-hyphenated.'; return; }}
  var hookEl = document.querySelector('.carousel-card-block[data-role="hook"]');
  var ctaEl = document.querySelector('.carousel-card-block[data-role="cta"]');
  var middleEls = document.querySelectorAll('#carMiddles .carousel-card-block');
  var mtrim = function(el){{ var m = el.querySelector('.car-media-secs'); return m && m.value.trim() ? Math.round(parseFloat(m.value) * 1000) : null; }};
  var secs = function(el){{ var d = el.querySelector('.car-duration'); return d && d.value.trim() ? Math.round(parseFloat(d.value) * 1000) : null; }};
  var hook = {{eyebrow: hookEl.querySelector('.car-eyebrow').value, headline: hookEl.querySelector('.car-headline').value, body: hookEl.querySelector('.car-body').value, duration_ms: secs(hookEl),
    has_media: hookEl.querySelector('.car-has-media').checked, media_url: hookEl.querySelector('.car-media').value, media_max_ms: mtrim(hookEl)}};
  var cta = {{eyebrow: ctaEl.querySelector('.car-eyebrow').value, headline: ctaEl.querySelector('.car-headline').value, body: ctaEl.querySelector('.car-body').value, cta_label: ctaEl.querySelector('.car-cta-label').value, duration_ms: secs(ctaEl),
    has_media: ctaEl.querySelector('.car-has-media').checked, media_url: ctaEl.querySelector('.car-media').value, media_max_ms: mtrim(ctaEl)}};
  var middles = [];
  middleEls.forEach(function(el){{
    middles.push({{eyebrow: el.querySelector('.car-eyebrow').value, headline: el.querySelector('.car-headline').value, body: el.querySelector('.car-body').value, has_media: el.querySelector('.car-has-media').checked, media_url: el.querySelector('.car-media').value, duration_ms: secs(el), media_max_ms: mtrim(el)}});
  }});
  status.textContent = 'Saving...';
  fetch('/authoring/api/carousel-save', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{slug: slug, hook: hook, middles: middles, cta: cta,
      variant: document.getElementById('carVariant').value,
      font: document.getElementById('carFont').value}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      status.textContent = res.ok ? 'Saved — check GitHub for the new PR shortly.' : 'FAILED: ' + (res.data.error || 'unknown error');
    }})
    .catch(function(e){{ status.textContent = 'FAILED: ' + e.message; }});
}});

document.getElementById('carExportBtn').addEventListener('click', function(){{
  var status = document.getElementById('carStatus');
  var btn = document.getElementById('carExportBtn');
  var cards = carAssembleCards();
  if (!cards[0].headline.trim() || !cards[cards.length - 1].headline.trim()) {{
    status.textContent = 'Hook and CTA cards both need a headline before exporting.';
    return;
  }}
  btn.disabled = true; btn.textContent = 'RENDERING...';
  status.textContent = 'Rendering ' + cards.length + ' card(s) at full export size (est. ' +
    carFormatCost(cards.length * CAR_SECONDS_PER_CARD * CAR_COST_PER_SECOND) + ') — this can take a while...';
  fetch('/authoring/api/carousel-export', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{cards: cards}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      btn.disabled = false; btn.textContent = 'EXPORT ALL AS PNG';
      if (!res.ok) {{ status.textContent = 'FAILED: ' + (res.data.error || 'unknown error'); return; }}
      res.data.images.forEach(function(img){{
        var a = document.createElement('a');
        a.href = 'data:image/png;base64,' + img.png_base64;
        a.download = img.filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }});
      status.textContent = 'Exported ' + res.data.images.length + ' image(s) — check your downloads.';
    }})
    .catch(function(e){{
      btn.disabled = false; btn.textContent = 'EXPORT ALL AS PNG';
      status.textContent = 'FAILED: ' + e.message;
    }});
}});

document.getElementById('carExportGifBtn').addEventListener('click', function(){{
  var status = document.getElementById('carStatus');
  var btn = document.getElementById('carExportGifBtn');
  var cards = carAssembleCards();
  if (!cards[0].headline.trim() || !cards[cards.length - 1].headline.trim()) {{
    status.textContent = 'Hook and CTA cards both need a headline before exporting.';
    return;
  }}
  if (cards.length > 12) {{
    status.textContent = 'Too many cards for one GIF (' + cards.length + ', max 12) — use EXPORT ALL AS PNG instead.';
    return;
  }}
  btn.disabled = true; btn.textContent = 'RENDERING...';
  status.textContent = 'Rendering ' + cards.length + ' card(s) into one animated GIF (est. ' +
    carFormatCost((cards.length * CAR_SECONDS_PER_CARD + CAR_GIF_STITCH_OVERHEAD_SECONDS) * CAR_COST_PER_SECOND) +
    ') — this can take a while...';
  fetch('/authoring/api/carousel-export-gif', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{cards: cards}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      btn.disabled = false; btn.textContent = 'EXPORT AS GIF';
      if (!res.ok) {{ status.textContent = 'FAILED: ' + (res.data.error || 'unknown error'); return; }}
      var a = document.createElement('a');
      a.href = 'data:image/gif;base64,' + res.data.gif_base64;
      a.download = (document.getElementById('carSlug').value.trim() || 'carousel') + '.gif';
      document.body.appendChild(a);
      a.click();
      a.remove();
      status.textContent = 'Exported animated GIF — check your downloads. Note: this crops all cards to a shared frame, unlike the individual PNGs — for the actual LinkedIn carousel upload, use EXPORT ALL AS PNG.';
    }})
    .catch(function(e){{
      btn.disabled = false; btn.textContent = 'EXPORT AS GIF';
      status.textContent = 'FAILED: ' + e.message;
    }});
}});

// Load an existing draft if ?slug=... is present (from the board above).
// CAROUSEL_DRAFTS carries each draft's full hook/middles/cta content, not
// just the board summary, so this actually repopulates every field —
// Save then overwrites the same slug's file in place (save_carousel.py
// always writes to posts/carousel-drafts/<slug>.json keyed by slug).
(function(){{
  var params = new URLSearchParams(window.location.search);
  var slug = params.get('slug');
  if (!slug) return;
  var draft = null;
  for (var i = 0; i < CAROUSEL_DRAFTS.length; i++) {{ if (CAROUSEL_DRAFTS[i].slug === slug) {{ draft = CAROUSEL_DRAFTS[i]; break; }} }}
  document.getElementById('carSlug').value = slug;
  if (draft && draft.variant) document.getElementById('carVariant').value = draft.variant;
  if (draft && draft.font) document.getElementById('carFont').value = draft.font;
  if (!draft) {{
    document.getElementById('carStatus').textContent = 'No saved draft found for slug "' + slug + '".';
    return;
  }}

  var hookEl = document.querySelector('.carousel-card-block[data-role="hook"]');
  hookEl.querySelector('.car-eyebrow').value = draft.hook.eyebrow || '';
  hookEl.querySelector('.car-headline').value = draft.hook.headline || '';
  hookEl.querySelector('.car-body').value = draft.hook.body || '';
  if (draft.hook.duration_ms) hookEl.querySelector('.car-duration').value = draft.hook.duration_ms / 1000;
  if (draft.hook.media_max_ms) hookEl.querySelector('.car-media-secs').value = draft.hook.media_max_ms / 1000;
  hookEl.querySelector('.car-media').value = draft.hook.media_url || '';
  var hookMedia = !!draft.hook.has_media;
  hookEl.querySelector('.car-has-media').checked = hookMedia;
  hookEl.querySelector('.car-no-media').checked = !hookMedia;
  hookEl.querySelectorAll('.car-media-wrap').forEach(function(w){{ w.style.display = hookMedia ? '' : 'none'; }});
  carRenderPreview(hookEl);

  var ctaEl = document.querySelector('.carousel-card-block[data-role="cta"]');
  ctaEl.querySelector('.car-eyebrow').value = draft.cta.eyebrow || '';
  ctaEl.querySelector('.car-headline').value = draft.cta.headline || '';
  ctaEl.querySelector('.car-body').value = draft.cta.body || '';
  ctaEl.querySelector('.car-cta-label').value = draft.cta.cta_label || '';
  if (draft.cta.duration_ms) ctaEl.querySelector('.car-duration').value = draft.cta.duration_ms / 1000;
  if (draft.cta.media_max_ms) ctaEl.querySelector('.car-media-secs').value = draft.cta.media_max_ms / 1000;
  ctaEl.querySelector('.car-media').value = draft.cta.media_url || '';
  var ctaMedia = !!draft.cta.has_media;
  ctaEl.querySelector('.car-has-media').checked = ctaMedia;
  ctaEl.querySelector('.car-no-media').checked = !ctaMedia;
  ctaEl.querySelectorAll('.car-media-wrap').forEach(function(w){{ w.style.display = ctaMedia ? '' : 'none'; }});
  carRenderPreview(ctaEl);

  draft.middles.forEach(function(m){{ carAddMiddle(m); }});

  document.getElementById('carStatus').textContent =
    'Loaded "' + slug + '" (' + draft.card_count + ' cards) — Save overwrites this same draft.';
}})();
"""
    return _page_shell("Teaser Card Carousel", body, script)


def build_single_post_page(single_post_drafts):
    """Single Post -- Authoring suite "template #2". One standalone card in
    the Field Report treatment: no deck, no position tag, so it carries a
    hook-sized headline AND its own call-to-action button (the atom's
    role='single'). Deliberately reuses the carousel's Worker routes --
    /carousel-preview takes one card already, and /carousel-export takes a
    list, which a one-element list satisfies -- so this template adds a
    form and a draft store, not a parallel render path."""
    drafts_json = json.dumps(single_post_drafts)

    body = f"""<div class="authoring-top">
  <div class="gate-note">&#128274; full.a2uicatalog.ai only</div>
  <h1>Single Post</h1>
  <p class="sub">One card, standing on its own — a real promo_carousel_card atom at role=single, rendered server-side and exported as a PNG (or a GIF, if its media animates).</p>
</div>
<div class="section">
  <h2 style="font-size:1.05rem;margin:0 0 12px">Drafted ({len(single_post_drafts)})</h2>
  {_single_post_board_html(single_post_drafts)}
</div>
<div class="section" style="padding-top:0">
  <h2 style="font-size:1.05rem;margin:24px 0 12px">Build a post</h2>
  <div class="fm-fields" style="grid-template-columns:1fr;margin-bottom:16px">
    <label>Slug (for saving/loading this draft) <input id="spSlug" type="text" placeholder="e.g. chat-print-channel-launch"></label>
  </div>
  <div class="fm-fields" style="margin-bottom:16px">
    <label>Card style
      <select id="spVariant">
        <option value="field_report">Field report — amber, blueprint grid, fills the frame</option>
        <option value="glow">Glow — cyan, corner glow, centred</option>
      </select>
    </label>
    <label>Headline font
      <select id="spFont">
        <option value="arimo">Arimo — Arial-metric (default)</option>
        <option value="lato">Lato — chunkiest, true Black 900</option>
        <option value="noto">Noto Sans — humanist</option>
      </select>
    </label>
  </div>

  <div class="carousel-card-block" data-role="single">
    <div class="pane-bar"><span>The card</span></div>
    <div class="fm-fields">
      <label>Eyebrow <input class="car-eyebrow" type="text" placeholder="e.g. FIELD REPORT &middot; GOOGLE CHAT"></label>
      <label>Headline <input class="car-headline" type="text" placeholder="The one line this post is about"></label>
      <label style="grid-column:1/-1">Body <textarea class="car-body" rows="3" placeholder="Supporting copy (optional)"></textarea></label>
      <label style="grid-column:1/-1">Call-to-action button (optional) <input class="car-cta-label" type="text" placeholder="e.g. Read the write-up →"></label>
      <label style="grid-column:1/-1">Media on this card?
        <span class="car-media-radio">
          <label><input type="radio" name="media-single" class="car-has-media" value="yes"> Yes</label>
          <label><input type="radio" name="media-single" class="car-no-media" value="no" checked> No — text only</label>
        </span>
      </label>
      <label class="car-media-wrap" style="grid-column:1/-1;display:none">Media URL (a site-relative /gallery/... path is fine; an animated GIF stays animated in the GIF export) <input class="car-media" type="text" placeholder="/gallery/google-chat-print-channel/chat-weather-live.gif"></label>
      <label class="car-media-wrap" style="display:none">Trim clip to (seconds) <input class="car-media-secs" type="number" step="0.5" min="0.5" placeholder="whole clip"></label>
    </div>
    <div class="carousel-preview"><img class="car-preview-img" alt="Card preview"><div class="car-preview-status"></div></div>
  </div>

  <div class="childlist-strip" style="display:flex;align-items:center;gap:10px;margin-top:16px;border-top:1px solid var(--border)">
    <button class="copy-btn" id="spSaveBtn" type="button">SAVE DRAFT</button>
    <button class="copy-btn" id="spExportBtn" type="button">EXPORT AS PNG</button>
    <button class="copy-btn" id="spExportGifBtn" type="button">EXPORT AS GIF</button>
    <span id="spStatus" style="color:var(--text-faint)"></span>
  </div>
  <p class="hint" id="spCostEstimate" style="margin-top:6px"></p>
</div>"""

    script = f"""
var SINGLE_POST_DRAFTS = {drafts_json};

// Same real Cloud Run pricing the carousel page quotes -- one card, so the
// estimate is a single render (plus the stitch pass for the GIF).
var SP_SECONDS_PER_CARD = 3.0;
var SP_GIF_STITCH_OVERHEAD_SECONDS = 2.0;
var SP_COST_PER_SECOND = 0.000024 + 0.0000025;

function spFormatCost(usd) {{
  if (usd < 0.01) return '<$0.01';
  return '$' + usd.toFixed(2);
}}

function spBlock() {{
  var el = document.querySelector('.carousel-card-block[data-role="single"]');
  var yes = el.querySelector('.car-has-media');
  var card = {{
    type: 'promo_carousel_card',
    role: 'single',
    variant: document.getElementById('spVariant').value,
    font: document.getElementById('spFont').value,
    eyebrow: el.querySelector('.car-eyebrow').value,
    headline: el.querySelector('.car-headline').value,
    body: el.querySelector('.car-body').value,
    cta_label: el.querySelector('.car-cta-label').value,
    has_media: !!(yes && yes.checked),
    media_url: el.querySelector('.car-media').value
  }};
  var msecs = el.querySelector('.car-media-secs');
  if (msecs && msecs.value.trim()) card.media_max_ms = Math.round(parseFloat(msecs.value) * 1000);
  return card;
}}

function spRenderPreview() {{
  var el = document.querySelector('.carousel-card-block[data-role="single"]');
  var card = spBlock();
  if (!card.headline.trim()) return;
  var img = el.querySelector('.car-preview-img');
  var status = el.querySelector('.car-preview-status');
  status.textContent = 'Rendering...';
  fetch('/authoring/api/carousel-preview', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{card: card}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      if (res.ok && res.data.png_base64) {{
        img.src = 'data:image/png;base64,' + res.data.png_base64;
        status.textContent = '';
      }} else {{
        status.textContent = 'FAILED: ' + (res.data.error || 'unknown error');
      }}
    }})
    .catch(function(e){{ status.textContent = 'FAILED: ' + e.message; }});
}}

(function spWire(){{
  var el = document.querySelector('.carousel-card-block[data-role="single"]');
  var timer = null;
  el.querySelectorAll('input, textarea').forEach(function(f){{
    f.addEventListener('input', function(){{
      clearTimeout(timer);
      timer = setTimeout(spRenderPreview, 800);
    }});
  }});
  el.querySelectorAll('.car-has-media, .car-no-media').forEach(function(r){{
    r.addEventListener('change', function(){{
      var on = el.querySelector('.car-has-media').checked;
      el.querySelectorAll('.car-media-wrap').forEach(function(w){{ w.style.display = on ? '' : 'none'; }});
      spRenderPreview();
    }});
  }});
  ['spVariant','spFont'].forEach(function(id){{
    document.getElementById(id).addEventListener('change', spRenderPreview);
  }});
  document.getElementById('spCostEstimate').textContent =
    'Estimated Cloud Run compute cost per export: ' +
    spFormatCost(SP_SECONDS_PER_CARD * SP_COST_PER_SECOND) + ' as a PNG, ' +
    spFormatCost((SP_SECONDS_PER_CARD + SP_GIF_STITCH_OVERHEAD_SECONDS) * SP_COST_PER_SECOND) + ' as a GIF ' +
    '(real Cloud Run compute pricing; well within the monthly free tier for normal use).';
}})();

document.getElementById('spSaveBtn').addEventListener('click', function(){{
  var status = document.getElementById('spStatus');
  var slug = document.getElementById('spSlug').value.trim();
  if (!/^[a-z0-9-]+$/.test(slug)) {{
    status.textContent = 'Slug must be lowercase letters, numbers and hyphens.';
    return;
  }}
  var card = spBlock();
  if (!card.headline.trim()) {{
    status.textContent = 'The card needs a headline before saving.';
    return;
  }}
  status.textContent = 'Saving...';
  fetch('/authoring/api/carousel-save', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{
      kind: 'single-post', slug: slug, card: card,
      variant: document.getElementById('spVariant').value,
      font: document.getElementById('spFont').value}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      status.textContent = res.ok ? 'Saved — check GitHub for the new PR shortly.' : 'FAILED: ' + (res.data.error || 'unknown error');
    }})
    .catch(function(e){{ status.textContent = 'FAILED: ' + e.message; }});
}});

function spExport(gif) {{
  var status = document.getElementById('spStatus');
  var btn = document.getElementById(gif ? 'spExportGifBtn' : 'spExportBtn');
  var label = gif ? 'EXPORT AS GIF' : 'EXPORT AS PNG';
  var card = spBlock();
  if (!card.headline.trim()) {{
    status.textContent = 'The card needs a headline before exporting.';
    return;
  }}
  btn.disabled = true; btn.textContent = 'RENDERING...';
  status.textContent = 'Rendering at full export size — this can take a moment...';
  fetch(gif ? '/authoring/api/carousel-export-gif' : '/authoring/api/carousel-export', {{
    method: 'POST',
    headers: {{'content-type': 'application/json'}},
    body: JSON.stringify({{cards: [card]}})
  }})
    .then(function(r){{ return r.json().then(function(d){{ return {{ok: r.ok, data: d}}; }}); }})
    .then(function(res){{
      btn.disabled = false; btn.textContent = label;
      if (!res.ok) {{ status.textContent = 'FAILED: ' + (res.data.error || 'unknown error'); return; }}
      var slug = document.getElementById('spSlug').value.trim() || 'single-post';
      var a = document.createElement('a');
      if (gif) {{
        a.href = 'data:image/gif;base64,' + res.data.gif_base64;
        a.download = slug + '.gif';
      }} else {{
        a.href = 'data:image/png;base64,' + res.data.images[0].png_base64;
        a.download = slug + '.png';
      }}
      document.body.appendChild(a); a.click(); a.remove();
      status.textContent = 'Exported — check your downloads.';
    }})
    .catch(function(e){{
      btn.disabled = false; btn.textContent = label;
      status.textContent = 'FAILED: ' + e.message;
    }});
}}

document.getElementById('spExportBtn').addEventListener('click', function(){{ spExport(false); }});
document.getElementById('spExportGifBtn').addEventListener('click', function(){{ spExport(true); }});

// Load an existing draft if ?slug=... is present (from the board above).
(function(){{
  var params = new URLSearchParams(window.location.search);
  var slug = params.get('slug');
  if (!slug) return;
  document.getElementById('spSlug').value = slug;
  var draft = null;
  for (var i = 0; i < SINGLE_POST_DRAFTS.length; i++) {{
    if (SINGLE_POST_DRAFTS[i].slug === slug) {{ draft = SINGLE_POST_DRAFTS[i]; break; }}
  }}
  if (!draft) {{
    document.getElementById('spStatus').textContent = 'No saved draft found for slug "' + slug + '".';
    return;
  }}
  if (draft.variant) document.getElementById('spVariant').value = draft.variant;
  if (draft.font) document.getElementById('spFont').value = draft.font;
  var el = document.querySelector('.carousel-card-block[data-role="single"]');
  var c = draft.card || {{}};
  el.querySelector('.car-eyebrow').value = c.eyebrow || '';
  el.querySelector('.car-headline').value = c.headline || '';
  el.querySelector('.car-body').value = c.body || '';
  el.querySelector('.car-cta-label').value = c.cta_label || '';
  el.querySelector('.car-media').value = c.media_url || '';
  if (c.media_max_ms) el.querySelector('.car-media-secs').value = c.media_max_ms / 1000;
  var on = !!c.has_media;
  el.querySelector('.car-has-media').checked = on;
  el.querySelector('.car-no-media').checked = !on;
  el.querySelectorAll('.car-media-wrap').forEach(function(w){{ w.style.display = on ? '' : 'none'; }});
  spRenderPreview();
  document.getElementById('spStatus').textContent =
    'Loaded "' + slug + '" — Save overwrites this same draft.';
}})();
"""
    return _page_shell("Single Post", body, script)


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
    carousel_drafts = _load_carousel_drafts()
    single_post_drafts = _load_single_post_drafts()

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

    carousel_dir = OUTPUT_DIR / "templates" / "teaser-card-carousel"
    carousel_dir.mkdir(parents=True, exist_ok=True)
    (carousel_dir / "index.html").write_text(
        build_carousel_page(carousel_drafts),
        encoding="utf-8",
    )

    single_post_dir = OUTPUT_DIR / "templates" / "single-post"
    single_post_dir.mkdir(parents=True, exist_ok=True)
    (single_post_dir / "index.html").write_text(
        build_single_post_page(single_post_drafts),
        encoding="utf-8",
    )

    # Top-level, not /authoring/workspace/ — Curtis wants it reachable as its
    # own surface, not nested under the authoring hub it happens to share a
    # Worker and an Access gate with (2026-08-04).
    workspace_dir = ROOT / "public-full" / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "index.html").write_text(build_workspace_page(), encoding="utf-8")

    wired = sum(1 for a in archetypes.values() for s in a["slots"] if s in spec_atoms)
    total = sum(len(a["slots"]) for a in archetypes.values())
    print(f"gen_authoring: wrote /authoring/, /authoring/promptbuilder/, /authoring/whatscooking/, "
          f"/authoring/templates/teaser-card-carousel/, /authoring/templates/single-post/, "
          f"/workspace/ "
          f"({len(archetypes)} archetypes, {wired}/{total} slots wired to spec.json, "
          f"{len(current_drafts)} draft(s) on the cooking board, "
          f"{len(carousel_drafts)} carousel draft(s), "
          f"{len(single_post_drafts)} single-post draft(s))")


if __name__ == "__main__":
    main()
