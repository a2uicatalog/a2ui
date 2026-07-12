#!/usr/bin/env python3
"""
Generate individual atom reference pages from atoms/schema.yaml.
Outputs to public/atoms/{type}/index.html — served at a2uicatalog.ai/atoms/{type}

Run:
  python3 scripts/generate_atom_pages.py
"""
import base64
import json
import re
import sys
import zlib
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT       = Path(__file__).parent.parent
SCHEMA     = ROOT / "atoms" / "schema.yaml"
OUTPUT_DIR = ROOT / "public" / "atoms"
DOMAIN     = "a2uicatalog.ai"
GAS_RENDERER = "https://script.google.com/macros/s/AKfycbwwGCeqX1jn0nnH5F-jc1dpXj1wlfJayMrF7V648oY6AgHJY-85b6-OQyWxOx5bFBMv/exec"

# Surfaces present in schema + ARD manifest but hidden from the human-facing
# filter UI — visible to agents querying the catalog, not shown as filter pills.
HIDDEN_SURFACES = {"gas-fakes"}

# Surfaces worth an individual chip on every index card. Most atoms share the
# same 5-7 surfaces, so per-card chips for all of them are wallpaper — the
# index shows chips only for notable surfaces (new/highlighted) and degraded
# ones, and collapses the rest to a count. The filter row above the grid is
# the authoritative "which atoms work on X" view.
NOTABLE_SURFACES = {"mcp-apps"}

sys.path.insert(0, str(ROOT / "renderers"))
try:
    import web_article as _web_renderer
    _RENDERER_TYPES = set(_web_renderer._RENDERERS.keys())
except Exception as e:
    print(f"ERROR: failed to import web_article renderer: {e}", file=sys.stderr)
    sys.exit(1)

# Representative example blocks for atoms supported by the web-article renderer.
# These are richer than example_payload() can generate automatically.
_EXAMPLE_BLOCKS = {
    "content_tabs": {"type": "content_tabs", "accent": "#6366f1", "tabs": [
        {"label": "4 Players", "blocks": [
            {"type": "body", "text": "One court, three rounds — every player partners with every other exactly once."},
            {"type": "match_schedule", "rounds": [
                {"label": "Round 1", "matches": [{"court": "Court 1", "team_a": ["P1", "P4"], "team_b": ["P2", "P3"]}]}]}]},
        {"label": "8 Players", "blocks": [
            {"type": "body", "text": "Two courts, seven rounds — a full partner rotation."}]}]},
    "standings_table": {"type": "standings_table", "primary_label": "PTS",
        "columns": ["Won", "Lost", "+/-"],
        "rows": [
            {"name": "Jesus", "played": 11, "primary": 27, "values": [181, 120, 61], "highlight": "leader"},
            {"name": "Colt", "played": 11, "primary": 27, "values": [174, 136, 38]},
            {"name": "Sean", "played": 11, "primary": 22, "values": [167, 110, 57]}]},
    "match_schedule": {"type": "match_schedule", "layout": "cards", "rounds": [
        {"label": "Round 1", "matches": [
            {"court": "Court 1", "team_a": ["Player 1", "Player 8"], "team_b": ["Player 2", "Player 7"], "score_a": 21, "score_b": 17},
            {"court": "Court 2", "team_a": ["Player 3", "Player 6"], "team_b": ["Player 4", "Player 5"]}]}]},
    "body":        {"type": "body", "text": "This is a body paragraph. It supports **bold**, *italic*, and `inline code` via lightweight markdown."},
    "heading":     {"type": "heading", "text": "Section Heading"},
    "subheading":  {"type": "subheading", "text": "Subheading text"},
    "quote":       {"type": "quote", "text": "The vocabulary IS the discovery layer.", "attribution": "A2UI"},
    "divider":     {"type": "divider"},
    "code":        {"type": "code", "language": "json", "content": '{\n  "type": "stat_card",\n  "value": "1B+",\n  "label": "daily executions"\n}'},
    "pipeline":    {"type": "pipeline", "steps": ["schema.yaml", "generate.py", "public/", "Cloudflare Edge"]},
    "bullet_list": {"type": "bullet_list", "items": [
        {"text": "First item in the list"},
        {"label": "Labelled item", "text": "with supporting description"},
        {"text": "Third item"},
    ]},
    "callout":     {"type": "callout", "callout_type": "info", "body": "This is an informational callout. Use `warning`, `tip`, or `note` for other styles."},
    "steps":       {"type": "steps", "steps": [
        {"title": "Step one", "body": "The first thing to do."},
        {"title": "Step two", "body": "Then this."},
        {"title": "Step three", "body": "Finally, this."},
    ]},
    "table":       {"type": "table", "caption": "Example fields", "headers": ["Field", "Type", "Required"], "rows": [
        ["value", "string", "yes"],
        ["label", "string", "yes"],
        ["trend", "string", "no"],
    ]},
    "key_value":   {"type": "key_value", "pairs": [
        {"key": "API_KEY", "value": "your-api-key-here"},
        {"key": "BASE_URL", "value": "https://a2uicatalog.ai"},
        {"key": "SURFACE",  "value": "web"},
    ]},
    "timeline":    {"type": "timeline", "events": [
        {"date": "2024", "title": "A2UI v1", "body": "First atoms defined."},
        {"date": "2025", "title": "467 atoms", "body": "Full schema published."},
        {"date": "2026", "title": "ARD catalog", "body": "Live on a2uicatalog.ai."},
    ]},
    "before_after": {"type": "before_after", "language": "js",
        "before_label": "Before", "after_label": "After",
        "before": "const html = buildPage(data);",
        "after":  'const html = render([{"type":"body","text":"Hello"}]);'},
    "annotated_code": {"type": "annotated_code", "language": "json",
        "code": '{\n  "type": "stat_card",  // [1]\n  "value": "1B+",      // [2]\n  "label": "daily executions"\n}',
        "callouts": [
            {"line": 1, "note": "The atom type — matches schema.yaml"},
            {"line": 2, "note": "The primary display value"},
        ]},
    # Added 2026-07-10 — the mcp-apps all-atoms sweep exposed that
    # example_payload() emits junk (true/1) for these atoms' array fields;
    # shapes below are read from the renderer source (ground truth).
    "breadcrumb": {"type": "breadcrumb", "items": [
        {"label": "Catalog", "slug": "catalog"},
        {"label": "Atoms", "slug": "atoms"},
        {"label": "Breadcrumb"}]},
    "chip_group": {"type": "chip_group", "chips": [
        {"label": "Web", "active": True},
        {"label": "Meet"},
        {"label": "Chat", "url": "#"}]},
    "checklist_interactive": {"type": "checklist_interactive", "items": [
        {"label": "Read the brief"},
        {"label": "Run the tests"},
        {"label": "Ship it"}]},
    "data_grid": {"type": "data_grid", "title": "Deployments",
        "columns": [{"header": "Name", "key": "name"},
                    {"header": "Status", "key": "status"}],
        "rows": [{"name": "web", "status": "live"},
                 {"name": "meet", "status": "beta"}]},
    "call_mood_board": {"type": "call_mood_board", "title": "Room mood",
        "moods": [
            {"mood": "Focused", "icon": "🎯", "intensity": 80, "color": "#6366f1"},
            {"mood": "Energised", "icon": "⚡", "intensity": 65, "color": "#00f2ff"}]},
    "module_map": {"type": "module_map", "title": "Course map", "columns": 2,
        "modules": [
            {"title": "Basics", "description": "Start here", "duration": "10 min", "icon": "📘"},
            {"title": "Advanced", "description": "Go deeper", "duration": "25 min", "icon": "🚀"}]},
    "punch_card": {"type": "punch_card", "title": "Commit activity",
        "data": [{"day": 1, "hour": 9, "count": 5},
                 {"day": 2, "hour": 14, "count": 9},
                 {"day": 4, "hour": 11, "count": 3}]},
    "testimonial_card": {"type": "testimonial_card",
        "quote": "The catalog cut our build time in half.",
        "author_name": "Ada L.", "author_title": "Platform Lead", "rating": 5},
    "annotation_highlight": {"type": "annotation_highlight",
        "text": "The renderer walks the block list and dispatches by type.",
        "notes": [{"term": "renderer", "explanation": "turns JSON into HTML"},
                  {"term": "type", "explanation": "the dispatch key"}]},
    "atom_anatomy": {"type": "atom_anatomy", "label": "stat_card",
        "schema": {"type": "stat_card", "value": "1,234", "label": "Daily users"}},
    "brevet_automatismes": {"type": "brevet_automatismes", "duration": 90,
        "questions": [{"question": "7 × 8 ?"}, {"question": "Racine de 81 ?"}]},
    "carousel": {"type": "carousel", "slides": [
        {"url": "https://picsum.photos/seed/a2ui1/800/400", "label": "Slide one"},
        {"url": "https://picsum.photos/seed/a2ui2/800/400", "label": "Slide two"}]},
    "catalogue_provenance": {"type": "catalogue_provenance", "label": "Sources",
        "sources": [{"catalogue": "a2ui-atoms-v1", "color": "#00f2ff"},
                    {"catalogue": "gdm-v0.2", "color": "#6366f1"}]},
    "chat_sequence": {"type": "chat_sequence", "messages": [
        {"role": "user", "name": "Ana", "text": "Ship it?"},
        {"role": "agent", "name": "Bot", "text": "Tests are green.", "align": "right"}]},
    "hub": {"type": "hub", "subjects": [
        {"label": "Maths", "color": "#6366f1", "slides": [
            {"blocks": [{"type": "heading", "text": "Fractions"}]}]},
        {"label": "Physics", "color": "#00f2ff", "slides": [
            {"blocks": [{"type": "body", "text": "Forces and motion."}]}]}]},
    "playbook": {"type": "playbook", "slides": [
        {"id": "intro", "accent": "#00f2ff",
         "blocks": [{"type": "heading", "text": "Kickoff"}]},
        {"id": "close",
         "blocks": [{"type": "body", "text": "Wrap-up."}]}]},
    "sparkline": {"type": "sparkline", "data": [3, 5, 2, 8, 6, 9], "color": "#00f2ff"},
    # Full-screen by default in the playground: the command deck is designed
    # as a full-viewport surface — a 520px letterbox is the exception, not
    # the rule (Curtis, 2026-07-10).
    "airspace_command_deck": {"type": "airspace_command_deck", "height": "fullscreen",
        "chyron_title": "LFBO TMA", "chyron_subtitle": "Toulouse Blagnac Approach Control"},
}

# ── v0.3 design system (approved 2026-07-10) ────────────────────────────────
# Tokens = a2ui-private/tests/design_handoff_nav_theme/tokens.css v0.2 verbatim.
# Light lives on plain :root so a page that never sets data-theme still gets a
# full token set; lifted dark only via [data-theme="dark"] (light is the
# default, dark is a toggle — per the approved handoff, not OS-derived).
# Legacy var names (--card/--muted/--cyan/--green) alias into the new tokens so
# every pre-v0.3 rule and the MCP hero inherit the theme without edits.
SITE_BASE_CSS = """
:root{
  color-scheme:light;
  --bg:oklch(98% 0.006 255);--surface:oklch(100% 0 0);--surface-2:oklch(96.5% 0.008 255);
  --border:oklch(90% 0.01 255);--border-strong:oklch(82% 0.02 255);
  --text:oklch(22% 0.02 255);--text-muted:oklch(46% 0.02 255);
  --accent:oklch(58% 0.19 277);--accent-contrast:oklch(100% 0 0);--accent-soft-bg:oklch(94% 0.03 277);
  --accent-2:oklch(62% 0.13 202);--positive:oklch(58% 0.15 146);--negative:oklch(55% 0.18 25);
  --warn:oklch(70% 0.15 87);--code-bg:oklch(96% 0.01 255);--radius:12px;
  --shadow:0 1px 2px oklch(0% 0 0 / .05),0 8px 24px oklch(0% 0 0 / .05);
  --glow:0 4px 24px oklch(58% 0.19 277 / .14);
  --header-glass:oklch(100% 0 0 / .72);
  --grad:linear-gradient(120deg,oklch(58% 0.19 277),oklch(70% 0.14 202));
  --card:var(--surface);--muted:var(--text-muted);--cyan:var(--accent-2);--green:var(--positive);
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:oklch(27% 0.025 255);--surface:oklch(33% 0.025 255);--surface-2:oklch(30% 0.02 255);
  --border:oklch(42% 0.02 255);--border-strong:oklch(50% 0.02 255);
  --text:oklch(95% 0.01 255);--text-muted:oklch(72% 0.02 255);
  --accent:oklch(72% 0.16 277);--accent-contrast:oklch(15% 0.02 255);--accent-soft-bg:oklch(38% 0.06 277);
  --accent-2:oklch(75% 0.12 202);--positive:oklch(72% 0.15 146);--negative:oklch(68% 0.17 25);
  --warn:oklch(85% 0.17 87);--code-bg:oklch(23% 0.02 255);
  --shadow:0 1px 2px oklch(0% 0 0 / .3),0 8px 24px oklch(0% 0 0 / .28);
  --glow:0 4px 28px oklch(72% 0.16 277 / .22);
  --header-glass:oklch(33% 0.025 255 / .72);
  --grad:linear-gradient(120deg,oklch(72% 0.16 277),oklch(80% 0.13 202));
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.6}
a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.site-header{position:sticky;top:0;z-index:100;background:var(--header-glass);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--border)}
.hdr-in{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:10px;padding:11px 24px}
.wordmark{display:flex;align-items:center;gap:9px;font-size:15px;font-weight:800;letter-spacing:-.2px;color:var(--text);text-decoration:none;white-space:nowrap}
.logo-mark{width:20px;height:20px;border-radius:6px;background:var(--grad);display:grid;place-items:center;color:#fff;font-size:10px;font-weight:900;flex-shrink:0}
.site-nav{display:flex;gap:4px;margin-right:auto;margin-left:12px}
.site-nav a{font-size:13px;font-weight:600;text-decoration:none;color:var(--muted);padding:5px 11px;border-radius:7px;transition:color .15s,background .15s}
.site-nav a:hover{color:var(--text);background:var(--surface-2)}
.site-nav a[aria-current="page"]{color:var(--accent);background:var(--accent-soft-bg)}
.theme-btn{font:inherit;font-size:14px;line-height:1;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:6px 9px;cursor:pointer;color:var(--text)}
.theme-btn:hover{border-color:var(--border-strong)}
.gh-pill{font-size:12px;font-weight:650;color:var(--text);text-decoration:none;border:1px solid var(--border);border-radius:8px;padding:6px 12px;background:var(--surface);white-space:nowrap}
.gh-pill:hover{border-color:var(--border-strong)}
.wrap{max-width:1100px;margin:0 auto;padding:36px 24px 96px}
footer{margin-top:64px;padding-top:24px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
footer a{color:var(--accent-2);text-decoration:none}
@media(max-width:700px){.site-nav{display:none}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
/* cursor_glow ships dark-tuned (screen blend ≈ invisible over a white ground);
   in the light default, re-blend the orb — it is the only direct body child
   carrying the atom's z-index:9000. */
:root:not([data-theme="dark"]) body>div[style*="z-index:9000"]{mix-blend-mode:multiply!important;opacity:.22!important}
"""

