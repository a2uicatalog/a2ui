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

Auth: Cloud Run's own IAM layer gates every request (--no-allow-unauthenticated)
-- there is no in-app secret to check or leak. Callers authenticate as
themselves: printer.py sends its own Google ID token (fetched via ADC), a
Gemini Enterprise agent tool presents its Agent Identity token. Both are
just granted roles/run.invoker; nothing here verifies bearer tokens anymore
(that was the pre-2026-07-17 design -- see a2ui-private/briefs/
gemini-enterprise-agent-tool.md for why it moved to per-caller IAM).

POST /render
  Body: {"block": {...atom...}, "width": 620, "title": "", "subtitle": ""}
  Returns: image/png bytes by default. If the request's Accept header is
    application/json (or includes it), returns {"ok": true, "png_base64":
    "..."} instead -- tool-calling frameworks (e.g. ADK's OpenAPIToolset)
    generally only parse JSON responses; a raw binary body gets silently
    mangled by such callers rather than treated as an image (confirmed by
    reading google.adk.tools.openapi_tool.rest_api_tool: it tries
    response.json(), and on failure falls back to response.text, which is
    not meaningful for PNG bytes). printer.py's browser/httpx caller wants
    the default raw-bytes form; an ADK tool should request JSON explicitly.
"""
import os
import re
import sys
import json
import base64
import gzip
import urllib.request

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
import chat_data
from render_wrap import wrap_atom_html
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# -- /chat config: replies with a Card image URL pointing at a2ui-ge-agent's
# /render.png bridge (same stateless, on-demand PNG-transport pattern already
# proven for Gemini Enterprise card images -- a2ui-ge-agent/main.py's
# render_png/_encode_block_qs). Chat's own card renderer fetches that URL
# itself, so there's no chat.googleapis.com attachments:upload call to make
# here at all -- that endpoint needs a real signed-in-user auth context
# (confirmed 403 "permission denied" when called via any broker/service
# identity that isn't an actual member of the target space), which nothing
# server-side can reliably provide. Sidesteps the problem instead of solving
# an auth puzzle that has no clean solution for an unattended service.
AGENT_BASE_URL = os.environ.get('AGENT_BASE_URL', 'https://a2ui-ge-agent-500864195757.us-central1.run.app')


def _encode_block_qs(block, width=620):
    """Must match a2ui-ge-agent's _encode_block_qs/_decode_block_qs exactly
    (same convention as a2uicatalog's own ?p= URLs)."""
    payload = json.dumps({'block': block, 'width': width}, separators=(',', ':')).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    return base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')


def _encode_deck_qs(cards, duration_ms=1000):
    """Sibling of _encode_block_qs for a2ui-ge-agent's /render.gif -- same
    gzip+b64url convention, just a list of {block, width} instead of one."""
    blocks = [{'block': c['block'], 'width': c['width']} for c in cards]
    payload = json.dumps({'blocks': blocks, 'duration_ms': duration_ms}, separators=(',', ':')).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    return base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')


def _render_block_png(block: dict, width: int = 620, title: str = '', subtitle: str = '') -> bytes:
    """Shared by /render and /chat — one browser-render code path, not two."""
    fn = web_article._RENDERERS.get(block.get('type'))
    if fn is None:
        raise ValueError(f"unknown atom '{block.get('type')}'")
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
        # full_page=True: viewport height above is just an initial hint, not a
        # crop -- taller cards (e.g. a 10-service status board) must not be
        # clipped. Confirmed via local Playwright test this was silently
        # truncating anything past 360px before this fix.
        png = page.screenshot(full_page=True)
        browser.close()
    return png


@app.route('/render', methods=['POST'])
def render():
    payload = request.get_json(force=True)
    block = payload.get('block')
    width = int(payload.get('width', 620))
    title = payload.get('title', '')
    subtitle = payload.get('subtitle', '')

    if not isinstance(block, dict) or 'type' not in block:
        return Response(json.dumps({'ok': False, 'error': 'missing block.type'}),
                        status=400, mimetype='application/json')
    if web_article._RENDERERS.get(block['type']) is None:
        return Response(json.dumps({'ok': False, 'error': f"unknown atom '{block['type']}'"}),
                        status=400, mimetype='application/json')

    png = _render_block_png(block, width, title, subtitle)

    if 'application/json' in request.headers.get('Accept', ''):
        return Response(json.dumps({'ok': True, 'png_base64': base64.b64encode(png).decode('ascii')}),
                        mimetype='application/json')
    return Response(png, mimetype='image/png')


# -- /chat: a Google Chat HTTP-endpoint app. Cloud Run's own IAM
# (--no-allow-unauthenticated) is the ONLY auth layer — Chat's calling
# identity (chat@system.gserviceaccount.com) needs roles/run.invoker on
# this service, granted once; no signature/token verification needed here,
# matching this service's existing per-caller-IAM pattern for /render.
_SLA_RE = re.compile(r'^sla\s+(\d+(\.\d+)?)', re.I)
_HELP_TEXT = ('Try:\n• `sla 82` — an SLA breach gauge\n• `map` — this render pipeline’s own path\n'
              '• `workspace stats` — Google Workspace service status (add `demo` for a real historical replay, or a date like `2026-05-31`)\n'
              '• `weather` — 3-day Toulouse forecast\n'
              '• add `gif` to either (e.g. `weather gif`) — the whole deck as one animated image')


_MONTHS = {name: i for i, name in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july',
     'august', 'september', 'october', 'november', 'december'], start=1)}
