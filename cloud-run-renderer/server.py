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
import collections
import hashlib
import hmac
import os
import re
import secrets
import sys
import time
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

# -- /chat config: replies with a Card image URL Chat's own card renderer
# fetches itself, so there's no chat.googleapis.com attachments:upload call
# to make here at all -- that endpoint needs a real signed-in-user auth
# context (confirmed 403 "permission denied" when called via any
# broker/service identity that isn't an actual member of the target space),
# which nothing server-side can reliably provide. Sidesteps the problem
# instead of solving an auth puzzle with no clean solution for an
# unattended service.
#
# Historically this pointed at a SEPARATE service (a2ui-ge-agent) whose only
# job was proxying: it received the plain, unauthenticated GET Chat's image
# fetcher makes, turned it into an authenticated POST against THIS service's
# own /render, and re-served the bytes publicly. That split existed only
# because Cloud Run IAM is all-or-nothing per service -- you can't gate the
# inbound /chat webhook while leaving one route public on the SAME
# deployment. /render.png and /render.gif below are that same proxy job,
# folded directly into this service (it already renders locally -- no
# remote call needed). AGENT_BASE_URL defaults to this service's own
# request host; set the env var only if you genuinely want a separate
# image-serving host (e.g. running /chat IAM-gated on one Cloud Run service
# and the image routes publicly on another, mirroring the old split). See
# README.md's "Two ways to deploy this" section.
AGENT_BASE_URL = os.environ.get('AGENT_BASE_URL', '')


def _self_base_url() -> str:
    return AGENT_BASE_URL or request.host_url.rstrip('/')


# -- Render token signing. Chat's anonymous image fetch means /render.png
# and /render.gif MUST stay reachable with no auth check -- that's Google's
# own constraint on the `image` widget, not a choice made here (see
# AGENT_BASE_URL's comment above). But "reachable" doesn't have to mean
# "does real Chromium work for any payload a stranger invents": signing
# every token this service itself generates means a forged or guessed `b=`
# value fails a cheap HMAC check and gets an instant 403, never reaching
# the renderer at all. Only URLs THIS service produced (via /chat or
# /deck) are ever honored.
#
# The key must be the SAME value across every instance of a multi-instance
# Cloud Run deployment -- a token signed on one instance has to verify on
# whichever instance happens to serve the follow-up GET. Set it explicitly
# (Secret Manager / --set-secrets, same posture as GAS_API_TOKEN) before
# deploying for real. The random fallback below is for local single-process
# testing only and prints a loud warning so a forgotten key is obvious in
# logs, not a silent multi-instance verification failure in production.
RENDER_SIGNING_KEY = os.environ.get('RENDER_SIGNING_KEY', '')
if not RENDER_SIGNING_KEY:
    RENDER_SIGNING_KEY = secrets.token_hex(32)
    print('WARNING: RENDER_SIGNING_KEY not set -- generated an ephemeral '
          'per-process key. Fine for local testing; in a real multi-instance '
          'Cloud Run deployment this WILL cause spurious "invalid render '
          'token" failures whenever a request lands on a different instance '
          'than the one that signed it. Set RENDER_SIGNING_KEY explicitly '
          '(Secret Manager, --set-secrets) before deploying.', flush=True)