# Theme init — MUST run before first paint (inline in <head>) or dark-toggle
# users get a light flash. Storage is try/catch-wrapped: localStorage THROWS in
# the MCP Apps view (opaque origin — gap G4); it degrades to session-only.
SITE_HEAD_JS = """<script>
(function(){var t='light';try{var s=localStorage.getItem('a2ui-theme');if(s==='dark'||s==='light')t=s}catch(e){}
document.documentElement.setAttribute('data-theme',t)})();
</script>"""

SITE_FOOT_JS = """<script>
document.addEventListener('click',function(e){
  var b=e.target.closest('.theme-btn');if(!b)return;
  var r=document.documentElement,t=r.getAttribute('data-theme')==='dark'?'light':'dark';
  r.setAttribute('data-theme',t);
  try{localStorage.setItem('a2ui-theme',t)}catch(err){}
});
</script>"""


def site_header(active=""):
    """Shared sticky glass header — identical on every surface (the v0.3 nav fix)."""
    def cur(k):
        return ' aria-current="page"' if k == active else ""
    return f"""<header class="site-header"><div class="hdr-in">
    <a class="wordmark" href="/"><span class="logo-mark">A2</span>A2UI Catalog</a>
    <nav class="site-nav">
      <a href="/"{cur('atoms')}>Atoms</a>
      <a href="/surfaces/mcp-apps"{cur('playground')}>MCP Playground</a>
      <a href="/renderer"{cur('renderer')}>Apps Script Renderer</a>
    </nav>
    <button class="theme-btn" type="button" aria-label="Toggle light/dark theme">◐</button>
    <a class="gh-pill" href="https://github.com/a2uicatalog/a2ui">GitHub ↗</a>
  </div></header>"""


PAGE_CSS = """
<style>""" + SITE_BASE_CSS + """
.wrap{max-width:860px}
nav.crumb{font-size:12px;color:var(--muted);margin-bottom:28px;font-family:ui-monospace,'SF Mono',Monaco,monospace}
nav.crumb a{color:var(--accent-2);text-decoration:none}
nav.crumb a:hover{text-decoration:underline}
h1{font-size:2.2rem;font-weight:800;letter-spacing:-1px;margin-bottom:8px}
.desc{font-size:1.1rem;color:var(--muted);margin-bottom:32px;line-height:1.7}
.label{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:12px}
.section{margin-bottom:40px}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:100px;margin:2px}
.bs{background:var(--accent-soft-bg);color:var(--accent)}
.bd{background:color-mix(in oklch,var(--warn) 14%,var(--surface));border:1px solid color-mix(in oklch,var(--warn) 40%,var(--surface));color:var(--warn)}
pre{background:var(--code-bg);border:1px solid var(--border);border-radius:10px;padding:20px;overflow-x:auto;margin:12px 0 24px}
pre code{color:var(--text);font-size:13px;font-family:ui-monospace,'SF Mono',Monaco,monospace}
table{width:100%;border-collapse:collapse;margin:12px 0 24px;font-size:14px}
th{text-align:left;padding:10px 14px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border)}
td{padding:10px 14px;border-bottom:1px solid var(--border);color:var(--muted);vertical-align:top}
td:first-child{color:var(--text);font-weight:600;font-family:ui-monospace,'SF Mono',Monaco,monospace}
.back{display:inline-block;margin-top:32px;font-size:13px;color:var(--muted);border:1px solid var(--border);border-radius:8px;padding:8px 14px;text-decoration:none;background:var(--surface)}
.back:hover{border-color:var(--accent);color:var(--accent)}
.try-btn{display:inline-block;margin-top:32px;margin-left:12px;font-size:13px;font-weight:700;color:var(--accent-contrast);background:var(--accent);border:none;border-radius:8px;padding:9px 18px;text-decoration:none;letter-spacing:.03em;cursor:pointer;transition:filter .15s,box-shadow .15s}
.try-btn:hover{filter:brightness(1.08);box-shadow:var(--glow)}
.preview-box{background:#fff;border:1px solid var(--border);border-radius:10px;padding:24px;margin-top:8px;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6}
.preview-box *{max-width:100%}
.preview-box p,.preview-box li,.preview-box td,.preview-box th,.preview-box td:first-child{color:#333;font-family:inherit}
.preview-box pre{background:#f4f4f4;border:1px solid #e0e0e0}
.preview-box pre code{color:#333}
.preview-box h2,.preview-box h3{color:#111}
.preview-box a{color:#0969da}
.preview-box ul{color:#333}
.deploy-box{margin-top:40px;padding:20px 24px;background:var(--accent-soft-bg);border:1px solid var(--border);border-radius:var(--radius)}
.deploy-box .label{margin-bottom:10px}
.deploy-box a{display:inline-block;margin-top:12px;font-size:12px;color:var(--accent);text-decoration:none;font-weight:600}
</style>
"""


def surface_badges(atom):
    surfaces = atom.get("surfaces", {})
    works_on = surfaces.get("works_on", [])
    degraded  = {d["surface"] for d in (surfaces.get("degraded_on") or [])}
    badges = []
    for s in works_on:
        if s in HIDDEN_SURFACES:
            continue
        cls = "bd" if s in degraded else "bs"
        suffix = " ⚠" if s in degraded else ""
        badges.append(f'<span class="badge {cls}">{s}{suffix}</span>')
    return "".join(badges) or "<span style='color:var(--muted)'>—</span>"


def fields_table(atom):
    fields = atom.get("fields", {})
    if not fields:
        return "<p style='color:var(--muted)'>No configurable fields.</p>"
    rows = ""
    for name, ftype in fields.items():
        optional = "optional" in str(ftype).lower()
        type_clean = str(ftype).replace(" (optional)", "").replace(" (Optional)", "")
        req = "optional" if optional else "required"
        rows += f"<tr><td>{name}</td><td>{type_clean}</td><td>{req}</td></tr>"
    return f"<table><thead><tr><th>Field</th><th>Type</th><th></th></tr></thead><tbody>{rows}</tbody></table>"


def _infer_list(name, atom_type):
    if name in ["blocks", "children"]:
        return [{"type": "body", "text": "Example content."}]
    if name == "steps":
        return [{"title": "Step one", "body": "First thing to do."}, {"title": "Step two", "body": "Then this."}]
    if name == "points":
        return ["First key point", "Second key point", "Third key point"]
    if name == "items":
        if any(x in atom_type for x in ["checklist", "icon_list", "bullet"]):
            return [{"label": "First item"}, {"label": "Second item"}]
        return [{"label": "Item 1"}, {"label": "Item 2"}]
    if name == "metrics":
        return [{"label": "Revenue", "value": "$1.2M", "trend": "up"}, {"label": "Users", "value": "42K", "trend": "up"}]
    if name == "events":
        return [{"date": "2025", "title": "Launch", "body": "First release."}, {"date": "2026", "title": "Today", "body": "Still growing."}]
    if name == "pairs":
        return [{"key": "API_KEY", "value": "your-key"}, {"key": "ENV", "value": "production"}]
    if name == "links":
        return [{"label": "GitHub", "url": "https://github.com/a2uicatalog/a2ui"}]
    if name == "tabs":
        return [{"label": "Tab 1", "content": "Content one."}, {"label": "Tab 2", "content": "Content two."}]
    if name == "headers":
        return ["Name", "Value", "Status"]
    if name == "rows":
        return [["Example", "42", "Active"], ["Another", "17", "Pending"]]
    if name == "callouts":
        return [{"line": 1, "note": "This line does X"}]
    if name == "slides":
        return [{"id": "s1", "label": "Slide 1", "blocks": []}]
    if name == "options":
        return [{"label": "Option A", "value": "a"}, {"label": "Option B", "value": "b"}, {"label": "Option C", "value": "c"}]
    if name == "nodes":
        if "file_tree" in atom_type or "tree" in atom_type:
            return [{"label": "src/", "children": [{"label": "index.ts"}]}, {"label": "package.json"}]
        if "sankey" in atom_type:
            return [{"id": "a", "label": "Source"}, {"id": "b", "label": "Target"}]
        return [{"id": "node-1", "label": "Node 1"}, {"id": "node-2", "label": "Node 2"}]
    if name == "features":
        return ["Core feature", "Advanced analytics", "API access"]
    if name in ["labels", "labels_x"]:
        return ["Category A", "Category B", "Category C", "Category D"]
    if name == "labels_y":
        return ["Low", "Medium", "High"]
    if name in ["color_scale", "colors"]:
        return ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
    if name == "periods":
        return ["Week 1", "Week 2", "Week 3", "Week 4"]
    if name == "themes":
        return [{"label": "Positive", "count": 42}, {"label": "Neutral", "count": 18}, {"label": "Negative", "count": 7}]
    if name == "specs":
        return [{"label": "Weight", "value": "1.2 kg"}, {"label": "Dimensions", "value": "20×15 cm"}]
    if name == "datasets":
        return [{"label": "Dataset A", "data": [65, 59, 80, 72]}, {"label": "Dataset B", "data": [28, 48, 40, 55]}]
    if name in ["series", "data_points"]:
        if name == "data_points":
            return [{"x": 10, "y": 20}, {"x": 30, "y": 45}, {"x": 50, "y": 35}]
        return [{"label": "Series A", "data": [10, 20, 30, 40]}, {"label": "Series B", "data": [5, 15, 25, 35]}]
    if name == "data":
        if "pie" in atom_type or "donut" in atom_type:
            return [{"label": "Category A", "value": 40}, {"label": "Category B", "value": 35}, {"label": "Category C", "value": 25}]
        if "calendar" in atom_type or "heatmap" in atom_type:
            return [{"date": "2026-06-01", "value": 5}, {"date": "2026-06-15", "value": 12}]
        return [10, 25, 40, 30, 55]
    if name == "skills":
        return [{"label": "Python", "value": 85}, {"label": "JavaScript", "value": 70}, {"label": "TypeScript", "value": 65}]
    if name == "stats":
        return [{"label": "Views", "value": "1.2M"}, {"label": "Clicks", "value": "42K"}, {"label": "CTR", "value": "3.5%"}]
    if name == "cards":
        return [{"title": "Card 1", "body": "First card content."}, {"title": "Card 2", "body": "Second card content."}]
    if name == "cohorts":
        return [{"label": "Jan 2025", "data": [100, 72, 58, 45]}, {"label": "Feb 2025", "data": [80, 65, 50, 38]}]
    if name == "shape":
        return [{"type": "rect", "width": "100%", "height": "20px"}, {"type": "rect", "width": "60%", "height": "20px"}]
    if name == "product_names":
        return ["Starter", "Pro", "Enterprise"]
    if name == "tiers":
        return [{"name": "Starter", "price": "$9/mo", "features": []}, {"name": "Pro", "price": "$29/mo", "features": []}]
    if name == "pros":
        return ["Scalable architecture", "Clean API design", "Excellent documentation"]
    if name == "cons":
        return ["Steeper learning curve", "Limited third-party plugins"]
    if name == "products":
        return [{"name": "Product A"}, {"name": "Product B"}]
    if name == "comparison_points":
        return [{"label": "Performance", "a": "Fast", "b": "Moderate"}, {"label": "Price", "a": "$9", "b": "$19"}]
    if name == "capability_names":
        return ["Vision", "Code execution", "Web search"]
    if name == "hotspots":
        return [{"x": 25, "y": 30, "label": "Feature A"}, {"x": 60, "y": 70, "label": "Feature B"}]
    if name == "menu_items":
        return [{"label": "Dashboard"}, {"label": "Settings"}, {"label": "Help"}]
    if name == "avatars":
        return [{"src": "https://example.com/image.png", "name": "Alice"}, {"src": "https://example.com/image.png", "name": "Bob"}]
    if name == "contributors":
        return [{"name": "Alice", "role": "Developer"}, {"name": "Bob", "role": "Designer"}]
    if name == "logos":
        return [{"src": "https://example.com/image.png", "alt": "Company A"}, {"src": "https://example.com/image.png", "alt": "Company B"}]
    if name == "keys":
        return ["Ctrl", "Shift", "K"]
    if name == "objectives":
        return ["Understand the core concept", "Apply it in practice", "Evaluate the results"]
    if name == "changes":
        return [{"type": "added", "text": "New feature added"}, {"type": "fixed", "text": "Bug fix applied"}]
    if name == "platforms":
        return ["twitter", "linkedin", "facebook"]
    if name == "enabled_emojis":
        return ["👍", "❤️", "🎉", "🚀"]
    if name == "headings":
        return [{"level": 2, "text": "Introduction"}, {"level": 2, "text": "Methods"}, {"level": 2, "text": "Results"}]
    if name == "commands":
        return [{"label": "New File", "shortcut": "Ctrl+N"}, {"label": "Open File", "shortcut": "Ctrl+O"}]
    if name == "footnotes":
        return [{"id": 1, "text": "Source: Example Report, 2026."}]
    if name == "capabilities":
        return [{"label": "Vision", "supported": True}, {"label": "Code execution", "supported": True}, {"label": "Web search", "supported": False}]
    if name == "breakdown":
        return [{"stars": 5, "count": 48}, {"stars": 4, "count": 30}, {"stars": 3, "count": 12}]
    if name == "tags":
        return ["typescript", "react", "a2ui"]
    if name == "models":
        return [{"name": "GPT-4", "context": "128k"}, {"name": "Claude Sonnet", "context": "200k"}]
    if name == "columns":
        return [{"title": "To Do", "cards": []}, {"title": "In Progress", "cards": []}, {"title": "Done", "cards": []}]
    if name == "selected":
        return ["Option A"]
    if name == "slots":
        return [{"time": "09:00", "title": "Opening keynote"}, {"time": "10:00", "title": "Workshop A"}]
    if name == "risks":
        return [{"label": "Scope creep", "severity": "high"}, {"label": "Timeline slip", "severity": "medium"}]
    if name == "words":
        return ["Amazing", "Fast", "Reliable", "Scalable"]
    if name == "answers":
        return [{"text": "Option A"}, {"text": "Option B"}, {"text": "Option C"}]
    if name in ["docs", "folder_id"]:
        return [{"title": "Doc 1", "url": "https://example.com"}, {"title": "Doc 2", "url": "https://example.com"}]
    if name == "terms":
        return [{"term": "API", "definition": "Application Programming Interface"}, {"term": "A2UI", "definition": "Adaptive Atom-based UI"}]
    if name == "lines":
        return ["$ npm install a2ui", "added 42 packages", "✓ Done in 1.2s"]
    if name == "choices":
        return [{"label": "Path A", "next": "node-a"}, {"label": "Path B", "next": "node-b"}]
    if name == "badges":
        return [{"label": "TypeScript", "color": "#3178c6"}, {"label": "React", "color": "#61dafb"}, {"label": "A2UI", "color": "#6366f1"}]
    if name == "paths":
        return [{"label": "Beginner Path", "steps": []}, {"label": "Advanced Path", "steps": []}]
    if name == "checkpoints":
        return [{"time": "1:30", "question": "What is X?"}, {"time": "3:00", "question": "How does Y work?"}]
    if name == "notes":
        return [{"text": "Important annotation", "range": "line 5"}]
    if name == "criteria":
        return [{"label": "Accuracy", "score": 4, "max": 5}, {"label": "Clarity", "score": 3, "max": 5}]
    return []


