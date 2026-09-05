"""Shared "atom fragment -> full HTML page" wrapper for chromium-based
rendering. Used by both scripts/printer.py's local chromium path and
cloud-run-renderer/server.py's headless render endpoint — one source of
truth for the wrapper markup, so the two never quietly drift apart."""


def wrap_atom_html(frag: str, width: int, title: str = '', subtitle: str = '', theme: str = 'light') -> str:
    """theme: 'light' (default) or 'dark'. Found live, 2026-09-04: this
    function had NO theme awareness at all before this -- background was
    hardcoded to #0b0b12 unconditionally, so a caller sending a theme
    field anywhere upstream (e.g. a signed /render.png?b= payload) had it
    silently dropped long before reaching here. A caller several layers
    up (a2h-printer's crypto-utils.js -> cloud-run-renderer/server.py's
    render()/render_png()) can set `theme` in its request; server.py
    threads it through to this function -- see that file's own callers."""
    dark = theme == 'dark'
    bg = '#0b0b12' if dark else '#ffffff'
    title_color = '#e5e7eb' if dark else '#1f2328'
    subtitle_color = '#94a3b8' if dark else '#5f6368'
    head = (f'<div style="color:{title_color};font:700 16px system-ui;margin-bottom:4px">{title}</div>' if title else '') + \
           (f'<div style="color:{subtitle_color};font:500 12px system-ui;margin-bottom:12px">{subtitle}</div>' if subtitle else '')
    return (f'<!doctype html><html><body style="margin:0;background:{bg};padding:24px;'
            f'width:{width}px;font-family:system-ui">{head}{frag}</body></html>')
