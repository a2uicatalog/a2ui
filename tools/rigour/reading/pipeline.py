"""Article -> slots -> one argument per slot -> grounded graph -> the simplest artifact whose BOM gate stands ->
provenance check on what was drawn -> a report with the gap list for a reviewer. Nothing is filled in."""
import re

from rigour import argument, bom as boms, builders, provenance
from . import extract as ex

COLOURS = dict(background='#f3f4f6', fill='#ffffff', color='#111827', mute='#4b5563', accent='#4f46e5', accent2='#0e7490')


def slot_record(sl, text):
    return argument.record(f"Slot {sl['id']}: {sl['rule']}", f"{sl['a']} → {sl['b']} ({sl['role']})",
                           [dict(quote=sl['quote'], text='the sentence that states it')], sl['warrant'],
                           rebuttals=[dict(text='the sentence is a fallback ("if that does not work"), not the topology', applies=sl['fallback']),
                                      dict(text='the sentence never says who does it; the subject was inferred, which needs a reviewer', applies=sl['implied'])],
                           qualifier=sl['provenance'], excerpt=text)


def graph_of(art, standing):
    path = [s for s in standing if s['role'] == 'path']
    deps = [s for s in standing if s['role'] == 'dependency']
    nxt = {s['a']: s for s in path}
    starts = [s['a'] for s in path if s['a'] not in {t['b'] for t in path}]
    chain, ordered = [], []
    if path and len(starts) == 1 and len(nxt) == len(path):          # one unbroken chain, no branches
        cur = starts[0]; chain.append(cur)
        while cur in nxt:
            ordered.append(nxt[cur]); cur = nxt[cur]['b']; chain.append(cur)
    names = {n: ex.as_written(n, art['text']) for s in standing for n in (s['a'], s['b'])}
    kinds = {n: next((k for w, k in ex.RULES['kinds'].items() if n.endswith(w)), 'server') for n in names}
    zones = []
    for z in ex.RULES['zones']:
        for s in ordered:
            if s['rule'] == z['from_relation'] and re.search(z['requires'].format(a=re.escape(s['a'])), s['quote'], re.I):
                zones.append(dict(id=z['id'], label=z['label'], members=[s['a'], s['b']], grounds=[s['id']]))
    messages = [dict(edge=i, text='your traffic', grounds=[s['id']]) for i, s in enumerate(ordered) if 'your traffic' in s['quote'].lower()]
    return dict(chain=chain, path=ordered, deps=[d for d in deps if d['a'] in chain], loose_deps=[d for d in deps if d['a'] not in chain],
                zones=zones, messages=messages, names=names, kinds=kinds, title=art['heading'])


def systems_of(names):
    """Named components that are systems, not devices (devices alone are not an architecture)."""
    kind = lambda n: next((k for w, k in ex.RULES['kinds'].items() if n.endswith(w)), 'server')
    return [n for n in names if kind(n) not in ex.RULES['device_kinds']]


def _v(name, singular, plural):
    """Verb agreement for a component name: 'the proxy does', 'the root servers do'."""
    return plural if name.split()[-1].endswith('s') else singular