def _infer_string(name, atom_type):
    n = name.lower()
    if n in ["value", "stat", "metric", "count", "figure", "amount"]:    return "1,234"
    if n in ["percent", "rate"]:                                           return "75%"
    if n in ["label", "title", "heading", "name", "display_name"]:
        return atom_type.replace("_", " ").title() if atom_type else "Example Title"
    if n in ["subtitle", "subtext", "tagline", "sub", "eyebrow"]:        return "A short supporting line"
    if n in ["description", "body", "content", "detail", "summary", "note", "copy"]:
        return "A concise description of the content."
    if n == "text":
        if any(x in atom_type for x in ["badge", "chip", "tag", "pill", "lozenge", "label", "status"]):
            return "New"
        return "A concise description of the content."
    if n == "badge":      return "New"
    if n == "status":     return "Active"
    if n == "tag":        return "Example"
    if n == "caption":    return "A descriptive caption"
    if n == "trend":      return "up"
    if n == "theme":      return "dark"
    if n == "align":      return "center"
    if n == "size":       return "md"
    if n == "variant":    return "primary"
    if n == "icon":       return "⭐"
    if n == "emoji":      return "🚀"
    if n in ["color", "accent", "accent2", "fill", "highlight"]: return "#6366f1"
    if n in ["bg", "background", "bg_color"]:                    return "#0c1117"
    if n == "animation":  return "fade"
    if n in ["duration", "transition"]: return "300ms"
    if n in ["delay", "stagger", "stagger_delay"]: return "0ms"
    if n == "language":   return "json"
    if n in ["code", "content", "snippet"]: return '{"type": "example"}'
    if n in ["before", "after"]: return "// example code"
    if n in ["id", "key", "slug"]: return "example-id"
    if n in ["author", "by"]: return "Author Name"
    if n in ["date", "timestamp"]: return "2026-06-28"
    if n == "repo":       return "a2uicatalog/a2ui"
    if n == "width":      return "100%"
    if "gap" in n or "spacing" in n or "padding" in n or "margin" in n: return "1.25rem"
    if "radius" in n:     return "8px"
    if n in ["callout_type", "alert_type"]: return "info"
    if "image" in n or "img" in n or "photo" in n or "avatar" in n:
        return "https://example.com/image.png"
    if "video" in n or "youtube" in n:
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    if "url" in n or "href" in n or "link" in n or "src" in n:
        return "https://example.com"
    # Common field names that hit the generic fallback
    if n == "message":    return "Your action was completed successfully."
    if n in ["type", "kind", "variant_type"]: return "info"
    if n == "question":   return "Which option do you prefer?"
    if n == "quote":      return "The vocabulary IS the discovery layer."
    if n == "headline":   return "Main headline text here"
    if n == "prompt":     return "Describe what you'd like to create."
    if n == "alt":        return "Descriptive alt text for this image"
    if n == "term":       return "API"
    if n == "definition": return "Application Programming Interface"
    if n == "price":      return "$29/mo"
    if n == "platform":   return "twitter"
    if n == "command":    return "npm install a2ui"
    if n == "output":     return "✓ Done in 1.2s"
    if n == "template":   return "Hello, {{name}}!"
    if n == "trigger":    return "click"
    if n == "range":      return "A1:D10"
    if n == "schema":     return '{"type": "example", "value": "1,234"}'
    if n == "height":     return "80px"
    if n == "header":     return "Section Header"
    if n == "currency":   return "USD"
    if n == "frequency":  return "monthly"
    if n == "subject":    return "Example subject matter"
    if n == "details":    return "Click to expand and read the full details."
    if n == "shell":      return "bash"
    if n == "method":     return "GET"
    if n == "action":     return "submit"
    if n == "alternative":return "new_component"
    if n == "logs":       return "2026-06-28 INFO: Process started\n2026-06-28 INFO: Completed."
    if n == "data":       return '{"key": "value", "count": 42}'
    if n == "version":    return "1.2.0"
    if n == "bio":        return "Short author biography goes here."
    if n == "attribution":return "Source: Example Report, 2026"
    if n == "behavior":   return "smooth"
    if n == "user":       return "How does this work?"
    if n == "response":   return "Here's a clear explanation of how it works."
    if n == "query":      return "inbox is:unread"
    if n == "counts":     return "42"
    if n == "email":      return "user@example.com"
    if n == "project":    return "my-project-id"
    if n == "collection": return "users"
    if n in ["from", "source"]: return "start-node"
    if n in ["to", "target"]:   return "end-node"
    if n == "center":     return "Core Concept"
    if n == "surface":    return "google-apps-script-web"
    if n == "result":     return "Improved"
    if n == "mime":       return "application/pdf"
    if n == "scenario":   return "Success path"
    if n == "requires":   return "complete_intro"
    if n == "course":     return "A2UI Fundamentals"
    if n == "situation":  return "A startup facing rapid growth challenges."
    if n == "front":      return "What is an atom?"
    if n == "back":       return "A self-contained UI block with a type and fields."
    if n == "q":          return "Eiffel Tower, Paris"
    if n == "sheet":      return "Sheet1"
    if n == "app":        return "MyWorkspace"
    if n == "alt_text":   return "Descriptive alt text for accessibility"
    if n == "auth_token": return "your-api-token"
    if n == "trigger_text": return "Click to trigger"
    if n == "author_name":  return "Author Name"
    if n == "spreadsheet_id": return "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
    if n == "course_id":  return "course-101"
    if n == "icon_type":  return "star"
    if n == "delta_type": return "increase"
    if n == "trend_direction": return "up"
    if n == "product_id": return "prod-001"
    return n.replace("_", " ").capitalize()


def example_payload(atom):
    atom_type = atom.get("type", "")
    fields    = atom.get("fields") or {}
    example   = {"type": atom_type}
    for name, ftype in fields.items():
        ft = str(ftype).lower()
        if "optional" in ft or "default" in ft:
            continue
        if "bool" in ft:
            example[name] = True
        elif "int" in ft or "number" in ft:
            n = name.lower()
            if any(x in n for x in ["percent", "progress", "score", "rating"]): example[name] = 75
            elif any(x in n for x in ["max", "total"]):                          example[name] = 5
            elif any(x in n for x in ["current", "step"]):                       example[name] = 2
            elif any(x in atom_type for x in ["progress", "gauge", "bar", "ring", "circle", "donut"]): example[name] = 75
            else:                                                                  example[name] = 1
        elif "list" in ft or "array" in ft or name in [
            "items", "blocks", "steps", "points", "events", "metrics",
            "pairs", "links", "tabs", "rows", "headers", "callouts", "slides",
        ]:
            example[name] = _infer_list(name, atom_type)
        elif "url" in ft or any(x in name.lower() for x in ["url", "href", "src"]):
            example[name] = "https://example.com"
        else:
            example[name] = _infer_string(name, atom_type)
    return json.dumps(example, indent=2)


def ard_entry(atom):
    atom_type = atom.get("type", "")
    surfaces  = atom.get("surfaces", {}).get("works_on", [])
    compact   = atom.get("compact_description", "")
    desc      = atom.get("description", "")
    queries   = []
    if compact:
        queries.append(f"show a {compact.rstrip('.')}")
    if desc and desc.lower() != compact.lower():
        queries.append(desc[:100].rstrip().lower())
    queries.append(f"render a {atom_type.replace('_', ' ')}")
    queries = list(dict.fromkeys(queries))[:3]
    entry = {
        "identifier": f"urn:air:{DOMAIN}:atom:{atom_type}",
        "displayName": atom_type.replace("_", " ").title(),
        "type": "application/vnd.a2ui.atom+json",
        "url": f"https://{DOMAIN}/atoms/{atom_type}",
        "capabilities": surfaces,
        "description": desc,
        "representativeQueries": queries,
    }
    return json.dumps(entry, indent=2)


def degraded_notes(atom):
    notes = atom.get("surfaces", {}).get("degraded_on", [])
    if not notes:
        return ""
    items = "".join(
        f"<tr><td>{d['surface']}</td><td>{d.get('note', '')}</td></tr>"
        for d in notes
    )
    return f"""
<div class="section">
  <div class="label">Degraded on</div>
  <table><thead><tr><th>Surface</th><th>Note</th></tr></thead><tbody>{items}</tbody></table>
</div>"""


# Config/style atoms that need companion blocks to render anything visible
_COMPANION_BLOCKS = {
    "palette": [{"type": "stat_card", "value": "1,234", "label": "Accent applied", "trend": "up"},
                {"type": "progress_bar", "value": 75, "label": "Progress with accent"}],
    "data_source": [{"type": "body", "text": "Data source connected."}],
}


def make_renderer_url(atom):
    atom_type = atom.get("type", "")
    block     = json.loads(example_payload(atom))
    blocks    = [block] + _COMPANION_BLOCKS.get(atom_type, [])
    payload   = {
        "title": atom_type.replace("_", " ").title(),
        "theme": "dark",
        "blocks": blocks,
    }
    raw = json.dumps(payload, ensure_ascii=False).encode()
    compressed = zlib.compress(raw, level=9, wbits=31)
    enc = base64.urlsafe_b64encode(compressed).rstrip(b'=').decode()
    return f"{GAS_RENDERER}?p={enc}"


def live_preview(atom):
    atom_type = atom.get("type", "")
    if atom_type not in _RENDERER_TYPES or _web_renderer is None:
        return ""
    block = _EXAMPLE_BLOCKS.get(atom_type) or json.loads(example_payload(atom))
    try:
        html = _web_renderer.render([block])
        if not html.strip():
            return ""
    except Exception:
        return ""
    return f"""
<div class="section">
  <div class="label">Live preview</div>
  <div class="preview-box">{html}</div>
</div>"""


def render_page(atom):
    atom_type    = atom.get("type", "")
    desc         = atom.get("description", "")
    compact      = atom.get("compact_description", "")
    display_name = atom_type.replace("_", " ").title()
    preview  = live_preview(atom)
    _surfaces = atom.get("surfaces", {}).get("works_on", [])
    _gas_only = _surfaces == ["google-apps-script-web"]
    try_btn  = (
        f'<a class="try-btn" href="{make_renderer_url(atom)}" target="_blank" rel="noopener">Try it live →</a>'
    ) if _gas_only else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{display_name} — A2UI Atomic Catalog</title>
  <meta name="description" content="{desc or compact}">
  {SITE_HEAD_JS}
  {PAGE_CSS}
