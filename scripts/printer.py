#!/usr/bin/env python3
"""printer.py — A2UI's analogue port: print a data-wired atom into Google Chat.

Renders any atom the web renderer knows to a pixel-exact PNG (headless chromium),
then hands the bytes to the pattern-10 owner-broker (`?api=chat_image` on the
wired renderer's API deployment), which uploads it as a Chat attachment AS THE
OWNER. The caller here holds only the API token — no chat scope, no user creds.

  data-wired atom → chromium PNG → token POST → GAS owner-broker → attachment

Config is read from the private ops overlay (never hard-coded):
  - endpoint : deployments.gas-wired-renderer.api_url   (ops/project-ops.yaml)
  - token    : api.token                                (ops/secrets.local.yaml)

CLI:
  python3 scripts/printer.py --block payloads/chart.json --caption "*Q2*" [--space spaces/XXX]
  echo '{"type":"chartjs_bar","labels":[...],"datasets":[...]}' | python3 scripts/printer.py -

Importable:
  from printer import print_to_chat
  print_to_chat(block, caption="*title*\\ncontext", space="spaces/AAQAmecuAs4")
"""
import os, sys, json, base64, argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, 'renderers'))


def _config():
    """Resolve broker endpoint + token from the private ops overlay."""
    import yaml
    ops = os.path.join(_ROOT, 'ops')
    dep = yaml.safe_load(open(os.path.join(ops, 'project-ops.yaml')))['deployments']['gas-wired-renderer']
    tok = yaml.safe_load(open(os.path.join(ops, 'secrets.local.yaml')))['api']['token']
    return dep['api_url'], tok


def _chat_raster_types():
    """Atom types declaring `chat_raster: svg` in atoms/schema.yaml — one
    source of truth, so a future SVG-emitting atom becomes eligible for the
    pure-Python raster path with a one-line schema addition, no code change
    here."""
    import yaml
    schema = yaml.safe_load(open(os.path.join(_ROOT, 'atoms', 'schema.yaml')))
    return {a['type'] for a in schema['blocks'] if a.get('chat_raster') == 'svg'}


def render_png(block: dict, width: int = 620, title: str = '', subtitle: str = '') -> bytes:
    """Render one atom block to PNG bytes.

    Atoms declared `chat_raster: svg` (the data-derived chart-family subset —
    see atoms/schema.yaml) go through the pure-Python SVG rasterizer
    (renderers/svg_raster.py): no browser, no chromium, just the same SVG
    string the web renderer already produces via its `_svg_<atom>()` helper.
    Everything else keeps using headless chromium for real CSS/DOM fidelity.
    """
    import web_article
    atom_type = block.get('type')
    fn = getattr(web_article, '_RENDERERS', {}).get(atom_type)
    if fn is None:
        raise ValueError(f"web renderer has no atom '{atom_type}'")

    if atom_type in _chat_raster_types():
        svg_fn = getattr(web_article, f'_svg_{atom_type}', None)
        if svg_fn is not None:
            svg_string = svg_fn(block)
            if svg_string:
                import svg_raster
                return svg_raster.rasterize_svg_to_png(svg_string, target_width=width,
                                                        background=(11, 11, 18))

    frag = fn(block)
    head = (f'<div style="color:#e5e7eb;font:700 16px system-ui;margin-bottom:4px">{title}</div>' if title else '') + \
           (f'<div style="color:#94a3b8;font:500 12px system-ui;margin-bottom:12px">{subtitle}</div>' if subtitle else '')
    html = (f'<!doctype html><html><body style="margin:0;background:#0b0b12;padding:24px;'
            f'width:{width}px;font-family:system-ui">{head}{frag}</body></html>')
    from playwright.sync_api import sync_playwright
    exe = next((p for p in ('/usr/bin/google-chrome', '/usr/bin/chromium') if os.path.exists(p)), None)
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=exe, args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': width + 40, 'height': 360}, device_scale_factor=2)
        pg.set_content(html, wait_until='networkidle')
        png = pg.screenshot()
        b.close()
    return png


def print_to_chat(block: dict, caption: str = '', space: str = '',
                  title: str = '', subtitle: str = '', filename: str = 'printed.png') -> dict:
    """Render `block` and post it into Chat via the owner-broker. Returns broker JSON."""
    import urllib.request
    png = render_png(block, title=title, subtitle=subtitle)
    api_url, token = _config()
    body = json.dumps({'png_base64': base64.b64encode(png).decode(),
                       'caption': caption or title or 'Printed image',
                       'space': space, 'filename': filename}).encode()
    req = urllib.request.Request(f'{api_url}?api=chat_image&token={token}',
                                 data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Print a data-wired atom into Google Chat')
    ap.add_argument('block', nargs='?', default='-', help='JSON file of the atom block, or - for stdin')
    ap.add_argument('--caption', default='', help='message text shown ABOVE the image (markdown)')
    ap.add_argument('--space', default='', help='spaces/XXX (default: broker CHAT_SPACE_DEFAULT)')
    ap.add_argument('--title', default='', help='title drawn on the printed image')
    ap.add_argument('--subtitle', default='', help='subtitle drawn on the printed image')
    a = ap.parse_args()
    block = json.load(sys.stdin if a.block == '-' else open(a.block))
    print(json.dumps(print_to_chat(block, caption=a.caption, space=a.space,
                                   title=a.title, subtitle=a.subtitle), indent=1))
