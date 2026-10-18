"""Explainer film from a problem/fix document: problem, then each step or branch the source states, as many as it
states up to the BOM's ceiling. Every caption is a trimmed run of the source's own words (or a supplied caption that
passes the same coverage check); every trim is reported. The film page and its evidence report are separate."""
import html as H
import os
import re
import sys

import yaml

from rigour import argument, bom as boms, theme as _theme
from renderers import web_article as atoms
from . import extract as ex


RULES = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'film.yaml'), encoding='utf-8'))
ICONS = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons.yaml'), encoding='utf-8'))
STOP = set(RULES['stopwords'])
ESCALATION = [re.compile(p, re.I) for p in RULES['escalation']]

# Renderer limits (motion_text: 4 lines of 60, 160 in all; timeline: 12 scenes, 24 blocks, 40 tracks).
LINE_MAX, TEXT_MAX, LINES_MAX, SCENES_MAX, BLOCKS_MAX, TRACKS_MAX = 60, 160, 4, 12, 24, 40
# Per text role: (size px, characters per line at that size and width, lines allowed, characters allowed before a trim)
ROLE = dict(headline=(54, 30, 3, 84), detail=(26, 58, 2, 112), option=(20, 60, 1, 60))
WPS = 2.6            # the pace scenes are timed for; the read_time rule checks against the BOM's ceiling


# ---- reading the source ----------------------------------------------------------------------------------------

def _blocks(src):
    return [(m.group(1).lower(), m.group(2)) for m in re.finditer(r'<(h[1-6]|p|ul|ol|table)\b[^>]*>(.*?)</\1>', src, re.S | re.I)]


def _sents(text):
    return [s.strip() for s in re.findall(r'(?:\b(?:e\.g|i\.e|etc|vs|cf)\.|[.?!](?=\w)|[^.?!])+(?:[.?!]+|$)', text) if s.strip()]


def words(s):
    return re.findall(r"[a-z0-9]+(?:['’-][a-z0-9]+)*", s.lower())


def uncovered(caption, source):
    """Content words of the caption that the source sentence does not contain (empty means covered)."""
    have = set(words(source))
    return [w for w in words(caption) if w not in STOP and w not in have]


def _section(title):
    t = title.lower().strip().rstrip(':')
    return next((k for k, names in RULES['sections'].items() if t in names), None)


def trim(sentence, limit):
    """The longest run of the sentence's opening words, cut only at a declared point, that fits the limit.
    Returns (caption, [trimmed fragments])."""
    s, cut = sentence.strip(), []
    for m in re.finditer(r'\s*\(([^)]*)\)', s):
        cut.append('(' + m.group(1) + ')')
    colon = s.rstrip().endswith(':')                         # a lead-in ("If you need access sooner:") keeps its colon
    s = re.sub(r'\s*\([^)]*\)', '', s).rstrip(' .:;')
    if len(s) > limit:
        best = None
        for c in RULES['cuts']:                                # cuts are in priority order: the strongest boundary that fits wins
            for m in re.finditer(re.escape(c), s.lower()):
                head = s[:m.start()].rstrip(' ,;')
                if len(head) <= limit and len(head.split()) >= 3 and (best is None or len(head) > len(best)):
                    best = head
            if best:
                break
        if best:
            cut.append(s[len(best):].strip(' ,;-'))
            s = best
    s = s + ':' if colon and not cut else s
    return (s[0].upper() + s[1:]) if s else s, cut


def caption(sentence, role):
    text, cut = trim(sentence, ROLE[role][3])
    return dict(text=text, source=sentence, trimmed=cut)


def _detail(sents, first_cut):
    """The second sentence, or else the tail the headline's trim removed (so a trim moves words, not drops them)."""
    if len(sents) > 1:
        return caption(sents[1], 'detail')
    tail = next((c for c in first_cut if c and not c.startswith('(')), None)
    if tail:
        tail = re.sub(r'^(?:--\s*|and\s+)', '', tail)
        return caption(tail, 'detail')
    return None


COND = re.compile(r'^((?:if|when|unless)\b[^,]+),\s+(.+)$', re.I)


def _conditional(sentence):
    """'If X, do Y' -> headline Y with X beneath, so a trim can never keep the condition and drop the action."""
    m = COND.match(sentence)
    if not m:
        s = _sents(sentence); head = caption(s[0], 'headline')
        return dict(head, detail=_detail(s, head['trimmed']))
    act, cond = caption(m.group(2), 'headline'), caption(m.group(1), 'detail')
    return dict(act, detail=cond)