</head>
<body>
  {site_header("atoms")}
  <div class="wrap">
  <nav class="crumb">
    <a href="/">A2UI Catalog</a> /
    <a href="/.well-known/ai-catalog.json">ARD Catalog</a> /
    atoms / {atom_type}
  </nav>

  <h1>{display_name}</h1>
  <p class="desc">{desc or compact}</p>

  <div class="section">
    <div class="label">Surfaces</div>
    {surface_badges(atom)}
  </div>

  {degraded_notes(atom)}

  {preview}

  <div class="section">
    <div class="label">Fields</div>
    {fields_table(atom)}
  </div>

  <div class="section">
    <div class="label">Example payload</div>
    <pre><code>{example_payload(atom)}</code></pre>
  </div>

  <div class="section">
    <div class="label">ARD catalog entry</div>
    <pre><code>{ard_entry(atom)}</code></pre>
  </div>

  <a class="back" href="/.well-known/ai-catalog.json">← Full ARD catalog</a>
  {try_btn}

  <div class="deploy-box">
    <div class="label">Deploy your own Google Apps Script renderer</div>
    <p style="font-size:13px;color:var(--muted);margin:0 0 12px;">The renderer is an open-source Google Apps Script web app. Deploy your own instance in 4 commands — you own the URL, no dependency on the demo endpoint.</p>
    <pre style="margin:0;font-size:12px;"><code>git clone https://github.com/a2uicatalog/a2ui
