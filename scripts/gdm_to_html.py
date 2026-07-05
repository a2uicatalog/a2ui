"""GDM component list → standalone HTML fragment.

Converts the flat list[dict] produced by MeetStudio playbook builders into
HTML that can be rendered in a normal browser without the Meet add-on runtime.
"""
from __future__ import annotations
import html as _html
from typing import Any


def render_slide(comps: list[dict]) -> str:
    """Convert a GDM component list to an HTML string."""
    if not comps:
        return '<div style="color:#64748b;padding:40px;text-align:center">No content</div>'

    by_id: dict[str, dict] = {
        c["id"]: c for c in comps if isinstance(c, dict) and "id" in c
    }

    root = by_id.get("root")
    if not root:
        # Flat list without id structure — render in order
        return "".join(_render_comp(c, by_id) for c in comps if isinstance(c, dict))

    return _render_comp(root, by_id)


def _render_children(comp: dict, by_id: dict) -> str:
    children = comp.get("children", [])
    parts = []
    for cid in (children if isinstance(children, list) else []):
        child = by_id.get(cid)
        if child:
            parts.append(_render_comp(child, by_id))
    return "".join(parts)


def _esc(v: Any) -> str:
    return _html.escape(str(v)) if v is not None else ""


def _render_comp(comp: dict, by_id: dict) -> str:
    ctype = comp.get("component", "")

    if ctype == "gdm-stage-grid":
        children = _render_children(comp, by_id)
        return (
            '<div style="background:#060b14;min-height:100%;width:100%;'
            'padding:28px 32px;font-family:Inter,system-ui,sans-serif;box-sizing:border-box;">'
            f'{children}</div>'
        )

    if ctype == "gdm-container":
        style = _container_style(comp)
        children = _render_children(comp, by_id)
        reveal = comp.get("reveal")
        delay  = comp.get("revealDelay", 0)
        anim   = (f'animation:gdmFadeUp 0.5s ease {delay}s both;' if reveal == "fadeUp"
                  else f'animation:gdmFadeIn 0.4s ease {delay}s both;' if reveal
                  else '')
        return f'<div style="{style}{anim}">{children}</div>'

    if ctype == "gdm-text":
        style   = _text_style(comp)
        raw     = comp.get("content", "")
        content = _esc(raw).replace("\n", "<br>")
        typeOn  = comp.get("typeOn", False)
        glitch  = comp.get("glitch", False)
        cls     = ' class="gdm-glitch"' if glitch else ""
        return f'<div{cls} style="{style}">{content}</div>'

    if ctype == "gdm-matrix-text":
        color = comp.get("color", "#00f2ff")
        text  = _esc(comp.get("text", ""))
        size  = comp.get("fontSize", "14px")
        return (f'<div style="color:{color};font-family:monospace;font-size:{size};'
                f'letter-spacing:0.06em;">{text}</div>')

    if ctype in ("gdm-button", "ext-button"):
        text    = _esc(comp.get("text", "Button"))
        variant = comp.get("variant", "primary")
        size    = comp.get("size", "md")
        pulse   = comp.get("pulse", False)
        style   = _button_style(variant, size)
        anim    = ' animation:gdmPulse 2s ease-in-out infinite;' if pulse else ''
        return f'<button style="{style}{anim}" disabled>{text}</button>'

    if ctype in ("gdm-badge", "ext-badge"):
        text  = _esc(comp.get("text", ""))
        btype = comp.get("type") or comp.get("variant") or "primary"
        pulse = comp.get("pulse", False)
        style = _badge_style(btype, pulse)
        return f'<span style="{style}">{text}</span>'

    if ctype == "gdm-html-panel":
        extra_style = comp.get("style", "")
        inner = comp.get("html", "")
        if extra_style:
            return f'<div style="{extra_style}">{inner}</div>'
        return inner

    if ctype == "gdm-video-embed":
        src = _esc(comp.get("src", ""))
        return (
            '<div style="background:#111827;border-radius:10px;padding:24px;'
            'text-align:center;color:#475569;font-size:13px;">'
            f'📹 <a href="{src}" target="_top" style="color:#38bdf8">{src}</a></div>'
        )

    if ctype == "ext-card":
        title = _esc(comp.get("title", ""))
        desc  = _esc(comp.get("description", ""))
        return (
            '<div style="background:#0f172a;border:1px solid #1e293b;'
            'border-radius:10px;padding:16px 20px;margin:6px 0;">'
            f'<div style="font-weight:600;color:#e2e8f0;font-size:14px;margin-bottom:4px">{title}</div>'
            f'<div style="font-size:12px;color:#64748b;line-height:1.5">{desc}</div>'
            '</div>'
        )

    # Unknown — pass through children
    return _render_children(comp, by_id)


