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
        # Viewport height=10, not 360: full_page=True correctly EXPANDS past
        # the initial viewport for taller content (a 10-service status board
        # was never clipped), but it also CLAMPS UP to at least the initial
        # viewport height for shorter content -- confirmed directly (a tiny
        # payload_reveal card came back as a 720px-tall PNG, mostly dead
        # background, at height=360; height=10 shrinks that to its true
        # ~300px content height with zero effect on taller cards).
        page = browser.new_page(viewport={'width': width + 40, 'height': 10}, device_scale_factor=2)
        page.set_content(html, wait_until='networkidle')
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
_HELP_TEXT = ('Try:\n• `intro` — what Cards v2 can (and can’t) do\n• `sla 82` — an SLA breach gauge\n• `map` — this render pipeline’s own path\n'
              '• `workspace stats` — Google Workspace service status (add `demo` for a real historical replay, or a date like `2026-05-31`)\n'
              '• `weather` — 3-day Toulouse forecast\n'
              '• add `gif` to either (e.g. `weather gif`) — the whole deck as one animated image')

# Plain-text explainer, triggered by `intro`/`about` -- meant as a spoken
# intro a bot can post at the start of a recording, before the
# workspace/weather demo commands run. Distinct from _HELP_TEXT (a command
# reference): this is prose, framing WHY the gif variants exist at all.
_INTRO_TEXT = (
    '👋 *A quick tour before the demo*\n\n'
    'Chat Cards v2 is Google’s native way to build rich, interactive messages — '
    'structured widgets (text, images, decorated text, buttons) laid out in fixed '
    'sections. It’s genuinely useful: this bot uses it for live use cases like '
    '*Service Status* (`workspace stats`) and a *Toulouse weather* forecast '
    '(`weather`) — real data in a clean, native card, extensible to whatever you '
    'wire up next.\n\n'
    'But the widget set is fixed — no custom layout, no real typography, no '
    'charts beyond what Google ships.\n\n'
    'Type `workspace stats gif` or `weather gif` next and you’ll see the exact '
    'same data rendered through *A2UI + real HTML/CSS* in headless Chromium '
    'instead — any layout, posted back into Chat as one image. Same data, no '
    'ceiling.'
)


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


def _alt_text_for_block(block: dict, title: str) -> str:
    """Chat's Image widget altText -- a rendered atom is otherwise a flat,
    opaque image to a screen reader. Pattern-matched per known block type
    (this file only ever builds these 7); anything unrecognised falls back
    to its title rather than silently shipping no alt text at all."""
    t = block.get('type')
    if t == 'service_status_board':
        v = block.get('verdict') or {}
        return f"{title}. {v.get('text', '')}. {v.get('detail', '')}".strip()
    if t == 'incident_log':
        return f"{title}. {len(block.get('incidents', []))} recent incidents shown."
    if t == 'stat_pulse':
        parts = [f"{s.get('value', '')} {s.get('label', '')}" for s in block.get('stats', [])]
        return f"{title}. " + ', '.join(parts) + '.'
    if t == 'weather_now':
        return (f"{title}. {block.get('condition', '')}, {block.get('temp', '')}°, "
                f"high {block.get('hi', '')}°, low {block.get('lo', '')}°.")
    if t == 'weather_outlook':
        parts = [f"{d.get('label', '')} {d.get('lo', '')}–{d.get('hi', '')}°, {d.get('precip', 0)}% precip"
                 for d in block.get('days', [])]
        return f"{title}. " + '; '.join(parts) + '.'
    if t == 'code_block':
        return f"{title}. JSON payload."
    if t == 'gauge_sla':
        return f"{block.get('label', '')}: {block.get('value', '')}{block.get('unit', '')}."
    return title


# -- TRUE native Cards v2 (no headless render at all) for workspace/weather --
# The article's whole point is CardsV2's fixed widget ceiling vs. real
# HTML/CSS -- so the "before" side of that comparison has to be an ACTUAL
# native card (decoratedText/textParagraph, Chat's own materialIcon set),
# never a render.png image dressed up in a card. Built from the exact same
# chat_data.py block dicts the /render.gif path consumes, so both sides of
# the demo are provably showing the same underlying data.

_WORKSPACE_STATE_ICON = {
    'operational': 'check_circle', 'information': 'info',
    'disruption': 'warning', 'critical': 'error',
}
_WEATHER_CODE_ICON = {
    'sun': 'wb_sunny', 'partly': 'partly_cloudy_day', 'cloud': 'cloud',
    'rain': 'rainy', 'storm': 'thunderstorm',
}