def read(src):
    """Article HTML -> film slots. Nothing is inferred: a slot exists only where the source's structure states it."""
    text = ex.text_of(src)
    title = ex.heading(src)
    sec, out = None, dict(title=title, problem=None, lead=None, decision=None, steps=[], escalation=None, unused=[])
    blocks = [b for b in _blocks(src) if not (b[0] == 'h1')]
    i, group = 0, None
    while i < len(blocks):
        tag, inner = blocks[i]
        plain = ex.text_of(inner)
        if tag.startswith('h'):
            sec = _section(plain); i += 1; continue
        if sec == 'problem' and tag == 'p' and not out['problem']:
            s = _sents(plain)
            head = caption(s[0], 'headline')
            out['problem'] = dict(head, detail=_detail(s, head['trimmed']))
        elif sec == 'resolution':
            strong = re.match(r'\s*<strong>(.*?)</strong>(.*)', inner, re.S | re.I)
            nxt = blocks[i + 1] if i + 1 < len(blocks) else (None, '')
            if tag == 'p' and strong and not ex.text_of(strong.group(2)):          # a bare bold line labels the list under it
                group = ex.text_of(strong.group(1)).rstrip(':')
            elif tag == 'p' and strong and re.match(r'if\b', ex.text_of(strong.group(1)), re.I):
                cond = re.sub(r'^if\s+', '', ex.text_of(strong.group(1)), flags=re.I).rstrip(':')
                s = _sents(ex.text_of(strong.group(2)))
                head = caption(s[0], 'headline')
                out['steps'].append(dict(kind='branch', condition=cond, cond_source=ex.text_of(strong.group(1)), **head,
                                         detail=_detail(s, head['trimmed'])))
            elif tag == 'p' and plain.endswith('?') and nxt[0] in ('ul', 'ol'):
                opts = [ex.text_of(li) for li in re.findall(r'<li[^>]*>(.*?)</li>', nxt[1], re.S)]
                out['decision'] = dict(caption(plain, 'headline'), options=[caption(o, 'option') for o in opts])
                i += 2; continue
            elif tag in ('ul', 'ol'):
                for li in re.findall(r'<li[^>]*>(.*?)</li>', inner, re.S):
                    s = _sents(ex.text_of(li))
                    head = caption(s[0], 'headline')
                    out['steps'].append(dict(kind='step', group=group, **head, detail=_detail(s, head['trimmed'])))
            elif tag == 'table':
                rows = [[ex.text_of(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)] for r in re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)]
                hdr = [h.lower() for h in rows[0]] if rows else []
                if 'symptom' in hdr and 'fix' in hdr:
                    si, fi = hdr.index('symptom'), hdr.index('fix')
                    ci = next((k for k, h in enumerate(hdr) if 'cause' in h), None)
                    for r in rows[1:]:
                        head = caption(r[ci] if ci is not None else r[fi], 'headline')
                        out['steps'].append(dict(kind='branch', condition=r[si], cond_source=r[si], **head,
                                                 detail=caption(r[fi], 'detail') if ci is not None else None))
                else:
                    out['unused'].append(plain)
            elif tag == 'p' and out['steps'] and any(p.search(plain) for p in ESCALATION):
                out['escalation'] = _conditional(_sents(plain)[0])
            elif tag == 'p' and not out['steps'] and not out['lead']:
                s = _sents(plain)
                out['lead'] = dict(caption(s[0], 'headline'), detail=caption(s[1], 'detail') if len(s) > 1 else None)
            else:
                out['unused'].append(plain)
        elif tag == 'p':
            out['unused'].append(plain)
        i += 1
    out['text'] = text
    return out


# ---- checks ------------------------------------------------------------------------------------------------------

def wrap(text, role):
    per, lines = ROLE[role][1], ['']
    for w in text.split():
        if lines[-1] and len(lines[-1]) + 1 + len(w) > per:
            lines.append(w)
        else:
            lines[-1] = (lines[-1] + ' ' + w).strip()
    return lines


def fits(text, role):
    lines = wrap(text, role)
    return len(lines) <= min(ROLE[role][2], LINES_MAX) and all(len(l) <= LINE_MAX for l in lines) and len(text) <= TEXT_MAX