def _sign(token: str) -> str:
    return hmac.new(RENDER_SIGNING_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()[:16]


def _encode_block_qs(block, width=620):
    """gzip + urlsafe-base64, '=' stripped, HMAC-signed -- same convention as
    a2uicatalog's own ?p= URLs plus the signature. Consumed by /render.png
    below via _decode_block_qs, which verifies the signature before
    trusting anything in the payload."""
    payload = json.dumps({'block': block, 'width': width}, separators=(',', ':')).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    token = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')
    return f'{token}.{_sign(token)}'


def _encode_deck_qs(cards, duration_ms=1000):
    """Sibling of _encode_block_qs for /render.gif -- same gzip+b64url+HMAC
    convention, just a list of {block, width} instead of one."""
    blocks = [{'block': c['block'], 'width': c['width']} for c in cards]
    payload = json.dumps({'blocks': blocks, 'duration_ms': duration_ms}, separators=(',', ':')).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    token = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')
    return f'{token}.{_sign(token)}'


class _InvalidToken(ValueError):
    """Distinct from a plain ValueError (bad width, oversized block, ...) so
    route handlers can return 403 for a forged/guessed token specifically,
    rather than lumping it in with ordinary 400-shaped request errors."""


def _decode_block_qs(s: str) -> dict:
    """Inverse of _encode_block_qs/_encode_deck_qs -- doesn't care which
    shape it decodes, the caller (render_png vs render_gif) does. Verifies
    the HMAC signature FIRST, before any base64/gzip/JSON parsing runs --
    a forged token is rejected on a cheap string comparison, never reaching
    the more expensive decode steps let alone the renderer."""
    token, sep, sig = s.rpartition('.')
    if not sep or not hmac.compare_digest(sig, _sign(token)):
        raise _InvalidToken('invalid or forged render token')
    padded = token + '=' * (-len(token) % 4)
    compressed = base64.urlsafe_b64decode(padded)
    return json.loads(gzip.decompress(compressed))


# -- Payload-size and render-rate bounds. MAX_RENDER_WIDTH/MAX_DECK_BLOCKS
# (further down) bound viewport size and block COUNT; neither bounds the
# size of a single block's OWN fields -- an attacker could pass width=620,
# one block, and still hand a sankey_flow a 50,000-entry nodes array. This
# closes that gap. MAX_RENDERS_PER_MINUTE is a genuine, computable cost
# ceiling -- unlike --max-instances/--concurrency (which only bound
# CONCURRENT cost), this bounds cost over time regardless of how long an
# attack runs. It's per-PROCESS, not a true cross-instance global limit --
# with --max-instances 3 the effective ceiling is up to 3x this value if
# traffic spreads across instances. A real global limit needs a shared
# store (Redis/Memorystore); out of scope for what this bundle ships with,
# and this in-process version still cuts worst-case cost substantially.
MAX_BLOCK_JSON_BYTES = 50_000
MAX_RENDERS_PER_MINUTE = 30
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Flask returns 413 past this, before parsing JSON at all.

_render_timestamps = collections.deque()


def _validated_block(block) -> dict:
    if not isinstance(block, dict) or 'type' not in block:
        raise ValueError('missing block.type')
    size = len(json.dumps(block))
    if size > MAX_BLOCK_JSON_BYTES:
        raise ValueError(f'block JSON too large: {size} bytes (max {MAX_BLOCK_JSON_BYTES})')
    return block


def _check_render_rate_limit():
    now = time.time()
    while _render_timestamps and now - _render_timestamps[0] > 60:
        _render_timestamps.popleft()
    if len(_render_timestamps) >= MAX_RENDERS_PER_MINUTE:
        raise RuntimeError(f'render rate limit exceeded ({MAX_RENDERS_PER_MINUTE}/minute) -- try again shortly')
    _render_timestamps.append(now)


_MEDIA_RECT_SELECTOR = '[data-promo-media]'
_DEVICE_SCALE = 2


def _render_block_png(block: dict, width: int = 620, title: str = '', subtitle: str = '',
                      want_media_rect: bool = False):
    """Shared by /render and /chat — one browser-render code path, not two.

    want_media_rect=True additionally returns the device-pixel rect of the
    card's media slot (promo_carousel_card's [data-promo-media] element), so
    an animated media_url can be composited into an otherwise-static card
    frame-by-frame without re-running the browser per frame -- see
    _composite_media_frames. Returns (png, rect_or_None) in that mode and a
    bare png otherwise, keeping every existing caller unchanged."""
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
        page = browser.new_page(viewport={'width': width + 40, 'height': 10},
                                device_scale_factor=_DEVICE_SCALE)
        page.set_content(html, wait_until='networkidle')
        rect = None
        if want_media_rect:
            el = page.query_selector(_MEDIA_RECT_SELECTOR)
            box = el.bounding_box() if el else None
            if box:
                # bounding_box() is CSS pixels; the screenshot is taken at
                # device_scale_factor, so scale to match the PNG's own space.
                rect = (int(box['x'] * _DEVICE_SCALE), int(box['y'] * _DEVICE_SCALE),
                        int(box['width'] * _DEVICE_SCALE), int(box['height'] * _DEVICE_SCALE))
        png = page.screenshot(full_page=True)
        browser.close()
    return (png, rect) if want_media_rect else png


# Bounds on the two attacker-controlled dimensions of a render request --
# added after the roast panel (2026-07-26) flagged that neither existed:
# an unbounded `width` lets one request force an arbitrarily huge Chromium
# viewport, and an unbounded deck size lets one request trigger unlimited
# real browser launches. Generous relative to real usage (default width is
# 620; real decks are 2-3 cards) so nothing legitimate hits these, but they
# give every render route a hard ceiling regardless of caller.
MAX_RENDER_WIDTH = 2000
MAX_DECK_BLOCKS = 12


def _validated_width(width) -> int:
    width = int(width)
    if not (1 <= width <= MAX_RENDER_WIDTH):
        raise ValueError(f'width must be between 1 and {MAX_RENDER_WIDTH}, got {width}')
    return width


@app.route('/render', methods=['POST'])
def render():
    payload = request.get_json(force=True)
    block = payload.get('block')
    title = payload.get('title', '')
    subtitle = payload.get('subtitle', '')

    try:
        block = _validated_block(block)
    except ValueError as e:
        return Response(json.dumps({'ok': False, 'error': str(e)}),
                        status=400, mimetype='application/json')
    if web_article._RENDERERS.get(block['type']) is None:
        return Response(json.dumps({'ok': False, 'error': f"unknown atom '{block['type']}'"}),
                        status=400, mimetype='application/json')
    try:
        width = _validated_width(payload.get('width', 620))
        _check_render_rate_limit()
    except (ValueError, RuntimeError) as e:
        return Response(json.dumps({'ok': False, 'error': str(e)}),
                        status=429 if isinstance(e, RuntimeError) else 400, mimetype='application/json')

    png = _render_block_png(block, width, title, subtitle)

    if 'application/json' in request.headers.get('Accept', ''):
        return Response(json.dumps({'ok': True, 'png_base64': base64.b64encode(png).decode('ascii')}),
                        mimetype='application/json')
    return Response(png, mimetype='image/png')


class _BoundedCache:
    """Size-capped LRU, plain dict semantics otherwise. Added after the
    roast panel (2026-07-26) flagged that the original unbounded dicts here
    were a real memory-leak vector specifically BECAUSE /render.png and
    /render.gif make the cache key (any width/block combination) reachable
    by anyone with the URL, not just this repo's own trusted callers.
    maxsize is generous relative to real traffic shapes (a handful of demo
    commands, each a few hundred KB rendered) -- this bounds the failure
    mode, it doesn't tune for a specific traffic volume."""
    def __init__(self, maxsize: int):
        self._maxsize = maxsize
        self._data = collections.OrderedDict()

    def get(self, key):
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key, value):
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self._maxsize:
            self._data.popitem(last=False)


