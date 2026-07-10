#!/usr/bin/env python3
"""
Generate individual atom reference pages from atoms/schema.yaml.
Outputs to public/atoms/{type}/index.html — served at a2uicatalog.ai/atoms/{type}

Run:
  python3 scripts/generate_atom_pages.py
"""
import base64
import json
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
}

PAGE_CSS = """
<style>
:root{--bg:#0c1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--cyan:#00f2ff;--green:#3fb950}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:16px;line-height:1.6}
body{max-width:860px;margin:0 auto;padding:48px 24px 96px}
nav{font-size:13px;color:var(--muted);margin-bottom:32px}
nav a{color:var(--cyan);text-decoration:none}
nav a:hover{text-decoration:underline}
h1{font-size:2.4rem;font-weight:800;letter-spacing:-1px;margin-bottom:8px}
.desc{font-size:1.15rem;color:var(--muted);margin-bottom:32px;line-height:1.7}
.label{font-size:11px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:var(--cyan);margin-bottom:12px}
.section{margin-bottom:40px}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:100px;margin:2px}
.bs{background:rgba(0,242,255,.08);border:1px solid rgba(0,242,255,.25);color:var(--cyan)}
.bd{background:rgba(255,196,0,.08);border:1px solid rgba(255,196,0,.25);color:#ffc400}
pre{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px;overflow-x:auto;margin:12px 0 24px}
pre code{color:var(--text);font-size:13px;font-family:monospace}
table{width:100%;border-collapse:collapse;margin:12px 0 24px;font-size:14px}
th{text-align:left;padding:10px 14px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border)}
td{padding:10px 14px;border-bottom:1px solid var(--border);color:var(--muted);vertical-align:top}
td:first-child{color:var(--text);font-weight:600;font-family:monospace}
.back{display:inline-block;margin-top:32px;font-size:13px;color:var(--muted);border:1px solid var(--border);border-radius:6px;padding:8px 14px;text-decoration:none}
.back:hover{border-color:var(--cyan);color:var(--cyan)}
.try-btn{display:inline-block;margin-top:32px;margin-left:12px;font-size:13px;font-weight:700;color:var(--bg);background:var(--cyan);border-radius:6px;padding:8px 18px;text-decoration:none;letter-spacing:.03em}
.try-btn:hover{background:#00d4e0}
.preview-box{background:#fff;border-radius:8px;padding:24px;margin-top:8px;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6}
.preview-box *{max-width:100%}
.preview-box p,.preview-box li,.preview-box td,.preview-box th,.preview-box td:first-child{color:#333;font-family:inherit}
.preview-box pre{background:#f4f4f4;border:1px solid #e0e0e0}
.preview-box pre code{color:#333}
.preview-box h2,.preview-box h3{color:#111}
.preview-box a{color:#0969da}
.preview-box ul{color:#333}
footer{margin-top:64px;padding-top:24px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);display:flex;justify-content:space-between}
footer a{color:var(--cyan);text-decoration:none}
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
  {PAGE_CSS}
</head>
<body>
  <nav>
    <a href="https://{DOMAIN}">A2UI Catalog</a> /
    <a href="https://{DOMAIN}/.well-known/ai-catalog.json">ARD Catalog</a> /
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

  <a class="back" href="https://{DOMAIN}/.well-known/ai-catalog.json">← Full ARD catalog</a>
  {try_btn}

  <div style="margin-top:40px;padding:20px 24px;background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.2);border-radius:10px;">
    <div style="font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#818cf8;margin-bottom:10px;">Deploy your own renderer</div>
    <p style="font-size:13px;color:var(--muted);margin:0 0 12px;">The renderer is open source. Deploy your own instance in 4 commands — you own the URL, no dependency on the demo endpoint.</p>
    <pre style="margin:0;font-size:12px;"><code>git clone https://github.com/a2uicatalog/a2ui
cd apps-script-surface/gas-schema-renderer
clasp push &amp;&amp; clasp deploy</code></pre>
    <a href="https://{DOMAIN}/renderer" style="display:inline-block;margin-top:12px;font-size:12px;color:#818cf8;text-decoration:none;">Full deploy guide →</a>
  </div>

  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span>MIT License</span>
  </footer>
</body>
</html>"""


