"""A BOM is a declared file (boms/<artifact>.yaml): what an artifact needs before it may be built. The gate turns it
into an argument record whose rebuttals are the BOM's clarity rules, every one evaluated, none skipped."""
import os
import yaml

from . import argument

BOMS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'boms')
REQUIRED = ('artifact', 'claim', 'warrant', 'slots', 'clarity', 'fallback')


def load(name, folder=BOMS):
    bom = yaml.safe_load(open(os.path.join(folder, name + '.yaml'), encoding='utf-8'))
    missing = [k for k in REQUIRED if k not in bom]
    if missing:
        raise ValueError(f'BOM {name}: missing {missing}')
    ids = [c['id'] for c in bom['clarity']]
    if len(ids) != len(set(ids)):
        raise ValueError(f'BOM {name}: duplicate clarity rule ids')
    return bom


def rebuttals(bom, facts):
    """One rebuttal per declared clarity rule. A rule the caller did not evaluate is an error, not a pass."""
    unevaluated = [c['id'] for c in bom['clarity'] if c['id'] not in facts]
    if unevaluated:
        raise ValueError(f"BOM {bom['artifact']}: clarity rules not evaluated: {unevaluated}")
    out = []
    for c in bom['clarity']:
        r = dict(id=c['id'], text=c['text'].format(value=c.get('value')), applies=bool(facts[c['id']]))
        if c.get('prefer'):
            r['prefer'] = c['prefer']
        out.append(r)
    return out


def gates(bom, grounds, facts, excerpt):
    """The artifact's argument records, its status, and the simpler artifact a fired rule prefers (if any).
    One record per clarity group (a rule's `group`, default "clarity") and per run of at most GROUNDS_MAX grounds,
    so no record carries more than the atom reads. Status is the worst of them."""
    rb = {r['id']: r for r in rebuttals(bom, facts)}
    groups = {}
    for c in bom['clarity']:
        groups.setdefault(c.get('group', 'clarity'), []).append(rb[c['id']])
    chunks = [grounds[i:i + argument.GROUNDS_MAX] for i in range(0, len(grounds), argument.GROUNDS_MAX)] or [[]]
    recs = []
    for g, rs in groups.items():
        for k, chunk in enumerate(chunks, 1):
            label = ([g] if len(groups) > 1 else []) + ([f'grounds {k} of {len(chunks)}'] if len(chunks) > 1 else [])
            recs.append(argument.record(f"Artifact: {bom['artifact']} (BOM gate{': ' + ', '.join(label) if label else ''})", bom['claim'],
                                        chunk, bom['warrant'], rebuttals=[dict(text=r['text'], applies=r['applies']) for r in rs],
                                        qualifier=bom.get('qualifier'), excerpt=excerpt))
    order = ['REBUTTED', 'UNGROUNDED', 'UNVERIFIED GROUNDS', 'STANDS']
    status = min((argument.status(r) for r in recs), key=order.index)
    prefer = next((r['prefer'] for r in rb.values() if r['applies'] and r.get('prefer')), None)
    return recs, status, prefer


gate = gates   # one name for callers that predate grouping; it always returns a list of records