cd apps-script-surface/gas-schema-renderer
clasp push &amp;&amp; clasp deploy</code></pre>
    <a href="/renderer">Full deploy guide →</a>
  </div>

  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span>MIT License</span>
  </footer>
  </div>
  {SITE_FOOT_JS}
{_cursor_glow_html()}
</body>
</html>"""


INDEX_CSS = """
<style>""" + SITE_BASE_CSS + """
header.hero{margin-bottom:36px;position:relative}
.halo{position:absolute;inset:-90px -10% auto;height:260px;pointer-events:none;background:radial-gradient(ellipse 55% 100% at 50% 0%,oklch(58% 0.19 277 / .10),transparent 70%)}
:root[data-theme="dark"] .halo{background:radial-gradient(ellipse 55% 100% at 50% 0%,oklch(72% 0.16 277 / .14),transparent 70%)}
h1{position:relative;font-size:2.6rem;font-weight:800;letter-spacing:-1.5px;margin-bottom:2px;text-wrap:balance}
.tagline{position:relative;font-size:1.15rem;font-weight:700;margin-bottom:6px;letter-spacing:-.01em;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;width:fit-content}
.sub{position:relative;color:var(--muted);font-size:1rem;margin-bottom:14px}
.sub a{color:var(--accent-2);text-decoration:none}
.hero-stats{position:relative;display:flex;gap:26px;margin-bottom:22px}
.hero-stats div{font-size:12px;color:var(--muted)}
.hero-stats b{display:block;font-size:19px;font-weight:800;color:var(--text);font-variant-numeric:tabular-nums;letter-spacing:-.3px}
.entry-paths{position:relative;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px}
.entry-path{display:block;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;text-decoration:none;transition:border-color .15s,box-shadow .15s,transform .15s}
.entry-path:hover{border-color:var(--accent);box-shadow:var(--glow);transform:translateY(-1px)}
.entry-kicker{display:block;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:8px}
.entry-path h3{font-size:15px;font-weight:700;color:var(--text);margin-bottom:4px;letter-spacing:-.1px}
.entry-path p{font-size:12.5px;color:var(--muted);line-height:1.5;margin:0}
.entry-path code{font-family:ui-monospace,'SF Mono',Monaco,monospace;font-size:11.5px;background:var(--code-bg);padding:1px 5px;border-radius:4px}
@media(max-width:760px){.entry-paths{grid-template-columns:1fr}}
.launch-banner{position:relative;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--accent-soft-bg);border:1px solid var(--border);border-radius:10px;padding:12px 18px;margin-bottom:22px;text-decoration:none;transition:border-color .15s,box-shadow .15s}
.launch-banner:hover{border-color:var(--accent);box-shadow:var(--glow)}
.launch-badge{flex-shrink:0;padding:4px 12px;border-radius:999px;background:var(--accent);color:var(--accent-contrast);font-size:12px;font-weight:800;letter-spacing:.07em;text-transform:uppercase}
.launch-text{flex:1;min-width:200px;font-size:13px;color:var(--text)}
.launch-arrow{flex-shrink:0;font-size:12px;font-weight:700;color:var(--accent)}
.hero-demo{position:relative;display:grid;grid-template-columns:1fr 44px 1fr;align-items:start;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;margin-bottom:22px;box-shadow:var(--shadow)}
.hero-demo-arrow{align-self:center}
.hero-demo-label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.hero-demo-json{background:var(--code-bg);border:1px solid var(--border);border-radius:8px;padding:14px 16px;font-size:12.5px;line-height:1.55;color:var(--text);overflow-x:auto;font-family:ui-monospace,'SF Mono',Monaco,monospace;margin:0}
.hero-demo-arrow{font-size:24px;color:var(--accent);text-align:center}
.hero-demo-render{min-width:0;background:#fff;border:1px solid var(--border);border-radius:8px;padding:16px 18px;color:#1a1a1a}
.hero-demo-render h2{font-size:1.25rem;margin:0 0 10px;color:#111}
@media(max-width:760px){.hero-demo{grid-template-columns:1fr;gap:8px}.hero-demo-arrow{transform:rotate(90deg);padding:4px 0}}
.showcase-frame{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;margin-bottom:22px}
.showcase-bar{display:flex;align-items:center;gap:12px;padding:9px 14px;background:var(--surface-2);border-bottom:1px solid var(--border)}
.showcase-traffic{display:flex;gap:5px}
.showcase-traffic i{width:8px;height:8px;border-radius:50%;background:var(--border-strong);display:block;opacity:.7}
.showcase-label{font-size:11.5px;color:var(--muted);font-family:ui-monospace,'SF Mono',Monaco,monospace}
.showcase-name{color:var(--accent);font-weight:700}
.showcase-stage{position:relative;height:168px;background:#0b0f1a}
.showcase-slide{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:18px;opacity:0;transition:opacity .5s ease;pointer-events:none}
.showcase-slide.active{opacity:1;pointer-events:auto}
.showcase-nav{display:flex;justify-content:center;gap:6px;padding:10px;background:var(--surface)}
.showcase-dot{width:6px;height:6px;padding:0;border-radius:50%;border:none;background:var(--border-strong);cursor:pointer;transition:background .15s,transform .15s}
.showcase-dot.active{background:var(--accent);transform:scale(1.3)}
@media(prefers-reduced-motion:reduce){.showcase-slide{transition:none}}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:28px}
#search{flex:1;min-width:220px;background:var(--surface);border:1px solid var(--border);border-radius:11px;padding:11px 16px;font-size:14px;color:var(--text);outline:none;box-shadow:var(--shadow);transition:border-color .15s,box-shadow .15s}
#search:focus{border-color:var(--accent);box-shadow:var(--glow)}
#search::placeholder{color:var(--muted)}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.filter{font-size:13px;font-weight:650;padding:5px 14px;border-radius:100px;border:1px solid var(--border);background:var(--surface);color:var(--muted);cursor:pointer;letter-spacing:.02em;text-decoration:none;transition:all .15s}
.filter:hover{border-color:var(--border-strong);color:var(--text)}
.filter.active{background:var(--accent-soft-bg);color:var(--accent);border-color:transparent}
.count{font-size:12px;color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.atom-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;text-decoration:none;display:flex;flex-direction:column;transition:transform .16s ease,border-color .16s,box-shadow .16s;content-visibility:auto;contain-intrinsic-size:auto 240px}
.atom-card:hover{border-color:var(--accent);box-shadow:var(--glow);transform:translateY(-2px)}
.stage{height:104px;overflow:hidden;flex-shrink:0;background:#fff;background-image:radial-gradient(#e9ebf3 1px,transparent 1px);background-size:14px 14px;border-bottom:1px solid var(--border)}
.stage-inner{width:200%;transform:scale(.5);transform-origin:top left;padding:16px;pointer-events:none;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6;color:#1a1a1a}
.stage-inner *{max-width:100%}
.stage-empty{display:grid;place-items:center}
.stage-empty code{font-family:ui-monospace,'SF Mono',Monaco,monospace;font-size:12px;color:#6b7280;background:#f2f3f8;border:1px solid #e2e4ee;border-radius:6px;padding:4px 10px}
.card-meta{padding:12px 15px 13px;display:flex;flex-direction:column;flex:1}
.atom-card h3{font-size:13.5px;font-weight:700;color:var(--text);margin-bottom:3px}
.atom-card p{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-footer{display:flex;justify-content:space-between;align-items:flex-end;gap:6px;margin-top:auto}
.badges{display:flex;flex-wrap:wrap;gap:4px;flex:1;align-items:center}
.badge{font-size:11px;font-weight:650;padding:3px 9px;border-radius:6px}
.bs{background:var(--surface-2);color:var(--muted)}
.bd{background:color-mix(in oklch,var(--warn) 14%,var(--surface));color:var(--warn)}
.bnew{background:var(--accent-soft-bg);color:var(--accent)}
.badge-more{font-size:11px;color:var(--muted);white-space:nowrap}
.origin{font-size:9px;font-weight:700;padding:2px 6px;border-radius:100px;letter-spacing:.06em;white-space:nowrap;flex-shrink:0;background:var(--surface-2);color:var(--muted)}
.hidden{display:none}
</style>
"""

INDEX_JS = """
<script>
const search = document.getElementById('search');
const cards  = Array.from(document.querySelectorAll('.atom-card'));
const counter = document.getElementById('count');
let activeFilter = 'all';

function update() {
  const q = search.value.toLowerCase();
  let shown = 0;
  cards.forEach(c => {
    const matchQ = !q || c.dataset.name.includes(q) || c.dataset.desc.includes(q);
    const matchF = activeFilter === 'all' || c.dataset.surfaces.includes(activeFilter);
    const show = matchQ && matchF;
    c.classList.toggle('hidden', !show);
    if (show) shown++;
  });
  counter.textContent = shown + ' atoms';
}

document.querySelectorAll('.filter').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.surface;
    update();
  });
});

search.addEventListener('input', update);
</script>
"""


# Preview-first cards (v0.3): the hub card renders a MINIATURE of its atom —
# the catalog's own thesis (JSON in, UI out) applied to the browse page.
# Guards (all logged, never silent): script-bearing previews are skipped
# (467 inline scripts on one page), oversized previews are skipped (page
# weight), and skipped atoms fall back to a mono type-chip stage so the grid
# rhythm holds. content-visibility:auto keeps offscreen cards unrendered.
_PREVIEW_MAX_CHARS = 3500
_preview_stats = {"rendered": 0, "no_renderer": 0, "script": 0, "oversize": 0, "error": 0}


def card_stage(atom):
    atom_type = atom.get("type", "")
    reason = None
    html = ""
    if atom_type not in _RENDERER_TYPES or _web_renderer is None:
        reason = "no_renderer"
    else:
        block = _EXAMPLE_BLOCKS.get(atom_type) or json.loads(example_payload(atom))
        try:
            html = _web_renderer.render([block])
        except Exception:
            reason = "error"
        else:
            low = html.lower()
            if not html.strip():
                reason = "error"
            elif "<script" in low:
                reason = "script"
            elif "<iframe" in low:
                # embeds (YouTube etc.) would fire real network loads per card
                reason = "script"
            elif len(html) > _PREVIEW_MAX_CHARS:
                reason = "oversize"
            elif low.count("<div") != low.count("</div"):
                # unbalanced markup would eat the card's own structure
                reason = "error"
    if reason:
        _preview_stats[reason] += 1
        return f'<div class="stage stage-empty"><code>{atom_type}</code></div>'
    # The whole card is an <a>; nested anchors are illegal HTML and make the
    # parser close the card early (meta spills out unstyled). Previews are
    # pointer-events:none decoration — neutralize links to spans.
    html = re.sub(r"<a\b", "<span", html).replace("</a>", "</span>")
    _preview_stats["rendered"] += 1
    return f'<div class="stage"><div class="stage-inner">{html}</div></div>'


def _showcase_html(slides):
    """Small browser mockup, cross-fading through hand-picked striking atoms —
    lands above the fold so a first-time visitor sees something impressive
    before they'd ever scroll to the grid. See _SHOWCASE_BLOCKS for selection
    criteria (self-contained only — no document/window-scoped effects)."""
    if not slides:
        return ""
    dots = "".join(
        f'<button class="showcase-dot{" active" if i == 0 else ""}" data-i="{i}" '
        f'aria-label="Show {name}"></button>'
        for i, (name, _) in enumerate(slides)
    )
    def _neutralize(html):
        return re.sub(r"<a\b", "<span", html).replace("</a>", "</span>")

    panes = "".join(
        f'<div class="showcase-slide{" active" if i == 0 else ""}" data-i="{i}">'
        f'{_neutralize(html)}</div>'
        for i, (name, html) in enumerate(slides)
    )
    return f'''<div class="showcase-frame">
      <div class="showcase-bar">
        <span class="showcase-traffic"><i></i><i></i><i></i></span>
        <span class="showcase-label">a2uicatalog.ai/atoms/<b class="showcase-name">{slides[0][0]}</b></span>
      </div>
      <div class="showcase-stage">{panes}</div>
      <div class="showcase-nav">{dots}</div>
    </div>
    <script>(function(){{
      var names={json.dumps([n for n, _ in slides])};
      var slides=document.querySelectorAll(".showcase-slide"),dots=document.querySelectorAll(".showcase-dot"),
          label=document.querySelector(".showcase-name");
      if(!slides.length)return;
      var i=0;
      function show(n){{
        i=n;
        slides.forEach(function(s,k){{s.classList.toggle("active",k===i)}});
        dots.forEach(function(d,k){{d.classList.toggle("active",k===i)}});
        if(label)label.textContent=names[i];
      }}
      dots.forEach(function(d){{d.addEventListener("click",function(){{show(+d.dataset.i)}})}});
      if(!window.matchMedia("(prefers-reduced-motion: reduce)").matches){{
        setInterval(function(){{show((i+1)%slides.length)}},3200);
      }}
    }})();</script>'''


def generate_index(atoms):
    all_surfaces = []
    for atom in atoms:
        for s in (atom.get("surfaces") or {}).get("works_on") or []:
            if s not in all_surfaces:
                all_surfaces.append(s)

    filter_pills = '<button class="filter active" data-surface="all">All</button>'
    for s in sorted(all_surfaces):
        if s not in HIDDEN_SURFACES:
            label = SURFACE_NAMES.get(s, s)
            filter_pills += f'<a class="filter" href="/surfaces/{s}" data-surface="{s}">{label}</a>'

    cards_html = ""
    for atom in atoms:
        atom_type = atom.get("type", "")
        desc      = atom.get("compact_description") or atom.get("description", "")
        surfaces  = (atom.get("surfaces") or {}).get("works_on") or []
        degraded  = {d["surface"] for d in ((atom.get("surfaces") or {}).get("degraded_on") or [])}
        display   = atom_type.replace("_", " ").title()
        source     = (atom.get("source") or {}).get("name", "a2ui").lower()
        origin_label = "a2uicatalog" if source == "a2ui" else source
        origin_cls = {"a2ui": "origin-a2ui", "uiverse": "origin-uiverse", "openui": "origin-openui"}.get(source, "origin-other")
        origin_html = f'<span class="origin {origin_cls}">{origin_label}</span>'
        visible_surfaces = [s for s in surfaces if s not in HIDDEN_SURFACES]
        # Chip inversion: chips only for notable/degraded surfaces; the common
        # bulk collapses to a count (data-surfaces keeps the full list, so the
        # filter row is unaffected). Small surface lists just show everything.
        if len(visible_surfaces) <= 3:
            shown = visible_surfaces
        else:
            shown = [s for s in visible_surfaces
                     if s in NOTABLE_SURFACES or s in degraded]
        rest = [s for s in visible_surfaces if s not in shown]

        def _chip_cls(s):
            if s in degraded:
                return "bd"
            return "bnew" if s in NOTABLE_SURFACES else "bs"

        badges = "".join(
            f'<span class="badge {_chip_cls(s)}">{SURFACE_NAMES.get(s, s)}</span>'
            for s in shown
        )
        if rest:
            more_label = f"+{len(rest)} surfaces" if shown else f"{len(rest)} surfaces"
            badges += f'<span class="badge-more">{more_label}</span>'
        surfaces_str = " ".join(visible_surfaces)
        cards_html += (
            f'<a class="atom-card" href="/atoms/{atom_type}" '
            f'data-name="{atom_type}" data-desc="{desc.lower()}" data-surfaces="{surfaces_str}">'
            f'{card_stage(atom)}'
            f'<div class="card-meta"><h3>{display}</h3><p>{desc}</p>'
            f'<div class="card-footer"><div class="badges">{badges}</div>{origin_html}</div></div></a>\n'
        )

    # The concept, performed rather than described: a real payload rendered by
    # the real web renderer at generate time. This is the one artifact on the
    # page that shows what an "atom" IS — JSON in, UI out.
    demo_blocks = [
        {"type": "gradient_heading", "text": "One schema. Any surface."},
    ]
    demo_json = json.dumps({"blocks": demo_blocks}, indent=2)
    demo_json = demo_json.replace("&", "&amp;").replace("<", "&lt;")
    demo_render = _web_renderer.render(demo_blocks)

    # Showcase strip — a curated set of visually striking atoms, cross-fading
    # in a small browser mockup right in the hero (above the fold on load).
    # First-page impression matters: if something looks cool immediately,
    # visitors stick around before scrolling. Hand-picked, not random — and
    # deliberately excludes viewport-following effects (cursor_glow/cursor_trail/
    # spotlight_cursor) that attach to document/window and would either fight
    # the page's own live cursor_glow or leak outside a clipped preview box.
    _SHOWCASE_BLOCKS = [
        ("glowing_stat", {"type": "glowing_stat", "value": "99.98%", "label": "Uptime", "colour": "#22d3ee"}),
        ("kinetic_headline", {"type": "kinetic_headline", "text": "Declarative for agents, useful for humans.", "style": "up", "size": "clamp(1.2rem,2.6vw,1.7rem)"}),
        ("terminal_boot", {"type": "terminal_boot", "title": "deploy.sh", "lines": ["$ a2ui deploy", "✓ schema validated", "✓ renderer live"]}),
        ("mesh_gradient", {"type": "mesh_gradient", "title": "One vocabulary", "text": "467 atoms, every surface"}),
        ("github_activity_grid", {"type": "github_activity_grid", "title": "Shipping daily"}),
        ("animated_counter", {"type": "animated_counter", "counters": [{"value": 467, "label": "atoms", "color": "#f4f4f5"}]}),
    ]
    showcase_slides = []
    for name, block in _SHOWCASE_BLOCKS:
        try:
            html = _web_renderer.render([block])
            if html.strip():
                showcase_slides.append((name, html))
        except Exception as e:
            print(f"WARNING: showcase atom '{name}' failed to render ({e}) — skipped", file=sys.stderr)
    if not showcase_slides:
        print("WARNING: all showcase atoms failed to render — showcase strip omitted", file=sys.stderr)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>A2UI Atomic Catalog</title>
  <meta name="description" content="467 typed UI atoms for web, Google Meet, Apps Script, and Chat. ARD-compliant catalog.">
  <link rel="ai-catalog" type="application/json" href="/.well-known/ai-catalog.json">
  {SITE_HEAD_JS}
  {INDEX_CSS}
</head>
<body>
  {site_header("atoms")}
  <div class="wrap">
  <header class="hero">
    <div class="halo"></div>
    <h1>A2UI Atomic Catalog</h1>
    <p class="tagline">Useful for Humans. Declarative for AI Agents.</p>
    <p class="sub">{len(atoms)} typed atoms for web, Meet, Apps Script, Chat &middot; <a href="/.well-known/ai-catalog.json">ARD catalog</a> &middot; <a href="https://github.com/a2uicatalog/a2ui">GitHub</a></p>
    <div class="hero-stats">
      <div><b>{len(atoms)}</b>atoms</div>
      <div><b>{len([s for s in all_surfaces if s not in HIDDEN_SURFACES])}</b>surfaces</div>
      <div><b>v1.0.0</b>spec</div>
    </div>
    <div class="entry-paths">
      <a class="entry-path" href="#grid">
        <span class="entry-kicker">Browse</span>
        <h3>Explore the catalog</h3>
        <p>Search and preview {len(atoms)} atoms live, right on this page.</p>
      </a>
      <a class="entry-path" href="/surfaces/mcp-apps">
        <span class="entry-kicker">Integrate</span>
        <h3>Connect an agent</h3>
        <p>MCP server at <code>a2uicatalog.ai/mcp</code> — an agent composes real UI from this vocabulary.</p>
      </a>
      <a class="entry-path" href="/renderer">
        <span class="entry-kicker">Self-host</span>
        <h3>Deploy your own renderer</h3>
        <p>Apps Script web app, 4 commands — you own the URL.</p>
      </a>
    </div>
    <a class="launch-banner" href="/surfaces/mcp-apps">
      <span class="launch-badge">Just launched</span>
      <span class="launch-text">MCP Apps is a first-class surface — catalog atoms and curated content, live inside a sandboxed MCP host</span>
      <span class="launch-arrow">See it launch →</span>
    </a>
    <div class="hero-demo">
      <div class="hero-demo-col">
        <div class="hero-demo-label">An agent emits JSON</div>
        <pre class="hero-demo-json">{demo_json}</pre>
      </div>
      <div class="hero-demo-arrow">→</div>
      <div class="hero-demo-col">
        <div class="hero-demo-label">A surface renders it</div>
        <div class="hero-demo-render">{demo_render}</div>
      </div>
    </div>
    {_showcase_html(showcase_slides)}
    <div class="controls">
      <input id="search" type="search" placeholder="Search atoms…" autocomplete="off">
      <div class="filters">{filter_pills}</div>
      <span class="count" id="count">{len(atoms)} atoms</span>
    </div>
  </header>
  <div class="grid" id="grid">
{cards_html}  </div>
  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span><a href="/.well-known/ai-catalog.json">ARD catalog JSON</a></span>
  </footer>
  </div>
  {INDEX_JS}
  {SITE_FOOT_JS}
{_cursor_glow_html()}
</body>
</html>"""


SURFACE_NAMES = {
    "web":                          "Web",
    "google-meet-stage":            "Google Meet Stage",
    "google-apps-script-web":       "Apps Script Web",
    "google-chat":                  "Google Chat",
    "google-apps-script-side-panel":"Apps Script Side Panel",
    "email":                        "Email",
    "pdf":                          "PDF",
    "mcp-apps":                     "MCP Apps",
}

GAS_SURFACES = {"google-meet-stage", "google-apps-script-web", "google-apps-script-side-panel", "google-chat"}

# Hand-authored launch hero for the mcp-apps surface page, prepended above the
# schema-driven atom gallery every other surface gets unmodified. Not a parallel
# pipeline -- see generate_surface_page()'s single MCP_APPS_HERO_HTML branch.
# Ported content: same protocol handshake + rocket demo built for
# public/mcp-apps-demo/ this session (a2ui-private/spec/mcp-apps-surface-v0.1.md v0.2).
MCP_APPS_HERO_HTML = """
<style>
:root{--mcp-indigo:#6366f1}
.mcp-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:999px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.4);color:var(--mcp-indigo);font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:16px}
.mcp-note{background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.2);border-radius:8px;padding:16px 20px;font-size:13px;color:var(--muted);margin:0 0 20px}
.mcp-note strong{color:var(--text)}
.mcp-status{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.mcp-status-dot{width:8px;height:8px;border-radius:50%;background:var(--muted);flex-shrink:0;transition:background .2s}
.mcp-status-dot.live{background:var(--green);box-shadow:0 0 8px rgba(63,185,80,.6)}
.mcp-status-dot.err{background:var(--negative)}
.mcp-host-frame{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:32px}
.mcp-host-frame iframe{width:100%;min-height:920px;border:0;display:block;background:#fff}
.mcp-protocol-note{font-size:13px;color:var(--muted);margin-bottom:40px;padding-top:20px;border-top:1px solid var(--border)}
.mcp-protocol-note code{background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1px 6px;font-family:'SF Mono',Monaco,monospace;font-size:12px;color:var(--text)}
.mcp-playground{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px 20px;margin-bottom:32px}
.mcp-playground-label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--mcp-indigo);margin-bottom:10px}
.mcp-playground textarea{width:100%;min-height:220px;background:var(--code-bg);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-family:'SF Mono',Monaco,monospace;font-size:12.5px;line-height:1.55;color:var(--text);resize:vertical;box-sizing:border-box}
.mcp-playground textarea:focus{outline:none;border-color:var(--mcp-indigo)}
.mcp-playground-row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}
.mcp-play-btn{padding:8px 20px;border-radius:8px;border:none;background:var(--mcp-indigo);color:#fff;cursor:pointer;font-size:13px;font-weight:700}
.mcp-play-btn:hover{background:#818cf8}
.mcp-play-btn.ghost{background:transparent;border:1px solid var(--border);color:var(--muted)}
.mcp-play-btn.ghost:hover{border-color:var(--mcp-indigo);color:var(--mcp-indigo)}
.mcp-play-err{font-size:12px;color:#f85149;min-height:16px;flex:1}
.mcp-presets{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.mcp-preset-chip{padding:5px 14px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;font-size:12px;font-weight:700;letter-spacing:.03em}
.mcp-preset-chip:hover{border-color:var(--mcp-indigo,#6366f1);color:var(--mcp-indigo,#6366f1)}
</style>

<div class="mcp-badge">Just launched · MCP Apps surface</div>
<p class="desc" style="max-width:640px;margin-bottom:24px">This page <strong>is</strong> a minimal MCP Apps Host — the same sandboxed iframe, the same <code>ui/initialize</code> JSON-RPC handshake a real chat client (claude.ai, Claude Desktop) uses to render an MCP server's UI resource. Catalog atoms and hand-curated content render side by side, both mediated the same way.</p>

<div class="mcp-note">
  <strong>What's real vs. simulated:</strong> the sandboxed iframe, the postMessage handshake, and the renderer are the genuine MCP Apps protocol and genuine catalog atom code. What's simulated is the tool call — this page feeds the view a fixed fixture payload instead of a live round-trip to <code>a2uicatalog.ai/mcp</code>, so you can see it work without installing an MCP client.
</div>

<div class="mcp-note">
  <strong>The fireworks aren't a catalog atom</strong> — that's <code>iso_fireworks_panel</code>, hand-curated content (<code>stage: preview</code>, no typed fields), rendered in the same surface, through the same block dispatch, right alongside the stable catalog atoms below it. The rocket that used to hold this slot? It <strong>graduated</strong>: <code>gdm_rocket_panel</code> is now a stable catalog atom with typed fields (<code>side</code>, <code>layer</code>, <code>loop</code>) and a published page. That's the actual point: MCP Apps' controlled opaqueness isn't just coexistence — it's the catalog's intake pipeline. Curated content ships first through the Host's mediated channel (never a raw DOM handoff), and what proves out becomes schema.
</div>

<div class="mcp-status">
  <span class="mcp-status-dot" id="mcp-status-dot"></span>
  <span id="mcp-status-text">Connecting to view…</span>
</div>

<div class="mcp-host-frame">
  <!-- allow-popups(-to-escape-sandbox): every link-bearing atom emits
       target="_blank" — without these tokens the sandbox silently
       swallows ALL outbound clicks (no error, nothing happens). Found
       2026-07-11 auditing chip_group; -escape-sandbox keeps the new tab
       itself unsandboxed rather than inheriting these restrictions. -->
  <iframe id="mcp-view" sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox" src="./renderer-bundle.html?v=__BUNDLE_HASH__" title="A2UI MCP Apps view"></iframe>
</div>

<div class="mcp-playground">
  <div class="mcp-playground-label">Playground — edit the payload, re-render the view · <a href="./play/" style="color:var(--mcp-indigo)">Open full-screen →</a></div>
  <div class="mcp-presets" id="mcp-presets"></div>
  <textarea id="mcp-playground-json" spellcheck="false" aria-label="A2UI payload JSON"></textarea>
  <div class="mcp-playground-row">
    <button class="mcp-play-btn" id="mcp-play-render">Render →</button>
    <button class="mcp-play-btn ghost" id="mcp-play-link">Copy link</button>
    <button class="mcp-play-btn ghost" id="mcp-play-publish">Short link…</button>
    <span class="mcp-play-err" id="mcp-play-err"></span>
  </div>
</div>

<p class="mcp-protocol-note">
  Handshake: the iframe (the <strong>View</strong>) posts <code>ui/initialize</code> to this page (the <strong>Host</strong>) on load. This page replies with a <code>McpUiInitializeResult</code>, the View acknowledges with <code>ui/notifications/initialized</code>, and this page then delivers the payload via <code>ui/notifications/tool-result</code> — the exact message sequence defined in the MCP Apps spec (<a href="https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx" target="_blank" rel="noopener">apps.mdx</a>). No <code>allow-same-origin</code> on the iframe — the View genuinely cannot reach this page's DOM.
</p>

<script>
__MCP_APPS_HOST_JS__
</script>

<script>
/* Graduation flyby — the rocket that earned its way out of this page's
   off-catalog slot climbs the right edge on a continuous loop (each pass
   starts below the fold, so there's a natural beat between launches).
   Standalone page chrome: the atom's real renderer lives inside the
   sandboxed iframe and can't reach this document (that's the point of the
   sandbox), so this is a compact re-draw in the same visual language.
   Skipped entirely under prefers-reduced-motion. */
(function(){
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var cv = document.createElement('canvas');
  cv.style.cssText = 'position:fixed;top:0;right:0;width:200px;height:100%;pointer-events:none;z-index:60;';
  document.body.appendChild(cv);
  var ctx = cv.getContext('2d');
  function resize(){ cv.width = 200; cv.height = window.innerHeight; }
  window.addEventListener('resize', resize); resize();
  var trail = [], t0 = null, DUR = 4600, S = 26;
  function drawRocket(cx, cy, s){
    var pulse = 0.85 + 0.15*Math.sin(Date.now()/90);
    var glow = ctx.createRadialGradient(cx, cy+s*1.05, 0, cx, cy+s*1.05, s*1.5*pulse);
    glow.addColorStop(0,'rgba(255,255,200,0.98)');
    glow.addColorStop(0.12,'rgba(255,180,0,0.9)');
    glow.addColorStop(0.4,'rgba(255,60,0,0.55)');
    glow.addColorStop(1,'rgba(255,20,0,0)');
    ctx.beginPath(); ctx.arc(cx, cy+s*1.05, s*1.5*pulse, 0, Math.PI*2);
    ctx.fillStyle = glow; ctx.fill();
    ctx.save(); ctx.translate(cx, cy);
    ctx.beginPath(); ctx.moveTo(-s*0.28,s*0.55); ctx.lineTo(-s*0.72,s*1.02); ctx.lineTo(-s*0.28,s*0.82);
    ctx.closePath(); ctx.fillStyle = '#0077b6'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(s*0.28,s*0.55); ctx.lineTo(s*0.72,s*1.02); ctx.lineTo(s*0.28,s*0.82);
    ctx.closePath(); ctx.fillStyle = '#0077b6'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(-s*0.22,s*0.68); ctx.lineTo(-s*0.3,s*0.98); ctx.lineTo(s*0.3,s*0.98); ctx.lineTo(s*0.22,s*0.68);
    ctx.closePath();
    var bell = ctx.createLinearGradient(-s*0.3,0,s*0.3,0);
    bell.addColorStop(0,'#4cc9f0'); bell.addColorStop(0.5,'#e0f7ff'); bell.addColorStop(1,'#4cc9f0');
    ctx.fillStyle = bell; ctx.fill();
    var body = ctx.createLinearGradient(-s*0.28,0,s*0.28,0);
    body.addColorStop(0,'#0a8cce'); body.addColorStop(0.25,'#00c8f0'); body.addColorStop(0.55,'#c8f4ff');
    body.addColorStop(0.8,'#00c8f0'); body.addColorStop(1,'#0a6ca0');
    ctx.beginPath(); ctx.roundRect(-s*0.28,-s*0.6,s*0.56,s*1.3,s*0.05);
    ctx.fillStyle = body; ctx.fill();
    ctx.beginPath();
    ctx.moveTo(0,-s*1.05);
    ctx.bezierCurveTo(-s*0.07,-s*0.78,-s*0.24,-s*0.68,-s*0.28,-s*0.6);
    ctx.lineTo(s*0.28,-s*0.6);
    ctx.bezierCurveTo(s*0.24,-s*0.68,s*0.07,-s*0.78,0,-s*1.05);
    ctx.closePath();
    var nose = ctx.createLinearGradient(-s*0.28,0,s*0.28,0);
    nose.addColorStop(0,'#0a6ca0'); nose.addColorStop(0.45,'#d8f8ff'); nose.addColorStop(1,'#0a6ca0');
    ctx.fillStyle = nose; ctx.fill();
    ctx.restore();
  }
  function frame(ts){
    if (!t0) t0 = ts;
    var p = (ts - t0) / DUR;
    if (p > 1.2) { t0 = ts; trail = []; p = 0; }   // trail faded — relaunch
    var h = cv.height, cx = cv.width*0.5 + Math.sin(p*9)*3;
    // accelerating climb: below the fold -> off the top
    var cy = (h + S*2) - (h + S*6) * p * p * (0.35 + 0.65*p);
    ctx.clearRect(0, 0, cv.width, cv.height);
    if (p <= 1) {
      trail.push({x: cx + (Math.random()-0.5)*S*0.08, y: cy + S*0.98, t: Date.now(), r: 2 + Math.random()*3});
    }
    trail = trail.filter(function(q){ return Date.now() - q.t < 300; });
    trail.forEach(function(q){
      var age = (Date.now() - q.t) / 300, a = (1-age)*0.7, r = q.r*(1+age*3);
      var g = ctx.createRadialGradient(q.x, q.y, 0, q.x, q.y, r);
      g.addColorStop(0, 'rgba(255,230,100,' + a + ')');
      g.addColorStop(0.4, 'rgba(255,90,0,' + (a*0.7) + ')');
      g.addColorStop(1, 'rgba(255,20,0,0)');
      ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, Math.PI*2); ctx.fillStyle = g; ctx.fill();
    });
    if (p <= 1) {
      drawRocket(cx, cy, S);
      /* the telemetry overlay from the atom version, towed below the rocket */
      var alt = Math.round(p*28000).toLocaleString(), spd = Math.round(80 + p*2200);
      ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center';
      /* ink follows the page theme — black was invisible on dark, green on light */
      ctx.fillStyle = document.documentElement.getAttribute('data-theme') === 'dark'
        ? 'rgba(235,245,255,0.75)' : 'rgba(0,0,0,0.85)';
      ctx.fillText('MCP APPS · A2UI CATALOG', cx, Math.min(h-16, cy + S*2.6));
      ctx.fillText('ALT ' + alt + ' ft · ' + (spd > 380 ? 'MACH 2+' : spd + ' kt'), cx, Math.min(h-4, cy + S*2.6 + 13));
    }
    requestAnimationFrame(frame);
  }
  setTimeout(function(){ requestAnimationFrame(frame); }, 900);
})();
</script>
"""

# Hand-picked demo schemas for the playground preset chips. Every payload
# here is covered by tests/test_mcp_apps_bundle.py::test_presets_render —
# a demo that rots fails CI, it doesn't fail on stage. Injected into
# MCP_APPS_HOST_JS below; chips render in both the hero and the play page.
PLAYGROUND_PRESETS = [
    {"id": "launch", "label": "Launch demo", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "heading", "level": 2, "text": "Catalog atoms — and curated content — live inside an MCP App"},
            {"type": "iso_fireworks_panel"},
            {"type": "stat_card", "value": "1", "label": "Atom just graduated", "delta": "preview → stable", "is_up": True},
            {"type": "body", "text": "The fireworks on the right are **not a catalog atom** — hand-curated content, rendered through the same block dispatch as everything here. The rocket that used to hold this slot just **graduated** into the catalog as `gdm_rocket_panel`, a stable atom with typed fields (see the Rocket preset). All of it arrived over one **ui/notifications/tool-result** message, exactly as a real MCP server delivers after a tool call."},
            {"type": "chip_group", "chips": [
                {"label": "MCP Apps", "active": True}, {"label": "Apps Script Web"},
                {"label": "Meet Stage"}, {"label": "Chat"}, {"label": "Email"},
                {"label": "PDF"}, {"label": "Side Panel"}, {"label": "Web"}]},
            {"type": "chartjs_bar", "title": "Atoms per surface (stable)",
             "labels": ["GAS Web", "MCP Apps", "Web", "Meet"], "values": [460, 462, 210, 190]},
            {"type": "paragraph", "text": "The sandbox has no `allow-same-origin`: this view cannot read or touch the parent page — true for the curated visual and the catalog atoms alike."},
            {"type": "flashcard_deck", "accent": "#00b8c4", "label_front": "PROTOCOL", "label_back": "ANSWER",
             "cards": [
                {"front": "What delivers this payload?", "back": "ui/notifications/tool-result, sent by the Host after ui/initialize completes."},
                {"front": "What renders it?", "back": "The same renderAtoms() the GAS catalog renderer uses in production — concatenated, not rewritten."},
                {"front": "Where's the model in this loop?", "back": "Between chat and tool call — the view itself only talks to the Host, never the network."}]},
        ]}},
    {"id": "rocket", "label": "Rocket (graduated)", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "heading", "level": 2, "text": "gdm_rocket_panel — graduated preview → stable"},
            {"type": "gdm_rocket_panel", "side": "right", "loop": True},
            {"type": "body", "text": "This launch animation began as hand-curated, field-less content in this demo's off-catalog slot. It has since **graduated into the catalog**: typed fields, schema validation, a published atom page. This render sets `loop: true` — the original Meet Stage component's ambient relaunch, now a field instead of a fork."},
            {"type": "stat_card", "value": "3", "label": "Typed fields earned", "delta": "side · layer · loop", "is_up": True},
            {"type": "paragraph", "text": "The fireworks in the Launch demo now hold the off-catalog slot this rocket came through. Same doorway, next candidate."},
        ]}},
    {"id": "dashboard", "label": "Ops dashboard", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "heading", "text": "Ops Review — Q3"},
            {"type": "stat_card", "value": "€2.4M", "label": "Revenue", "delta": "+18%", "is_up": True},
            {"type": "progress_bar", "value": 72, "label": "Quarter target"},
            {"type": "chartjs_bar", "title": "Signups by week", "labels": ["W1", "W2", "W3", "W4"], "values": [120, 180, 240, 310]},
            {"type": "sparkline", "data": [4, 7, 5, 9, 12, 11, 15], "color": "#00f2ff"},
            {"type": "data_grid", "title": "Deployments",
             "columns": [{"header": "Service", "key": "name"}, {"header": "Status", "key": "status"}],
             "rows": [{"name": "web", "status": "live"}, {"name": "meet", "status": "beta"}, {"name": "mcp-apps", "status": "live"}]},
        ]}},
    {"id": "study", "label": "Study kit", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "heading", "text": "Course map"},
            {"type": "module_map", "title": "A2UI in a day", "columns": 2, "modules": [
                {"title": "Atoms", "description": "The vocabulary", "duration": "10 min", "icon": "🧩"},
                {"title": "Payloads", "description": "JSON in, UI out", "duration": "15 min", "icon": "📦"},
                {"title": "Surfaces", "description": "Eight render targets", "duration": "20 min", "icon": "🖥️"},
                {"title": "MCP Apps", "description": "The chat surface", "duration": "25 min", "icon": "⚡"}]},
            {"type": "progress_bar", "value": 25, "label": "Module 1 of 4"},
            {"type": "flashcard_deck", "accent": "#6366f1", "cards": [
                {"front": "What is an atom?", "back": "A typed UI block an agent can emit as JSON."},
                {"front": "What renders it here?", "back": "The catalog renderer, inside a sandboxed MCP Apps view."}]},
        ]}},
    {"id": "airspace", "label": "Airspace radar", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "adsb_feed", "name": "adsb1", "refresh": 15},
            {"type": "metar_feed", "name": "wx1", "station": "LFBO"},
            {"type": "airspace_command_deck", "height": "fullscreen",
             "data_source": "adsb1", "weather_source": "wx1",
             "chyron_title": "LFBO TMA", "chyron_subtitle": "Toulouse Blagnac Approach Control",
             "ticker_text": "✈ A2UI CATALOG PLAYGROUND · MCP APPS VIEW · LIVE ADS-B VIA DECLARED DATA PROXY · SIMULATED UNTIL THE FEED ANSWERS ✈"}]}},
    {"id": "editorial", "label": "Editorial", "payload": {
        "theme": "dark",
        "blocks": [
            {"type": "article_hero", "title": "The Meeting Is the Interface", "subtitle": "Notes on agent-native UI"},
            {"type": "quote", "text": "The catalog is a vocabulary. The payload is a sentence.", "attribution": "a2uithoughts.md"},
            {"type": "timeline", "title": "How we got here", "events": [
                {"date": "May 2026", "label": "GAS jail", "text": "One URL renders a full app."},
                {"date": "June 2026", "label": "Meet Stage", "text": "Same atoms, broadcast to every screen."},
                {"date": "July 2026", "label": "MCP Apps", "text": "Same renderer, inside the chat surface."}]},
            {"type": "key_takeaways", "items": [
                "Declarative payloads travel anywhere",
                "One renderer source, eight surfaces",
                "Paste a schema — that IS the demo"]},
        ]}},
    {"id": "ariane", "label": "Ariane 6", "payload": {
        "theme": "dark",
        "blocks": [{"type": "geo_iso_rocket_launch"}]}},
]


