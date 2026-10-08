#!/usr/bin/env python3
"""atom_image: draw one A2UI atom with the catalogue's own renderer and screenshot it to a cropped PNG, for a slide that has no native recipe for the atom.

  python atom_image.py block.json out.png [--light]      (needs node for the renderer, chromium on PATH or CHROMIUM=..., and pillow)

The page uses the real host stylesheet (the first <style> of the MCP Apps bundle) and the dark theme the decks use. Nothing is fetched: external requests are not made, so an
atom that needs the network (a remote image, a live API) draws as it would offline. The result is a picture, not editable shapes; `alt_text()` gives the text it should carry."""
import sys, json, re, os, subprocess, tempfile, html as htmlmod
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import deck_kit as k
from PIL import Image, ImageChops

def _shell_css():
    sys.path.insert(0, str(k.REPO / 'scripts'))
    import gen_mcp_apps_bundle as gen
    return re.search(r"<style>(.*?)</style>", gen.build_bundle(), re.S).group(1)

def alt_text(markup, limit=250):
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', markup, flags=re.S | re.I); t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', htmlmod.unescape(t)).strip()[:limit]

def chromium():
    for c in (os.environ.get('CHROMIUM'), 'chromium', 'chromium-browser', 'google-chrome'):
        if c and subprocess.run(['which', c], capture_output=True).returncode == 0: return c
    raise SystemExit('chromium not found: set CHROMIUM=/path/to/chromium')

def render(block, out_png, dark=True, width=1100, scale=2):
    """-> (markup, (w, h) in CSS px). Writes out_png. Raises SystemExit if the page is blank."""
    markup = k.catalogue_atom_html(block)
    if isinstance(markup, list): markup = ''.join(markup)
    bg = '#14161c' if dark else '#ffffff'
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>atom</title><style>' + _shell_css() + '</style></head>'
            f'<body class="{"asw-dark-theme" if dark else ""}" style="margin:0;padding:24px;background:var(--bg,{bg});color:var(--text)"><main id="m" style="width:{width - 48}px">{markup}</main></body></html>')
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / 'a.html'; f.write_text(page); shot = Path(td) / 's.png'
        subprocess.run([chromium(), '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--mute-audio', '--disable-dev-shm-usage', '--virtual-time-budget=2500',
                        f'--force-device-scale-factor={scale}', f'--window-size={width},1600', f'--screenshot={shot}', 'file://' + str(f)], capture_output=True, timeout=90)
        if not shot.exists(): raise SystemExit('chromium did not produce a screenshot')
        im = Image.open(shot).convert('RGB')
    bgc = im.getpixel((2, 2)); diff = ImageChops.difference(im, Image.new('RGB', im.size, bgc)); box = diff.getbbox()
    if not box: raise SystemExit('the atom drew nothing (blank page)')
    m = 16 * scale; box = (max(0, box[0] - m), max(0, box[1] - m), min(im.width, box[2] + m), min(im.height, box[3] + m))
    im.crop(box).save(out_png, optimize=True)
    return markup, ((box[2] - box[0]) // scale, (box[3] - box[1]) // scale)

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) != 2: raise SystemExit(__doc__)
    mk, size = render(json.loads(Path(a[0]).read_text()), a[1], dark='--light' not in sys.argv)
    print(a[1], size, '| alt:', alt_text(mk)[:100])