for _abbr, _i in list(_MONTHS.items()):
    _MONTHS[_abbr[:3]] = _i


def _parse_requested_date(text: str):
    """Extracts an explicit date from free text -- '2026-05-31', '31 may
    [2026]', 'may 31[, 2026]'. Returns a UTC datetime (noon, if no time
    given) or None if nothing parses. Year defaults to the current year."""
    from datetime import datetime as _dt, timezone as _tz
    now = _dt.now(_tz.utc)

    m = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', text)
    if m:
        y, mo, d = map(int, m.groups())
        return _dt(y, mo, d, 12, 0, tzinfo=_tz.utc)

    month_names = '|'.join(_MONTHS.keys())
    m = re.search(rf'\b(\d{{1,2}})\s+({month_names})\.?\s*,?\s*(\d{{4}})?\b', text, re.I)
    if m:
        d, mo_name, y = int(m.group(1)), m.group(2).lower(), m.group(3)
        return _dt(int(y) if y else now.year, _MONTHS[mo_name], d, 12, 0, tzinfo=_tz.utc)

    m = re.search(rf'\b({month_names})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(\d{{4}})?\b', text, re.I)
    if m:
        mo_name, d, y = m.group(1).lower(), int(m.group(2)), m.group(3)
        return _dt(int(y) if y else now.year, _MONTHS[mo_name], d, 12, 0, tzinfo=_tz.utc)

    return None


def _reveal_card(block: dict, source_title: str) -> dict:
    """A payload_reveal card -- the code_block atom, syntax-lit JSON of the
    exact block that drew a previous card. The meta-demo: schema in, pixels out."""
    return {
        'block': {'type': 'code_block', 'language': 'json',
                  'content': json.dumps(block, indent=2, ensure_ascii=False)},
        'width': 640,
        'title': f'The Payload — What Drew {source_title}',
    }


