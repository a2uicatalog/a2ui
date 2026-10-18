"""High-level design (HLD) from an article: the artifact (diagram, components, flows, open questions) and, separately,
the evidence report. The artifact carries no argument machinery; everything in it is traceable in the report."""
import html as H
import re

from rigour import argument, bom as boms, builders, provenance
from renderers import web_article as atoms
from . import pipeline, extract as ex

KIND_LABEL = {'device': 'Device', 'app': 'Application', 'server': 'Server', 'tool': 'Service', 'store': 'Network / store',
              'model': 'Model', 'surface': 'Surface', 'user': 'User'}


def build(src, source_name=''):
    r = pipeline.run(src)
    g, art = r['graph'], r['article']
    rule = {x['id']: x for x in ex.RULES['relations']}
    edges, zones = [], []
    for s in r['standing']:
        if rule[s['rule']].get('hld') == 'placement':          # hosting is containment in an HLD, not a flow step
            m = re.search(r'\b(?:your|the) ' + re.escape(s['a']) + r'\b', s['quote'], re.I)
            label = (m.group(0) if m else s['a']); label = label[0].upper() + label[1:]
            zones.append(dict(id=s['id'], label=label, members=[s['b']], grounds=[s['id']]))
            continue
        edges.append(dict(id=s['id'], a=s['a'], b=s['b'], label=s['label'], role=s['role'], inverse=rule[s['rule']].get('inverse', '')))
    names = {n: ex.as_written(n, art['text']) for e in edges for n in (e['a'], e['b'])}
    kinds = {n: next((k for w, k in ex.RULES['kinds'].items() if n.endswith(w)), 'server') for n in names}
    hg = dict(names=names, kinds=kinds, title=art['heading'], zones=[z for z in zones if all(m in names for m in z['members'])])
    nodes = sorted(names)
    bom = boms.load('hld')
    v = {c['id']: c.get('value') for c in bom['clarity']}
    width = builders.hld(hg, edges)[4] if edges else 0
    facts = dict(min_nodes=len(nodes) < 2, max_nodes=len(nodes) > v['max_nodes'],
                 label_words=any(len(e['label'].split()) > v['label_words'] for e in edges), fits_row=width > v['fits_row'])
    grounds = [dict(quote=s['quote'], text=f"standing {s['role']} slot {s['id']}") for s in r['standing']]
    gate_rec, gate_status, _ = boms.gate(bom, grounds, facts, art['text'])
    block = steps = elements = None
    if gate_status == 'STANDS':
        block, elements, steps, pieces, _ = builders.hld(hg, edges, pipeline.COLOURS)
    findings = provenance.check(elements or [], r['slot_status'])
    return dict(r=r, gates=gate_rec, status=gate_status, block=block, elements=elements or [], steps=steps or {},
                edges=edges, names=names, kinds=kinds, zones=hg['zones'], provenance=findings, source=source_name)


def _components(h):
    rows = []
    for n in sorted(h['names'], key=lambda n: min([h['steps'].get(e['id'], 99) for e in h['edges'] if n in (e['a'], e['b'])])):
        out = [f"{e['label']} {h['names'][e['b']]}" for e in h['edges'] if e['a'] == n]
        inn = [f"{e['inverse']} {h['names'][e['a']]}" for e in h['edges'] if e['b'] == n]
        where = [f"runs on {z['label'][0].lower() + z['label'][1:]}" for z in h['zones'] if n in z['members']]
        rows.append([h['names'][n], KIND_LABEL.get(h['kinds'][n], h['kinds'][n]), '; '.join(where + out + inn)])
    return dict(type='table', headers=['Component', 'Type', 'Role in this design'], rows=rows,
                col_widths=['26%', '18%', '56%'])


def _flows(h):
    path = sorted([e for e in h['edges'] if e['id'] in h['steps']], key=lambda e: h['steps'][e['id']])
    other = [e for e in h['edges'] if e['id'] not in h['steps']]
    rows = [[str(h['steps'][e['id']]), h['names'][e['a']], h['names'][e['b']], e['label']] for e in path]
    rows += [['—', h['names'][e['a']], h['names'][e['b']], e['label'] + ' (not a request hop)'] for e in other]
    return dict(type='table', headers=['Step', 'From', 'To', 'Interaction'], rows=rows,
                col_widths=['10%', '28%', '28%', '34%'])


CSS = ('body{margin:0;background:#fff;color:#111827;font-family:system-ui,-apple-system,Segoe UI,sans-serif}'
       'main{max-width:960px;margin:0 auto;padding:28px 20px 56px}h1{font-size:1.5rem;margin:2px 0 4px}'
       '.eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#4f46e5}'
       '.src{color:#4b5563;font-size:.85rem;margin:0 0 18px}h2{font-size:1rem;margin:28px 0 8px}'
       '.diagram{background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:10px}'
       '.open{border-left:4px solid #b45309;background:#fffbeb;padding:10px 16px;color:#78350f}.open li{margin:4px 0}'
       'a{color:#4338ca}')


def artifact_page(h):
    r, h_ = h['r'], (lambda b: atoms._RENDERERS[b['type']](b))
    out = (f'<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
           f'<title>HLD: {H.escape(r["article"]["heading"])}</title><style>{CSS}</style><main>'
           f'<div class=eyebrow>High-level design</div><h1>{H.escape(r["article"]["heading"])}</h1>'
           f'<p class=src>Drawn only from what {H.escape(h["source"] or "the source")} states. '
           f'Every component and interaction is traceable in the <a href="report.html">evidence report</a>.</p>')
    if h['block']:
        out += '<h2>Architecture</h2><div class=diagram>' + h_(h['block']) + '</div>'
        out += '<h2>Components</h2>' + h_(_components(h)) + '<h2>Interactions</h2>' + h_(_flows(h))
    else:
        out += ('<h2>Architecture</h2><p>The source does not state enough components and interactions to draw a design '
                'without guessing. The open questions below say what is missing.</p>')
    if r['questions']:
        out += '<h2>Open questions</h2><div class=open><ul>' + ''.join(f'<li>{H.escape(q)}</li>' for q in r['questions']) + '</ul></div>'
    return out + '</main></html>'


def report_page(h):
    r, h_ = h['r'], (lambda b: atoms._RENDERERS[b['type']](b))
    out = (f'<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
           f'<title>Evidence: {H.escape(r["article"]["heading"])}</title><style>{CSS}</style><main>'
           f'<div class=eyebrow>Evidence report</div><h1>{H.escape(r["article"]["heading"])}</h1>'
           f'<p class=src>Companion to the <a href="artifact.html">high-level design</a>. Source: {H.escape(h["source"])}. '
           f'Provenance check: {"every drawn element rests on a standing slot" if not h["provenance"] else H.escape("; ".join(h["provenance"]))}.</p>'
           '<h2>Gate</h2>' + ''.join(h_(g) for g in h['gates']))
    if r['gaps']:
        out += '<h2>Gaps</h2><div class=open><ul>' + ''.join(f'<li>{H.escape(x)}</li>' for x in r['gaps']) + '</ul></div>'
    out += f'<h2>Slots ({len(r["slot_records"])})</h2>' + ''.join(h_(x) for x in r['slot_records'])
    return out + '</main></html>'
