"""svg_lab: a demonstration macro for the 'rich' output policy (rich.py), built from the Opus SVG review. Variant `admitted` draws one panel for each thing an SVG shown as an <img> may carry under that policy
(a gradient, motion that ends within 5 s, a dark-mode switch, one soft shadow). Variant `refused` runs known-bad SVGs through the verifier AT DRAW TIME and draws each refusal with the verifier's own reason,
so the picture cannot claim more than the code enforces: if any bad sample is ever admitted the macro raises instead of drawing."""
from . import common as C
from .rich import verify_rich
W, H = 720, 520
STYLE = ('@media (prefers-color-scheme: dark){.d3-bg{fill:#1b1d3a}.d3-panel{fill:#26294d;stroke:#3c4072}.d3-fg{fill:#f2f3ff}.d3-mu{fill:#b9bde0}.d3-sw{fill:#e0912f}.d3-card{fill:#3a3e6e}.d3-bad{fill:#ff8a9c}}')
INK, MUTED, PANEL, EDGE, BAD = '#1f2150', '#59607a', '#f4f5ff', '#d5d8ee', '#a82a40'
def _wrap(body, label, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{C.esc(label)}"><style>{STYLE}</style>{defs}'
            f'<rect class="d3-bg" width="{W}" height="{H}" rx="24" fill="#ffffff"/>{body}</svg>')
def _t(x, y, s, size=14, anchor='start', weight=400, cls='d3-fg', fill=INK): return C.label(x, y, s, size, anchor, fill, weight, f'class="{cls}"')
def _panel(x, y, w, h): return f'<rect class="d3-panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{PANEL}" stroke="{EDGE}" stroke-width="1"/>'
def _bad_samples():
    wrap = lambda inner: f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">{inner}</svg>'
    chain = ''.join('<feDropShadow dx="1" dy="1" stdDeviation="2"/>' for _ in range(24))
    return [('24 chained shadow filters (a 1 KB file that can hang a tab)', wrap(f'<defs><filter id="f">{chain}</filter></defs><rect width="9" height="9" fill="#ff0000" filter="url(#f)"/>')),
            ('CSS @keyframes in a style block', wrap('<style>@keyframes a{from{opacity:0}to{opacity:1}}</style><rect width="9" height="9" fill="#ff0000"/>')),
            ('An animation that never stops', wrap('<rect width="9" height="9" fill="#ff0000"><animate attributeName="opacity" from="0" to="1" dur="1s" repeatCount="indefinite" fill="freeze"/></rect>')),
            ('A 12 second animation', wrap('<rect width="9" height="9" fill="#ff0000"><animate attributeName="opacity" from="0" to="1" dur="12s" repeatCount="1" fill="freeze"/></rect>')),
            ('animateMotion along a path', wrap('<rect width="9" height="9" fill="#ff0000"><animateMotion dur="2s" path="M0,0 L50,50"/></rect>')),
            ('A script element', wrap('<script>alert(1)</script>')),
            ('A fill that points at another site', wrap('<rect width="9" height="9" fill="url(https://example.com/a.svg#x)"/>')),
            ('feTurbulence (expensive, unbounded)', wrap('<defs><filter id="f"><feTurbulence baseFrequency="0.05"/></filter></defs><rect width="9" height="9" fill="#ff0000" filter="url(#f)"/>'))]
def _refusals():
    out = []
    for name, s in _bad_samples():
        try: verify_rich(s)
        except C.SvgPolicyError as e: out.append((name, C.plain(str(e))))
        else: raise AssertionError(f'svg_lab: the rich policy admitted a sample that must be refused: {name}')
    return out
