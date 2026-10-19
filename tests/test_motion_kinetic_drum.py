"""motion_kinetic_drum must close every element it opens.

Found 2026-10-19 in a launch film: the Python renderer closed the drum's rig <div> but not its frame <div> (the GAS
twin closed both). Inside a motion_timeline, every block after the drum then nested inside it -- inside scene 1's
layer -- so once that layer faded out, every later scene computed opacity 1 and still never painted.
"""
import os
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from renderers import web_article as wa  # noqa: E402

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Nesting(HTMLParser):
    """The open-element stack, and for every data-mt-id the ids of the timeline elements around it."""
    def __init__(self):
        super().__init__()
        self.stack, self.parents, self.unbalanced = [], {}, []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        mid = dict(attrs).get('data-mt-id')
        if mid:
            self.parents[mid] = [m for _, m in self.stack if m]
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


def test_drum_closes_what_it_opens():
    for axis in ('x', 'y'):
        for extra in ({}, {'fill': True}, {'backdrop': '#101820'}):
            html = wa._RENDERERS['motion_kinetic_drum'](dict(type='motion_kinetic_drum', phrases=['One', 'Two', 'Three'], axis=axis, **extra))
            n = _parse(html)
            assert not n.unbalanced and not n.stack, (axis, extra, n.unbalanced, n.stack)


def test_scenes_after_a_drum_scene_are_not_nested_inside_it():
    def text(i, t):
        return dict(type='motion_text', id=i, text=t, place=dict(x=8, y=30, w=84))
    layers = [
        dict(type='motion_layer', id='s1', blocks=[text('t1', 'One'), dict(type='motion_kinetic_drum', id='d1', phrases=['Kinetic', 'Drum'], place=dict(x=55, y=20, w=40, h=60))]),
        dict(type='motion_layer', id='s2', blocks=[text('t2', 'Two')]),
        dict(type='motion_layer', id='s3', blocks=[text('t3', 'Three')]),
    ]
    tl = dict(type='motion_timeline', title='drum nesting', aspect='16:9', duration=12, blocks=layers,
              tracks=[dict(target='d1', keys=[dict(t=0, p=0), dict(t=3, p=1)])],
              scenes=[dict(layer='s1', t=0), dict(layer='s2', t=4), dict(layer='s3', t=8)])
    n = _parse(wa._RENDERERS['motion_timeline'](tl))
    assert not n.unbalanced, n.unbalanced
    for sid in ('s2', 's3', 't2', 't3'):
        assert sid in n.parents, sid
        assert 's1' not in n.parents[sid] and 'd1' not in n.parents[sid], (sid, n.parents[sid])
