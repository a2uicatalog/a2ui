"""Build the A2UI Playbook Catalogue web app.

Pre-renders every MeetStudio playbook to HTML using the GDM renderer,
then assembles a single-page app with sidebar navigation + slide viewer.

Usage:
    python3 scripts/build_playbook_webapp.py
"""

from __future__ import annotations
import sys, json, asyncio, os
from pathlib import Path

MEETSTUDIO = Path(os.environ.get("MEETSTUDIO_PATH", str(Path(__file__).parent.parent.parent / "gemini/addons/meetstudio")))
CATALOGUE  = Path(__file__).parent.parent
OUT_DIR    = CATALOGUE / "apps-script-surface" / "a2ui-playbook-webapp"

sys.path.insert(0, str(MEETSTUDIO))
sys.path.insert(0, str(CATALOGUE / "scripts"))

from gdm_to_html import render_slide


# ── Playbook registry ─────────────────────────────────────────────────────────
# (module_name, playbook_id, display_title, category, description)
REGISTRY = [
    ("a2ui_pitch",          "a2ui_pitch",         "A2UI Autopilot Pitch",         "A2UI Series",   "Self-running elevator pitch. Fires once and plays to completion."),
    ("a2ui_efficiency",     "a2ui_efficiency",     "Token Efficiency",             "A2UI Series",   "35× fewer output tokens. Identical UI. Side-by-side comparison."),
    ("a2ui_explainer",      "a2ui_explainer",      "A2UI Explainer",               "A2UI Series",   "8-slide interactive explainer for the A2UI protocol."),
    ("a2ui_explainer_v2",   "a2ui_explainer_v2",   "A2UI Explainer v2",            "A2UI Series",   "9-slide standalone rebuild with the full ext-* catalogue."),
    ("a2ui_launch",         "a2ui_launch",         "A2UI Launch",                  "A2UI Series",   "LinkedIn-angle showcase of the a2ui-catalogue."),
    ("a2ui_catalogue",      "a2ui_catalogue",      "Atom Catalogue",               "A2UI Series",   "Full atom catalogue browser — 65 slides across all categories."),
    ("itil5_learning_map",  "itil5_learning_map",  "ITIL 5 Learning Map",          "Learning",      "8-slide interactive learning map for ITIL 5 certification."),
    ("ai_native_atoms",     "ai_native_atoms",     "AI-Native Atoms",              "Showcase",      "7 atoms unique to AI-first content — no human author could write these."),
    ("animation_demo",      "animation_demo",      "Animation Demo",               "Showcase",      "All 10 animation atoms fired to the Meet stage."),
    ("dataviz_demo",        "dataviz_demo",        "DataViz Demo",                 "Showcase",      "Production-grade data visualisation — charts, heatmaps, treemaps."),
    ("new_atoms_showcase",  "new_atoms_showcase",  "New Atoms Showcase",           "Showcase",      "Premium presentation of Donut Stat & Heatmap atoms."),
    ("tier2_atoms",         "tier2_atoms",         "Tier-2 Vendor Atoms",          "Showcase",      "Polaris, Atlassian, IBM Carbon design system atoms."),
    ("openui_atoms_demo",   "openui_atoms_demo",   "OpenUI Atoms Demo",            "Showcase",      "29 atoms from Geist, Aceternity, and Magic UI."),
    ("ext_button_showcase", "ext_button_showcase", "ext-button Showcase",          "Showcase",      "All ext-button variants, sizes, and states on a single stage."),
    ("aeropulse_gtm",       "aeropulse_gtm",       "AeroPulse GTM",                "AeroPulse",     "GTM creative alignment demo — vote on brand direction."),
    ("aeropulse_gtm_v2",    "aeropulse_gtm_v2",    "AeroPulse GTM v2",             "AeroPulse",     "Upgraded with ext-* atoms, live voting, and brand video grid."),
    ("aeropulse_gtm_v3",    "aeropulse_gtm_v3",    "AeroPulse GTM v3",             "AeroPulse",     "Three-video grid with single-choice vote."),
    ("market_pulse",        "market_pulse",        "Market Pulse",                 "Live Data",     "Live market data fetched via Stooq, updated every tick."),
    ("dataviz_demo",        "dataviz_demo",        "DataViz Demo",                 "Live Data",     "BigQuery-backed charts and real-time visualisations."),
    ("read_the_room",       "read_the_room",       "Read the Room",                "Audience",      "Self-briefing with live audience feedback loop."),
    ("patterns",            "patterns",            "Playbook Patterns",            "Meta",          "Selector + 6 pre-mapped pattern demos — the design language."),
]
# Deduplicate by playbook_id
seen = set()
REGISTRY = [r for r in REGISTRY if not (r[1] in seen or seen.add(r[1]))]