def _icon(name: str) -> dict:
    return {'materialIcon': {'name': name}}


def _native_workspace_card(board: dict, log: dict, pulse: dict) -> list:
    # Deliberately the FULL deck (status + incidents + pulse), not trimmed --
    # the resulting 1200+px-tall native card next to the rendered version's
    # ~380px IS the point (see the article's callout sentence on this exact
    # contrast). Tried board-only for visual balance; reverted -- the height
    # disparity argues the article's thesis better than a tidy comparison
    # would.
    verdict = board.get('verdict') or {}
    overall_icon = {'ok': 'check_circle', 'warn': 'warning', 'crit': 'error'}.get(verdict.get('level'), 'info')
    widgets_overall = [{'decoratedText': {
        'startIcon': _icon(overall_icon), 'topLabel': 'Overall status',
        'text': verdict.get('text', ''), 'bottomLabel': verdict.get('detail', ''), 'wrapText': True,
    }}]
    widgets_services = [{'decoratedText': {
        'startIcon': _icon(_WORKSPACE_STATE_ICON.get(s['state'], 'info')),
        'text': s['name'], 'bottomLabel': s['state'].capitalize(),
    }} for s in board.get('services', [])]
    widgets_incidents = [{'decoratedText': {
        'startIcon': _icon('report'),
        'topLabel': f"{i['service']} · {i['when']}" + (' · ongoing' if i.get('ongoing') else ''),
        'text': i['summary'], 'bottomLabel': i['duration'], 'wrapText': True,
    }} for i in log.get('incidents', [])[:4]]
    widgets_pulse = [{'decoratedText': {
        'topLabel': s['label'], 'text': s['value'], 'bottomLabel': s.get('delta', ''),
    }} for s in pulse.get('stats', [])]
    return [{
        'cardId': 'a2ui-native-workspace',
        'card': {
            'header': {'title': board.get('title', 'Workspace status'), 'subtitle': board.get('stamp', '')},
            'sections': [
                {'header': 'Overall', 'widgets': widgets_overall},
                {'header': 'Services', 'widgets': widgets_services, 'collapsible': True, 'uncollapsibleWidgetsCount': 3},
                {'header': log.get('title', 'Recent incidents'), 'widgets': widgets_incidents or
                    [{'textParagraph': {'text': 'No incidents in the last 7 days.'}}]},
                {'header': pulse.get('title', '30-day pulse'), 'widgets': widgets_pulse},
            ],
        },
    }]


def _native_weather_card(now_card: dict, outlook_card: dict) -> list:
    widgets_now = [{'decoratedText': {
        'startIcon': _icon(_WEATHER_CODE_ICON.get(now_card.get('code'), 'cloud')),
        'topLabel': 'Now', 'text': f"{now_card.get('temp', '')}°C — {now_card.get('condition', '')}",
        'bottomLabel': f"H:{now_card.get('hi', '')}°  L:{now_card.get('lo', '')}°",
    }}] + [{'decoratedText': {'topLabel': s['label'], 'text': s['value']}}
           for s in now_card.get('stats', [])]
    widgets_days = [{'decoratedText': {
        'startIcon': _icon(_WEATHER_CODE_ICON.get(d.get('code'), 'cloud')),
        'topLabel': f"{d['label']} · {d['date']}",
        'text': f"H:{d['hi']}°  L:{d['lo']}°", 'bottomLabel': f"{d['precip']}% precip",
    }} for d in outlook_card.get('days', [])]
    return [{
        'cardId': 'a2ui-native-weather',
        'card': {
            'header': {'title': now_card.get('city_line', 'Weather'), 'subtitle': now_card.get('stamp', '')},
            'sections': [
                {'header': 'Now', 'widgets': widgets_now},
                {'header': outlook_card.get('title', 'Outlook'), 'widgets': widgets_days},
            ],
        },
    }]


# -- EXPERIMENTAL (2026-07-19): native buttonList widgets for the workspace/
# weather decks only -- untested against Chat's actual renderer, unlike the
# image/altText pattern above. If Chat rejects or mishandles this, it's
# fully isolated: _build_button_widget + the two callers below + the
# CARD_CLICKED branch in chat_event() + 'links'/'refresh_cmd' in
# _route_chat_command's workspace/weather returns -- delete all four and
# nothing else is affected. openLink buttons are the safe half; the
# 'Refresh' action button additionally depends on Chat's CARD_CLICKED event
# shape, which is unconfirmed for an HTTP-endpoint Chat app.
def _build_button_widget(links, refresh_cmd):
    buttons = []
    if refresh_cmd:
        buttons.append({'text': 'Refresh', 'onClick': {'action': {
            'function': 'refresh', 'parameters': [{'key': 'cmd', 'value': refresh_cmd}]}}})
    for link in (links or []):
        buttons.append({'text': link['text'], 'onClick': {'openLink': {'url': link['url']}}})
    return {'buttonList': {'buttons': buttons}} if buttons else None


