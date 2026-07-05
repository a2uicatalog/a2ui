"""Meet stage renderer — block list → viewport-fitted HTML for gdm-html-panel.

Generates self-contained HTML that fills 100vw × 100vh with no scrolling.
Content is organised into named sections mapped to CSS grid areas.

Usage:
    from renderers.meet_stage import render, LAYOUTS

    html = render([
        {"area": "header", "blocks": [{"type": "heading", "text": "Q2 Board"}]},
        {"area": "k1",     "blocks": [{"type": "stat_card", "label": "ARR", "value": "$4.2M"}]},
        {"area": "main",   "blocks": [table_block, progress_block]},
    ], layout="kpi")
"""

from typing import List, Dict, Any
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from renderers.web_article import _md_inline, _youtube_id


# ── Layouts ───────────────────────────────────────────────────────────────────

LAYOUTS = {
    "hero": {
        "description": "Single full-viewport area",
        "template": '"main"',
        "rows": "1fr",
        "cols": "1fr",
    },
    "kpi": {
        "description": "4 KPI cards + main content area",
        "template": '"k1 k2 k3 k4" "main main main main"',
        "rows": "auto 1fr",
        "cols": "1fr 1fr 1fr 1fr",
    },
    "dashboard": {
        "description": "Header + 3-col stats + main content",
        "template": '"header header header" "k1 k2 k3" "main main main"',
        "rows": "auto auto 1fr",
        "cols": "1fr 1fr 1fr",
    },
    "split": {
        "description": "Left content 60% + right panel 40%",
        "template": '"left right"',
        "rows": "1fr",
        "cols": "3fr 2fr",
    },
    "split_3": {
        "description": "Three equal columns",
        "template": '"left centre right"',
        "rows": "1fr",
        "cols": "1fr 1fr 1fr",
    },
    "ticker": {
        "description": "Title + main content + bottom ticker strip",
        "template": '"header" "main" "footer"',
        "rows": "auto 1fr auto",
        "cols": "1fr",
    },
    "board": {
        "description": "Header + 4 KPI cards + two content columns",
        "template": '"header header header header" "k1 k2 k3 k4" "left left right right"',
        "rows": "auto auto 1fr",
        "cols": "1fr 1fr 1fr 1fr",
    },
}

_BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stage { width: 100vw; height: 100vh; display: grid; gap: 10px; padding: 14px; }

.section {
  overflow: hidden; min-height: 0;
  display: flex; flex-direction: column; gap: 6px;
  justify-content: flex-start;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 12px 14px;
}

.card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