def dangling(c):
    """A headline that keeps a sentence's condition but trimmed away what to do about it."""
    return bool(re.match(r'(?:if|when|unless)\b', c['text'], re.I)) and not c['text'].endswith(':') and bool(c['trimmed'])


def org_like(text):
    """Capitalised words past the first that are not declared technical terms and not inside quotes."""
    bare = re.sub(r'"[^"]*"|“[^”]*”', '', text)
    toks = re.findall(r"\b[A-Z][A-Za-z0-9-]*", bare)
    first = re.match(r'\s*([A-Za-z0-9-]+)', bare)
    return [t for t in toks if t not in RULES['allowed_caps'] and not (t.endswith('s') and t[:-1] in RULES['allowed_caps']) and not (first and t == first.group(1) and bare.strip().startswith(t))]


def apply_proposals(art, proposals):
    """Supplied captions (e.g. a model's rewrite) replace the trimmed ones only where they pass the coverage check."""
    rejected = []
    for sid, scene in _slots(art):
        p = (proposals or {}).get(sid)
        if not p:
            continue
        miss = uncovered(p, scene['source'])
        if miss:
            rejected.append(dict(slot=sid, proposed=p, missing=miss, source=scene['source']))
        else:
            scene.update(text=p, supplied=True)
    return rejected


def _slots(art):
    if art['problem']:
        yield 'problem', art['problem']
    if art['lead']:
        yield 'lead', art['lead']
    if art['decision']:
        yield 'decision', art['decision']
    for k, s in enumerate(art['steps'], 1):
        yield f'step{k}', s
    if art['escalation']:
        yield 'escalation', art['escalation']


def _term_at(text, term):
    m = re.search(r'(?<![a-z0-9-])' + re.escape(term) + r'(?![a-z0-9-])', text.lower())
    return m.start() if m else None


def icon_for(text):
    """(icon, word) for a caption: its leading verb if that verb is a declared action, else the earliest declared
    object word in it. None when nothing matches: no placeholder icon."""
    lead = (words(text) or [''])[0]
    for name, verbs in ICONS['actions'].items():
        if lead in verbs:
            return name, lead
    hits = [(at, name, t) for name, terms in ICONS['objects'].items() for t in terms if (at := _term_at(text, t)) is not None]
    # in a compound ("network printer") the last word names the thing; the words before it only describe it
    hits = [h for h in hits if not any(o[0] == h[0] + len(h[2]) + 1 for o in hits)]
    if not hits:
        return None
    _, name, t = min(hits)
    return name, t


# ---- the film ------------------------------------------------------------------------------------------------------

def _T(i, text, x, y, w, **k):
    return dict(type='motion_text', id=i, text=text, place=dict(x=x, y=y, w=w), **k)


def _P(i, a, b, ease='expo-out'):
    return dict(target=i, keys=[dict(t=a, p=0), dict(t=b, p=1, ease=ease)])


def scenes_of(art, bom):
    """The scene plan: (slot id, eyebrow chrome, headline caption, detail caption, options, step index)."""
    ch, plan = bom['chrome'], []
    plan.append(('title', ch['title_eyebrow'], dict(text=art['title'], source=art['title'], trimmed=[]), None, [], None))
    if art['problem']:
        plan.append(('problem', ch['problem'], art['problem'], art['problem']['detail'], [], None))
    if art['lead']:
        plan.append(('lead', ch['lead'], art['lead'], art['lead']['detail'], [], None))
    if art['decision']:
        plan.append(('decision', ch['decision'], art['decision'], None, art['decision']['options'], None))
    n = len(art['steps'])
    for k, s in enumerate(art['steps'], 1):
        eb = ch['branch'].format(condition=s['condition']) if s['kind'] == 'branch' else ch['step'].format(i=k, n=n)
        plan.append((f'step{k}', eb, s, s['detail'], [], (k, n)))
    if art['escalation']:
        plan.append(('escalation', ch['escalation'], art['escalation'], art['escalation']['detail'], [], None))
    plan.append(('end', ch['end'], dict(text=art['title'], source=art['title'], trimmed=[]), None, [], None))
    return plan


