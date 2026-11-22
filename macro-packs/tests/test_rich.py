"""The opt-in rich output policy (d3pack/rich.py) and the svg_lab demo macro: every admitted feature is admitted at its limit and refused one step past it, every refused class is refused, the base
verify_svg is unchanged and still refuses all of it, the demo draws only what the policy admits, and a rich result is only accepted as an Image by the rich verifier. Run: python3 tests/test_rich.py (stdlib only)."""
import sys, re, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.dont_write_bytecode = True
import d3pack
from d3pack import common as C
from d3pack.rich import verify_rich
lab = sys.modules['d3pack.svg_lab']
fails = []; n = 0
def ok(name, c):
    global n; n += 1
    if not c: fails.append(name); print('FAIL', name)
def refused(f, s):
    try: f(s); return False
    except C.SvgPolicyError as e:
        if os.environ.get('SHOW'): print('   refused:', str(e)[:100])
        return True
def admitted(s):
    try: verify_rich(s); return True
    except C.SvgPolicyError as e: print('   not admitted:', e); return False
W = lambda inner, extra='': f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"{extra}>{inner}</svg>'
R = '<rect width="9" height="9" fill="#ff0000"{}>{}</rect>'
stops = lambda k: ''.join(f'<stop offset="{i / max(k - 1, 1):.2f}" stop-color="#4b4acf"/>' for i in range(k))
grad = lambda k: W(f'<defs><linearGradient id="g">{stops(k)}</linearGradient></defs>' + R.format(' fill="url(#g)"'.replace(' fill="url(#g)"', ''), '').replace('fill="#ff0000"', 'fill="url(#g)"'))
anim = lambda dur, rep, begin='0s', fill='freeze', attr='opacity': R.format('', f'<animate attributeName="{attr}" from="0" to="1" dur="{dur}" begin="{begin}" repeatCount="{rep}" fill="{fill}"/>')
filt = lambda prims, sd='4': W('<defs><filter id="f">' + prims.format(sd=sd) + '</filter></defs>' + R.format(' filter="url(#f)"', '').replace('fill="#ff0000" filter', 'fill="#ff0000" filter'))
SH = '<feDropShadow dx="0" dy="2" stdDeviation="{sd}"/>'
# gradients
ok('a gradient with 8 stops is admitted', admitted(grad(8))); ok('a gradient with 9 stops is refused', refused(verify_rich, grad(9)))
ok('a fill pointing at a missing id is refused', refused(verify_rich, W(R.format('', '').replace('fill="#ff0000"', 'fill="url(#nope)"'))))
ok('a fill pointing at a filter id (wrong type) is refused', refused(verify_rich, W('<defs><filter id="f"><feGaussianBlur stdDeviation="2"/></filter></defs>' + R.replace('#ff0000', 'url(#f)').format('', ''))))
ok('a gradient href is refused', refused(verify_rich, W('<defs><linearGradient id="g" href="#h">' + stops(2) + '</linearGradient></defs>')))
# animation
ok('an animation ending at exactly 5 s is admitted', admitted(W(anim('5s', '1')))); ok('5 s of repeats (1 s x 5) is admitted', admitted(W(anim('1s', '5'))))
ok('an animation ending at 5.001 s is refused', refused(verify_rich, W(anim('5.001s', '1')))); ok('begin 2 s + dur 4 s is refused', refused(verify_rich, W(anim('4s', '1', '2s'))))
ok('repeatCount indefinite is refused', refused(verify_rich, W(anim('1s', 'indefinite')))); ok('repeatCount 0 is refused', refused(verify_rich, W(anim('1s', '0'))))
ok('fill remove is refused', refused(verify_rich, W(anim('1s', '1', fill='remove')))); ok('animating width is refused', refused(verify_rich, W(anim('1s', '1', attr='width'))))
ok('animateMotion and set are refused', refused(verify_rich, W(R.format('', '<animateMotion dur="1s" path="M0,0 L9,9"/>'))) and refused(verify_rich, W(R.format('', '<set attributeName="opacity" to="0"/>'))))
ok('animate with a href is refused', refused(verify_rich, W(R.format('', '<animate href="#x" attributeName="opacity" from="0" to="1" dur="1s" repeatCount="1" fill="freeze"/>'))))
ok('an animateTransform translate is admitted', admitted(W(R.format('', '<animateTransform attributeName="transform" type="translate" from="0 0" to="9 9" dur="1s" repeatCount="1" fill="freeze"/>'))))
ok('an animateTransform skew is refused', refused(verify_rich, W(R.format('', '<animateTransform attributeName="transform" type="skewX" from="0" to="9" dur="1s" repeatCount="1" fill="freeze"/>'))))
many = lambda k: W(''.join(R.format('', '<animate attributeName="opacity" from="0" to="1" dur="1s" repeatCount="1" fill="freeze"/>') for _ in range(k)))
ok('20 animated elements are admitted, 21 refused', admitted(many(20)) and refused(verify_rich, many(21)))
# filters
ok('one feDropShadow filter is admitted', admitted(filt(SH))); ok('blur 8 is admitted, 8.5 refused', admitted(filt(SH, '8')) and refused(verify_rich, filt(SH, '8.5')))
ok('a stdDeviation with two numbers is refused', refused(verify_rich, filt(SH, '4 4')))
ok('the 24-primitive chain that hangs a tab is refused', refused(verify_rich, filt(SH * 24))); ok('even two primitives are refused', refused(verify_rich, filt(SH * 2)))
ok('feTurbulence and feImage are refused', refused(verify_rich, filt('<feTurbulence baseFrequency="0.05"/>')) and refused(verify_rich, filt('<feImage href="data:image/png;base64,AAAA"/>')))
ok('a filter with no primitive is refused', refused(verify_rich, filt('')))
two = W('<defs><filter id="a"><feGaussianBlur stdDeviation="1"/></filter><filter id="b"><feGaussianBlur stdDeviation="1"/></filter><filter id="c"><feGaussianBlur stdDeviation="1"/></filter></defs>')
ok('three filters are refused', refused(verify_rich, two))
ok('51 filtered elements are refused, 50 admitted', admitted(W('<defs><filter id="f"><feGaussianBlur stdDeviation="1"/></filter></defs>' + R.format(' filter="url(#f)"', '') * 50)) and refused(verify_rich, W('<defs><filter id="f"><feGaussianBlur stdDeviation="1"/></filter></defs>' + R.format(' filter="url(#f)"', '') * 51)))
ok('an animated element inside a filtered group is refused', refused(verify_rich, W('<defs><filter id="f"><feGaussianBlur stdDeviation="1"/></filter></defs><g filter="url(#f)">' + anim('1s', '1') + '</g>')))
ok('a filtered element that is itself animated is refused', refused(verify_rich, W('<defs><filter id="f"><feGaussianBlur stdDeviation="1"/></filter></defs>' + R.format(' filter="url(#f)"', '<animate attributeName="opacity" from="0" to="1" dur="1s" repeatCount="1" fill="freeze"/>'))))
# style
S = lambda css: W(f'<style>{css}</style>' + R.format('', ''))
GOOD = '@media (prefers-color-scheme: dark){.d3-bg{fill:#1b1d3a}.d3-fg{fill:#f2f3ff}}'
ok('the fixed dark-mode template is admitted', admitted(S(GOOD)))
for name, css in (('@keyframes', '@keyframes a{from{opacity:0}}'), ('@import', '@import url(https://example.com/a.css);'), ('@font-face', '@font-face{font-family:x;src:url(https://example.com/f.woff)}'),
                  ('a url() value', GOOD.replace('fill:#1b1d3a', 'fill:url(https://example.com/x)')), ('a bare selector', GOOD.replace('.d3-bg', 'svg')), ('an unprefixed class', GOOD.replace('.d3-bg', '.bg')),
                  ('an extra property', GOOD.replace('fill:#1b1d3a', 'fill:#1b1d3a;animation:a 1s infinite')), ('a non-hex colour', GOOD.replace('#1b1d3a', 'red')), ('another media query', GOOD.replace('dark', 'light')),
                  ('a style comment', GOOD.replace('{.d3-bg', '/*x*/{.d3-bg')), ('a second block', GOOD + GOOD)): ok(f'style: {name} is refused', refused(verify_rich, S(css)))