h2 { font-size: clamp(0.9rem, 2.2vw, 1.5rem); font-weight: 700; color: #00f2ff; text-shadow: 0 0 18px rgba(0,242,255,0.5); }
h3 { font-size: clamp(0.8rem, 1.8vw, 1.1rem); font-weight: 600; color: #00f2ff; text-shadow: 0 0 12px rgba(0,242,255,0.35); }
p  { font-size: clamp(0.72rem, 1.4vw, 0.9rem); line-height: 1.5; color: #c8cdd4; }

table { width: 100%; border-collapse: collapse; font-size: clamp(0.65rem, 1.2vw, 0.82rem); }
th { background: rgba(0,242,255,0.1); color: #00f2ff; padding: 5px 10px;
     text-align: left; border-bottom: 1px solid rgba(0,242,255,0.2); white-space: nowrap; }
td { padding: 5px 10px; color: #c8cdd4; border-bottom: 1px solid rgba(255,255,255,0.05); }
tr:hover td { background: rgba(255,255,255,0.03); }

pre, code { font-family: 'JetBrains Mono', monospace; }
pre { background: #0d1117; border-radius: 6px; padding: 10px; overflow: auto;
      font-size: clamp(0.62rem, 1.1vw, 0.78rem); color: #cdd6f4; flex:1; min-height:0; }

.stat-value { font-size: clamp(1.6rem, 3.5vw, 3rem); font-weight: 900;
              font-family: monospace; color: #fff; line-height: 1; }
.stat-label { font-size: clamp(0.6rem, 1.1vw, 0.75rem); font-weight: 700;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }
.stat-delta { font-size: clamp(0.65rem, 1.2vw, 0.82rem); font-weight: 700; margin-left: 6px; }
.up   { color: #00ff88; }
.down { color: #ff4444; }

.badge { display: inline-flex; align-items: center; border-radius: 100px;
         padding: 2px 9px; font-size: clamp(0.6rem, 1.1vw, 0.75rem);
         font-weight: 700; letter-spacing: 0.04em; margin: 2px; }

.progress-wrap { background: rgba(255,255,255,0.08); border-radius: 100px;
                 height: 7px; overflow: hidden; margin: 3px 0; }
.progress-fill { height: 100%; border-radius: 100px; }

hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 4px 0; }

@keyframes glow {
  0%,100% { box-shadow: 0 0 4px currentColor; }
  50%     { box-shadow: 0 0 12px currentColor; }
}
.glow { animation: glow 2s ease-in-out infinite; }
"""


# ── Block renderers ────────────────────────────────────────────────────────────

def _heading(b):
    return f'<h2>{_md_inline(b.get("text",""))}</h2>'

def _subheading(b):
    return f'<h3>{_md_inline(b.get("text",""))}</h3>'

def _body(b):
    paras = b.get("text","").strip().split("\n\n")
    return "".join(f'<p>{_md_inline(p.strip())}</p>' for p in paras if p.strip())

def _stat_card(b):
    value  = b.get("value","—")
    label  = b.get("label","")
    delta  = b.get("delta","")
    is_up  = b.get("is_up", True)
    accent = b.get("accent","#00f2ff")
    arrow  = "▲" if is_up else "▼"
    cls    = "up" if is_up else "down"
    delta_html = f'<span class="stat-delta {cls}">{arrow} {delta}</span>' if delta else ""
    return (
        f'<div class="card" style="border-color:{accent}44;flex:1;box-shadow:0 0 20px {accent}18;">'
        f'<div class="stat-label" style="color:{accent};">{label}</div>'
        f'<div class="stat-value" style="text-shadow:0 0 24px {accent}88;">{value}{delta_html}</div>'
        f'</div>'
    )

def _progress_bar(b):
    value  = min(100, max(0, int(b.get("value",0))))
    label  = b.get("label","")
    accent = b.get("accent","#00f2ff")
    return (
        f'<div style="margin:2px 0;">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
        f'<span style="font-size:clamp(0.65rem,1.2vw,0.8rem);color:#c8cdd4;">{label}</span>'
        f'<span style="font-size:clamp(0.65rem,1.2vw,0.8rem);font-weight:700;color:{accent};">{value}%</span>'
        f'</div>'
        f'<div class="progress-wrap">'
        f'<div class="progress-fill glow" style="width:{value}%;background:{accent};color:{accent};"></div>'
        f'</div></div>'
    )

def _table(b):
    headers = b.get("headers",[])
    rows    = b.get("rows",[])
    th = "".join(f'<th>{h}</th>' for h in headers)
    trs = "".join('<tr>'+"".join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)
    return f'<div style="overflow:auto;flex:1;min-height:0;"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

def _badge_group(b):
    COLOR = {
        "green":  ("#00ff88","#003322"), "cyan":   ("#00f2ff","#002233"),
        "blue":   ("#4285f4","#001a44"), "yellow": ("#f9ab00","#332200"),
        "red":    ("#ff4444","#330011"), "purple": ("#a855f7","#1a0033"),
        "grey":   ("#9aa0a6","#1a1a1a"),
    }
    title = b.get("title","")
    t_html = f'<div style="font-size:clamp(0.6rem,1.1vw,0.75rem);opacity:0.6;margin-bottom:4px;">{title}</div>' if title else ""
    badges = "".join(
        f'<span class="badge" style="color:{COLOR.get(bg.get("color","grey"),COLOR["grey"])[0]};background:{COLOR.get(bg.get("color","grey"),COLOR["grey"])[1]};">{bg.get("text","")}</span>'
        for bg in b.get("badges",[])
    )
    return f'{t_html}<div style="display:flex;flex-wrap:wrap;">{badges}</div>'

def _bullet_list(b):
    lis = "".join(
        f'<li style="margin-bottom:3px;color:#c8cdd4;font-size:clamp(0.68rem,1.3vw,0.85rem);">'
        + (f'<strong style="color:#00f2ff;">{_md_inline(item["label"])}</strong> ' if item.get("label") else "")
        + f'{_md_inline(item.get("text",""))}</li>'
        for item in b.get("items",[])
    )
    return f'<ul style="padding-left:1.1em;">{lis}</ul>'

def _callout(b):
    COLORS = {"info":"#1a73e8","warning":"#f9ab00","tip":"#34a853","danger":"#ea4335"}
    ICONS  = {"info":"ℹ️","warning":"⚠️","tip":"💡","danger":"🚨"}
    kind  = b.get("kind","info")
    color = COLORS.get(kind,"#1a73e8")
    icon  = ICONS.get(kind,"ℹ️")
    title = b.get("title","")
    text  = _md_inline(b.get("text",""))
    title_html = f'<strong style="color:{color};">{icon} {title}</strong><br/>' if title else f'{icon} '
    return (
        f'<div style="border-left:3px solid {color};padding:6px 10px;background:{color}18;border-radius:0 6px 6px 0;font-size:clamp(0.68rem,1.3vw,0.85rem);">'
        f'{title_html}<span>{text}</span></div>'
    )

def _code(b):
    lang = b.get("language","")
    content = b.get("content","").replace("<","&lt;").replace(">","&gt;")
    label = f'<div style="font-size:0.7rem;color:#1a73e8;margin-bottom:4px;">{lang}</div>' if lang else ""
    return f'{label}<pre><code>{content}</code></pre>'

def _divider(b):
    return '<hr/>'

def _youtube(b):
    # Stage-safe embed: autoplay+muted (required pair for Chrome autoplay policy),
    # controls=0 hides the player bar, loop+playlist loops the video.
    # NEVER add referrerpolicy="no-referrer" — YouTube uses the Referer header to
    # validate the embedding domain; suppressing it causes Error 153.
    vid = _youtube_id(b.get("url",""))
    params = (
        f"?autoplay=1&mute=1&controls=0&loop=1&playlist={vid}"
        f"&rel=0&modestbranding=1&playsinline=1&iv_load_policy=3&fs=0"
    )
    return (
        f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;flex:1;">'
        f'<iframe src="https://www.youtube.com/embed/{vid}{params}" '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" '
        f'allow="autoplay; encrypted-media"></iframe>'
        f'</div>'
    )

_BLOCK_RENDERERS = {
    "heading":      _heading,
    "subheading":   _subheading,
    "body":         _body,
    "stat_card":    _stat_card,
    "progress_bar": _progress_bar,
    "table":        _table,
    "badge_group":  _badge_group,
    "bullet_list":  _bullet_list,
    "callout":      _callout,
    "code":         _code,
    "divider":      _divider,
    "youtube":      _youtube,
}


# ── Section + Stage builder ───────────────────────────────────────────────────

def _render_section(section: Dict) -> str:
    area   = section.get("area","")
    blocks = section.get("blocks",[])
    style  = f'grid-area:{area};' if area else ''
    parts  = []
    for block in blocks:
        btype = block.get("type","")
        fn    = _BLOCK_RENDERERS.get(btype)
        if fn:
            parts.append(fn(block))
        else:
            parts.append(f'<em style="color:#555;">[{btype}]</em>')
    return f'<div class="section" style="{style}">{"".join(parts)}</div>'


def render(sections: List[Dict], layout: str = "hero") -> str:
    """Render sections as viewport-fitted HTML for the Meet stage.

    Args:
        sections: List of dicts with 'area' (grid area name) and 'blocks' (list of block dicts)
        layout:   One of LAYOUTS keys

    Returns:
        Self-contained HTML string for gdm-html-panel with bare=True

    Example:
        html = render([
            {"area": "k1",   "blocks": [{"type": "stat_card", "label": "ARR", "value": "$4.2M", "accent": "#00f2ff"}]},
            {"area": "k2",   "blocks": [{"type": "stat_card", "label": "MRR", "value": "$348K", "accent": "#00ff88"}]},
            {"area": "main", "blocks": [table_block, progress_block]},
        ], layout="kpi")
    """
    layout_def = LAYOUTS.get(layout, LAYOUTS["hero"])
    grid_style = (
        f'grid-template-areas:{layout_def["template"]};'
        f'grid-template-rows:{layout_def["rows"]};'
        f'grid-template-columns:{layout_def["cols"]};'
    )
    sections_html = "".join(_render_section(s) for s in sections)
    return (
        f'<style>{_BASE_CSS}'
        f'.stage{{grid-template-areas:{layout_def["template"]};'
        f'grid-template-rows:{layout_def["rows"]};'
        f'grid-template-columns:{layout_def["cols"]};}}'
        f'</style>'
        f'<div class="stage">{sections_html}</div>'
    )
