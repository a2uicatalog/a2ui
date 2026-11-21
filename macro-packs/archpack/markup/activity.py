"""The steps table's `Activity` column: one plain-English sentence per edge (port of mermaid_arch/activity.mjs).

A fixed template, no model, no randomness: the same graph gives the same sentences.
"""
from __future__ import annotations

import re

from ._js import rx, trim

LEAD_VERBS = {
    'looks up': 'in', 'types': 'into', 'asks': '', 'answers': '', 'creates': 'in', 'discovers': 'from', 'reads': 'from', 'writes': 'to', 'mounts': 'in',
    'dispatches': 'to', 'streams': 'to', 'sends': 'to', 'posts': 'to', 'calls': '', 'fetches': 'from', 'renders': 'in', 'returns': 'to', 'lists': 'from',
    'saves': 'in', 'stores': 'in', 'loads': 'from', 'requests': 'from', 'checks': '', 'validates': '', 'notifies': '', 'hands': 'to', 'forwards': 'to',
    'publishes': 'to', 'subscribes': 'to', 'queries': '', 'updates': '', 'deletes': 'from', 'opens': '', 'pushes': 'to', 'pulls': 'from', 'resolves': '',
    'verifies': '', 'signs': '', 'receives': 'from', 'reports': 'to', 'triggers': '', 'invokes': '', 'runs': 'on', 'executes': '',
}

_P1 = rx(r'://')
_P2 = rx(r'\s*:\s*')
_P3 = rx(r'\s*(?:->|-->|=>|→)\s*')
_P4 = rx(r'\s+')
_DANG = rx(r'[\s,;:&\-–—]+$')
_UP = rx(r'[A-Z]')
_ACR = rx(r'^[A-Z0-9]{2,}')
_LOWER_PLAIN = rx(r'^[a-z][a-z ]*$')
_ART = rx(r'^(a|an|the)\b')
_AND_OR = rx(r'^(and|or)\b', re.I)
_LOWER_PLAIN2 = rx(r'^[a-z][a-z ,+-]*$')
_ART2 = rx(r'^(a|an|the|\d)\b', re.I)


def _plain(t):
    t = _P1.sub(' ', str(t))
    t = _P2.sub(', ', t)
    t = _P3.sub(' to ', t)
    return trim(_P4.sub(' ', t))


def _keep(w):
    return bool(_UP.search(w[1:])) or bool(_ACR.match(w))


def _dangling(t):
    return _DANG.sub('', str(t))


def in_sentence(label):
    return ' '.join(w if _keep(w) else w.lower() for w in _plain(_dangling(label)).split(' '))


def activity(from_label, to_label, label, style=None, both=None, reply=None):
    F = in_sentence(from_label)
    T = 'the ' + in_sentence(to_label)
    L = in_sentence(label or '')
    if not L:
        s = '%s and %s talk to each other' % (F, T) if both else '%s calls %s' % (F, T)
    else:
        verb = next((v for v in LEAD_VERBS if L == v or L.startswith(v + ' ')), None)
        if verb is not None:
            rest = trim(L[len(verb):])
            prep = LEAD_VERBS[verb]
            if not rest:
                s = '%s %s %s' % (F, verb, T)
            elif _AND_OR.match(rest) or both:
                s = '%s %s %s %s' % (F, verb, rest, T)
            else:
                s = '%s %s %s %s %s' % (F, verb, rest, prep or 'with', T)
        elif both:
            s = '%s and %s exchange %s%s' % (F, T, 'the ' if (_LOWER_PLAIN.match(L) and not _ART.match(L)) else '', L)
        else:
            article = 'the ' if (_LOWER_PLAIN2.match(L) and not _ART2.match(L)) else ''
            s = '%s %s %s%s to %s' % (F, 'returns' if (reply and style != 'async' and style != 'optional') else 'sends', article, L, T)
    if style == 'async':
        s += ' (async)'
    elif style == 'optional':
        s += ' (optional)'
    return s[0].upper() + s[1:]
