"""cloud-run-renderer/server.py — headless "print any atom" render service.

The Article-2 SVG rasterizer closed the gap for 5 pure-data-derived chart
atoms. Everything else genuinely needs real CSS/DOM layout, which is what
scripts/printer.py's local-chromium path already provides — but only ever
on Curtis's own laptop, since it needs an already-running Playwright
instance. This service is that same rendering step, running as a real
unattended Cloud Run service instead: any atom, any caller (an agent, a
webhook, a Gemini Enterprise tool), no laptop required.

Deliberately render-ONLY. It does not know about Chat, spaces, captions, or
the owner-broker — the existing GAS `_apiChatImage_`/`_uploadImageAndPost_`
broker already does that job, and is already proven fully generic over any
PNG bytes (see a2uithoughts.md). This service's whole job is: atom block in,
PNG bytes out. Whoever calls it (printer.py today) still does the posting.

POST /render
  Headers: Authorization: Bearer <A2UI_RENDER_TOKEN>
  Body:    {"block": {...atom...}, "width": 620, "title": "", "subtitle": ""}
  Returns: image/png bytes
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
# In the container, the Dockerfile COPYs renderers/ in alongside this file
# (build context is the repo root). Running server.py directly out of the
# repo for local verification (no container), it's the sibling one level up
# instead — support both without two copies of this file.
_bundled = os.path.join(_HERE, 'renderers')
_sibling = os.path.join(os.path.dirname(_HERE), 'renderers')
sys.path.insert(0, _bundled if os.path.isdir(_bundled) else _sibling)

from flask import Flask, request, Response
import web_article
from render_wrap import wrap_atom_html
from playwright.sync_api import sync_playwright

app = Flask(__name__)

_TOKEN = os.environ.get('A2UI_RENDER_TOKEN', '')


@app.route('/render', methods=['POST'])
def render():
    auth = request.headers.get('Authorization', '')
    if not _TOKEN or auth != f'Bearer {_TOKEN}':
        return Response(json.dumps({'ok': False, 'error': 'unauthorized'}),
                        status=401, mimetype='application/json')

    payload = request.get_json(force=True)
    block = payload.get('block')
    width = int(payload.get('width', 620))
    title = payload.get('title', '')
    subtitle = payload.get('subtitle', '')

    if not isinstance(block, dict) or 'type' not in block:
        return Response(json.dumps({'ok': False, 'error': 'missing block.type'}),
                        status=400, mimetype='application/json')

    fn = web_article._RENDERERS.get(block['type'])
    if fn is None:
        return Response(json.dumps({'ok': False, 'error': f"unknown atom '{block['type']}'"}),
                        status=400, mimetype='application/json')

    frag = fn(block)
    html = wrap_atom_html(frag, width, title, subtitle)

    # A fresh sync_playwright() context per request, not a cached long-lived
    # browser — Playwright's sync API is thread-affined (its dispatcher
    # greenlet is pinned to whichever OS thread started it), and a WSGI
    # server is free to hand different requests to different threads even
    # with one worker. Reusing a browser across requests broke with
    # `greenlet.error: cannot switch to a different thread` the moment a
    # second request landed on a different thread than the first. Matches
    # scripts/printer.py's already-proven-correct per-call pattern exactly.
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': width + 40, 'height': 360}, device_scale_factor=2)
        page.set_content(html, wait_until='networkidle')
        png = page.screenshot()
        browser.close()

    return Response(png, mimetype='image/png')


@app.route('/status', methods=['GET'])
def status():
    # NOT /healthz — Cloud Run's own infrastructure intercepts that exact
    # path before it ever reaches the container (confirmed empirically:
    # every other unmatched path, including a made-up one, correctly
    # reaches Flask's own 404; only /healthz silently 404'd upstream).
    return {'ok': True}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