def timeline(plan, B, icons=None):
    layers, tracks, scenes, timing, t = [], [], [], [], 0.0
    for sid, eb, head, det, opts, prog in plan:
        on_screen = [head['text']] + ([det['text']] if det else []) + [o['text'] for o in opts]
        n_words = sum(len(x.split()) for x in on_screen)
        dur = round(max(4.0, 1.4 + n_words / WPS + 0.8), 1)
        big = sid in ('title', 'end')
        kids = [_T(sid + '_e', eb.upper() if len(eb) <= LINE_MAX else eb[:LINE_MAX], 7, 20 if not big else 30, 86, size=18, weight='bold', tracking=0.3,
                   color=B['accent2'], reveal='fade'),
                _T(sid + '_h', '\n'.join(wrap(head['text'], 'headline')), 7, 27 if not big else 37, 64, size=ROLE['headline'][0] + (10 if big else 0),
                   font='display', weight='black', reveal='mask', tracking=-0.02, line_height=1.05, color=B['ink'])]
        tr = [_P(sid + '_h', t + 0.3, t + 1.3)]
        if det:
            kids.append(_T(sid + '_d', '\n'.join(wrap(det['text'], 'detail')), 7, 62, 64, size=ROLE['detail'][0], weight='bold',
                           color=B['muted'], reveal='fade', mode='words', line_height=1.35))
            tr.append(_P(sid + '_d', t + 1.0, t + 2.0))
        for j, o in enumerate(opts):
            kids.append(dict(type='motion_pill', id=f'{sid}_o{j}', text=o['text'], size=ROLE['option'][0], accent=B['accent'],
                             place=dict(x=7, y=58 + j * 9, w=70)))
            tr.append(_P(f'{sid}_o{j}', t + 1.0 + 0.3 * j, t + 1.8 + 0.3 * j))
        if sid in (icons or {}):                       # drawn on in the scene's accent, from the theme
            name = icons[sid][0]
            kids.append(dict(type='motion_path', id=sid + '_i', d=ICONS['paths'][name], w=96, h=96, width=4, marker=False,
                             color=B['accent2'], label=name, place=dict(x=74, y=22 if not big else 30, w=18)))
            tr.append(_P(sid + '_i', t + 0.5, t + 2.1, 'quart-in-out'))
        if prog:
            k, n = prog
            kids.append(dict(type='motion_shape', id=sid + '_pt', shape='line', thickness=4, fill=B['panel'], place=dict(x=7, y=88, w=86, h=1)))
            kids.append(dict(type='motion_shape', id=sid + '_pf', shape='line', thickness=4, fill=B['accent'], place=dict(x=7, y=88, w=round(86 * k / n, 1), h=1)))
        layers.append(dict(type='motion_layer', id=sid, place=dict(z=2), blocks=kids))
        tracks += tr
        scenes.append(dict(layer=sid, t=round(t, 1)))
        timing.append(dict(slot=sid, t=round(t, 1), dur=dur, words=n_words, on_screen=on_screen, eyebrow=eb,
                           icon=(icons or {}).get(sid, (None,))[0]))
        t += dur
    total = round(t, 1)
    glow = dict(type='motion_shape', id='glow', shape='circle', fill=B['accent'], fill2=B['accent2'], angle=135, blur=170, draw='fade',
                place=dict(x=58, y=-20, w=60, h=107, z=0))
    tl = dict(type='motion_timeline', title=plan[0][2]['text'], aspect='16:9', duration=total, theme='dark', accent=B['accent'],
              background=B['bg'], backdrop='flat', poster=round(timing[1]['t'] + 2, 1) if len(timing) > 1 else 1, stitch='push', overlap=0.6,
              blocks=[glow] + layers, tracks=[dict(target='glow', keys=[dict(t=0, p=0), dict(t=total, p=.7, ease='ease-in-out')])] + tracks,
              scenes=scenes, morphs=[])
    return tl, timing


def _grounds(slot, label):
    """What a slot rests on, verbatim: a branch cites the condition it answers as well as its own sentence."""
    out = [dict(quote=slot['source'], text=label)]
    if slot.get('kind') == 'branch':
        out.insert(0, dict(quote=slot['cond_source'], text=label + ' (the condition it answers)'))
    return out