_render_cache = _BoundedCache(maxsize=200)  # (json-key, width) -> PNG bytes


def _render_block_png_cached(block: dict, width: int) -> bytes:
    cache_key = (json.dumps(block, sort_keys=True), width)
    cached = _render_cache.get(cache_key)
    if cached is None:
        # Rate limit + size validation ONLY on a genuine cache miss -- a
        # repeat request for something already rendered costs nothing real
        # and shouldn't eat into the same budget as an actual Chromium
        # launch.
        _validated_block(block)
        _check_render_rate_limit()
        cached = _render_block_png(block, width)
        _render_cache.set(cache_key, cached)
    return cached


@app.route('/render.png', methods=['GET'])
def render_png():
    """GET sibling of POST /render, for anywhere that can only fetch a plain
    URL and can't send a POST body or an Authorization header -- Google
    Chat's own `image` widget `imageUrl` fetch is exactly that case (see
    AGENT_BASE_URL's comment above for the full story). ?b=<_encode_block_qs
    output>; deploy-free by design -- a new atom or width is just a new
    query string against this same route, never a new server-side handler."""
    try:
        spec = _decode_block_qs(request.args.get('b', ''))
        width = _validated_width(spec.get('width', 620))
        png = _render_block_png_cached(spec['block'], width)
    except _InvalidToken as e:
        return Response(f'render.png failed: {e}', status=403, mimetype='text/plain')
    except RuntimeError as e:
        return Response(f'render.png failed: {e}', status=429, mimetype='text/plain')
    except ValueError as e:
        return Response(f'render.png failed: {e}', status=400, mimetype='text/plain')
    except Exception as e:
        return Response(f'render.png failed: {e}', status=502, mimetype='text/plain')
    return Response(png, mimetype='image/png',
                     headers={'Cache-Control': 'public, max-age=300'})