def _admitted():
    defs = ('<defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4b4acf"/><stop offset="0.5" stop-color="#00a3ad"/><stop offset="1" stop-color="#e0912f"/></linearGradient>'
            '<linearGradient id="g2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4b4acf" stop-opacity="1"/><stop offset="1" stop-color="#4b4acf" stop-opacity="0.08"/></linearGradient>'
            '<filter id="f1"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#1f2150" flood-opacity="0.35"/></filter></defs>')
    b = _t(W / 2, 40, 'What an SVG image can do', 26, 'middle', 700)
    b += _panel(20, 64, 330, 200) + _t(40, 92, '1  Gradient', 17, weight=700)
    b += f'<rect x="40" y="108" width="290" height="56" rx="12" fill="url(#g1)"/><rect x="40" y="178" width="290" height="30" rx="8" fill="url(#g2)"/>' + _t(40, 236, 'Linear, up to 8 stops, same file only', 13, cls='d3-mu', fill=MUTED)
    b += _panel(370, 64, 330, 200) + _t(390, 92, '2  Motion that ends', 17, weight=700)
    b += f'<line x1="400" y1="136" x2="670" y2="136" stroke="{EDGE}" stroke-width="2"/><circle cx="400" cy="136" r="14" fill="#cc3f56"><animateTransform attributeName="transform" type="translate" from="0 0" to="250 0" dur="2s" begin="0s" repeatCount="1" fill="freeze"/></circle>'
    b += f'<circle cx="400" cy="190" r="14" fill="#00a3ad" fill-opacity="1"><animate attributeName="opacity" from="0.15" to="1" dur="1s" begin="0s" repeatCount="3" fill="freeze"/></circle>' + _t(390, 236, 'Starts on load, ends by 3 s, then holds (max 5 s)', 13, cls='d3-mu', fill=MUTED)
    b += _panel(20, 284, 330, 200) + _t(40, 312, '3  Follows dark mode', 17, weight=700)
    b += '<rect class="d3-sw" x="40" y="330" width="100" height="74" rx="12" fill="#4b4acf"/>' + _t(160, 352, 'Switch your device to dark', 14) + _t(160, 374, 'and this panel recolours.', 14) + _t(40, 462, 'Chromium, Firefox: yes. Safari: no', 13, cls='d3-mu', fill=MUTED)
    b += _panel(370, 284, 330, 200) + _t(390, 312, '4  A soft shadow', 17, weight=700)
    b += '<rect class="d3-card" x="400" y="336" width="250" height="84" rx="14" fill="#ffffff" filter="url(#f1)"/>' + _t(525, 384, 'One filter, one primitive', 15, 'middle', 600) + _t(390, 462, 'Blur at most 8, never animated, never chained', 13, cls='d3-mu', fill=MUTED)
    b += _t(W / 2, 508, 'Drawn by Python, checked by the rich policy. The default policy would refuse every panel here.', 12, 'middle', cls='d3-mu', fill=MUTED)
    return _wrap(b, 'Four panels: a gradient, motion that ends within three seconds, a dark mode switch and a soft shadow', defs)
def _refused(rows):
    b = _t(W / 2, 40, 'What the policy refuses', 26, 'middle', 700)
    for i, (name, why) in enumerate(rows):
        y = 64 + i * 54; why = why if len(why) <= 92 else why[:89] + '...'
        b += _panel(20, y, 680, 46) + _t(36, y + 20, 'REFUSED', 12, weight=700, cls='d3-bad', fill=BAD) + _t(104, y + 20, name, 14, weight=700) + _t(104, y + 38, why, 12, cls='d3-mu', fill=MUTED)
    return _wrap(b, 'Eight samples the rich policy refuses, each with the reason the verifier gave')
def svg_lab(version=1):
    """No inputs. Returns {'admitted': Result, 'refused': Result, '_default': 'admitted'}; both results carry policy='rich'."""
    rows = _refusals(); adm = _admitted(); ref = _refused(rows)
    table = ('Admitted under the rich policy: linear gradients (at most 8 stops); animate on opacity and animateTransform translate or rotate, ending within 5 s, at most 20 animated elements; '
             'one filter primitive (feDropShadow or feGaussianBlur, blur at most 8, at most 2 filters, never animated); one dark-mode style block from a fixed template. '
             'Checked in Chromium 153 and Firefox ESR 140: all run inside an image and load nothing external. WebKit applies dark mode inside an image: no. '
             'Reduced motion stops CSS animation in all three engines but SMIL ignores it, so motion here is capped at 5 s. '
             'Refused, with the verifier reason: ' + '; '.join(f'{n}: {w}' for n, w in rows) + '.')
    summary = 'One picture, four things an SVG image can do safely: a gradient, motion that ends within 5 seconds, a dark-mode switch and one soft shadow. The other view lists what the checker refuses.'
    mk = lambda svg_, title, summ: C.Result(kind='svg_lab', title=title, svg=verify_rich(svg_), summary=C.plain(summ), table=C.plain(table), notes=[], alt=f'Svg lab: {title}. {C.plain(summ)}', policy='rich')
    return {'admitted': mk(adm, 'What an SVG image can do', summary), 'refused': mk(ref, 'What the policy refuses', 'Eight unsafe SVGs, each refused by the verifier with its own reason.'), '_default': 'admitted'}
