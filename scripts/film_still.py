"""film_still: the poster of a motion_timeline film = its settled frame as static HTML (I91, 2026-10-24).

A film is a pure function of time (`seek(t)` in the player script). Where motion cannot play (PDF, email, Chat, print)
the film should degrade to a meaningful still instead of a blank stage. `film_poster_html(film)` renders the film with the
real renderer, evaluates every track at the poster time in Python (a port of the player's `at`/`ap`), writes the result
into the elements as inline styles, and strips everything that moves: the player script, the controls, @keyframes and
`animation:` (a `forwards` animation is replaced by its end state). The output has no script and no CSS animation.

Poster time: `t` argument, else the film's own `poster` field (seconds), else the renderer's default (60% of duration),
the same frame the player shows under prefers-reduced-motion.

Not reproduced (the element stays at its natural place / unclipped): path following (`a` keys on a track with a path)
and the `lz` clip shape (needs a canvas). Both are rare; a still of them is the unanimated layout.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from renderers import web_article as wa  # noqa: E402


def film_cfg(film: dict) -> tuple[dict, str]:
    """Render the film and return (its player config as a dict, the rendered html). The config is the JS object literal
    the renderer hands the player (W, H, dur, poster, tg = per-element keyframes in [t, value, ease] triples)."""
    html = wa._render_motion_timeline(film)
    m = re.search(r'var C=(\{.*?\});var root=', html, re.S)
    if not m:
        raise ValueError('not a renderable motion_timeline')
    cfg = json.loads(re.sub(r'(?<=[{,])([A-Za-z_]\w*):', r'"\1":', m.group(1)))
    return cfg, html


def _bez(a, b, t):
    u = 1 - t
    return 3 * u * u * t * a + 3 * u * t * t * b + t * t * t


def _ez(e, u):
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    if not e:
        return u
    if e == 1:
        return 0.0
    lo, hi, t = 0.0, 1.0, u
    for _ in range(28):
        t = (lo + hi) / 2
        if _bez(e[0], e[2], t) < u:
            lo = t
        else:
            hi = t
    return _bez(e[1], e[3], t)


def value_at(keys, t):
    """Port of the player's at(): keys are [t, value, ease] with ease null | 1 (hold) | four bezier numbers."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            a, b = keys[i - 1], keys[i]
            return a[1] + (b[1] - a[1]) * _ez(b[2] if len(b) > 2 else None, (t - a[0]) / (b[0] - a[0]))
    return keys[-1][1]


def _fx(v, d):
    return f'{v:.{d}f}'


def _fm(v, d, pre, suf):
    """Port of the player's number formatter (thousands separators, rounding half up)."""
    neg, v = v < 0, abs(v)
    m = 10 ** d
    k = int(v * m + 0.5)
    ip, fp = k // m, str(k % m).rjust(d, '0')
    return ('-' if neg and k > 0 else '') + pre + f'{ip:,}' + ('.' + fp if d > 0 else '') + suf