INDEX_CSS = """
<style>
:root{--bg:#0c1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--cyan:#00f2ff;--green:#3fb950}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:16px;line-height:1.6}
body{max-width:1100px;margin:0 auto;padding:48px 24px 96px}
header{margin-bottom:40px}
h1{font-size:2.8rem;font-weight:900;letter-spacing:-2px;margin-bottom:6px;color:#fff;text-shadow:0 0 30px rgba(0,242,255,.7),0 0 60px rgba(0,242,255,.4),0 0 100px rgba(0,242,255,.2)}
.tagline{font-size:1.15rem;color:var(--cyan);font-weight:600;margin-bottom:6px;letter-spacing:.01em}
.sub{color:var(--muted);font-size:1rem;margin-bottom:24px}
.sub a{color:var(--cyan);text-decoration:none}
.launch-banner{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.3);border-radius:10px;padding:12px 18px;margin-bottom:24px;text-decoration:none;transition:border-color .15s,background .15s}
.launch-banner:hover{border-color:#6366f1;background:rgba(99,102,241,.14)}
.launch-badge{flex-shrink:0;padding:4px 12px;border-radius:999px;background:rgba(99,102,241,.2);border:1px solid rgba(99,102,241,.5);color:#8183f4;font-size:12px;font-weight:800;letter-spacing:.07em;text-transform:uppercase}
.launch-text{flex:1;min-width:200px;font-size:13px;color:var(--text)}
.launch-arrow{flex-shrink:0;font-size:12px;font-weight:700;color:#8183f4}
.hero-demo{display:grid;grid-template-columns:1fr 44px 1fr;align-items:start;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:24px}
.hero-demo-arrow{align-self:center}
.hero-demo-label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.hero-demo-json{background:#0a0e14;border:1px solid var(--border);border-radius:8px;padding:14px 16px;font-size:12.5px;line-height:1.55;color:#9ecbff;overflow-x:auto;font-family:'SF Mono',Monaco,monospace;margin:0}
.hero-demo-arrow{font-size:24px;color:var(--cyan);text-align:center}
.hero-demo-render{min-width:0}
.hero-demo-render h2{font-size:1.25rem;margin:0 0 10px;color:var(--text)}
@media(max-width:760px){.hero-demo{grid-template-columns:1fr;gap:8px}.hero-demo-arrow{transform:rotate(90deg);padding:4px 0}}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:28px}
#search{flex:1;min-width:220px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 16px;font-size:14px;color:var(--text);outline:none}
#search:focus{border-color:var(--cyan)}
#search::placeholder{color:var(--muted)}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.filter{font-size:13px;font-weight:700;padding:5px 14px;border-radius:100px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;letter-spacing:.03em}
.filter.active,.filter:hover{border-color:var(--cyan);color:var(--cyan);background:rgba(0,242,255,.07)}
.count{font-size:12px;color:var(--muted);margin-left:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.atom-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;text-decoration:none;display:block;transition:border-color .15s,background .15s}
.atom-card:hover{border-color:var(--cyan);background:rgba(0,242,255,.04)}
.atom-card h3{font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px}
.atom-card p{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-footer{display:flex;justify-content:space-between;align-items:flex-end;gap:6px;margin-top:8px}
.badges{display:flex;flex-wrap:wrap;gap:4px;flex:1;align-items:center}
.badge{font-size:12px;font-weight:600;padding:3px 10px;border-radius:100px}
.bs{background:rgba(0,242,255,.08);border:1px solid rgba(0,242,255,.2);color:var(--cyan)}
.bd{background:rgba(255,196,0,.08);border:1px solid rgba(255,196,0,.2);color:#ffc400}
.bnew{background:rgba(99,102,241,.12);border:1px solid rgba(99,102,241,.4);color:#8183f4}
.badge-more{font-size:12px;color:var(--muted);white-space:nowrap}
.origin{font-size:9px;font-weight:700;padding:2px 6px;border-radius:100px;letter-spacing:.06em;white-space:nowrap;flex-shrink:0}
.origin-a2ui{background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);color:#a5b4fc}
.origin-uiverse{background:rgba(236,72,153,.12);border:1px solid rgba(236,72,153,.3);color:#f9a8d4}
.origin-openui{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);color:#6ee7b7}
.origin-other{background:rgba(156,163,175,.1);border:1px solid rgba(156,163,175,.25);color:#9ca3af}
.hidden{display:none}
footer{margin-top:64px;padding-top:24px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);display:flex;justify-content:space-between}
footer a{color:var(--cyan);text-decoration:none}
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
            f'<h3>{display}</h3><p>{desc}</p>'
            f'<div class="card-footer"><div class="badges">{badges}</div>{origin_html}</div></a>\n'
        )

    # The concept, performed rather than described: a real payload rendered by
    # the real web renderer at generate time. This is the one artifact on the
    # page that shows what an "atom" IS — JSON in, UI out.
    demo_blocks = [
        {"type": "heading", "text": "Q2 Review"},
        {"type": "stat_card", "value": "1,234", "label": "Daily users", "delta": "+12%", "is_up": True},
        {"type": "progress_bar", "value": 72, "label": "Quarter target"},
    ]
    demo_json = json.dumps({"blocks": demo_blocks}, indent=2)
    demo_json = demo_json.replace("&", "&amp;").replace("<", "&lt;")
    demo_render = _web_renderer.render(demo_blocks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>A2UI Atomic Catalog</title>
  <meta name="description" content="467 typed UI atoms for web, Google Meet, Apps Script, and Chat. ARD-compliant catalog.">
  <link rel="ai-catalog" type="application/json" href="/.well-known/ai-catalog.json">
  {INDEX_CSS}
</head>
<body>
  <header>
    <h1>A2UI Atomic Catalog</h1>
    <p class="tagline">Useful for Humans. Declarative for AI Agents.</p>
    <p class="sub">{len(atoms)} typed atoms for web, Meet, Apps Script, Chat &middot; <a href="/.well-known/ai-catalog.json">ARD catalog</a> &middot; <a href="https://github.com/a2uicatalog/a2ui">GitHub</a></p>
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
    <div class="controls">
      <input id="search" type="search" placeholder="Search atoms…" autocomplete="off">
      <div class="filters">{filter_pills}</div>
      <span class="count" id="count">{len(atoms)} atoms</span>
    </div>
  </header>
  <div class="grid">
{cards_html}  </div>
  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span><a href="/.well-known/ai-catalog.json">ARD catalog JSON</a></span>
  </footer>
  {INDEX_JS}
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
.mcp-status-dot.err{background:#f85149}
.mcp-host-frame{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:32px}
.mcp-host-frame iframe{width:100%;min-height:920px;border:0;display:block;background:#fff}
.mcp-protocol-note{font-size:13px;color:var(--muted);margin-bottom:40px;padding-top:20px;border-top:1px solid var(--border)}
.mcp-protocol-note code{background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1px 6px;font-family:'SF Mono',Monaco,monospace;font-size:12px;color:var(--text)}
.mcp-playground{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px 20px;margin-bottom:32px}
.mcp-playground-label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--mcp-indigo);margin-bottom:10px}
.mcp-playground textarea{width:100%;min-height:220px;background:#0a0e14;border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-family:'SF Mono',Monaco,monospace;font-size:12.5px;line-height:1.55;color:#9ecbff;resize:vertical;box-sizing:border-box}
.mcp-playground textarea:focus{outline:none;border-color:var(--mcp-indigo)}
.mcp-playground-row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}
.mcp-play-btn{padding:8px 20px;border-radius:8px;border:none;background:var(--mcp-indigo);color:#fff;cursor:pointer;font-size:13px;font-weight:700}
.mcp-play-btn:hover{background:#818cf8}
.mcp-play-btn.ghost{background:transparent;border:1px solid var(--border);color:var(--muted)}
.mcp-play-btn.ghost:hover{border-color:var(--mcp-indigo);color:var(--mcp-indigo)}
.mcp-play-err{font-size:12px;color:#f85149;min-height:16px;flex:1}
</style>

<div class="mcp-badge">Just launched · MCP Apps surface</div>
<p class="desc" style="max-width:640px;margin-bottom:24px">This page <strong>is</strong> a minimal MCP Apps Host — the same sandboxed iframe, the same <code>ui/initialize</code> JSON-RPC handshake a real chat client (claude.ai, Claude Desktop) uses to render an MCP server's UI resource. Catalog atoms and hand-curated content render side by side, both mediated the same way.</p>

<div class="mcp-note">
  <strong>What's real vs. simulated:</strong> the sandboxed iframe, the postMessage handshake, and the renderer are the genuine MCP Apps protocol and genuine catalog atom code. What's simulated is the tool call — this page feeds the view a fixed fixture payload instead of a live round-trip to <code>a2uicatalog.ai/mcp</code>, so you can see it work without installing an MCP client.
</div>

<div class="mcp-note">
  <strong>The launch animation isn't a catalog atom (yet)</strong> — it's <code>gdm_rocket_panel</code>, hand-curated content (ported from a Google Meet Stage add-on demo, <code>stage: preview</code>), rendered in the same surface, through the same block dispatch, right alongside the stable catalog atoms below it. That's the actual point: MCP Apps' controlled opaqueness means an agent isn't limited to what's been pre-enumerated into the catalog — curated and catalog-declarative content sit side by side in one iframe, both still only reachable through the Host's mediated channel, not a raw DOM handoff.
</div>

<div class="mcp-status">
  <span class="mcp-status-dot" id="mcp-status-dot"></span>
  <span id="mcp-status-text">Connecting to view…</span>
</div>

<div class="mcp-host-frame">
  <iframe id="mcp-view" sandbox="allow-scripts" src="./renderer-bundle.html" title="A2UI MCP Apps view"></iframe>
</div>

<div class="mcp-playground">
  <div class="mcp-playground-label">Playground — edit the payload, re-render the view</div>
  <textarea id="mcp-playground-json" spellcheck="false" aria-label="A2UI payload JSON"></textarea>
  <div class="mcp-playground-row">
    <button class="mcp-play-btn" id="mcp-play-render">Render →</button>
    <button class="mcp-play-btn ghost" id="mcp-play-link">Copy link</button>
    <span class="mcp-play-err" id="mcp-play-err"></span>
  </div>
</div>

<p class="mcp-protocol-note">
  Handshake: the iframe (the <strong>View</strong>) posts <code>ui/initialize</code> to this page (the <strong>Host</strong>) on load. This page replies with a <code>McpUiInitializeResult</code>, the View acknowledges with <code>ui/notifications/initialized</code>, and this page then delivers the payload via <code>ui/notifications/tool-result</code> — the exact message sequence defined in the MCP Apps spec (<a href="https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx" target="_blank" rel="noopener">apps.mdx</a>). No <code>allow-same-origin</code> on the iframe — the View genuinely cannot reach this page's DOM.
</p>

<script>
(function () {
  var iframe = document.getElementById('mcp-view');
  var dot = document.getElementById('mcp-status-dot');
  var text = document.getElementById('mcp-status-text');

  function setStatus(cls, msg) {
    dot.className = 'mcp-status-dot' + (cls ? ' ' + cls : '');
    text.textContent = msg;
  }

  var FIXTURE = {
    content: [{ type: 'text', text: 'Rendered A2UI atoms in the MCP Apps view.' }],
    structuredContent: {
      theme: 'dark',
      blocks: [
        { type: 'heading', level: 2, text: 'Catalog atoms — and curated content — live inside an MCP App' },
        { type: 'gdm_rocket_panel' },
        { type: 'body', text: 'The launch animation above is **not a catalog atom** — it\\'s hand-curated content, rendered through the same block dispatch as everything below. Both arrived over the same **ui/notifications/tool-result** message a real MCP server sends after a tool call.' },
        { type: 'paragraph', text: 'The sandbox has no `allow-same-origin`: this view cannot read or touch the parent page, matching MCP Apps\\' security model — true for the curated visual above and the catalog atoms below alike.' },
        {
          type: 'flashcard_deck',
          accent: '#00b8c4',
          label_front: 'PROTOCOL',
          label_back: 'ANSWER',
          cards: [
            { front: 'What delivers this payload?', back: 'ui/notifications/tool-result, sent by the Host after ui/initialize completes.' },
            { front: 'What renders it?', back: 'A ported slice of the same renderAtoms() the GAS catalog renderer uses in production.' },
            { front: 'Where\\'s the model in this loop?', back: 'Between chat and tool call — the view itself only talks to the Host, never the network.' }
          ]
        }
      ]
    }
  };

  // ---- playground wiring ----
  var editor = document.getElementById('mcp-playground-json');
  var renderBtn = document.getElementById('mcp-play-render');
  var linkBtn = document.getElementById('mcp-play-link');
  var errEl = document.getElementById('mcp-play-err');

  var viewReady = false;
  var hashDone = false;
  var hashPayload = null;

  function send(payload) {
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
    var payload = hashPayload || FIXTURE.structuredContent;
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
    var payload;
    try { payload = JSON.parse(editor.value); }
    catch (e) { errEl.textContent = 'Invalid JSON: ' + e.message; return; }
    if (typeof CompressionStream === 'undefined') { errEl.textContent = 'Link encoding needs a newer browser'; return; }
    var stream = new Blob([JSON.stringify(payload)]).stream().pipeThrough(new CompressionStream('gzip'));
    new Response(stream).arrayBuffer().then(function (buf) {
      var bytes = new Uint8Array(buf);
      var bin = '';
      for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      var enc = btoa(bin).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
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
  });

  setTimeout(function () {
    if (dot.className.indexOf('live') === -1) {
      setStatus('err', 'No response from view — check console');
    }
  }, 5000);
})();
</script>
"""