ok('a style nested in a group is refused', refused(verify_rich, W(f'<g><style>{GOOD}</style></g>')))
ok('two style elements are refused', refused(verify_rich, W(f'<style>{GOOD}</style><style>{GOOD}</style>')))
# everything the base policy refuses stays refused
for name, inner in (('script', '<script>alert(1)</script>'), ('foreignObject', '<foreignObject width="9" height="9"/>'), ('image', '<image href="https://example.com/a.png" width="9" height="9"/>'), ('use', '<use href="#a"/>'),
                    ('an event handler', R.format(' onload="x()"', '')), ('a link', '<a href="https://example.com"><rect width="9" height="9" fill="#ff0000"/></a>'), ('a repeated id', '<rect id="a" width="9" height="9" fill="#ff0000"/><rect id="a" width="9" height="9" fill="#ff0000"/>'),
                    ('text under 12 px', '<text x="1" y="20" font-size="9" fill="#000000">x</text>'), ('a comment', '<!-- x --><rect width="9" height="9" fill="#ff0000"/>')): ok(f'{name} is refused', refused(verify_rich, W(inner)))
ok('a DOCTYPE with an entity is refused', refused(verify_rich, '<!DOCTYPE svg [<!ENTITY x "y">]><svg xmlns="http://www.w3.org/2000/svg"/>')); ok('the wrong namespace is refused', refused(verify_rich, '<svg xmlns="http://example.com/"/>'))
ok('over 60 KB is refused', refused(verify_rich, W('<rect width="9" height="9" fill="#ff0000"/>' * 1500)))
# the base policy is unchanged: it refuses every rich feature, so rich output cannot ride through it
for name, s in (('a gradient', grad(2)), ('an animation', W(anim('1s', '1'))), ('a filter', filt(SH)), ('a style block', S(GOOD))): ok(f'the default verify_svg still refuses {name}', refused(C.verify_svg, s))
# the demo
r = d3pack.call('svg_lab', {}, isolate=False); ok('svg_lab returns admitted and refused', set(r) == {'admitted', 'refused', '_default'} and r['_default'] == 'admitted')
for k in ('admitted', 'refused'):
    v = r[k]; ok(f'svg_lab {k}: policy rich, passes the rich verifier, fails the base verifier', v['policy'] == 'rich' and admitted(v['svg']) and refused(C.verify_svg, v['svg']))
    ok(f'svg_lab {k}: it becomes an Image data URI and a result without the rich mark would not', C._dm(v)['img'].startswith('data:image/svg+xml;base64,') and refused(lambda s: C.data_uri(s), v['svg']))