def _route_chat_command(text: str):
    """Returns None (no match), {'text_only': str} (a plain-text reply, no
    rendering -- see `intro`), or {'cards': [{block, width, title}, ...],
    'caption': str} -- uniform shape whether it's one card (sla/map) or a
    multi-card deck (workspace/weather), so chat_event() never branches on
    card count."""
    stripped = text.strip()

    if re.match(r'^(intro|about)\b', stripped, re.I):
        return {'text_only': _INTRO_TEXT}

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
        deck = [
            {'block': board, 'width': 640, 'title': 'Service Status'},
            {'block': log, 'width': 640, 'title': 'Incident Log'},
            {'block': pulse, 'width': 640, 'title': '30-Day Pulse'},
        ]
        return {
            'cards': deck + [_reveal_card(board, 'Card 1')],
            # The GIF variant drops the reveal card -- its natural height is
            # 2-3x the dashboard cards (a full JSON dump vs. a compact
            # widget), so forcing it into the shared-canvas height either
            # shrinks its text hard to read or reintroduces letterboxing for
            # everything else. Still fully available via the plain (non-gif)
            # multi-card reply, and standalone via /render.png -- see /deck.
            'gif_cards': deck,
            # The actual "before" side of the article's comparison -- real
            # Chat widgets, zero headless rendering. Only chat_event()'s
            # non-gif branch uses this; `gif` still goes through /render.gif
            # against `gif_cards` above, same data either way.
            'native_cards_v2': _native_workspace_card(board, log, pulse),
            'caption': ('Google Workspace status — live from the public incidents feed.' if as_of is None
                        else f"Google Workspace status as of {as_of.strftime('%d %b %Y')} — a point-in-time query, not live."),
            'links': [{'text': 'View live status page',
                       'url': 'https://www.google.com/appsstatus/dashboard/summary'}],
            'refresh_cmd': stripped,
        }

    if re.search(r'\b(weather|forecast|toulouse)\b', stripped, re.I):
        data = chat_data.fetch_weather()
        now_card, outlook_card = chat_data.build_weather_cards(data)
        deck = [
            {'block': now_card, 'width': 640, 'title': 'Now'},
            {'block': outlook_card, 'width': 640, 'title': 'Outlook'},
        ]
        return {
            'cards': deck + [_reveal_card(outlook_card, 'Card 2')],
            'gif_cards': deck,  # see the workspace branch's comment above
            'native_cards_v2': _native_weather_card(now_card, outlook_card),
            'caption': 'Toulouse forecast — live from Open-Meteo.',
            'links': [{'text': 'View live forecast',
                       'url': 'https://www.google.com/search?q=weather+in+toulouse'}],
            'refresh_cmd': stripped,
        }

    return None