def _route_chat_command(text: str):
    """Returns None (no match) or {'cards': [{block, width, title}, ...], 'caption': str}
    -- uniform shape whether it's one card (sla/map) or a multi-card deck
    (workspace/weather), so chat_event() never branches on card count."""
    stripped = text.strip()

    m = _SLA_RE.match(stripped)
    if m:
        return {
            'cards': [{
                'block': {'type': 'gauge_sla', 'value': float(m.group(1)), 'max_value': 100,
                          'unit': '%', 'label': 'P1 Incident SLA'},
                'width': 420, 'title': 'gauge_sla — P1 Incident SLA',
            }],
            'caption': 'gauge_sla — rendered via Cloud Run (real chromium).',
        }

    if re.match(r'^(map|pipeline)\b', stripped, re.I):
        return {
            'cards': [{
                'block': {
                    'type': 'geo_mercator_radar',
                    'title': 'a2uicatalog render pipeline — live path',
                    'color': '#00f2ff', 'height': 280,
                    'nodes': [
                        {'id': 'bel', 'lat': 50.8, 'lon': 4.4, 'label': 'europe-west1 — Cloud Run render'},
                        {'id': 'iowa', 'lat': 41.6, 'lon': -93.6, 'label': 'us-central1 — Vertex AI Agent Engine'},
                        {'id': 'chat', 'lat': 35.7, 'lon': 95.0, 'label': 'Google Chat'},
                    ],
                    'links': [{'source': 'iowa', 'target': 'bel'}, {'source': 'bel', 'target': 'chat'}],
                },
                'width': 760, 'title': 'a2uicatalog render pipeline — live path',
            }],
            'caption': 'geo_mercator_radar — this request’s own route, drawn live.',
        }

    if re.search(r'\b(workspace|itsm)\b', stripped, re.I):
        incidents = chat_data.fetch_workspace_incidents()
        as_of = _parse_requested_date(stripped)
        if as_of is None and re.search(r'\b(demo|replay)\b', stripped, re.I):
            as_of = chat_data.largest_incident_as_of(incidents)
        board, log, pulse = chat_data.build_workspace_cards(incidents, as_of=as_of)
        return {
            'cards': [
                {'block': board, 'width': 640, 'title': 'Service Status'},
                {'block': log, 'width': 640, 'title': 'Incident Log'},
                {'block': pulse, 'width': 640, 'title': '30-Day Pulse'},
                _reveal_card(board, 'Card 1'),
            ],
            'caption': ('Google Workspace status — live from the public incidents feed.' if as_of is None
                        else f"Google Workspace status as of {as_of.strftime('%d %b %Y')} — a point-in-time query, not live."),
        }

    if re.search(r'\b(weather|forecast|toulouse)\b', stripped, re.I):
        data = chat_data.fetch_weather()
        now_card, outlook_card = chat_data.build_weather_cards(data)
        return {
            'cards': [
                {'block': now_card, 'width': 640, 'title': 'Now'},
                {'block': outlook_card, 'width': 640, 'title': 'Outlook'},
                _reveal_card(outlook_card, 'Card 2'),
            ],
            'caption': 'Toulouse forecast — live from Open-Meteo.',
        }

    return None


@app.route('/chat', methods=['POST'])
def chat_event():
    event = request.get_json(force=True, silent=True) or {}
    if event.get('type') != 'MESSAGE':
        return Response(json.dumps({}), mimetype='application/json')

    message = event.get('message', {}) or {}
    text = message.get('argumentText') or message.get('text') or ''
    as_gif = bool(re.search(r'\bgif\b', text, re.I))

    try:
        parsed = _route_chat_command(text)
    except Exception as e:
        return Response(json.dumps({'text': f'Error fetching data: {e}'}), mimetype='application/json')

    if not parsed:
        return Response(json.dumps({'text': _HELP_TEXT}), mimetype='application/json')

    try:
        if as_gif:
            # The whole deck collapsed into one self-contained, shareable
            # image (1s/frame) instead of separate cardsV2 entries -- works
            # anywhere an imageUrl does, not just inside Chat.
            gif_url = f"{AGENT_BASE_URL}/render.gif?b={_encode_deck_qs(parsed['cards'], duration_ms=1000)}"
            card = {
                'cardsV2': [{
                    'cardId': 'a2ui-render-gif',
                    'card': {
                        'header': {'title': parsed['cards'][0].get('title', 'a2ui renderer')},
                        'sections': [{'widgets': [{'image': {
                            'imageUrl': gif_url,
                            'onClick': {'openLink': {'url': gif_url}},
                        }}]}],
                    },
                }],
                'text': parsed['caption'],
            }
        else:
            cards_v2 = []
            for i, spec in enumerate(parsed['cards']):
                img_url = f"{AGENT_BASE_URL}/render.png?b={_encode_block_qs(spec['block'], spec['width'])}"
                cards_v2.append({
                    'cardId': f'a2ui-render-{i}',
                    'card': {
                        'header': {'title': spec.get('title', 'a2ui renderer')},
                        'sections': [{'widgets': [{'image': {
                            'imageUrl': img_url,
                            'onClick': {'openLink': {'url': img_url}},
                        }}]}],
                    },
                })
            card = {'cardsV2': cards_v2, 'text': parsed['caption']}
    except Exception as e:
        return Response(json.dumps({'text': f'Error: {e}'}), mimetype='application/json')

    return Response(json.dumps(card), mimetype='application/json')


@app.route('/status', methods=['GET'])
def status():
    # NOT /healthz — Cloud Run's own infrastructure intercepts that exact
    # path before it ever reaches the container (confirmed empirically:
    # every other unmatched path, including a made-up one, correctly
    # reaches Flask's own 404; only /healthz silently 404'd upstream).
    return {'ok': True}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