ok('svg_lab is deterministic', d3pack.call('svg_lab', {}, isolate=False)['admitted']['svg'] == r['admitted']['svg'])
ok('svg_lab animations end within 5 s', all(float(m) * float(c) <= 5 for m, c in zip(re.findall(r'dur="(\d+(?:\.\d+)?)s"', r['admitted']['svg']), re.findall(r'repeatCount="(\d)"', r['admitted']['svg']))))
ok('the refused view lists 8 samples with real reasons', r['refused']['svg'].count('REFUSED') == 8 and 'hang a tab' in r['refused']['svg'])
ok('the table says what each browser does and names the refusals', 'Chromium 153' in r['admitted']['table'] and 'WebKit' in r['admitted']['table'] and 'animateMotion' in r['admitted']['table'])
real = lab._bad_samples(); ok('every demo "bad" sample is refused, by the verifier, now', len(real) == 8 and all(refused(verify_rich, s) for _, s in real))
orig = lab._bad_samples; lab._bad_samples = lambda: [('ok sample', W(R.format('', '')))]
try: lab.svg_lab(); ok('the demo raises if a sample it claims is refused is ever admitted', False)
except AssertionError: ok('the demo raises if a sample it claims is refused is ever admitted', True)
finally: lab._bad_samples = orig

# --- rich is a superset of base (18 Nov 2026: it was not; 29 of the 51 drawings the pack makes, all passing base, were refused by rich) ---
def _admitted_by_base():
    out = []
    for k, (macro, params) in sorted(d3pack._demos().items()):
        try: res = d3pack.PACK[macro](**params)
        except Exception: continue
        for mode, r in res.items():
            if mode == '_default' or not isinstance(r, dict) or 'svg' not in r: continue
            try: C.verify_svg(r['svg'])
            except C.SvgPolicyError: continue
            out.append((k + ':' + mode, r['svg']))
    return out
corpus = _admitted_by_base()
ok('the corpus is real (at least 40 drawings the base policy admits)', len(corpus) >= 40)
within = [(k, sv) for k, sv in corpus if len(sv.encode()) <= 60_000 and sv.count('<') <= 400]
ok('every drawing the base policy admits, within the rich budgets, is admitted by rich (%d of %d)' % (len(within), len(corpus)), all(not refused(verify_rich, sv) for k, sv in within))
bad = [k for k, sv in within if refused(verify_rich, sv)]
ok('no superset exceptions: ' + ', '.join(bad[:5]), not bad)
SV = lambda body: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" role="img" aria-label="t">%s</svg>' % body
for name, body in (('polygon', '<polygon points="0,0 10,0 5,8" fill="#abc" stroke="#000" stroke-width="2"/>'),
                   ('stroke-linejoin on a group', '<g stroke="#000" stroke-width="2" stroke-linejoin="round"><line x1="0" y1="0" x2="5" y2="5"/></g>'),
                   ('fill-rule on a path', '<path d="M 0 0 L 5 5 L 0 5 Z" fill="#abc" fill-rule="evenodd"/>'),
                   ('stroke-opacity on a path', '<path d="M 0 0 L 5 5" stroke="#000" stroke-opacity="0.5"/>'),
                   ('stroke-dasharray on a line', '<line x1="0" y1="0" x2="5" y2="5" stroke="#000" stroke-dasharray="2 2"/>'),
                   ('paint-order and a stroke on text', '<text x="1" y="20" font-size="14" fill="#000" stroke="#fff" stroke-width="3" paint-order="stroke" font-family="sans-serif">a</text>'),
                   ('a text rotate transform', '<text x="1" y="20" font-size="14" transform="rotate(-90 1 20)">a</text>'),
                   ('data-* integers', '<rect x="1" y="1" width="5" height="5" data-box="3"/>'),
                   ('a clipPath and a clip-path that names it', '<defs><clipPath id="c1"><rect x="0" y="0" width="5" height="5"/></clipPath></defs><g clip-path="url(#c1)"><rect x="0" y="0" width="9" height="9"/></g>')):
    ok('rich admits ' + name + ' (as the base does)', not refused(verify_rich, SV(body)) and not refused(C.verify_svg, SV(body)))