def gaps_of(art, g, standing):
    placed = set(g['chain']) | {d['b'] for d in g['deps']}
    fallback_only = {s['b'] for s in art['slots'] if s['fallback']}
    out = []
    standing_path = [s for s in standing if s['role'] == 'path']
    if not standing_path:
        if len(systems_of(art['mentioned'])) >= ex.RULES['fallback_min_systems']:
            out.append((f"the article names {len(art['mentioned'])} components ({', '.join(art['mentioned'])}) but never says how they connect",
                        f"How do the {', '.join(art['mentioned'])} connect to each other?"))
        return out                     # no architecture claimed: placement gaps would be noise
    if not g['chain']:
        out.append(('the article\u2019s connections do not form one unbroken path: '
                    + '; '.join(f"{s['a']} \u2192 {s['b']}" for s in standing_path),
                    'In what order do these connections run, and do they form one path?'))
    explained = {n for d in g['loose_deps'] for n in (d['a'], d['b'])} | {s['b'] for s in art['slots'] if s['implied']}
    for s in art['slots']:
        if s['implied'] and not s['fallback']:
            out.append((f"the article mentions a query to the {s['b']} but never says what sends it",
                        f"What sends the query to the {s['b']}?"))
    for d in g['loose_deps']:
        out.append((f"the article links the {d['a']} to the {d['b']} ({d['label']}), but never connects the {d['a']} to the rest of the path",
                    f"How {_v(d['a'], 'does', 'do')} the {d['a']} connect to the rest of the design?"))
    for w in art['mentioned']:
        if w in fallback_only or w in explained or any(w == p or p.endswith(' ' + w) or w.endswith(' ' + p) for p in placed):
            continue
        out.append((f'the article names the {w} but never says where it sits',
                    f"Where {_v(w, 'does', 'do')} the {w} sit, and what {_v(w, 'does', 'do')} {_v(w, 'it', 'they')} connect to?"))
    for c in ex.RULES['crossings']:
        for s in g['path']:
            if c['phrase'] in s['quote'].lower() and not any(s['b'] in z['members'] for z in g['zones']):
                out.append((f"the article says the {s['a']} reaches the {s['b']} {c['phrase']}, but never says which side of that "
                            f"boundary the {s['b']} sits on", f"Which side of {c['boundary']} {_v(s['b'], 'does', 'do')} the {s['b']} sit on?"))
    return out


def run(src):
    art = ex.extract(src)
    recs = [slot_record(s, art['text']) for s in art['slots']]
    slot_status = {s['id']: argument.status(r) for s, r in zip(art['slots'], recs)}
    standing = [s for s in art['slots'] if slot_status[s['id']] == 'STANDS']
    g = graph_of(art, standing)
    arch_bom, stack_bom = boms.load('motion_arch'), boms.load('layer_stack')
    words = max((len(e['label'].split()) for e in g['path'] + g['deps']), default=0)
    arch_facts = dict(min_nodes=len(g['chain']) < 2,
                      max_nodes=len(g['chain']) + len(g['deps']) > next(c['value'] for c in arch_bom['clarity'] if c['id'] == 'max_nodes'),
                      one_piece=len(g['chain']) >= 2 and bool(g['loose_deps']),
                      label_words=words > next(c['value'] for c in arch_bom['clarity'] if c['id'] == 'label_words'),
                      lone_chain=len(g['chain']) >= 2 and not g['deps'] and not g['zones'],
                      fits_row=bool(g['chain']) and builders.arch_width(g) > next(c['value'] for c in arch_bom['clarity'] if c['id'] == 'fits_row'))
    grounds = [dict(quote=s['quote'], text=f"standing {s['role']} slot {s['id']}") for s in g['path'] + g['deps']]
    arch_rec, arch_status, prefer = boms.gate(arch_bom, grounds, arch_facts, art['text'])
    stack_rec, stack_status, _ = boms.gate(stack_bom, [dict(quote=s['quote'], text=f"standing path slot {s['id']}") for s in g['path']],
                                           dict(min_chain=len(g['chain']) < 2), art['text'])
    if arch_status == 'STANDS':
        block, elements, built, gate_rec = *builders.motion_arch(g, COLOURS), 'motion_arch', arch_rec
    elif stack_status == 'STANDS':
        block, elements = builders.layer_stack(g)
        built, gate_rec = 'layer_stack' + (' (simplest form)' if prefer == 'layer_stack' else ''), arch_rec
    elif len(systems_of(art['mentioned'])) >= ex.RULES['fallback_min_systems']:
        block, elements = builders.bullet_list(art['mentioned'], {w: ex.as_written(w, art['text']) for w in art['mentioned']})
        built, gate_rec = 'bullet_list (names only)', stack_rec
    else:
        block, elements, gate_rec = None, [], stack_rec
        built = 'nothing to draw: the current rules found no architecture in this article'
    return dict(article=art, slot_records=recs, slot_status=slot_status, graph=g, gate=gate_rec[0], gates_records=gate_rec,
                gates={'motion_arch': arch_status, 'layer_stack': stack_status}, block=block, elements=elements,
                built=built, provenance=provenance.check(elements, slot_status),
                gaps=[x[0] for x in gaps_of(art, g, standing)], questions=[x[1] for x in gaps_of(art, g, standing)],
                standing=standing)