_deck_gif_cache = _BoundedCache(maxsize=100)  # (json-key, duration_ms) -> GIF bytes

# Cap on how many frames one animated media_url contributes to a deck. Real
# source GIFs here are 8-10fps over 12-57s (117-450+ frames). Sampling down
# to this many keeps the output GIF a sane size; crucially the SAMPLED frames
# are stretched to preserve the source's real-time duration (see
# _fetch_media_frames), so a sampled clip plays at true speed -- slightly
# choppier, never faster. 90 frames over a ~21s clip is ~4fps, which reads
# fine for screen-recording content.
MAX_MEDIA_FRAMES = 90
# Per-card dwell time for promo_carousel_card, by role. A single flat
# duration across the whole deck read badly: the CTA card is the one that
# actually asks the viewer to do something AND the one sitting on screen
# when a looping GIF wraps around, so it needs materially longer than a
# middle card. The hook gets a little extra too -- it carries the headline
# a scroller decides on. Any card can override this with its own
# duration_ms; a non-promo atom falls back to the deck-level duration_ms.
_PROMO_ROLE_DURATION_MS = {'hook': 3000, 'middle': 2200, 'cta': 4500}


def _card_duration_ms(block, deck_default_ms: int) -> int:
    """Explicit per-card duration_ms > role default > deck default."""
    if not isinstance(block, dict):
        return deck_default_ms
    own = block.get('duration_ms')
    if isinstance(own, (int, float)) and own > 0:
        # Bounded so one card can't stall a deck for minutes.
        return int(max(200, min(30_000, own)))
    if block.get('type') == 'promo_carousel_card':
        return _PROMO_ROLE_DURATION_MS.get(block.get('role', 'middle'), deck_default_ms)
    return deck_default_ms
# Device-pixel width ceiling for the deck GIF only. Cards render at
# device_scale_factor=2 for crisp PNG export (a 1080px card is 2240 real
# pixels); that is enormous for an animated GIF, where every frame pays it.
# The PNG export path is untouched by this -- it keeps full resolution.
MAX_GIF_WIDTH = 1000


