#!/usr/bin/env python3
"""payload_to_deck: an A2UI payload ({"blocks":[...]}) -> deck scenes -> PPTX. One recipe per atom; atoms without a recipe are reported, never guessed.

  python payload_to_deck.py payload.json -o out.pptx [--target google-slides] [--report r.json] [--preview dir]

RECIPES is the single list of atoms that work on the `slides` and `pptx` surfaces: atoms/schema.yaml carries `slides`/`pptx` in works_on for exactly
these atoms (tests/test_payload_to_deck.py enforces both directions). A recipe turns one block into scene dicts for deck_build (or a *pending heading*
that the next block picks up). Long lists and tables are split over continuation slides rather than truncated."""
import sys, json, re, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import deck_build as db

from recipe_helpers import s, chunks, sentences, http, item_text, list_scenes, r_list, stat, cards_scenes

def r_pipeline(b, h): return [dict(type='bullets', f=dict(heading=h or 'Pipeline', items=[f'{i + 1}. {s(x)}' for i, x in enumerate(b.get('steps') or [])]))]
def r_title(b, h): return [dict(type='title', f=dict(headline=s(b.get('title')), eyebrow=s(b.get('badge') or b.get('tag') or b.get('series_label')), sub=s(b.get('subtitle') or b.get('subtext'))))]
def r_closing(b, h): return [dict(type='title', f=dict(headline=s(b.get('text')), sub=', '.join(s(t) for t in b.get('tags') or [])))]
def r_quote(b, h):
    who = s(b.get('attribution') or b.get('author_name') or b.get('expert_name')); role = s(b.get('author_title') or b.get('expert_title'))
    org = s(b.get('expert_organization')); role = ', '.join(x for x in (role, org) if x)
    return [dict(type='quote', f=dict(quote=s(b.get('text') or b.get('quote') or b.get('review_text')), name=who, role=role))]
def r_cta(b, h):
    p, sec = b.get('primary_cta') or {}, b.get('secondary_cta') or {}
    f = dict(headline=s(b.get('heading')), b1=s(p.get('label')), l1=http(p.get('url')))
    if sec.get('label'): f.update(b2=s(sec['label']), l2=http(sec.get('url')))
    return [dict(type='cta', f=f)]
def r_stats(b, h):
    if b['type'] == 'pull_stat': rows = [stat(s(b.get('value')) + (s(b.get('unit')) if s(b.get('unit')) in ('%', 'x') else ''), b.get('label'))]
    elif b['type'] == 'social_proof_banner': rows = [stat(b.get('metric_value'), b.get('metric_label'))]
    elif b['type'] == 'metric_delta': rows = [stat(b.get('current_value'), b.get('label'))]
    else: rows = [stat(s(m.get('prefix')) + s(m.get('value')) + s(m.get('suffix')), m.get('label'), m.get('sub')) for m in (b.get('metrics') or b.get('stats') or b.get('items') or [])]
    return [dict(type='stats', f=dict(kicker=h or '', stats=pg)) for pg in chunks(rows, 4)]
def r_table(b, h):
    hd = [s(x) for x in b.get('headers') or []]; rows = [[s(c) for c in r] for r in b.get('rows') or []]
    pages = chunks(rows, 8); title = s(b.get('caption')) or h or 'Table'
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=hd, rows=pg)) for n, pg in enumerate(pages)]
def r_kv(b, h):
    rows = [[s(i.get('key')), s(i.get('description'))] for i in b.get('items') or []]
    return [dict(type='table', f=dict(heading=s(b.get('title')) or h or 'Reference', headers=['Name', 'Description'], rows=pg)) for pg in chunks(rows, 8)]
CALLOUT_LABEL = {'info': 'Note', 'warning': 'Warning', 'danger': 'Warning', 'error': 'Warning', 'success': 'Good to know', 'tip': 'Tip'}
def r_callout(b, h):
    text = s(b.get('text') or b.get('description') or b.get('body')); title = s(b.get('title')) or CALLOUT_LABEL.get(s(b.get('kind') or b.get('variant')).lower(), 'Note')
    cards = cards_scenes(h or 'Note', [(title, text)]) if text else None
    return cards or [dict(type='bullets', f=dict(heading=s(b.get('title')) or h or 'Note', items=sentences(text)))]
