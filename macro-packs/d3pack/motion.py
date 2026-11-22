"""verify_motion (19 Nov 2026): the stricter policy for an entrance animation, a SUBSET of verify_rich, from the Opus judgement of the same day (option E).
Admitted on top of everything verify_rich admits, nothing more (plus ONE opt-in that verify_rich itself does not allow: a fill animation between two #rrggbb colours on a path, rect, circle or polygon that ENDS ON THE ELEMENT'S OWN FILL, for a status colour change): only opacity, rotate and translate animations (rich already limits to these), every animation plays ONCE (repeatCount 1), ends within 1.5 s (begin + dur), at most 8 animations, and every animation ENDS ON THE IDENTITY
(opacity 1, rotate 0, translate 0 0), so the picture at rest, with the animations stripped, is exactly the picture at the end of the motion. Motion and filters never meet: no filter element and no filter attribute anywhere when anything animates (a filtered picture is redrawn at about 380 ms a frame while it animates).
Angles and offsets are bounded (|angle| <= 90, |offset| <= 60 canvas px), which also bounds the 'unbounded rotate' finding for animated elements. Reduced motion cannot be honoured inside an Image (measured), so the CALLER decides: a factory draws motion only when asked (motion=True), and a tick message never carries one.
Returns the svg or raises SvgPolicyError."""
import re
import xml.etree.ElementTree as ET
from . import common as C
from .rich import verify_rich, _seconds, _begins
MAX_MOTION_SECONDS, MAX_MOTION_ANIMATIONS, MAX_ANGLE, MAX_OFFSET = 1.5, 8, 90.0, 60.0
LONG_MOTION_SECONDS = 15.0   # the ceiling for the explicit long opt-in (verify_motion(svg, max_seconds=...)); nothing is longer
def verify_motion(svg, max_seconds=None):
    if max_seconds is not None and not (0 < max_seconds <= LONG_MOTION_SECONDS): raise C.SvgPolicyError(f'max_seconds must be above 0 and at most {LONG_MOTION_SECONDS:g}')
    _lim = MAX_MOTION_SECONDS if max_seconds is None else max_seconds
    verify_rich(svg, allow_fill_animation=True, max_seconds=max_seconds if max_seconds is None else max(max_seconds, 0.001)); root = ET.fromstring(svg); parent = {c: p for p in root.iter() for c in p}; tag = lambda e: e.tag.rpartition('}')[2]; anims = [e for e in root.iter() if tag(e) in ('animate', 'animateTransform')]
    if not anims: return svg
    if len(anims) > MAX_MOTION_ANIMATIONS: raise C.SvgPolicyError(f'more than {MAX_MOTION_ANIMATIONS} animations')
    if any(tag(e) == 'filter' or e.get('filter') is not None for e in root.iter()): raise C.SvgPolicyError('a picture that animates must have no filter (a filtered picture is redrawn at about 380 ms a frame while it animates)')
    for e in anims:
        a = e.attrib
        if a['repeatCount'] != '1': raise C.SvgPolicyError('a motion animation plays once (repeatCount 1)')
        if _begins(a.get('begin', '0s'), _seconds(a['dur'], 'dur'), max_seconds) + _seconds(a['dur'], 'dur') > _lim + 1e-9: raise C.SvgPolicyError(f'a motion animation must end within {_lim:g} s')
        if tag(e) == 'animate' and a['attributeName'] == 'fill':   # a status colour change: it ENDS ON THE ELEMENT'S OWN FILL, so the picture at rest is the picture at the end
            if (parent[e].get('fill') or '').lower() != a['to'].lower(): raise C.SvgPolicyError("a fill animation must end on the element's own fill (the picture at rest is the picture at the end)")
        elif tag(e) == 'animate':
            if float(a['to']) != 1.0: raise C.SvgPolicyError('an opacity animation must end at 1 (the picture at rest is the picture at the end)')
        else:
            f, t = [float(x) for x in a['from'].split()], [float(x) for x in a['to'].split()]
            if a['type'] == 'translate':
                if any(x != 0.0 for x in t): raise C.SvgPolicyError('a translate animation must end at 0 0')
                if any(abs(x) > MAX_OFFSET for x in f): raise C.SvgPolicyError(f'a translate may start at most {MAX_OFFSET:g} px away')
            else:
                if t[0] != 0.0: raise C.SvgPolicyError('a rotate animation must end at angle 0')
                if abs(f[0]) > MAX_ANGLE: raise C.SvgPolicyError(f'a rotate may start at most {MAX_ANGLE:g} degrees away')
                if len(t) == 3 and len(f) == 3 and (f[1], f[2]) != (t[1], t[2]): raise C.SvgPolicyError('a rotate animation keeps its centre')
                if len(f) != len(t): raise C.SvgPolicyError('a rotate animation gives from and to the same number of values')
    return svg