@app.route('/chat', methods=['POST'])
def chat_event():
    event = request.get_json(force=True, silent=True) or {}
    event_type = event.get('type')

    if event_type == 'CARD_CLICKED':
        # EXPERIMENTAL -- see _build_button_widget's comment. Chat's click
        # callback carries only the button's declared parameters, not the
        # original message, so 'cmd' (the verbatim original text, incl. any
        # gif/demo/date flags) is round-tripped through the button itself --
        # re-running _route_chat_command(cmd) reproduces the exact same view.
        action = event.get('action', {}) or {}
        params = {p.get('key'): p.get('value') for p in (action.get('parameters') or [])}
        text = params.get('cmd', '')
    elif event_type == 'MESSAGE':
        message = event.get('message', {}) or {}
        text = message.get('argumentText') or message.get('text') or ''
    else:
        return Response(json.dumps({}), mimetype='application/json')

    as_gif = bool(re.search(r'\bgif\b', text, re.I))

    try:
        parsed = _route_chat_command(text)
    except Exception as e:
        return Response(json.dumps({'text': f'Error fetching data: {e}'}), mimetype='application/json')

    if not parsed:
        return Response(json.dumps({'text': _HELP_TEXT}), mimetype='application/json')

    if 'text_only' in parsed:
        return Response(json.dumps({'text': parsed['text_only']}), mimetype='application/json')

    button_widget = _build_button_widget(parsed.get('links'), parsed.get('refresh_cmd'))

    try:
        if as_gif:
            # The whole deck collapsed into one self-contained, shareable
            # image (1.5s/frame) instead of separate cardsV2 entries -- works
            # anywhere an imageUrl does, not just inside Chat. Uses
            # 'gif_cards' when the command declares one (drops the
            # payload-reveal card -- see _route_chat_command), else falls
            # back to the full 'cards' list unchanged (sla/map single-card
            # commands never define gif_cards, so behave exactly as before).
            gif_cards = parsed.get('gif_cards', parsed['cards'])
            gif_url = f"{AGENT_BASE_URL}/render.gif?b={_encode_deck_qs(gif_cards, duration_ms=1500)}"
            first = gif_cards[0]
            widgets = [{'image': {
                'imageUrl': gif_url,
                'altText': _alt_text_for_block(first['block'], first.get('title', '')),
                'onClick': {'openLink': {'url': gif_url}},
            }}]
            if button_widget:
                widgets.append(button_widget)
            card = {
                'cardsV2': [{
                    'cardId': 'a2ui-render-gif',
                    'card': {
                        'header': {'title': first.get('title', 'a2ui renderer')},
                        'sections': [{'widgets': widgets}],
                    },
                }],
                'text': parsed['caption'],
            }
        elif 'native_cards_v2' in parsed:
            # Real Chat widgets, no headless render involved -- see
            # _native_workspace_card/_native_weather_card.
            native = parsed['native_cards_v2']
            if button_widget:
                native[-1]['card']['sections'].append({'widgets': [button_widget]})
            card = {'cardsV2': native, 'text': parsed['caption']}
        else:
            cards_v2 = []
            n = len(parsed['cards'])
            for i, spec in enumerate(parsed['cards']):
                img_url = f"{AGENT_BASE_URL}/render.png?b={_encode_block_qs(spec['block'], spec['width'])}"
                widgets = [{'image': {
                    'imageUrl': img_url,
                    'altText': _alt_text_for_block(spec['block'], spec.get('title', '')),
                    'onClick': {'openLink': {'url': img_url}},
                }}]
                if button_widget and i == n - 1:
                    widgets.append(button_widget)
                cards_v2.append({
                    'cardId': f'a2ui-render-{i}',
                    'card': {
                        'header': {'title': spec.get('title', 'a2ui renderer')},
                        'sections': [{'widgets': widgets}],
                    },
                })
            card = {'cardsV2': cards_v2, 'text': parsed['caption']}
    except Exception as e:
        return Response(json.dumps({'text': f'Error: {e}'}), mimetype='application/json')

    return Response(json.dumps(card), mimetype='application/json')


# -- /deck: JSON sibling of /chat for non-Chat callers (e.g. the Gemini
# Enterprise agent, a2ui-private/a2ui-ge-agent). Reuses the exact SAME
# _route_chat_command logic Chat's own handler runs -- single source of
# truth for the workspace/weather fetch+shape rules (incl. the AS-OF date
# parsing and demo replay), so a second caller never re-derives or drifts
# from that logic. Returns encoded query strings (never renders pixels
# itself) so callers build their own /render.png or /render.gif URL
# against a2ui-ge-agent, same as this service's own /chat route does.
@app.route('/deck', methods=['GET'])
def deck():
    text = request.args.get('text', '')
    try:
        parsed = _route_chat_command(text)
    except Exception as e:
        return Response(json.dumps({'ok': False, 'error': f'Error fetching data: {e}'}),
                        status=502, mimetype='application/json')
    if not parsed:
        return Response(json.dumps({'ok': False, 'error': 'no matching command', 'help': _HELP_TEXT}),
                        status=404, mimetype='application/json')
    cards_out = [{'title': c.get('title', ''), 'b': _encode_block_qs(c['block'], c['width'])}
                 for c in parsed['cards']]
    return Response(json.dumps({
        'ok': True,
        'caption': parsed['caption'],
        'cards': cards_out,
        'deck_b': _encode_deck_qs(parsed['cards'], duration_ms=1500),
    }), mimetype='application/json')


@app.route('/status', methods=['GET'])
def status():
    # NOT /healthz — Cloud Run's own infrastructure intercepts that exact
    # path before it ever reaches the container (confirmed empirically:
    # every other unmatched path, including a made-up one, correctly
    # reaches Flask's own 404; only /healthz silently 404'd upstream).
    return {'ok': True}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