def r_body(b, h): return [dict(type='bullets', f=dict(heading=h or 'Overview', items=sentences(b.get('text'))[:6]))]
def r_heading(b, h): return 'PENDING'

RECIPES = {
    'page_header': r_title, 'gradient_hero': r_title, 'closing': r_closing,
    'heading': r_heading, 'subheading': r_heading, 'body': r_body,
    'bullet_list': r_list('List'), 'numbered_list': r_list('Steps'), 'steps': r_list('Steps'), 'icon_list': r_list('List'), 'action_items': r_list('Action items'), 'pipeline': r_pipeline,
    'quote': r_quote, 'blockquote_with_avatar': r_quote, 'testimonial_card': r_quote, 'expert_endorsement': r_quote, 'review_callout': r_quote,
    'pull_stat': r_stats, 'metric_row': r_stats, 'icon_stat_row': r_stats, 'social_proof_banner': r_stats, 'metric_delta': r_stats,
    'table': r_table, 'key_value': r_kv,
    'callout': r_callout, 'text_callout': r_callout, 'highlight_box': r_callout,
    'cta_section': r_cta,
}
from recipes_more import NEW_RECIPES
RECIPES.update(NEW_RECIPES)
IGNORED = {'divider', 'section_break'}                    # carry no content a slide needs

def _groups(seq, weight, count_cap, budget):
    """Split a sequence into runs of at most `count_cap` entries whose summed weight stays within `budget` (an estimate of what one slide holds)."""
    out, cur, w = [], [], 0
    for x in seq:
        wx = weight(x)
        if cur and (len(cur) >= count_cap or w + wx > budget): out.append(cur); cur, w = [], 0
        cur.append(x); w += wx
    return out + ([cur] if cur else [])

def paginate(scenes):
    """A recipe may return more than one slide can hold. Split bullets (6 items, about 520 characters) and tables (8 rows, about 10 wrapped lines) into continuation slides; never truncate."""
    import math
    out = []
    for sc in scenes:
        if sc['type'] == 'bullets': key, groups = 'items', (lambda seq: _groups(seq, lambda t: math.ceil(max(1, len(t)) / 75) * 0.333 + 0.44, 6, 4.4))
        elif sc['type'] == 'table': key, groups = 'rows', (lambda seq, nc=len(sc['f']['headers']): _groups(seq, lambda r: max(1, math.ceil(max(len(c) for c in r) / (80 / nc))) * 0.333 + 0.2, 8, 3.9))
        else: out.append(sc); continue
        seq = sc['f'].get(key) or []; pages = groups(seq) if seq else []
        if len(pages) <= 1: out.append(sc); continue
        base = re.sub(r' \(\d+/\d+\)$', '', sc['f']['heading'])
        for n, pg in enumerate(pages): out.append(dict(sc, f=dict(sc['f'], **{key: pg}, heading=f'{base} ({n + 1}/{len(pages)})')))
    return out

def merge_stats(scenes):
    """Consecutive stats scenes become one slide of up to four figures (a kicker given to the first is kept)."""
    out = []
    for sc in scenes:
        prev = out[-1] if out else None
        if sc['type'] == 'stats' and prev and prev['type'] == 'stats' and len(prev['f']['stats']) + len(sc['f']['stats']) <= 4:
            prev['f']['stats'] = prev['f']['stats'] + sc['f']['stats']; prev['f']['kicker'] = prev['f']['kicker'] or sc['f']['kicker']
            prev['src'] = dict(prev['src'], also=[*prev['src'].get('also', []), sc['src']['block']])
        else: out.append(sc)
    return out