def element_style(vals: dict, track: dict, w: int, h: int, x0: float, y0: float) -> str:
    """The inline style the player's ap() would set for one element at one moment (vals = each property at that time)."""
    v, tr, out = dict(vals), '', ''
    if track.get('d'):  # path following is not reproduced: drop the path-driven position
        v.pop('a', None)
    if 'x' in v or 'y' in v:
        tr += f"translate({_fx((v.get('x', x0) - x0) * w / 100, 2)}px,{_fx((v.get('y', y0) - y0) * h / 100, 2)}px) "
    if 'rx' in v:
        tr += f"rotateX({_fx(v['rx'], 2)}deg) "
    if 'ry' in v:
        tr += f"rotateY({_fx(v['ry'], 2)}deg) "
    if 'rotate' in v:
        tr += f"rotate({_fx(v['rotate'], 2)}deg) "
    if 'scale' in v:
        tr += f"scale({_fx(max(0, v['scale']), 4)})"
    if tr:
        out += 'transform:' + tr.strip() + ';'
    if 'opacity' in v:
        out += 'opacity:' + _fx(max(0, min(1, v['opacity'])), 3) + ';'
    if 'blur' in v:
        out += ('filter:blur(' + _fx(min(40, v['blur']), 2) + 'px);') if v['blur'] > 0.05 else 'filter:none;'
    if 'clip' in v:
        cl = max(0, min(1, v['clip']))
        cs = round(v.get('cs', 0))
        if cl < 0.999 or cs == 5:
            if cs == 1:
                out += f'clip-path:circle({_fx(cl * 75, 2)}% at 50% 50%);'
            elif cs == 2:
                out += f'mask-image:conic-gradient(#000 {_fx(cl * 360, 2)}deg,transparent 0);'
            elif cs == 3:
                out += f'mask-image:repeating-linear-gradient(90deg,#000 0,#000 {_fx(cl * 10, 3)}%,transparent {_fx(cl * 10, 3)}%,transparent 10%);'
            elif cs == 4:
                out += f'clip-path:polygon(0 0,{_fx(cl * 140, 2)}% 0,{_fx(cl * 140 - 40, 2)}% 100%,0 100%);'
            elif cs == 5:
                e5 = cl * 170 - 15
                out += f'clip-path:polygon({_fx(e5 - 14, 2)}% 0,{_fx(e5 + 8, 2)}% 0,{_fx(e5 - 32, 2)}% 100%,{_fx(e5 - 54, 2)}% 100%);'
            elif cs == 6:
                out += f'clip-path:polygon(0 0,{_fx(cl * 170 - 15, 2)}% 0,{_fx(cl * 170 - 55, 2)}% 100%,0 100%);'
            elif cs == 7:
                hh = _fx((1 - cl) * 50, 3)
                out += f'clip-path:inset(0 {hh}% 0 {hh}%);'
            elif cs == 9:
                pass  # lz needs a canvas: unclipped
            else:
                out += f'clip-path:inset(0 {_fx((1 - cl) * 100, 2)}% 0 0);'
    if 'p' in v:
        out += '--p:' + _fx(v['p'], 4) + ';'
    if 'step' in v:
        out += '--s:' + _fx(v['step'], 4) + ';'
    return out


_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class _Freeze(HTMLParser):
    """Rewrites the rendered film: inline styles for the poster time, no script, no controls, numbers at their poster value."""

    def __init__(self, styles, ps, kf):
        super().__init__(convert_charrefs=False)
        self.styles, self.ps, self.kf = styles, ps, kf
        self.out, self.stack, self.skip, self.num = [], [], 0, None

    def _attrs(self, tag, attrs, raw):
        d = dict(attrs)
        cls = d.get('class') or ''
        if tag == 'script':
            return None
        style = d.get('style')
        extra = ''
        if style is not None:
            m = re.search(r'animation:\s*([\w-]+)[^;"]*', style)
            if m:
                body = self.kf.get(m.group(1), '')
                style = re.sub(r'animation:[^;]*;?', '', style)
                extra += body
        mid = d.get('data-mt-id')
        if mid is not None:
            extra += self.styles.get(mid, '')
        if 'mt-vp' in cls.split() and False:
            pass
        if extra or (style is not None and style != d.get('style')):
            s = (style or '')
            if s and not s.endswith(';'):
                s += ';'
            new = (s + extra)
            if style is None:
                raw = raw[:-1].rstrip('/').rstrip() + f' style="{new}"' + ('/>' if raw.endswith('/>') else '>')
            else:
                raw = re.sub(r'style="[^"]*"', lambda _m: f'style="{new}"', raw, count=1)
        return raw

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        if self.skip:
            if tag not in _VOID:
                self.skip += 1
            return
        if tag == 'script':
            self.skip = 1
            return
        d = dict(attrs)
        owner = d.get('data-mt-id') or (self.stack[-1][1] if self.stack else None)
        if tag not in _VOID:
            self.stack.append((tag, owner))
        if 'data-mt-num' in d and owner in self.ps:
            try:
                a, b = float(d.get('data-from', 0)), float(d.get('data-to', 0))
                dec = int(d.get('data-dec') or 0)
                pre = d.get('data-pre') or ''
                suf = d.get('data-suf') or ''
                self.num = _fm(a + (b - a) * self.ps[owner], dec, pre, suf)
            except ValueError:
                self.num = None
        self.out.append(self._attrs(tag, attrs, raw))

    def handle_startendtag(self, tag, attrs):
        if self.skip:
            return
        self.out.append(self._attrs(tag, attrs, self.get_starttag_text()))

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag in _VOID:
            return
        if self.stack:
            self.stack.pop()
        self.num = None if self.num is None else self.num
        self.out.append(f'</{tag}>')

    def handle_data(self, data):
        if self.skip:
            return
        if self.num is not None:
            data, self.num = self.num, None
        self.out.append(data)

    def handle_entityref(self, name):
        if not self.skip:
            self.out.append(f'&{name};')

    def handle_charref(self, name):
        if not self.skip:
            self.out.append(f'&#{name};')

    def handle_comment(self, data):
        if not self.skip:
            self.out.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self.out.append(f'<!{decl}>')