def generate_surface_page(surface, atoms):
    display = SURFACE_NAMES.get(surface, surface)
    is_gas  = surface in GAS_SURFACES
    hero    = MCP_APPS_HERO_HTML if surface == "mcp-apps" else ""
    atoms_lead = (
        f"{len(atoms)} catalog atoms also render on this surface"
        if hero else f"{len(atoms)} atoms available on this surface"
    )

    items_html = ""
    for atom in atoms:
        atom_type    = atom.get("type", "")
        desc         = atom.get("compact_description") or atom.get("description", "")
        display_name = atom_type.replace("_", " ").title()
        has_preview  = atom_type in _RENDERER_TYPES and _web_renderer is not None and not is_gas

        if has_preview:
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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{display} Atoms — A2UI Atomic Catalog</title>
  <meta name="description" content="{len(atoms)} A2UI atoms for the {display} surface.">
  {PAGE_CSS}
  <style>
  .surface-atom{{border-bottom:1px solid var(--border);padding:28px 0}}
  .surface-atom:last-child{{border-bottom:none}}
  .sa-name{{font-size:1.1rem;font-weight:700;color:var(--text);text-decoration:none}}
  .sa-name:hover{{color:var(--cyan)}}
  .sa-desc{{font-size:14px;color:var(--muted);margin:4px 0 12px}}
  .preview-box{{background:#fff;border-radius:8px;padding:24px;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6}}
  .preview-box *{{max-width:100%}}
  </style>
</head>
<body>
  <nav>
    <a href="https://{DOMAIN}">A2UI Catalog</a> / surfaces / {surface}
  </nav>

  <h1>{display}</h1>
  {hero}
  <p class="desc">{atoms_lead}</p>

  {items_html}

  <footer>
    <span>A2UI Atomic Catalog · <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span><a href="/.well-known/ai-catalog.json">ARD catalog JSON</a></span>
  </footer>
</body>
</html>"""


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

    print(f"✓ {count} atom pages → {OUTPUT_DIR}")
    print(f"✓ {len(surface_map)} surface pages → {surfaces_dir}")
    print(f"✓ index → {index_path}")


if __name__ == "__main__":
    main()