def picture_scene(b, heading, pics_dir, idx):
    """No native recipe: draw the atom with the catalogue's own renderer and put the picture on a media slide (not editable; alt text from the atom's own text)."""
    import atom_image
    Path(pics_dir).mkdir(parents=True, exist_ok=True); png = Path(pics_dir) / f"{idx:03d}-{b['type']}.png"
    markup, _ = atom_image.render(b, str(png))
    alt = atom_image.alt_text(markup) or f"{b['type'].replace('_', ' ')} atom"
    title = (heading or b['type'].replace('_', ' ').capitalize())[:70]
    return [dict(type='media', f=dict(heading=title, media=str(png), alt=f"{b['type'].replace('_', ' ')}: {alt}"[:250]))]

def convert(payload, pictures=None):
    """-> (scenes, report). The report lists every block: converted (to how many slides), ignored, or unsupported (no recipe)."""
    blocks = payload.get('blocks') if isinstance(payload, dict) else payload
    scenes, rep, heading = [], dict(converted=[], ignored=[], unsupported=[]), None
    for i, b in enumerate(blocks or []):
        t = b.get('type') if isinstance(b, dict) else None
        if t in IGNORED: rep['ignored'].append(dict(block=i, type=t)); continue
        if t not in RECIPES:
            if not pictures or not t: rep['unsupported'].append(dict(block=i, type=t, reason='no slide recipe for this atom')); continue
            try: out = picture_scene(b, heading, pictures, i); mode = 'picture'
            except (SystemExit, Exception) as e: rep['unsupported'].append(dict(block=i, type=t, reason=f'picture fallback failed: {e}')); continue
            heading = None
            for sc in out: sc['src'] = dict(block=i, type=t)
            scenes += out; rep['converted'].append(dict(block=i, type=t, slides=len(out), mode=mode)); continue
        try: out = RECIPES[t](b, heading)
        except Exception as e: rep['unsupported'].append(dict(block=i, type=t, reason=f'recipe failed: {e}')); continue
        if out == 'PENDING': heading = s(b.get('text')); continue
        if t not in ('page_header', 'gradient_hero', 'closing'): heading = None
        out = paginate(out)
        for sc in out: sc['src'] = dict(block=i, type=t)
        scenes += out; rep['converted'].append(dict(block=i, type=t, slides=len(out)))
    scenes = merge_stats(scenes)
    if heading: scenes.append(dict(type='title', f=dict(headline=heading), src=dict(block=len(blocks or []), type='heading'))); rep['converted'].append(dict(block='trailing', type='heading', slides=1))
    return scenes, rep

def run(payload, out=None, target=None, preview_dir=None, title='', pictures=None):
    scenes, rep = convert(payload, pictures)
    deck = json.dumps(dict(title=title or (payload.get('title') if isinstance(payload, dict) else '') or 'Deck', target=target, scenes=[{k: v for k, v in sc.items() if k != 'src'} for sc in scenes]))
    r = db.run(deck, out, target, False, preview_dir)
    for e in r['errors']:                                                # map a deck error back to the block that caused it
        if e.get('slide'): e['block'] = scenes[e['slide'] - 1]['src']
    r['conversion'] = rep; r['unsupported'] = rep['unsupported']
    return r

def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument('payload'); ap.add_argument('-o', '--out'); ap.add_argument('--target'); ap.add_argument('--report'); ap.add_argument('--preview'); ap.add_argument('--pictures', metavar='DIR', help='draw atoms that have no native recipe as pictures into DIR (needs chromium)')
    a = ap.parse_args(argv); r = run(json.loads(Path(a.payload).read_text()), a.out, a.target, a.preview, '', a.pictures)
    if a.report: Path(a.report).write_text(json.dumps(r, indent=1))
    for e in r['errors']: print('ERROR  ', e['message'], e.get('block', ''))
    for u in r['unsupported']: print('skipped', f"block {u['block']} ({u['type']}): {u['reason']}")
    print(('ok' if r['ok'] else 'FAILED'), f"- {r.get('slides', 0)} slide(s) from {len(r['conversion']['converted'])} block(s), {len(r['unsupported'])} unsupported")
    return 0 if r['ok'] else 1
if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