def _fetch_media_frames(url: str, max_frames: int = MAX_MEDIA_FRAMES, max_ms: int = 0):
    """(frames, per_frame_ms) for an animated media_url, or None.

    per_frame_ms preserves the source's REAL-TIME duration: if a 21s clip is
    sampled down to 90 frames, each sampled frame is held ~236ms so the clip
    still takes 21s to play. Getting this wrong is what made the first
    implementation play a 21s recording in 1.5s (~14x too fast) -- the fix is
    not "more frames", it is honouring the source's own duration.

    Returns None for anything that isn't usefully animated (a still image, a
    fetch failure, an unreadable file) -- every caller treats None as "just
    use the static screenshot", so a broken or non-animated media_url can
    never break an export, it only means no extra motion."""
    from PIL import Image, ImageSequence
    import io
    import urllib.request
    try:
        # An explicit UA is required, not cosmetic: Cloudflare (which fronts
        # a2uicatalog.ai, the usual home for these media files) 403s
        # urllib's default "Python-urllib/x.y" as a bot. Without this the
        # fetch fails, we fall back to the still frame, and the export
        # silently loses its animation -- confirmed live 2026-07-26.
        req = urllib.request.Request(url, headers={'User-Agent': 'a2ui-atom-renderer'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        im = Image.open(io.BytesIO(raw))
        n = getattr(im, 'n_frames', 1)
        if n < 2:
            return None
        # max_ms trims the clip from its START -- a 45s screen recording
        # would otherwise dominate a whole deck, since an animated card
        # dwells for its clip's real length. Trimming happens BEFORE
        # sampling so the kept section gets the full frame budget rather
        # than a thinned-out version of the whole clip.
        if max_ms:
            elapsed, keep = 0, n
            for i, fr in enumerate(ImageSequence.Iterator(im)):
                elapsed += fr.info.get('duration', 100) or 100
                if elapsed >= max_ms:
                    keep = i + 1
                    break
            n = max(2, min(n, keep))
        frames, source_ms = [], 0
        idxs = set(round(i * (n - 1) / (max_frames - 1)) for i in range(max_frames)) \
            if n > max_frames else set(range(n))
        for i, frame in enumerate(ImageSequence.Iterator(im)):
            if i >= n:
                break
            # Sum EVERY frame's duration, not just sampled ones, so the total
            # is the kept section's true length regardless of sampling.
            source_ms += frame.info.get('duration', 100) or 100
            if i in idxs:
                frames.append(frame.convert('RGB').copy())
        if not frames:
            return None
        return frames, max(20, round(source_ms / len(frames)))
    except Exception as e:
        print(f'media frames unavailable for {url}: {e}', flush=True)
        return None


def _composite_media_frames(base_png: bytes, rect, frames, max_width: int = MAX_GIF_WIDTH):
    """One card screenshot + N media frames -> N full-card images.

    The card's chrome (headline, eyebrow, footer, glow) is rendered ONCE by
    the browser; each media frame is then pasted into rect on a copy of that
    screenshot with PIL. That keeps an animated media_url actually animated
    in the exported deck GIF without paying a full ~3s Playwright render per
    source frame -- re-rendering per frame would take minutes per card and
    blow the request timeout, which is why the deck GIF flattened embedded
    animation before this existed.

    The base is downscaled to the GIF's final width BEFORE any frame is
    composited, and rect is scaled with it. This matters enormously: cards
    render at device_scale_factor=2, so a width=1080 export card is 2240px
    wide (~19MB per RGB frame). Compositing 50+ of those and only shrinking
    afterwards peaked at 2087MiB and OOM-killed a 2GiB Cloud Run instance --
    doing the identical work at output resolution is ~5x smaller per frame
    for a pixel-identical result, since the frames were always going to be
    scaled to MAX_GIF_WIDTH anyway."""
    from PIL import Image
    import io
    base = Image.open(io.BytesIO(base_png)).convert('RGB')
    if base.width > max_width:
        ratio = max_width / base.width
        rect = tuple(max(1, round(v * ratio)) for v in rect)
        base = base.resize((max_width, max(1, round(base.height * ratio))), Image.LANCZOS)
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return [base]
    out = []
    for fr in frames:
        canvas = base.copy()
        # 'cover' semantics, matching the media slot's own object-fit:cover:
        # scale to fill the slot, centre-crop the overflow, never letterbox.
        scale = max(w / fr.width, h / fr.height)
        resized = fr.resize((max(1, round(fr.width * scale)), max(1, round(fr.height * scale))),
                            Image.LANCZOS)
        left = (resized.width - w) // 2
        top = (resized.height - h) // 2
        canvas.paste(resized.crop((left, top, left + w, top + h)), (x, y))
        out.append(canvas)
    return out


def _render_deck_gif(blocks: list, duration_ms: int = 1000, target_margin: int = 24) -> bytes:
    """GET-servable sibling of the GIF-deck idea already proven in
    a2uicatalog-printer/a2ui-ge-agent: render each {block, width} spec
    through the SAME _render_block_png_cached path (a frame already shown
    singly is never re-rendered), then stitch into one animated GIF -- a
    multi-card deck collapsed into one self-contained, shareable image that
    works anywhere an imageUrl does, not just inside Chat's cardsV2.

    Crops every frame to a SHARED bounding box (the union across all
    frames, not each frame's own) before resizing to the median frame
    height, so cropping never introduces frame-to-frame jitter -- ported
    from a2ui-ge-agent's _render_deck_gif_autocrop rather than the plainer
    median-resize-only version this function shipped with initially (roast
    panel, 2026-07-26): that version left the exact letterboxing artifact
    autocrop already solves elsewhere in this codebase. Every card here is
    rendered at the SAME design width by the caller (one type system, not
    one width per card), so only height varies frame to frame; resizing to
    the MEDIAN height (not the max) keeps the common case untouched and
    only mildly stretches/squashes the outliers."""
    if len(blocks) > MAX_DECK_BLOCKS:
        raise ValueError(f'deck too large: {len(blocks)} blocks (max {MAX_DECK_BLOCKS})')
    cache_key = (json.dumps(blocks, sort_keys=True), duration_ms)
    cached = _deck_gif_cache.get(cache_key)
    if cached is not None:
        return cached
    from PIL import Image, ImageChops
    import io

    # One card normally contributes ONE frame. A card whose media_url is
    # itself animated instead contributes one frame per sampled source frame
    # (same card chrome, moving media) -- so the embedded animation survives
    # into the deck GIF instead of being flattened to a still. Entirely
    # transparent to the caller: no flag, no separate endpoint, it just
    # animates when the supplied file happens to animate.
    images, durations = [], []
    for spec in blocks:
        block = spec['block']
        w = _validated_width(spec.get('width', 620))
        media_url = block.get('media_url') if isinstance(block, dict) else None
        media = None
        rect = None
        if media_url and block.get('has_media', True):
            png, rect = _render_block_png(block, w, want_media_rect=True)
            if rect:
                raw_max = block.get('media_max_ms')
                media = _fetch_media_frames(
                    web_article._promo_media_src(media_url)
                    if hasattr(web_article, '_promo_media_src') else media_url,
                    max_ms=int(raw_max) if isinstance(raw_max, (int, float)) and raw_max > 0 else 0)
        else:
            png = _render_block_png_cached(block, w)

        if media and rect:
            media_frames, per_frame_ms = media
            composited = _composite_media_frames(png, rect, media_frames)
            # Drop the decoded source frames as soon as they've been pasted:
            # a 90-frame 1100x551 clip is ~160MB of RGB that is dead weight
            # for the rest of this function. Memory is the real constraint
            # here -- an animated deck OOM-killed a 1GiB Cloud Run instance
            # before the frame lists below were made in-place.
            media_frames.clear()
            del media
            images.extend(composited)
            # The card dwells for the CLIP's own length, at the clip's own
            # speed -- it does not get squeezed into duration_ms. That was
            # the original bug: a 21s recording crammed into a 1.5s slot
            # played ~14x too fast. duration_ms (deck-level OR a per-card
            # override) is therefore the dwell time for STILL cards only;
            # an animated card's length is a property of its clip, and
            # honouring an override here would just reintroduce the
            # fast-forward.
            durations.extend([per_frame_ms] * len(composited))
        else:
            still = Image.open(io.BytesIO(png)).convert('RGB')
            # Normalise to the same width _composite_media_frames already
            # reduced animated cards to. The shared-bbox crop below assumes
            # every frame is in ONE coordinate space, so a deck mixing a
            # downscaled animated card with a full-size still one would crop
            # both against the wrong box.
            if still.width > MAX_GIF_WIDTH:
                r = MAX_GIF_WIDTH / still.width
                still = still.resize((MAX_GIF_WIDTH, max(1, round(still.height * r))), Image.LANCZOS)
            images.append(still)
            durations.append(_card_duration_ms(block, duration_ms))

    boxes = []
    for im in images:
        bg = im.getpixel((2, 2))
        bg_im = Image.new('RGB', im.size, bg)
        bbox = ImageChops.difference(im, bg_im).getbbox()
        if bbox:
            boxes.append(bbox)
    if boxes:
        left = max(0, min(b[0] for b in boxes) - target_margin)
        top = max(0, min(b[1] for b in boxes) - target_margin)
        right = min(max(im.width for im in images), max(b[2] for b in boxes) + target_margin)
        bottom = min(max(im.height for im in images), max(b[3] for b in boxes) + target_margin)
        # In-place, one frame at a time: building a second full list here
        # doubled peak memory, and with ~90 composited 1160x1400 frames that
        # alone is ~250MB per copy. Same for the resize and quantize passes
        # below -- each used to allocate a whole new list while the previous
        # one was still alive. Real OOM at 1GiB, not a theoretical concern.
        for i, im in enumerate(images):
            images[i] = im.crop((left, top, right, bottom))

    heights = sorted(im.height for im in images)
    target_h = heights[len(heights) // 2]
    canvas_w = max(im.width for im in images)
    # A deck carrying an animated media_url can run to ~90 frames; at the
    # 2x device-pixel width cards are rendered for PNG export that would be
    # a huge GIF. Scale the whole deck down to MAX_GIF_WIDTH first so frame
    # count buys motion instead of megabytes (still cards are unaffected in
    # practice -- they were already well under it at typical widths).
    if canvas_w > MAX_GIF_WIDTH:
        ratio = MAX_GIF_WIDTH / canvas_w
        canvas_w, target_h = MAX_GIF_WIDTH, max(1, round(target_h * ratio))
    for i, im in enumerate(images):
        if (im.width, im.height) != (canvas_w, target_h):
            images[i] = im.resize((canvas_w, target_h), Image.LANCZOS)
    frames = images

    # Encoding matters enormously once a deck carries animation: a ~21s clip
    # at 90 frames came out at 33.5MB with the original settings (full-frame,
    # per-frame local palettes), which is unusable for LinkedIn or a blog
    # embed. Three changes, all of which also HELP quality-per-byte here:
    #  * one shared 192-colour palette for the whole deck (a global colour table written
    #    once, instead of a local one per frame),
    #  * dither=NONE -- these are flat-UI screen recordings, so dithering adds
    #    noise that both looks worse and defeats LZW compression, and
    #  * disposal=1 + optimize=True, which lets PIL store only the changed
    #    rectangle per frame. That is the big one for this atom specifically:
    #    consecutive media frames differ ONLY inside the media slot, the card
    #    chrome around it is pixel-identical.
    pal_src = frames[0] if len(frames) == 1 else frames[len(frames) // 2]
    palette = pal_src.quantize(colors=192, method=Image.MEDIANCUT)
    for i, f in enumerate(frames):
        # In-place again, and a real saving beyond avoiding the duplicate
        # list: the quantized P-mode frame is 1 byte/px against RGB's 3, so
        # each replacement immediately frees 2/3 of that frame's memory.
        frames[i] = f.quantize(palette=palette, dither=Image.NONE)

    buf = io.BytesIO()
    # Per-frame durations (a list), not one flat value: an animated card runs
    # at its clip's own real-time pace, still cards keep duration_ms.
    frames[0].save(buf, format='GIF', save_all=True, append_images=frames[1:],
                    duration=durations, loop=0, disposal=1, optimize=True)
    gif = buf.getvalue()
    _deck_gif_cache.set(cache_key, gif)
    return gif


@app.route('/render.gif', methods=['GET'])
def render_gif():
    """Deck-to-GIF sibling of /render.png: ?b=<_encode_deck_qs output>,
    same codec -- _decode_block_qs doesn't care which shape it decodes."""
    try:
        spec = _decode_block_qs(request.args.get('b', ''))
        gif = _render_deck_gif(spec['blocks'], spec.get('duration_ms', 1000))
    except ImportError as e:
        # Specifically distinguished from the generic except below: this
        # means requirements.txt and the actual installed environment have
        # drifted (e.g. Pillow missing) -- a maintainer needs to see THAT,
        # not a bare atom/decode error. Real incident, 2026-07-26: this
        # exact failure shipped once because local verification ran in an
        # environment with Pillow already installed from an unrelated
        # earlier step, masking that requirements.txt didn't list it.
        return Response(f'render.gif failed: missing dependency ({e}) -- '
                         f'check requirements.txt is installed', status=500, mimetype='text/plain')
    except _InvalidToken as e:
        return Response(f'render.gif failed: {e}', status=403, mimetype='text/plain')
    except RuntimeError as e:
        return Response(f'render.gif failed: {e}', status=429, mimetype='text/plain')
    except ValueError as e:
        return Response(f'render.gif failed: {e}', status=400, mimetype='text/plain')
    except Exception as e:
        return Response(f'render.gif failed: {e}', status=502, mimetype='text/plain')
    return Response(gif, mimetype='image/gif',
                     headers={'Cache-Control': 'public, max-age=300'})


@app.route('/render-deck', methods=['POST'])
def render_deck():
    """POST sibling of /render.gif -- deck in a JSON body, GIF bytes out.

    /render.gif exists for Chat's anonymous image-widget fetch, which can
    only do a plain GET, hence the signed ?b= token. An IAM-authenticated
    caller (the Authoring suite's carousel export, via blog-worker) is
    already authenticated by Cloud Run itself and cannot mint that HMAC
    without being handed the signing key -- sharing a server secret with a
    Worker just to re-authenticate an already-authenticated request would be
    strictly worse than this route. Same body convention as POST /render,
    and no URL-length ceiling on the deck, which a GET would also impose.

    Body: {"blocks": [{"block": {...}, "width": 1080}, ...], "duration_ms": 1500}
    Returns: image/gif bytes, or {"ok": true, "gif_base64": "..."} when the
    Accept header asks for JSON (same rationale as /render's JSON mode)."""
    payload = request.get_json(force=True)
    blocks = payload.get('blocks')
    if not isinstance(blocks, list) or not blocks:
        return Response(json.dumps({'ok': False, 'error': "missing 'blocks' list"}),
                        status=400, mimetype='application/json')
    try:
        for spec in blocks:
            if not isinstance(spec, dict):
                raise ValueError('each blocks[] entry must be an object')
            spec['block'] = _validated_block(spec.get('block'))
            spec['width'] = _validated_width(spec.get('width', 620))
        gif = _render_deck_gif(blocks, payload.get('duration_ms', 1000))
    except ImportError as e:
        return Response(json.dumps({'ok': False, 'error': f'missing dependency ({e})'}),
                        status=500, mimetype='application/json')
    except RuntimeError as e:
        return Response(json.dumps({'ok': False, 'error': str(e)}),
                        status=429, mimetype='application/json')
    except ValueError as e:
        return Response(json.dumps({'ok': False, 'error': str(e)}),
                        status=400, mimetype='application/json')

    if 'application/json' in request.headers.get('Accept', ''):
        return Response(json.dumps({'ok': True, 'gif_base64': base64.b64encode(gif).decode('ascii')}),
                        mimetype='application/json')
    return Response(gif, mimetype='image/gif')


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
            gif_url = f"{_self_base_url()}/render.gif?b={_encode_deck_qs(gif_cards, duration_ms=1500)}"
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
                img_url = f"{_self_base_url()}/render.png?b={_encode_block_qs(spec['block'], spec['width'])}"
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