def _import_playbook(mod_name: str):
    try:
        return __import__("playbooks." + mod_name, fromlist=[mod_name])
    except Exception as e:
        return None


def _call_builder(builder, space_id="demo"):
    """Call builder, handling both sync and async builders."""
    import asyncio, inspect
    if asyncio.iscoroutinefunction(builder):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(builder(space_id, 0))
        except Exception:
            return []
    try:
        return builder(space_id, 0)
    except Exception:
        return []


def prerender_all() -> list[dict]:
    """Pre-render all registered playbooks. Returns catalogue list."""
    from playbooks.manager import playbook_manager as pm

    # Import everything to populate the registry
    for mod_name, *_ in REGISTRY:
        _import_playbook(mod_name)

    catalogue = []
    for mod_name, pb_id, title, category, description in REGISTRY:
        pb = pm._playbooks.get(pb_id)
        if not pb:
            print(f"  skip {pb_id} (not in registry)")
            continue

        slides = []
        for slide in list(pb.values())[:12]:   # cap at 12 slides per playbook
            try:
                comps = _call_builder(slide.builder)
                if isinstance(comps, list) and comps:
                    html = render_slide(comps)
                else:
                    html = "<div style='color:#475569;padding:40px;text-align:center'>Slide requires live session data</div>"
            except Exception as e:
                html = f"<div style='color:#ef4444;padding:24px;font-size:12px;font-family:monospace'>Render error: {e}</div>"

            slides.append({"id": slide.slide_id, "label": slide.label, "html": html})

        catalogue.append({
            "id":          pb_id,
            "title":       title,
            "category":    category,
            "description": description,
            "slides":      slides,
        })
        print(f"  ✓ {pb_id}: {len(slides)} slides")

    return catalogue


# ── SPA builder ───────────────────────────────────────────────────────────────