# ── Style helpers ─────────────────────────────────────────────────────────────

def _container_style(comp: dict) -> str:
    s = ["display:flex"]
    direction = comp.get("direction", "row")
    s.append(f"flex-direction:{direction}")
    if comp.get("grow") is not None:
        s.append(f"flex-grow:{comp['grow']}")
    if comp.get("shrink") is not None:
        s.append(f"flex-shrink:{comp['shrink']}")
    if comp.get("flex") is not None:
        s.append(f"flex:{comp['flex']}")
    if comp.get("width"):
        s.append(f"width:{comp['width']}")
    if comp.get("height"):
        s.append(f"min-height:{comp['height']}")
    if comp.get("wrap"):
        s.append("flex-wrap:wrap")
    if comp.get("gap"):
        s.append(f"gap:{comp['gap']}")
    if comp.get("padding"):
        s.append(f"padding:{comp['padding']}")
    if comp.get("background"):
        s.append(f"background:{comp['background']}")
    if comp.get("border"):
        s.append(f"border:{comp['border']}")
    if comp.get("borderRadius"):
        s.append(f"border-radius:{comp['borderRadius']}")
    if comp.get("align"):
        s.append(f"align-items:{comp['align']}")
    if comp.get("justify"):
        s.append(f"justify-content:{comp['justify']}")
    if comp.get("overflow"):
        s.append(f"overflow:{comp['overflow']}")
    if comp.get("glass"):
        s.append("backdrop-filter:blur(10px);background:rgba(255,255,255,0.05)")
    if comp.get("columns"):
        s.append(f"display:grid;grid-template-columns:repeat({comp['columns']},1fr)")
    return ";".join(s) + ";"


def _text_style(comp: dict) -> str:
    s = []
    if comp.get("size"):
        s.append(f"font-size:{comp['size']}")
    if comp.get("weight"):
        s.append(f"font-weight:{comp['weight']}")
    if comp.get("color"):
        s.append(f"color:{comp['color']}")
    if comp.get("align"):
        s.append(f"text-align:{comp['align']}")
    if comp.get("letterSpacing"):
        s.append(f"letter-spacing:{comp['letterSpacing']}")
    if comp.get("font"):
        s.append(f"font-family:{comp['font']}")
    existing = comp.get("style", "").rstrip(";")
    if existing:
        s.append(existing)
    return ";".join(s) + ";"


def _button_style(variant: str, size: str = "md") -> str:
    pad = {"sm": "6px 14px", "md": "10px 22px", "lg": "14px 32px"}.get(size, "10px 22px")
    fsize = {"sm": "12px", "md": "13px", "lg": "15px"}.get(size, "13px")
    base = (f"padding:{pad};font-size:{fsize};font-weight:600;border-radius:8px;"
            "border:none;cursor:default;letter-spacing:0.04em;")
    colors = {
        "primary": "background:#1d4ed8;color:#fff;",
        "ghost":   "background:transparent;color:#94a3b8;border:1px solid #334155;",
        "danger":  "background:#dc2626;color:#fff;",
        "success": "background:#16a34a;color:#fff;",
        "outline": "background:transparent;color:#00f2ff;border:1px solid #00f2ff;",
    }
    return base + colors.get(variant, colors["primary"])


def _badge_style(btype: str, pulse: bool = False) -> str:
    colors = {
        "primary": ("rgba(29,78,216,0.2)", "#60a5fa", "rgba(29,78,216,0.4)"),
        "danger":  ("rgba(220,38,38,0.2)", "#f87171", "rgba(220,38,38,0.4)"),
        "success": ("rgba(22,163,74,0.2)", "#4ade80", "rgba(22,163,74,0.4)"),
        "warning": ("rgba(234,179,8,0.2)", "#facc15", "rgba(234,179,8,0.4)"),
        "ghost":   ("rgba(100,116,139,0.2)", "#94a3b8", "rgba(100,116,139,0.3)"),
    }
    bg, fg, border = colors.get(btype, colors["primary"])
    anim = "animation:gdmPulse 2s ease-in-out infinite;" if pulse else ""
    return (f"display:inline-flex;align-items:center;gap:5px;padding:3px 10px;"
            f"border-radius:999px;font-size:10px;font-weight:700;letter-spacing:0.12em;"
            f"text-transform:uppercase;background:{bg};color:{fg};border:1px solid {border};"
            f"font-family:monospace;{anim}")