def build(src, source_name='', proposals=None, theme=None):
    bom = boms.load('explainer_film')
    v = {c['id']: c.get('value') for c in bom['clarity']}
    art = read(src)
    rejected = apply_proposals(art, proposals)
    plan = scenes_of(art, bom)
    B = _theme.load(theme)
    icons = {sid: (*hit, head['source']) for sid, _, head, _, _, _ in plan if (hit := icon_for(head['text']))}
    tl, timing = timeline(plan, B, icons)
    shown = [(sid, role, c) for sid, _, head, det, opts, _ in plan for role, c in
             [('headline', head)] + ([('detail', det)] if det else []) + [('option', o) for o in opts]]
    facts = dict(
        has_problem=not art['problem'], has_steps=not art['steps'],
        max_steps=len(art['steps']) > v['max_steps'],
        caption_fit=any(not fits(c['text'], role) for _, role, c in shown),
        read_time=any(x['words'] / max(x['dur'] - 1.0, 0.1) > v['read_time'] for x in timing),
        renderer_limits=len(tl['scenes']) > SCENES_MAX or len(tl['blocks']) > BLOCKS_MAX or len(tl['tracks']) > TRACKS_MAX,
        max_duration=tl['duration'] > v['max_duration'],
        caption_coverage=any(uncovered(c['text'], c['source']) for _, _, c in shown),
        dangling_condition=any(dangling(c) for _, role, c in shown if role == 'headline'),
        icon_grounded=any(_term_at(src, term) is None for _, term, src in icons.values()),
        org_names=any(org_like(c['text']) for sid, _, c in shown if sid not in ('title', 'end')))
    # the load-bearing slots are the grounds: the problem and each step up to the ceiling (past it, max_steps rebuts)
    grounds = ([dict(quote=art['problem']['source'], text='problem')] if art['problem'] else []) + \
              [g for k, s in enumerate(art['steps'][:v['max_steps']], 1) for g in _grounds(s, f'step {k}')]
    gate_recs, status, _ = boms.gates(bom, grounds, facts, art['text'])
    fired = [c['id'] for c in bom['clarity'] if facts[c['id']]]
    layout_only = {'max_steps', 'caption_fit', 'read_time', 'renderer_limits', 'max_duration'}
    built = 'explainer_film' if status == 'STANDS' else ('storyboard_list' if fired and set(fired) <= layout_only and art['steps'] else 'open_questions_only')
    questions = []
    if not art['problem']:
        questions.append('What problem does the article solve? It has no issue section the film can open on.')
    if not art['steps']:
        questions.append('What should the reader do? The article states no steps or fixes under a resolution heading.')
    if facts['max_steps']:
        questions.append(f"The article has {len(art['steps'])} steps, more than one film holds ({v['max_steps']}). Should it become two films, "
                         'or are some steps optional?')
    for sid, role, c in shown:
        for o in org_like(c['text']) if sid not in ('title', 'end') else []:
            questions.append(f'Is "{o}" ({sid}) an organisation or product name? Films must not name one.')
    records = [argument.record(f'Scene {sid}: {role}', c['text'], _grounds(c, 'the sentence it is cut from'),
                               "since the caption is the source sentence's own words, trimmed at a declared cut point",
                               rebuttals=[dict(text='the caption uses words the sentence does not: ' + ', '.join(uncovered(c['text'], c['source'])),
                                               applies=bool(uncovered(c['text'], c['source']))) if uncovered(c['text'], c['source'])
                                          else dict(text='the caption uses words the sentence does not', applies=False),
                                          dict(text='the caption names what looks like an organisation: ' + ', '.join(org_like(c['text'])),
                                               applies=bool(org_like(c['text'])))],
                               qualifier='supplied' if c.get('supplied') else ('derived' if c['trimmed'] else 'sourced'), excerpt=art['text'])
               for sid, role, c in shown if sid not in ('title', 'end')]
    return dict(art=art, bom=bom, plan=plan, timeline=tl, timing=timing, shown=shown, facts=facts, gates=gate_recs, status=status,
                built=built, questions=questions, records=records, rejected=rejected, source=source_name, theme=B, icons=icons)


# ---- pages -----------------------------------------------------------------------------------------------------------

CSS = ('body{margin:0;background:#fff;color:#111827;font-family:system-ui,-apple-system,Segoe UI,sans-serif}'
       'main{max-width:1100px;margin:0 auto;padding:28px 20px 56px}h1{font-size:1.5rem;margin:2px 0 4px}'
       '.eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#4f46e5}'
       '.src{color:#4b5563;font-size:.85rem;margin:0 0 18px}h2{font-size:1rem;margin:28px 0 8px}'
       '.open{border-left:4px solid #b45309;background:#fffbeb;padding:10px 16px;color:#78350f}.open li{margin:4px 0}'
       '.cut{color:#6b7280;font-size:.85rem}a{color:#4338ca}')


