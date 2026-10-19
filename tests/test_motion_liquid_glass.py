"""motion_liquid_glass: closes what it opens (so later timeline scenes are not swallowed, the bug class found in
motion_kinetic_drum on 2026-10-19), and degrades sensibly: no backdrop-filter, no WebGL or canvas, no script, and no
animation of its own that would ignore reduced motion -- every movement comes from the timeline's p and s dials.
"""
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from renderers import web_article as wa  # noqa: E402

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Nesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.parents, self.unbalanced = [], {}, []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        mid = dict(attrs).get('data-mt-id')
        if mid:
            self.parents.setdefault(mid, [m for _, m in self.stack if m])
        self.stack.append((tag, mid))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.unbalanced.append(tag)
            return
        self.stack.pop()


def _parse(html):
    n = Nesting()
    n.feed(html)
    n.close()
    return n


CHILDREN = [{'type': 'motion_text', 'text': 'Behind the glass', 'size': 40}, {'type': 'motion_pill', 'text': 'Lens'}]


def test_glass_closes_what_it_opens():
    for shape in ('pill', 'circle', 'bar'):
        for extra in ({}, {'zoom': 1.5, 'blur': 0, 'dispersion': 0}, {'label': 'Glass'}):
            n = _parse(wa._RENDERERS['motion_liquid_glass'](dict(type='motion_liquid_glass', blocks=CHILDREN, shape=shape, **extra)))
            assert not n.unbalanced and not n.stack, (shape, extra, n.unbalanced, n.stack)


def test_glass_needs_no_backdrop_filter_webgl_script_or_own_animation():
    html = wa._RENDERERS['motion_liquid_glass'](dict(type='motion_liquid_glass', blocks=CHILDREN))
    for banned in ('backdrop-filter', '<canvas', 'webgl', '<script', '@keyframes', 'animation:'):
        assert banned not in html.lower(), banned
    assert 'var(--p' in html and 'var(--s' in html   # driven by the timeline's dials, which honour reduced motion


def test_the_lens_copy_of_the_children_is_hidden_from_assistive_tech():
    # the children are drawn twice: the stage (read normally), then the magnified copy inside the aria-hidden lens
    html = wa._RENDERERS['motion_liquid_glass'](dict(type='motion_liquid_glass', blocks=CHILDREN))
    lens = re.search(r'<div aria-hidden="true" style="position:absolute;left:calc', html).start()
    at = [m.start() for m in re.finditer('Behind the glass', html)]
    assert at and len(at) % 2 == 0
    assert all(x < lens for x in at[:len(at) // 2]) and all(x > lens for x in at[len(at) // 2:])


def test_scenes_after_a_glass_scene_are_not_nested_inside_it():
    def text(i, t):
        return dict(type='motion_text', id=i, text=t, place=dict(x=8, y=30, w=84))
    layers = [
        dict(type='motion_layer', id='s1', blocks=[dict(type='motion_liquid_glass', id='g1', blocks=CHILDREN, place=dict(x=10, y=10, w=80, h=80))]),
        dict(type='motion_layer', id='s2', blocks=[text('t2', 'Two')]),
        dict(type='motion_layer', id='s3', blocks=[text('t3', 'Three')]),
    ]
    tl = dict(type='motion_timeline', title='glass nesting', aspect='16:9', duration=12, blocks=layers,
              tracks=[dict(target='g1', keys=[dict(t=0, p=0, step=0), dict(t=3, p=1, step=1)])],
              scenes=[dict(layer='s1', t=0), dict(layer='s2', t=4), dict(layer='s3', t=8)])
    n = _parse(wa._RENDERERS['motion_timeline'](tl))
    assert not n.unbalanced, n.unbalanced
    for sid in ('s2', 's3', 't2', 't3'):
        assert sid in n.parents and 's1' not in n.parents[sid] and 'g1' not in n.parents[sid], (sid, n.parents.get(sid))