# Host-side handshake + playground logic, shared VERBATIM by the surface-page
# hero and the full-screen play page (same element ids in both DOMs) — one
# implementation, zero drift. Substituted into both page templates below.
MCP_APPS_HOST_JS = r"""
(function () {
  var iframe = document.getElementById('mcp-view');
  var dot = document.getElementById('mcp-status-dot');
  var text = document.getElementById('mcp-status-text');

  function setStatus(cls, msg) {
    dot.className = 'mcp-status-dot' + (cls ? ' ' + cls : '');
    text.textContent = msg;
  }

  // Presets injected from PLAYGROUND_PRESETS in the generator — every payload
  // is CI-rendered through the real bundle. PRESETS[0] is the Launch demo and
  // doubles as the default fixture, so the flagship demo is itself tested.
  var PRESETS = __MCP_APPS_PRESETS__;
  var FIXTURE = {
    content: [{ type: 'text', text: 'Rendered A2UI atoms in the MCP Apps view.' }],
    structuredContent: PRESETS[0].payload
  };

  // ---- playground wiring ----
  var editor = document.getElementById('mcp-playground-json');
  var renderBtn = document.getElementById('mcp-play-render');
  var linkBtn = document.getElementById('mcp-play-link');
  var editorTouched = false;
  if (typeof editor !== 'undefined' && editor) {
    editor.addEventListener('input', function () { editorTouched = true; });
  }

  // ── Create short link: the HUMAN consent gate (mirror of the agent-side
  // acknowledge_storage schema requirement). Two-step, in-page, terms first.
  var publishBtn = document.getElementById('mcp-play-publish');
  if (publishBtn) publishBtn.addEventListener('click', function () {
    errEl.textContent = '';
    if (publishBtn.getAttribute('data-armed') !== '1') {
      publishBtn.setAttribute('data-armed', '1');
      publishBtn.textContent = 'Store & create — yes';
      errEl.textContent = 'Short links work by STORING this payload on a2uicatalog.ai for one week. ' +
        'Anyone with the link can view it. You get a delete code to remove it early. ' +
        'Click again to proceed, or wait to cancel.';
      setTimeout(function () {
        publishBtn.setAttribute('data-armed', '0');
        publishBtn.textContent = 'Short link…';
      }, 15000);
      return;
    }
    publishBtn.setAttribute('data-armed', '0');
    publishBtn.textContent = 'Short link…';
    var payload;
    try { payload = normalize(JSON.parse(editor.value)); }
    catch (e) { errEl.textContent = 'Invalid JSON: ' + e.message; return; }
    errEl.textContent = 'Publishing…';
    fetch('/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 'pub-web', method: 'tools/call',
        params: { name: 'publish_url', arguments: { payload: payload, acknowledge_storage: true } } }) })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        var sc = resp && resp.result && resp.result.structuredContent;
        if (!sc || !sc.ok) { errEl.textContent = (sc && sc.error) || 'publish failed'; return; }
        var short = sc.short_url + location.hash;
        navigator.clipboard.writeText(short)['catch'](function () {});
        errEl.textContent = 'Copied: ' + short + ' — stored until ' + sc.stored_until +
          '. Delete code (shown once, save it): ' + sc.delete_token;
      })
      ['catch'](function (e) { errEl.textContent = String(e && e.message || e); });
  });
  var errEl = document.getElementById('mcp-play-err');

  // Public hook: the surface page's atom gallery loads examples through this.
  window.__a2uiPlaygroundLoad = function (payload) {
    errEl.textContent = '';
    editor.value = JSON.stringify(normalize(payload), null, 2);
    if (viewReady) send(payload);
  };

  var presetBox = document.getElementById('mcp-presets');
  if (presetBox) {
    PRESETS.forEach(function (p) {
      var btn = document.createElement('button');
      btn.className = 'mcp-preset-chip';
      btn.textContent = p.label;
      btn.addEventListener('click', function () {
        errEl.textContent = '';
        editor.value = JSON.stringify(normalize(p.payload), null, 2);
        if (viewReady) send(p.payload);
      });
      presetBox.appendChild(btn);
    });
  }

  var viewReady = false;
  var hashDone = false;
  var hashPayload = null;

  // Be generous with pasted schemas: a full {"blocks": []} payload, a bare
  // array of blocks, or a single block object all render. Copy-paste from a
  // post should just work.
  function normalize(payload) {
    if (Array.isArray(payload)) return { theme: 'dark', blocks: payload };
    // Envelopes pass through UNTOUCHED — the view decodes/boots them itself.
    // Without this, a wired surface (type, no blocks) got wrapped as a single
    // unknown ATOM (the black-page incident, 2026-07-11).
    if (payload && (payload.type === 'a2ui_wired_surface' ||
                    (payload.version === 'v1.0' && payload.createSurface))) {
      // Session token from the link (&t=): injected as app.session so the
      // view's action transport namespaces the store per tournament/session.
      var tk = (location.hash.match(/[#&]t=([\w-]{1,64})/) || [])[1];
      if (tk && payload.type === 'a2ui_wired_surface') {
        var appCfg = {};
        Object.keys(payload.app || {}).forEach(function (k) { appCfg[k] = payload.app[k]; });
        appCfg.session = tk;
        var wrapped = {};
        Object.keys(payload).forEach(function (k) { wrapped[k] = payload[k]; });
        wrapped.app = appCfg;
        return wrapped;
      }
      return payload;
    }
    if (payload && !payload.blocks && (payload.type || payload.component)) {
      return { theme: 'dark', blocks: [payload] };
    }
    return payload || {};
  }

  function send(payload) {
    payload = normalize(payload);
    iframe.contentWindow.postMessage({
      jsonrpc: '2.0',
      method: 'ui/notifications/tool-result',
      params: {
        content: [{ type: 'text', text: 'Rendered A2UI atoms in the MCP Apps view.' }],
        structuredContent: payload
      }
    }, '*');
    setStatus('live', 'Rendered ' + ((payload.blocks || []).length) + ' blocks via ui/notifications/tool-result');
  }

  function maybeStart() {
    if (!viewReady || !hashDone) return;
    var payload = normalize(hashPayload || FIXTURE.structuredContent);
    editor.value = JSON.stringify(payload, null, 2);
    send(payload);
  }

  // #p= in the fragment: gzip + base64url, '=' stripped — the exact encoding
  // scripts/make_url.py emits, so agents can mint playground links with the
  // existing tooling.
  function b64uToBytes(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var bin = atob(s);
    var arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }

  (function decodeHash() {
    // ?id= — a published short link (publish_url): payload BY REFERENCE from
    // /s/<id>.json, no size ceiling, nothing in the fragment but the session.
    var pid = (location.search.match(/[?&]id=([a-z0-9][a-z0-9-]{2,63})/) || [])[1];
    if (pid) {
      // Published links are END-USER artifacts: hide the dev chrome (chip bar,
      // payload drawer) unless ?chrome=1 asks for it back. #p= playground
      // links keep their chrome — that's the workbench.
      if (!/[?&]chrome=1/.test(location.search)) {
        document.querySelectorAll('.play-bar, .play-drawer, #mcp-drawer-toggle')
          .forEach(function (el) { el.style.display = 'none'; });
        // Keep the SHORT url in the address bar (what was shared = what is
        // seen = what gets re-shared). Same-origin path swap, session
        // fragment preserved.
        try { history.replaceState(null, '', '/s/' + pid + location.hash); } catch (e) {}
      }
      fetch('/s/' + pid + '.json')
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (j) { hashPayload = j; hashDone = true; maybeStart(); })
        .catch(function () {
          setStatus('err', 'Published link unknown or expired (links live one week)');
          hashDone = true; maybeStart();
        });
      return;
    }
    var m = location.hash.match(/[#&]p=([^&]+)/);
    if (!m || typeof DecompressionStream === 'undefined') { hashDone = true; maybeStart(); return; }
    try {
      var stream = new Blob([b64uToBytes(m[1])]).stream().pipeThrough(new DecompressionStream('gzip'));
      new Response(stream).text().then(function (txt) {
        try { hashPayload = JSON.parse(txt); } catch (e) { hashPayload = null; }
        hashDone = true; maybeStart();
      }).catch(function () { hashDone = true; maybeStart(); });
    } catch (e) { hashDone = true; maybeStart(); }
  })();

  renderBtn.addEventListener('click', function () {
    errEl.textContent = '';
    var payload;
    try { payload = JSON.parse(editor.value); }
    catch (e) { errEl.textContent = 'Invalid JSON: ' + e.message; return; }
    if (!viewReady) { errEl.textContent = 'View not ready yet'; return; }
    send(payload);
  });

  linkBtn.addEventListener('click', function () {
    errEl.textContent = '';
    // Page loaded from a PUBLISHED link and payload untouched: copy the short
    // form — that copy already exists, no new storage event. Everything else
    // copies the long nothing-stored data-URL; publishing is the explicit
    // "Short link…" flow above, never a side effect of copying.
    var pubId = (location.search.match(/[?&]id=([a-z0-9][a-z0-9-]{2,63})/) || [])[1]
             || (location.pathname.match(/^\/s\/([a-z0-9][a-z0-9-]{2,63})$/) || [])[1];
    if (pubId && !editorTouched) {
      var short = 'https://a2uicatalog.ai/s/' + pubId + location.hash;
      navigator.clipboard.writeText(short).then(function () {
        errEl.textContent = 'Short link copied';
      })['catch'](function () { errEl.textContent = short; });
      return;
    }
    var payload;
    try { payload = normalize(JSON.parse(editor.value)); }
    catch (e) { errEl.textContent = 'Invalid JSON: ' + e.message; return; }
    if (typeof CompressionStream === 'undefined') { errEl.textContent = 'Link encoding needs a newer browser'; return; }
    var stream = new Blob([JSON.stringify(payload)]).stream().pipeThrough(new CompressionStream('gzip'));
    new Response(stream).arrayBuffer().then(function (buf) {
      var bytes = new Uint8Array(buf);
      var bin = '';
      for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      var enc = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      var url = location.origin + location.pathname + '#p=' + enc;
      navigator.clipboard.writeText(url).then(function () {
        linkBtn.textContent = 'Copied ✓';
        setTimeout(function () { linkBtn.textContent = 'Copy link'; }, 2000);
      }).catch(function () { errEl.textContent = url; });
    });
  });

  window.addEventListener('message', function (ev) {
    if (ev.source !== iframe.contentWindow) return;
    var msg = ev.data;
    if (!msg || msg.jsonrpc !== '2.0') return;

    if (msg.method === 'ui/initialize') {
      setStatus('', 'Handshake: ui/initialize received, replying…');
      iframe.contentWindow.postMessage({
        jsonrpc: '2.0',
        id: msg.id,
        result: {
          protocolVersion: '2026-01-26',
          hostContext: { theme: 'dark', displayMode: 'inline' },
          capabilities: { serverTools: {}, logging: {} }
        }
      }, '*');
      return;
    }

    if (msg.method === 'ui/notifications/initialized') {
      setStatus('', 'View ready — delivering payload…');
      viewReady = true;
      maybeStart();
      return;
    }

    // View->host tools/call (wired-transport v0.1): forward to /mcp (same
    // origin) and reply with the matching JSON-RPC id. Only app-callable
    // tools pass — the spec's host-side visibility enforcement.
    if (msg.method === 'tools/call' && msg.id !== undefined) {
      var APP_TOOLS = { store_append: 1, store_read: 1, store_clear: 1, render_ping: 1, distill_document: 1 };
      var toolName = msg.params && msg.params.name;
      if (!APP_TOOLS[toolName]) {
        iframe.contentWindow.postMessage({ jsonrpc: '2.0', id: msg.id,
          error: { code: -32601, message: 'tool not app-callable from this host: ' + toolName } }, '*');
        return;
      }
      fetch('/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', id: msg.id, method: 'tools/call', params: msg.params }) })
        .then(function (r) { return r.json(); })
        .then(function (resp) { iframe.contentWindow.postMessage(resp, '*'); })
        .catch(function (e) {
          iframe.contentWindow.postMessage({ jsonrpc: '2.0', id: msg.id,
            error: { code: -32603, message: String(e && e.message || e) } }, '*');
        });
      return;
    }
  });

  setTimeout(function () {
    if (dot.className.indexOf('live') === -1) {
      setStatus('err', 'No response from view — check console');
    }
  }, 5000);
})();
""".strip()