def _head(kind, title, extra=''):
    return (f'<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{kind}: {H.escape(title)}</title><style>{CSS}</style><main><div class=eyebrow>{kind}</div><h1>{H.escape(title)}</h1>{extra}')


def _r(b):
    return atoms._RENDERERS[b['type']](b)


def artifact_page(f):
    out = _head('Explainer film', f['art']['title'],
                f'<p class=src>Made only from what {H.escape(f["source"] or "the source")} states: every caption is its own words, trimmed. '
                f'What was trimmed or left out is in the <a href="report.html">evidence report</a>.</p>')
    if f['built'] == 'explainer_film':
        out += f'<h2>Film ({f["timeline"]["duration"]:.0f} s, {len(f["art"]["steps"])} steps)</h2><div style="color:#151a26">{_r(dict(f["timeline"]))}</div>'
        # three columns: narrow columns of unbreakable words overflow the table on small screens
        rows = [[str(k), f"{x['eyebrow']} · {x['dur']:.1f} s" + (f" · icon: {x['icon']}" if x['icon'] else ''), ' · '.join(x['on_screen'])]
                for k, x in enumerate(f['timing'], 1)]
        out += '<h2>Script</h2>' + _r(dict(type='table', headers=['#', 'Scene', 'On screen'], rows=rows, col_widths=['6%', '30%', '64%']))
    elif f['built'] == 'storyboard_list':
        out += ('<h2>Storyboard</h2><p>The steps do not fit one film under the template\'s rules, so here they are as a list. '
                'The open questions say why.</p>' + _r(dict(type='bullet_list', items=[dict(text=s['text']) for s in f['art']['steps']])))
    else:
        out += '<h2>Film</h2><p>The source does not state enough to make a film without guessing. The open questions below say what is missing.</p>'
    if f['questions']:
        out += '<h2>Open questions</h2><div class=open><ul>' + ''.join(f'<li>{H.escape(q)}</li>' for q in f['questions']) + '</ul></div>'
    return out + '</main></html>'


def report_page(f):
    out = _head('Evidence report', f['art']['title'],
                f'<p class=src>Companion to the <a href="artifact.html">explainer film</a>. Source: {H.escape(f["source"])}. '
                f'Built: {f["built"].replace("_", " ")}.</p><h2>Gate</h2>' + ''.join(_r(g) for g in f['gates']))
    # scene names that wrap (the eyebrow), three columns: bare slot ids are unbreakable and overflow on small screens
    name = {x['slot']: x['eyebrow'] for x in f['timing']}
    below = {id(head): det for _, _, head, det, _, _ in f['plan'] if det}
    trims = [(name[sid], c['text'], t + (' (moved to the line below)' if id(c) in below and not uncovered(t, below[id(c)]['text']) else ' (left out)'))
             for sid, _, c in f['shown'] for t in c['trimmed'] if t]
    if trims:
        out += ('<h2>Trimmed from captions</h2>' + _r(dict(type='table', headers=['Scene', 'Caption', 'Trimmed'],
                rows=[list(x) for x in trims], col_widths=['22%', '39%', '39%'])))
    if f['icons']:
        out += ('<h2>Icons</h2>' + _r(dict(type='table', headers=['Scene', 'Icon', 'Because the source says'],
                rows=[[name[sid], icon, f'"{term}" in: {src}'] for sid, (icon, term, src) in f['icons'].items()], col_widths=['24%', '16%', '60%'])))
    if f['art']['unused']:
        out += '<h2>Left out of the film</h2><div class=open><ul>' + ''.join(f'<li>{H.escape(u)}</li>' for u in f['art']['unused']) + '</ul></div>'
    if f['rejected']:
        out += ('<h2>Supplied captions rejected</h2>' + _r(dict(type='table', headers=['Scene', 'Supplied', 'Words not in the source'],
                rows=[[name.get(r['slot'], r['slot']), r['proposed'], ', '.join(r['missing'])] for r in f['rejected']], col_widths=['22%', '48%', '30%'])))
    out += f'<h2>Scenes ({len(f["records"])})</h2>' + ''.join(_r(x) for x in f['records'])
    return out + '</main></html>'