_SPA_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <base target="_top">
  <title>A2UI Playbook Catalogue</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}

    :root {{
      --bg:       #04060f;
      --bg2:      #090d1a;
      --bg3:      #0f1626;
      --border:   rgba(255,255,255,0.07);
      --text:     #e2e8f0;
      --muted:    #64748b;
      --accent:   #00f2ff;
      --purple:   #a78bfa;
      --green:    #34d399;
      --sidebar:  260px;
      --topbar:   52px;
    }}

    html, body {{ height:100%; background:var(--bg); color:var(--text);
      font-family:'Inter',system-ui,sans-serif; overflow:hidden; }}

    /* ── Top bar ── */
    .topbar {{
      position:fixed; top:0; left:0; right:0; height:var(--topbar);
      background:var(--bg2); border-bottom:1px solid var(--border);
      display:flex; align-items:center; padding:0 18px; gap:14px; z-index:100;
    }}
    .topbar-logo {{ font-size:14px; font-weight:800; letter-spacing:0.05em; }}
    .topbar-logo span {{ color:var(--accent); }}
    .topbar-meta {{ font-size:11px; color:var(--muted); margin-left:auto; }}

    .badge-live {{
      display:inline-flex; align-items:center; gap:5px;
      padding:3px 10px; border-radius:99px;
      background:rgba(52,211,153,0.12); border:1px solid rgba(52,211,153,0.3);
      color:var(--green); font-size:10px; font-weight:700; letter-spacing:0.1em;
      text-transform:uppercase;
    }}
    .badge-dot {{ width:6px; height:6px; border-radius:50%; background:var(--green);
      animation:blink 1.4s ease-in-out infinite; }}

    /* ── Layout ── */
    .layout {{
      display:flex; height:100vh;
      padding-top:var(--topbar);
    }}

    /* ── Sidebar ── */
    .sidebar {{
      width:var(--sidebar); flex-shrink:0;
      background:var(--bg2); border-right:1px solid var(--border);
      overflow-y:auto; padding:12px 0;
    }}
    .sidebar::-webkit-scrollbar {{ width:4px; }}
    .sidebar::-webkit-scrollbar-thumb {{ background:#1e293b; border-radius:2px; }}

    .cat-label {{
      padding:14px 16px 6px;
      font-size:9px; font-weight:700; letter-spacing:0.18em;
      text-transform:uppercase; color:var(--muted);
    }}

    .pb-item {{
      padding:9px 16px; cursor:pointer;
      border-left:2px solid transparent;
      transition:all .15s;
    }}
    .pb-item:hover {{ background:rgba(255,255,255,0.04); }}
    .pb-item.active {{
      background:rgba(0,242,255,0.06);
      border-left-color:var(--accent);
    }}
    .pb-item-title {{ font-size:12px; font-weight:600; color:var(--text); }}
    .pb-item-desc  {{ font-size:10px; color:var(--muted); margin-top:2px;
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}

    /* ── Main panel ── */
    .main {{
      flex:1; display:flex; flex-direction:column; overflow:hidden;
    }}

    /* ── Slide header ── */
    .slide-header {{
      padding:10px 20px; background:var(--bg3);
      border-bottom:1px solid var(--border);
      display:flex; align-items:center; gap:10px; flex-shrink:0;
    }}
    .slide-title {{ font-size:13px; font-weight:600; color:var(--text); }}
    .slide-count {{ font-size:11px; color:var(--muted); margin-left:auto; }}
    .slide-nav-btn {{
      padding:4px 12px; border-radius:5px; border:1px solid var(--border);
      background:transparent; color:var(--muted); font-size:11px; cursor:pointer;
      font-family:inherit; transition:all .15s;
    }}
    .slide-nav-btn:hover {{ border-color:var(--accent); color:var(--accent); }}
    .slide-nav-btn:disabled {{ opacity:0.3; cursor:default; }}

    /* ── Slide tabs strip ── */
    .slide-tabs {{
      display:flex; gap:4px; padding:6px 16px;
      background:var(--bg2); border-bottom:1px solid var(--border);
      overflow-x:auto; flex-shrink:0;
    }}
    .slide-tabs::-webkit-scrollbar {{ height:3px; }}
    .slide-tabs::-webkit-scrollbar-thumb {{ background:#1e293b; }}
    .slide-tab {{
      padding:4px 12px; border-radius:4px; font-size:10px; font-weight:600;
      letter-spacing:0.06em; cursor:pointer; white-space:nowrap;
      color:var(--muted); background:transparent;
      border:1px solid transparent; transition:all .12s; flex-shrink:0;
    }}
    .slide-tab:hover {{ color:var(--text); border-color:var(--border); }}
    .slide-tab.active {{
      background:rgba(0,242,255,0.1); color:var(--accent);
      border-color:rgba(0,242,255,0.3);
    }}

    /* ── Slide viewport ── */
    .slide-viewport {{
      flex:1; overflow:auto; background:var(--bg);
      position:relative;
    }}
    .slide-frame {{
      min-height:100%;
      /* Slides are authored for ~480px sidebar or full-page — let them fill */
    }}

    /* ── Empty state ── */
    .empty-state {{
      display:flex; flex-direction:column; align-items:center;
      justify-content:center; height:100%; gap:12px; color:var(--muted);
    }}
    .empty-icon {{ font-size:48px; opacity:0.3; }}
    .empty-text {{ font-size:14px; }}

    /* ── GDM animation keyframes (used by rendered slides) ── */
    @keyframes gdmFadeUp {{
      from {{ opacity:0; transform:translateY(20px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    @keyframes gdmFadeIn {{
      from {{ opacity:0; }}
      to   {{ opacity:1; }}
    }}
    @keyframes gdmPulse {{
      0%,100% {{ opacity:1; }}
      50%      {{ opacity:0.5; }}
    }}
    @keyframes blink {{
      0%,100% {{ opacity:1; }}
      50%      {{ opacity:0.3; }}
    }}
  </style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo"><span>A2</span>UI</div>
  <span style="color:var(--border)">|</span>
  <span style="font-size:12px;color:var(--muted)">Playbook Catalogue</span>
  <div class="badge-live" style="margin-left:auto">
    <span class="badge-dot"></span>
    {playbook_count} playbooks &nbsp;·&nbsp; {slide_count} slides
  </div>
</div>

<div class="layout">

  <!-- Sidebar -->
  <nav class="sidebar" id="sidebar">
    {sidebar_html}
  </nav>

  <!-- Main -->
  <div class="main">
    <div class="slide-header" id="slide-header">
      <div class="slide-title" id="current-title">Select a playbook</div>
      <span class="slide-count" id="slide-count"></span>
    </div>
    <div class="slide-tabs" id="slide-tabs" style="display:none"></div>
    <div class="slide-viewport">
      <div class="slide-frame" id="slide-frame">
        <div class="empty-state">
          <div class="empty-icon">🎭</div>
          <div class="empty-text">Select a playbook from the left to preview its slides</div>
        </div>
      </div>
    </div>
  </div>

</div>

<script>
const CATALOGUE = {catalogue_json};

// Index for fast lookup
const BY_ID = {{}};
CATALOGUE.forEach(function(pb) {{ BY_ID[pb.id] = pb; }});

let currentPb   = null;
let currentSlide = 0;

function selectPlaybook(pbId) {{
  const pb = BY_ID[pbId];
  if (!pb) return;
  currentPb    = pb;
  currentSlide = 0;

  // Sidebar active
  document.querySelectorAll('.pb-item').forEach(function(el) {{
    el.classList.toggle('active', el.dataset.id === pbId);
  }});

  // Header
  document.getElementById('current-title').textContent = pb.title;

  // Tabs
  const tabs = document.getElementById('slide-tabs');
  tabs.style.display = pb.slides.length > 1 ? 'flex' : 'none';
  tabs.innerHTML = pb.slides.map(function(s, i) {{
    return '<div class="slide-tab' + (i === 0 ? ' active' : '') +
           '" data-idx="' + i + '" onclick="selectSlide(' + i + ')">' +
           s.label + '</div>';
  }}).join('');

  renderSlide(0);
}}

function selectSlide(idx) {{
  if (!currentPb) return;
  idx = Math.max(0, Math.min(idx, currentPb.slides.length - 1));
  currentSlide = idx;

  document.querySelectorAll('.slide-tab').forEach(function(el) {{
    el.classList.toggle('active', parseInt(el.dataset.idx) === idx);
  }});

  renderSlide(idx);
}}

function renderSlide(idx) {{
  if (!currentPb || !currentPb.slides[idx]) return;
  const slide = currentPb.slides[idx];
  const total = currentPb.slides.length;

  document.getElementById('slide-count').textContent =
    total > 1 ? 'Slide ' + (idx + 1) + ' / ' + total : '';

  document.getElementById('slide-frame').innerHTML = slide.html;
}}

// Auto-select first playbook
if (CATALOGUE.length) selectPlaybook(CATALOGUE[0].id);
</script>
</body>
</html>
"""


def _build_sidebar(catalogue: list[dict]) -> str:
    from collections import defaultdict
    by_cat: dict[str, list] = defaultdict(list)
    for pb in catalogue:
        by_cat[pb["category"]].append(pb)

    parts = []
    for cat, items in by_cat.items():
        parts.append(f'<div class="cat-label">{cat}</div>')
        for pb in items:
            desc = pb["description"][:60] + ("…" if len(pb["description"]) > 60 else "")
            parts.append(
                f'<div class="pb-item" data-id="{pb["id"]}" onclick="selectPlaybook(\'{pb["id"]}\')">'
                f'<div class="pb-item-title">{pb["title"]}</div>'
                f'<div class="pb-item-desc">{desc}</div>'
                f'</div>'
            )
    return "\n".join(parts)


def build(catalogue: list[dict]) -> str:
    sidebar = _build_sidebar(catalogue)
    total_slides = sum(len(pb["slides"]) for pb in catalogue)
    return _SPA_TEMPLATE.format(
        playbook_count = len(catalogue),
        slide_count    = total_slides,
        sidebar_html   = sidebar,
        # Escape </script> and <!-- so the browser parser doesn't close the
        # script tag early when the pre-rendered slide HTML contains them.
        catalogue_json = (
            json.dumps(catalogue, ensure_ascii=False)
            .replace("</", "<\\/")
            .replace("<!--", "<\\!--")
        ),
    )


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Pre-rendering playbooks…")
    catalogue = prerender_all()
    print(f"\nRendered {len(catalogue)} playbooks")

    print("Building SPA…")
    html = build(catalogue)

    out = OUT_DIR / "Index.html"
    out.write_text(html, encoding="utf-8")
    size_kb = len(html.encode()) // 1024
    print(f"✓ Written {size_kb} KB → {out}")
