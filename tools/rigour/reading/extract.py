"""Reading (domain side): source HTML -> candidate slots, each with the sentence it came from, the rule that made
it, and its provenance. Rules come from reading/rules.yaml; nothing is inferred beyond them."""
import html
import os
import re
import sys

import yaml


RULES = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.yaml'), encoding='utf-8'))
COMPILED = [dict(r, rx=re.compile(r['pattern'])) for r in RULES['relations']]
# A sentence that only says what to try when something else fails ("If that does not work, ...") describes a
# fallback, not the design: its slots are rebutted, never drawn. Declared in rules.yaml.
FALL = re.compile('|'.join(RULES['fallback']), re.I)


def text_of(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def sentences(src):
    """Sentences per block element, so a heading never fuses with the sentence under it."""
    out = []
    for block in re.split(r'</(?:h[1-6]|p|li)>', src):
        # a full stop ends a sentence unless it belongs to an abbreviation (e.g., i.e., etc.) or sits inside a word (example.com)
        out += [s.strip() for s in re.findall(r'(?:\b(?:e\.g|i\.e|etc|vs|cf)\.|\.(?=\w)|[^.])*\.', text_of(block)) if s.strip()]
    return out


def heading(src):
    m = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', src, re.S)
    return text_of(m.group(1)) if m else 'Architecture'


def as_written(name, text):
    m = re.search(re.escape(name), text, re.I)
    w = m.group(0) if m else name
    return w[0].upper() + w[1:]


def resolve(name, eligible):
    """A short mention ('the gateway') resolves to the ONE longer eligible name ending in it; otherwise it stays."""
    hits = sorted({k for k in eligible if k != name and k.endswith(' ' + name)})
    return (hits[0], 'derived') if len(hits) == 1 else (name, 'sourced')


DETERMINERS = re.compile(r'^(?:the|a|an|such|this|these|those|its|their|your)\s+')


def bare(name):
    """A component name without leading determiners: 'such programs' and 'the resolver' name programs and resolver."""
    name = name.strip()
    while DETERMINERS.match(name):
        name = DETERMINERS.sub('', name, count=1)
    return name


def extract(src):
    text, slots = text_of(src), []
    for s in sentences(src):
        low = s.lower()
        for rule in COMPILED:
            for m in rule['rx'].finditer(low):
                a = bare(m.groupdict().get('a') or rule.get('implied_subject') or '')
                b = bare(m.group('b'))
                slots.append(dict(id=f's{len(slots) + 1}', rule=rule['id'], role=rule['role'], a=a, b=b, label=rule['label'],
                                  warrant=rule['warrant'], quote=s, fallback=bool(FALL.match(s)),
                                  implied=not m.groupdict().get('a')))
    eligible = [n for sl in slots if not sl['fallback'] for n in (sl['a'], sl['b'])]   # never alias to fallback-only names
    for sl in slots:
        sl['a'], pa = resolve(sl['a'], eligible)
        sl['b'], pb = resolve(sl['b'], eligible)
        # an implied subject is a reader's inference, not something the sentence states
        sl['provenance'] = 'inferred' if sl['implied'] else ('derived' if 'derived' in (pa, pb) else 'sourced')
    found = [w for w in RULES['lexicon'] if re.search(r'\b' + re.escape(w) + r'\b', text.lower())]
    mentioned = [w for w in found if not any(o != w and o.endswith(' ' + w) for o in found)]
    return dict(text=text, heading=heading(src), slots=slots, mentioned=mentioned)