ok('rich admits a polygon filled with a gradient', not refused(verify_rich, SV('<defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000000"/><stop offset="1" stop-color="#ffffff"/></linearGradient></defs><polygon points="0,0 10,0 5,8" fill="url(#g1)"/>')))
# ... and nothing unsafe came in with it
for name, body in (('a clip-path naming no clipPath', '<g clip-path="url(#nope)"><rect x="0" y="0" width="9" height="9"/></g>'),
                   ('a clip-path naming a gradient', '<defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000000"/></linearGradient></defs><g clip-path="url(#g1)"><rect x="0" y="0" width="9" height="9"/></g>'),
                   ('a clip-path that is not a url', '<g clip-path="none"><rect x="0" y="0" width="9" height="9"/></g>'),
                   ('stroke-linejoin other than round', '<g stroke-linejoin="miter"><rect x="0" y="0" width="9" height="9"/></g>'),
                   ('paint-order other than stroke', '<text x="1" y="20" font-size="14" paint-order="fill">a</text>'),
                   ('a transform on a rect', '<rect x="0" y="0" width="9" height="9" transform="translate(5 5)"/>'),
                   ('a non-integer data attribute', '<rect x="0" y="0" width="9" height="9" data-box="x"/>'),
                   ('a polygon with a colour name', '<polygon points="0,0 10,0 5,8" fill="red"/>'),
                   ('a polygon with a url() stroke', '<polygon points="0,0 10,0 5,8" stroke="url(#g)"/>'),
                   ('a polygon with a script-looking points value', '<polygon points="javascript:alert(1)"/>'),
                   ('an onclick on a polygon', '<polygon points="0,0 10,0 5,8" onclick="x()"/>'),
                   ('an href on a polygon', '<polygon points="0,0 10,0 5,8" href="http://x"/>'),
                   ('a style element outside the template', '<style>rect{fill:red}</style>'),
                   ('a clipPath with a child that is not allowed', '<defs><clipPath id="c1"><image href="x"/></clipPath></defs>')):
    ok('rich still refuses ' + name, refused(verify_rich, SV(body)))
# --- the style element must have NO child elements (security review 18 Nov 2026, finding 1: CSS after a child element of <style> was never checked, yet a browser builds the stylesheet from all of its text) ---
CSS = '@media (prefers-color-scheme: dark){.d3-a{fill:#000000}}'
ok('the plain dark-mode style is still admitted', admitted(W(f'<style>{CSS}</style>' + R.format('', ''))))
for name, inner in (('a g child then more CSS', f'<style>{CSS}<g/>body{{display:none}} svg{{background:url(https://evil.example/b)}}</style>'),
                    ('a title child then more CSS', f'<style>{CSS}<title>t</title>p{{color:red}}</style>'),
                    ('a defs child then an @import', f'<style>{CSS}<defs/>@import url(https://evil.example/x.css);</style>'),
                    ('a child element and no trailing text', f'<style>{CSS}<g/></style>'),
                    ('a child element before the CSS', f'<style><g/>{CSS}</style>')):
    ok('rich refuses a style with ' + name, refused(verify_rich, W(inner + R.format('', ''))))
PFX = '<s:svg xmlns:s="http://www.w3.org/2000/svg" width="10" height="10"><s:style>' + CSS + '<s:g/>body{display:none}</s:style></s:svg>'
ok('rich refuses the same trick with a namespace prefix on every element', refused(verify_rich, PFX))
ok('the base policy still refuses every style', refused(C.verify_svg, W(f'<style>{CSS}</style>' + R.format('', ''))))
print(f'rich policy checks: {n}, failed {len(fails)}'); sys.exit(1 if fails else 0)
