"""film_vtt: WebVTT captions for a motion_timeline film (I88, 2026-10-24).

A film has no voice-over or caption field: the words a viewer reads are its `motion_text` blocks (and `demo_caption`
lines). `film_to_vtt(film)` turns those into cues. A cue's start and end are when the text is on screen, read from the
same keyframes the player uses (renderers' player config): the text's own opacity and reveal progress `p`, times the
opacity of the layers it sits in (scene hand-overs are layer opacity tracks). Sampled every 50 ms, so the cue times
follow the film's real timeline, not the scene list.

Wiring: the MP4/GIF export runs in the visitor's browser (public/vendors/client-export, a2ui-private motion-demos/builder/
export_mp4.mjs), which can only save a file it is handed; call film_to_vtt on the film payload next to the encoder and offer
the .vtt beside the .mp4. A captions file cannot be muxed into the MP4 container by that encoder.
Usage: python scripts/film_vtt.py film.json > film.vtt
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_still import film_cfg, value_at  # noqa: E402

STEP = 0.05
MIN_CUE = 0.2
P_SHOWN = 0.5        # a revealed text counts as on screen once its reveal progress passes this
OPACITY_SHOWN = 0.5


def ts(sec: float) -> str:
    """WebVTT timestamp HH:MM:SS.mmm."""
    ms = int(round(max(0.0, sec) * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}'


def esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _plain(text) -> str:
    """The accent markers (*word*) are styling, not words; line breaks become spaces."""
    return re.sub(r'\s+', ' ', str(text or '').replace('*', '')).strip()


def _walk(blocks, chain=()):
    for b in blocks if isinstance(blocks, list) else []:
        if not isinstance(b, dict):
            continue
        yield b, chain
        yield from _walk(b.get('blocks'), chain + ((b.get('id'),) if b.get('id') else ()))


def _intervals(flags, dur):
    out, start = [], None
    for i, on in enumerate(flags):
        t = i * STEP
        if on and start is None:
            start = t
        elif not on and start is not None:
            out.append((start, t))
            start = None
    if start is not None:
        out.append((start, dur))
    return [(a, min(b, dur)) for a, b in out if b - a >= MIN_CUE]


def film_to_vtt(film: dict) -> str:
    """WebVTT text for a motion_timeline block (or a payload whose first block is one)."""
    if film.get('type') != 'motion_timeline':
        film = next((b for b in film.get('blocks', []) if isinstance(b, dict) and b.get('type') == 'motion_timeline'), None)
        if film is None:
            raise ValueError('no motion_timeline in payload')
    cfg, _ = film_cfg(film)
    dur = float(cfg['dur'])
    tracks = {}
    for g in cfg['tg']:
        tracks.setdefault(g['i'], {}).update({k: v for k, v in g['p'].items() if v})
    n = int(dur / STEP) + 1
    times = [i * STEP for i in range(n)]

    def on_screen(chain, gate=None):
        flags = []
        for t in times:
            ok = True
            for i in chain:
                k = tracks.get(i, {}).get('opacity')
                if k and value_at(k, t) < OPACITY_SHOWN:
                    ok = False
                    break
            flags.append(ok and (gate(t) if gate else True))
        return flags

    cues = []
    for order, (b, anc) in enumerate(_walk(film.get('blocks'))):
        bid = b.get('id')
        mine = tracks.get(bid, {}) if bid else {}
        chain = anc + ((bid,) if bid else ())

        def shown(t, mine=mine):
            p = mine.get('p')
            return p is None or value_at(p, t) >= P_SHOWN
        if b.get('type') == 'motion_text' and _plain(b.get('text')):
            for a, z in _intervals(on_screen(chain, shown), dur):
                cues.append((a, z, order, bid, esc(_plain(b.get('text')))))
        elif b.get('type') == 'demo_caption' and isinstance(b.get('lines'), list):
            for li, line in enumerate(b['lines'][:12]):
                line = line if isinstance(line, dict) else {'text': line}
                text = _plain(line.get('text'))
                if not text:
                    continue
                st = mine.get('step')

                def at_line(t, st=st, li=li):
                    return abs(value_at(st, t) - li) < 0.5 if st else li == 0
                who = _plain(line.get('who')) or 'agent'
                for a, z in _intervals(on_screen(chain, at_line), dur):
                    cues.append((a, z, order * 100 + li, bid, '<v ' + esc(who) + '>' + esc(text) + '</v>'))
    cues.sort(key=lambda c: (c[0], c[1], c[2]))
    out, seen = ['WEBVTT', ''], {}
    for a, z, _o, bid, text in cues:
        ident = bid or 'cue'
        seen[ident] = seen.get(ident, 0) + 1
        if seen[ident] > 1:
            ident += '.' + str(seen[ident])
        out += [ident, ts(a) + ' --> ' + ts(z), text, '']
    return '\n'.join(out)


if __name__ == '__main__':
    sys.stdout.write(film_to_vtt(json.load(open(sys.argv[1]))))