def _keyframe_ends(html: str) -> dict:
    """name -> the declarations of the `to` state of each @keyframes (what a `forwards` animation settles on)."""
    ends = {}
    for m in re.finditer(r'@keyframes\s+([\w-]+)\s*\{(.*?)\}\s*\}', html, re.S):
        t = re.search(r'to\s*\{([^}]*)\}', m.group(2) + '}')
        if t:
            ends[m.group(1)] = t.group(1).strip().rstrip(';') + ';'
    return ends


def film_poster_html(film: dict, t: float | None = None, width: int | None = None) -> str:
    """The film's settled frame as static HTML (no script, no animation). `film` is a motion_timeline block, or a payload
    whose first block is one. `t` overrides the poster time (seconds); `width` is the rendered stage width in px
    (default: the stage's native width, e.g. 1280 for 16:9), so the still lays out the same everywhere."""
    if film.get('type') != 'motion_timeline':
        tl = next((b for b in film.get('blocks', []) if isinstance(b, dict) and b.get('type') == 'motion_timeline'), None)
        if tl is None:
            raise ValueError('no motion_timeline in payload')
        film = tl
    cfg, html = film_cfg(film)
    W, H = cfg['W'], cfg['H']
    when = float(t if t is not None else cfg['poster'])
    when = max(0.0, min(float(cfg['dur']), when))
    uid = re.search(r'<div id="mt-(\w+)"', html).group(1)
    # the geometry each element starts from (data-mt-x/y), to turn absolute x/y keys into offsets
    origin = {m.group(1): (float(m.group(2) or 0), float(m.group(3) or 0)) for m in
              re.finditer(r'data-mt-id="([^"]+)"(?:[^>]*?data-mt-x="([^"]*)")?(?:[^>]*?data-mt-y="([^"]*)")?', html)}
    styles, ps = {}, {}
    for g in cfg['tg']:
        vals = {k: value_at(ks, when) for k, ks in g['p'].items() if ks}
        x0, y0 = origin.get(g['i'], (0.0, 0.0))
        styles[g['i']] = styles.get(g['i'], '') + element_style(vals, g, W, H, x0, y0)
        if 'p' in vals:
            ps[g['i']] = vals['p']
    html = html[html.index('<div id="mt-'):]                     # drop the host-page style prefix
    html = re.sub(r'<div style="display:flex;align-items:center;gap:12px;padding:10px 4px 0;.*?</span></div>', '', html, count=1, flags=re.S)
    kf = _keyframe_ends(html)
    fr = _Freeze(styles, ps, kf)
    fr.feed(html)
    fr.close()
    out = ''.join(fr.out)
    out = re.sub(r'<style>[^<]*@keyframes[^<]*</style>', '', out)
    out = re.sub(r'\.mt-root\[data-pl="1"\][^<]*', '', out)
    k = (width or W) / W
    out = out.replace('visibility:hidden;perspective', 'visibility:visible;transform:scale(' + _fx(k, 5) + ');perspective', 1)
    out = out.replace('position:relative;width:100%;aspect-ratio:' + f'{W}/{H}', 'position:relative;width:' + str(round(W * k)) + 'px;aspect-ratio:' + f'{W}/{H}', 1)
    return out


def film_poster_document(film: dict, t: float | None = None, width: int | None = None, lang: str = 'en') -> str:
    """The same still as a complete HTML document (for an <iframe>, a PDF renderer or a screenshot)."""
    body = film_poster_html(film, t, width)
    bg = wa._mo_tl_bg[0]
    return ('<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Film poster</title><style>html,body{margin:0;background:' + bg + '}</style></head><body>' + body + '</body></html>')
