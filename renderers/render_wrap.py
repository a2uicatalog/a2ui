"""Shared "atom fragment -> full HTML page" wrapper for chromium-based
rendering. Used by both scripts/printer.py's local chromium path and
cloud-run-renderer/server.py's headless render endpoint — one source of
truth for the wrapper markup, so the two never quietly drift apart."""


def wrap_atom_html(frag: str, width: int, title: str = '', subtitle: str = '') -> str:
    head = (f'<div style="color:#e5e7eb;font:700 16px system-ui;margin-bottom:4px">{title}</div>' if title else '') + \
           (f'<div style="color:#94a3b8;font:500 12px system-ui;margin-bottom:12px">{subtitle}</div>' if subtitle else '')
    return (f'<!doctype html><html><body style="margin:0;background:#0b0b12;padding:24px;'
            f'width:{width}px;font-family:system-ui">{head}{frag}</body></html>')