# Full-screen play page — the catalog playground for MCP Apps. Edge-to-edge
# View (like a GAS ?p= link renders full-page), floating chip bar, payload
# drawer. Same element ids as the hero -> same MCP_APPS_HOST_JS verbatim.
MCP_APPS_PLAY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>A2UI Live Renderer — the catalog playground for MCP Apps</title>
  <meta name="description" content="Full-screen A2UI renderer running as a spec-conformant MCP Apps View. Paste a payload, or open a #p= link minted by scripts/make_url.py.">
  <style>
  :root{--bg:#0c1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--indigo:#6366f1;--green:#3fb950}
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
  #mcp-view{position:fixed;inset:0;width:100%;height:100%;border:0;background:#fff}
  .play-bar{position:fixed;top:12px;left:12px;right:12px;display:flex;gap:10px;align-items:center;z-index:10;pointer-events:none}
  .play-bar>*{pointer-events:auto}
  .play-chip{display:inline-flex;align-items:center;gap:8px;background:rgba(12,17,23,.88);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:999px;padding:7px 16px;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);text-decoration:none}
  a.play-chip:hover,label.play-chip:hover{border-color:var(--indigo);color:var(--indigo)}
  label.play-chip{cursor:pointer}
  .mcp-status-dot{width:8px;height:8px;border-radius:50%;background:var(--muted);flex-shrink:0;transition:background .2s}
  .mcp-status-dot.live{background:var(--green);box-shadow:0 0 8px rgba(63,185,80,.6)}
  .mcp-status-dot.err{background:var(--negative)}
  #mcp-drawer-toggle{display:none}
  .play-drawer{position:fixed;top:0;right:0;bottom:0;width:min(560px,94vw);background:rgba(12,17,23,.97);backdrop-filter:blur(10px);border-left:1px solid var(--border);padding:64px 18px 18px;transform:translateX(100%);transition:transform .25s ease;z-index:9;display:flex;flex-direction:column;gap:12px}
  #mcp-drawer-toggle:checked ~ .play-drawer{transform:translateX(0)}
  .play-drawer-label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--indigo)}
  .play-drawer textarea{flex:1;width:100%;background:#0a0e14;border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-family:'SF Mono',Monaco,monospace;font-size:12.5px;line-height:1.55;color:#9ecbff;resize:none}
  .play-drawer textarea:focus{outline:none;border-color:var(--indigo)}
  .play-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .mcp-play-btn{padding:8px 20px;border-radius:8px;border:none;background:var(--indigo);color:#fff;cursor:pointer;font-size:13px;font-weight:700}
  .mcp-play-btn:hover{background:#818cf8}
  .mcp-play-btn.ghost{background:transparent;border:1px solid var(--border);color:var(--muted)}
  .mcp-play-btn.ghost:hover{border-color:var(--indigo);color:var(--indigo)}
  .mcp-play-err{font-size:12px;color:#f85149;min-height:16px;flex:1}
.mcp-presets{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.mcp-preset-chip{padding:5px 14px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;font-size:12px;font-weight:700;letter-spacing:.03em}
.mcp-preset-chip:hover{border-color:var(--mcp-indigo,#6366f1);color:var(--mcp-indigo,#6366f1)}
  </style>
</head>
<body>
  <iframe id="mcp-view" sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox" src="/surfaces/mcp-apps/renderer-bundle.html?v=__BUNDLE_HASH__" title="A2UI MCP Apps view"></iframe>

  <div class="play-bar">
    <a class="play-chip" href="/surfaces/mcp-apps/">← A2UI · MCP Apps</a>
    <span class="play-chip"><span class="mcp-status-dot" id="mcp-status-dot"></span><span id="mcp-status-text">Connecting…</span></span>
    <label class="play-chip" for="mcp-drawer-toggle">✏ Payload</label>
  </div>

  <input type="checkbox" id="mcp-drawer-toggle">
  <aside class="play-drawer">
    <div class="play-drawer-label">Paste an A2UI payload — full {"blocks": []}, a bare array, or a single block</div>
    <div class="mcp-presets" id="mcp-presets"></div>
    <textarea id="mcp-playground-json" spellcheck="false" aria-label="A2UI payload JSON"></textarea>
    <div class="play-row">
      <button class="mcp-play-btn" id="mcp-play-render">Render →</button>
      <button class="mcp-play-btn ghost" id="mcp-play-link">Copy link</button>
      <button class="mcp-play-btn ghost" id="mcp-play-publish">Short link…</button>
      <span class="mcp-play-err" id="mcp-play-err"></span>
    </div>
  </aside>

<script>
__MCP_APPS_HOST_JS__
</script>
__MCP_GLOW__
</body>
</html>
"""


def _mcp_apps_host_js():
    """Host JS with the CI-tested demo presets injected."""
    return MCP_APPS_HOST_JS.replace(
        "__MCP_APPS_PRESETS__", json.dumps(PLAYGROUND_PRESETS, ensure_ascii=False))


_CURSOR_GLOW_CACHE = None

def _cursor_glow_html():
    """Site-wide cursor glow = the catalog's OWN cursor_glow atom, rendered at
    build time via Node from the real atoms_effects.gs source (no hand-fork).
    The atom emits its closer as <\\/script> for GAS's innerHTML injection
    path; a STATIC page needs the literal closer or the element never
    terminates (mirror image of the 2026-07-10 bundle bug) — hence the
    unescape. Empty string (with a loud warning) if Node is unavailable."""
    global _CURSOR_GLOW_CACHE
    if _CURSOR_GLOW_CACHE is not None:
        return _CURSOR_GLOW_CACHE
    import subprocess
    effects = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atoms_effects.gs").read_text()
    anchor = "_RENDERERS['cursor_glow'] = function"
    start = effects.index(anchor)
    i = effects.index("{", start)
    depth = 0
    while i < len(effects):
        if effects[i] == "{":
            depth += 1
        elif effects[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    fn = effects[start:i + 1] + ";"
    # v0.3: brand indigo (the atom's own default colour), dark-tuned screen
    # blend; the light theme re-blends it via the SITE_BASE_CSS override.
    js = ("var _RENDERERS = {};\n" + fn +
          "\nconsole.log(_RENDERERS['cursor_glow']({colour:'#6366f1', size: 460, opacity: 0.12}));")
    try:
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
        assert out.returncode == 0, out.stderr
        _CURSOR_GLOW_CACHE = out.stdout.strip().replace("<\\/script>", "</script>")
    except Exception as e:
        print(f"WARNING: cursor_glow render failed ({e}) — pages ship WITHOUT the glow", file=sys.stderr)
        _CURSOR_GLOW_CACHE = ""
    return _CURSOR_GLOW_CACHE


def generate_surface_page(surface, atoms):
    display = SURFACE_NAMES.get(surface, surface)
    is_gas  = surface in GAS_SURFACES
    hero    = (MCP_APPS_HERO_HTML.replace("__BUNDLE_HASH__", _bundle_hash())
               .replace("__MCP_APPS_HOST_JS__", _mcp_apps_host_js())
               if surface == "mcp-apps" else "")
    atoms_lead = (
        f"{len(atoms)} catalog atoms also render on this surface"
        if hero else f"{len(atoms)} atoms available on this surface"
    )

    is_playground = surface == "mcp-apps"
    items_html = ""
    gallery_examples = {}
    for atom in atoms:
        atom_type    = atom.get("type", "")
        desc         = atom.get("compact_description") or atom.get("description", "")
        display_name = atom_type.replace("_", " ").title()
        has_preview  = (atom_type in _RENDERER_TYPES and _web_renderer is not None
                        and not is_gas and not is_playground)

        if is_playground:
            # Astryx move, on our own rails: the gallery is a LIST on the
            # left of your scroll; the render happens in the live MCP Apps
            # view at the top. Example payloads ship in one map below.
            block = dict(_EXAMPLE_BLOCKS.get(atom_type)
                         or json.loads(example_payload(atom)))
            block["component"] = atom_type
            gallery_examples[atom_type] = block
            action = (f'<button class="try-btn a2ui-render-btn" data-atom="{atom_type}">'
                      f'Render in live view ↑</button>')
        elif has_preview:
            action = live_preview(atom)
        else:
            url    = make_renderer_url(atom)
            action = f'<a class="try-btn" href="{url}" target="_blank" rel="noopener">Try it live →</a>'

        items_html += f"""
<div class="surface-atom">
  <div class="sa-header">
    <a class="sa-name" href="/atoms/{atom_type}">{display_name}</a>
    <p class="sa-desc">{desc}</p>
  </div>
  {action}
</div>"""

    gallery_script = ""
    if is_playground and gallery_examples:
        examples_json = json.dumps(gallery_examples, ensure_ascii=False).replace("</script", "<\\/script")
        gallery_script = f"""<script>
// catalogue-left / render-right: each gallery item loads its example into
// the live MCP Apps view at the top (window.__a2uiPlaygroundLoad from the
// shared host JS).
var A2UI_GALLERY_EXAMPLES = {examples_json};
document.addEventListener('click', function (e) {{
  var btn = e.target.closest('.a2ui-render-btn');
  if (!btn) return;
  var block = A2UI_GALLERY_EXAMPLES[btn.dataset.atom];
  if (!block || !window.__a2uiPlaygroundLoad) return;
  var siteTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  window.__a2uiPlaygroundLoad({{ theme: siteTheme, blocks: [block] }});
  var frame = document.querySelector('.mcp-host-frame');
  if (frame) frame.scrollIntoView({{ behavior: 'smooth' }});
}});
</script>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{display} Atoms — A2UI Atomic Catalog</title>
  <meta name="description" content="{len(atoms)} A2UI atoms for the {display} surface.">
  {SITE_HEAD_JS}
  {PAGE_CSS}
  <style>
  .surface-atom{{border-bottom:1px solid var(--border);padding:28px 0}}
  .surface-atom:last-child{{border-bottom:none}}
  .sa-name{{font-size:1.1rem;font-weight:700;color:var(--text);text-decoration:none}}
  .sa-name:hover{{color:var(--accent)}}
  .sa-desc{{font-size:14px;color:var(--muted);margin:4px 0 12px}}
  .preview-box{{background:#fff;border:1px solid var(--border);border-radius:10px;padding:24px;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6}}
  .preview-box *{{max-width:100%}}
  </style>
</head>
<body>
  {site_header("playground" if surface == "mcp-apps" else "atoms")}
  <div class="wrap">
  <nav class="crumb">
    <a href="/">A2UI Catalog</a> / surfaces / {surface}
  </nav>

  <h1>{display}</h1>
  {hero}
  <p class="desc">{atoms_lead}</p>

  {items_html}

  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span><a href="/.well-known/ai-catalog.json">ARD catalog JSON</a></span>
  </footer>
  </div>
  {SITE_FOOT_JS}
{gallery_script}
{_cursor_glow_html()}
</body>
</html>"""


def _bundle_hash():
    """Content hash of the generated bundle — stamped into iframe src as a
    cache-buster (edge caches served a STALE bundle behind a fixed URL; the
    americano cache-HIT incident, 2026-07-11)."""
    import hashlib
    f = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"
    return hashlib.sha1(f.read_bytes()).hexdigest()[:10] if f.exists() else "0"


def main():
    with open(SCHEMA) as f:
        raw = yaml.safe_load(f)

    blocks = raw.get("blocks", [])
    # Staging: only stable atoms are published (stage: preview stays repo-only)
    blocks = [b for b in blocks if b.get("stage", "stable") == "stable"]

    # Deduplicate by type
    seen, unique = set(), []
    for block in blocks:
        t = block.get("type")
        if t and t not in seen:
            seen.add(t)
            unique.append(block)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for atom in unique:
        atom_type = atom.get("type", "")
        if not atom_type:
            continue
        page_dir = OUTPUT_DIR / atom_type
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_page(atom))
        count += 1

    index_path = ROOT / "public" / "index.html"
    index_path.write_text(generate_index(unique))
    # Never truncate silently: say exactly which hub cards got a live preview
    # stage and why the rest fell back to the type-chip stage.
    print(f"hub previews: {_preview_stats['rendered']} rendered, "
          f"fallbacks — no_renderer {_preview_stats['no_renderer']}, "
          f"script {_preview_stats['script']}, oversize {_preview_stats['oversize']}, "
          f"error {_preview_stats['error']}; "
          f"index.html {index_path.stat().st_size // 1024} KiB")

    # Surface pages
    surfaces_dir = ROOT / "public" / "surfaces"
    surfaces_dir.mkdir(parents=True, exist_ok=True)
    surface_map: dict[str, list] = {}
    for atom in unique:
        for s in (atom.get("surfaces") or {}).get("works_on") or []:
            surface_map.setdefault(s, []).append(atom)

    for surface, surface_atoms in surface_map.items():
        sdir = surfaces_dir / surface
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "index.html").write_text(generate_surface_page(surface, surface_atoms))

    # Full-screen playground — the catalog playground for MCP Apps
    if "mcp-apps" in surface_map:
        play_dir = surfaces_dir / "mcp-apps" / "play"
        play_dir.mkdir(parents=True, exist_ok=True)
        (play_dir / "index.html").write_text(
            MCP_APPS_PLAY_HTML.replace("__BUNDLE_HASH__", _bundle_hash())
            .replace("__MCP_APPS_HOST_JS__", _mcp_apps_host_js())
            .replace("__MCP_GLOW__", _cursor_glow_html()))
        print(f"✓ full-screen playground → {play_dir}/index.html")

    print(f"✓ {count} atom pages → {OUTPUT_DIR}")
    print(f"✓ {len(surface_map)} surface pages → {surfaces_dir}")
    print(f"✓ index → {index_path}")


if __name__ == "__main__":
    main()
