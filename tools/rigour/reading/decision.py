"""Decision block from a problem/fix document: the alternatives it states, as one themed choice. CSS-only (radio inputs),
so it works pasted into a CMS or inside a sandboxed iframe with scripts off. Card labels are the source's own
conditions; panel lines are its own whole sentences, each marked as an instruction or an explanation. The audience
(reader or operator) changes only the declared framing words."""
import base64
import html as H
import re

from rigour import argument, bom as boms, theme as _theme
from renderers import web_article as atoms
from . import extract as ex, film

IMPERATIVE = set(film.RULES['imperatives'])


def _segments(text):
    """A case's sentences, each split once more at a declared ' -- ' aside; every segment is a verbatim substring."""
    out = []
    for s in film._sents(text):
        out += [p.strip() for p in s.split(' -- ') if p.strip()]
    return out


def _role(seg):
    return 'do' if (film.words(seg) or [''])[0] in IMPERATIVE else 'why'


def _cap(s):
    return s[0].upper() + s[1:] if s else s


def cases(art, src):
    """Each branch the source states: label (its own condition), lines (its own sentences), and the verbatim quote."""
    out = []
    for b in art['steps']:
        if b['kind'] != 'branch':
            continue
        if b['cond_source'] != b['condition']:                     # an "If X:" paragraph: re-read its whole text
            m = next(m for m in re.finditer(r'<p>\s*<strong>(.*?)</strong>(.*?)</p>', src, re.S | re.I)
                     if ex.text_of(m.group(1)) == b['cond_source'])
            body = ex.text_of(m.group(2))
            lines = [(_role(s), s) for s in _segments(body)]
        else:                                                      # a symptom / cause / fix table row
            lines = [('why', b['source'])] + ([('do', b['detail']['source'])] if b.get('detail') else [])
        out.append(dict(label=_cap(b['condition']), cond_source=b['cond_source'], lines=lines))
    return out


def pair(options, cs):
    """A listed answer joins a case only when it contains every content word of the case's condition, and is the only
    answer that does. Anything looser is a guess, so it is reported instead of shown."""
    paired, misses = {}, []
    for k, c in enumerate(cs):
        hits = [o for o in options if not film.uncovered(c['label'], o['source'])]
        if len(hits) == 1:
            paired[k] = hits[0]['source']
        else:
            best = max(options, key=lambda o: len(set(film.words(c['label'])) & set(film.words(o['source']))), default=None)
            misses.append((c['label'], best['source'] if best else None, film.uncovered(c['label'], best['source']) if best else []))
    return paired, misses


def build(src, source_name='', audience='reader', theme=None, preselect=None):
    bom = boms.load('decision_block')
    ch, v = bom['chrome'][audience], {c['id']: c.get('value') for c in bom['clarity']}
    art = film.read(src)
    text = art['text']
    cs = cases(art, src)
    options = art['decision']['options'] if art['decision'] else []
    paired, misses = pair(options, cs)
    esc = art['escalation']
    shown = [c['cond_source'] for c in cs] + [s for c in cs for _, s in c['lines']] + list(paired.values()) + \
            ([esc['source']] if esc else []) + ([art['decision']['source']] if art['decision'] else [])
    facts = dict(has_branches=len(cs) < 2, max_branches=len(cs) > v['max_branches'],
                 has_action=any(not any(r == 'do' for r, _ in c['lines']) for c in cs),
                 verbatim=any(not argument.verified(s, text) for s in shown),
                 pairing=False,                                   # unmatched answers are left off, never shown wrongly
                 org_names=any(film.org_like(s[1:]) for s in shown))
    grounds = [g for c in cs for g in ([dict(quote=c['cond_source'], text=f"case {c['label']!r}: condition")] +
                                       [dict(quote=s, text=f"case {c['label']!r}: {r}") for r, s in c['lines']])]
    gates, status, _ = boms.gates(bom, grounds, facts, text)
    questions = []
    if len(cs) < 2:
        questions.append('The article states steps, not alternatives, so there is no choice to offer. '
                         'It reads better as the film or a numbered list.' if art['steps'] else 'What alternatives does the article cover?')
    for c in cs:
        if not any(r == 'do' for r, _ in c['lines']):
            questions.append(f'What should the reader do when "{c["label"]}"? The article explains it but gives no instruction.')
    if cs and not esc:
        questions.append('When should this be escalated? The article does not say what to do if none of these works.')
    for label, best, miss in misses:
        if best:
            questions.append(f'Is "{best}" the case "{label}"? The answer does not mention: {", ".join(miss)}.')
    for s in shown:
        for o in film.org_like(s[1:]):
            questions.append(f'Is "{o}" an organisation or product name?')
    return dict(art=art, bom=bom, chrome=ch, audience=audience, cases=cs, paired=paired, misses=misses, esc=esc,
                facts=facts, gates=gates, status=status, questions=questions, source=source_name,
                theme=film._theme.load(theme), preselect=preselect)


# ---- the block -------------------------------------------------------------------------------------------------------

def _icon(name, B, cls='ic'):
    return (f'<svg class="{cls}" viewBox="0 0 96 96" aria-hidden="true" focusable="false"><path pathLength="1" d="{film.ICONS["paths"][name]}"/></svg>')


def block_html(d, uid='db'):
    """The decision block itself: one <div> plus its scoped <style>. No script, no external file."""
    B, ch, art = d['theme'], d['chrome'], d['art']
    q = art['decision']['source'] if art['decision'] else None
    ask = ch['ask'].format(question=q) if q else ch['no_question']
    css = f'''
#{uid}{{--bg:{B["bg"]};--panel:{B["panel"]};--panel2:{B["panel2"]};--ink:{B["ink"]};--ink2:{B["ink2"]};--mute:{B["muted"]};
 --acc:{B["accent"]};--acc2:{B["accent2"]};font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);
 background:radial-gradient(120% 90% at 100% 0%,color-mix(in srgb,var(--acc) 22%,transparent),transparent 60%),var(--bg);
 border-radius:20px;padding:clamp(18px,4vw,34px);box-sizing:border-box;max-width:100%}}
#{uid} *{{box-sizing:border-box}}
#{uid} .eb{{font-size:12px;font-weight:800;letter-spacing:.24em;text-transform:uppercase;color:var(--acc2);margin:0 0 10px}}
#{uid} .ask{{font-size:clamp(22px,3.4vw,34px);font-weight:900;letter-spacing:-.02em;line-height:1.1;margin:0 0 20px}}
#{uid} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}}
#{uid} input{{position:absolute;opacity:0;pointer-events:none}}
#{uid} label{{display:flex;gap:12px;align-items:flex-start;cursor:pointer;padding:16px;border-radius:14px;background:var(--panel);
 border:1.5px solid color-mix(in srgb,var(--ink) 12%,transparent);transition:border-color .2s,transform .2s,box-shadow .2s}}
#{uid} label:hover{{transform:translateY(-2px);border-color:color-mix(in srgb,var(--acc) 60%,transparent)}}
#{uid} .n{{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-weight:800;font-size:14px;
 background:color-mix(in srgb,var(--acc) 22%,transparent);color:var(--ink)}}
#{uid} .k{{display:block;font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--mute);margin-bottom:4px}}
#{uid} .t{{display:block;font-size:16px;font-weight:700;line-height:1.3}}
#{uid} .s{{display:block;font-size:13px;color:var(--mute);margin-top:6px;line-height:1.35}}
#{uid} .pan{{display:none;margin-top:16px;padding:clamp(16px,3vw,26px);border-radius:16px;
 background:linear-gradient(160deg,var(--panel2),var(--panel));border:1.5px solid color-mix(in srgb,var(--acc) 45%,transparent)}}
#{uid} .row{{display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:start;padding:10px 0}}
#{uid} .row+.row{{border-top:1px solid color-mix(in srgb,var(--ink) 10%,transparent)}}
#{uid} .lab{{font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--acc2);display:block;margin-bottom:4px}}
#{uid} .why .tx{{color:var(--ink2);font-size:15px;line-height:1.45}} #{uid} .do .tx{{font-size:18px;font-weight:700;line-height:1.35}}
#{uid} .ic{{width:40px;height:40px;fill:none;stroke:var(--acc2);stroke-width:5;stroke-linecap:round;stroke-linejoin:round}}
#{uid} .ic path{{stroke-dasharray:1;stroke-dashoffset:0}}
#{uid} .dot{{width:40px;height:40px;border-radius:50%;border:2px solid color-mix(in srgb,var(--ink) 20%,transparent)}}
#{uid} .after{{margin-top:14px;padding:14px 16px;border-radius:12px;background:color-mix(in srgb,var(--panel) 70%,transparent);
 font-size:14px;color:var(--ink2)}} #{uid} .after b{{color:var(--ink)}}
@keyframes {uid}draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}
@media (prefers-reduced-motion:no-preference){{#{uid} input:checked~.pan .ic path{{animation:{uid}draw .9s cubic-bezier(.65,0,.35,1) both}}}}'''
    ids = [f'{uid}_{k}' for k in range(len(d['cases']))]
    for k, i in enumerate(ids):
        css += (f'\n#{i}:checked~.pan.p{k}{{display:block}}'
                f'\n#{i}:checked~.cards label[for={i}]{{border-color:var(--acc);box-shadow:0 0 0 3px color-mix(in srgb,var(--acc) 35%,transparent),0 12px 30px -12px var(--acc)}}'
                f'\n#{i}:checked~.cards label[for={i}] .n{{background:var(--acc);color:#fff}}'
                f'\n#{i}:focus-visible~.cards label[for={i}]{{outline:3px solid var(--acc2);outline-offset:3px}}')
    inputs = ''.join(f'<input type="radio" id="{i}" name="{uid}"{" checked" if d["preselect"] == k else ""}>' for k, i in enumerate(ids))
    cards = ''
    for k, (i, c) in enumerate(zip(ids, d['cases'])):
        sub = f'<span class="s">{H.escape(d["paired"][k])}</span>' if k in d['paired'] else ''
        cards += (f'<label for="{i}"><span class="n">{k + 1}</span><span><span class="k">{H.escape(ch["card"])}</span>'
                  f'<span class="t">{H.escape(c["label"])}</span>{sub}</span></label>')
    panels = ''
    for k, c in enumerate(d['cases']):
        rows = ''
        for role, s in c['lines']:
            hit = film.icon_for(s) if role == 'do' else None
            mark = _icon(hit[0], d['theme']) if hit else '<span class="dot" aria-hidden="true"></span>'
            rows += (f'<div class="row {role}">{mark}<div><span class="lab">{H.escape(ch[role])}</span>'
                     f'<span class="tx">{H.escape(_cap(s))}</span></div></div>')
        after = (f'<div class="after"><b>{H.escape(ch["after"])}</b> {H.escape(d["esc"]["source"])}</div>' if d['esc'] else '')
        panels += f'<div class="pan p{k}" id="{ids[k]}_p" role="region" aria-label="{H.escape(c["label"])}">{rows}{after}</div>'
    return (f'<style>{css}</style><div id="{uid}"><p class="eb">{H.escape(ch["eyebrow"])}</p>'
            f'<p class="ask" id="{uid}_q">{H.escape(ask)}</p>{inputs}'
            f'<div class="cards" role="radiogroup" aria-labelledby="{uid}_q">{cards}</div>{panels}</div>')


# A host page can size the iframe from this; with scripts blocked (sandbox) it is simply inert.
RESIZE = ('<script>(function(){function s(){try{parent.postMessage({type:"a2ui-embed-height",height:document.documentElement.scrollHeight},"*")}'
          'catch(e){}}addEventListener("load",s);addEventListener("change",function(){setTimeout(s,30)});'
          'if(window.ResizeObserver)new ResizeObserver(s).observe(document.documentElement)})()</script>')


def embed_page(d):
    """The block alone, for an iframe: no page chrome, no external files, transparent around the block."""
    return ('<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(d["art"]["title"])}</title><style>html,body{{margin:0;background:transparent}}body{{padding:0}}</style>'
            + (block_html(d) if d['status'] == 'STANDS' else '') + RESIZE + '</html>')


def snippets(d, height=640):
    """Two ways to paste the block into a host page as an iframe, no hosting needed: a base64 data: URI as src, and
    srcdoc (inline HTML) for hosts that refuse data: URIs. Neither gets past a host CSP or sanitiser that bans iframes;
    sandbox omits allow-scripts, so the block runs CSS-only and the resize script is inert unless the host allows it."""
    page = embed_page(d)
    uri = 'data:text/html;base64,' + base64.b64encode(page.encode('utf-8')).decode()
    attrs = f'title="{H.escape(d["art"]["title"])}" style="width:100%;height:{height}px;border:0" loading="lazy" sandbox=""'
    return dict(data_uri=f'<iframe {attrs} src="{uri}"></iframe>',
                srcdoc=f'<iframe {attrs} srcdoc="{H.escape(page, quote=True)}"></iframe>', bytes_page=len(page.encode()), bytes_uri=len(uri))


CSS = film.CSS + '.pair{color:#4b5563;font-size:.9rem}'


def artifact_page(d):
    who = d['audience']
    out = film._head(f'Decision block ({who})', d['art']['title'],
                     f'<p class=src>Made only from what {H.escape(d["source"] or "the source")} states: every label and line is its own words. '
                     f'Evidence in the <a href="report.html">report</a>; the block alone, for an iframe, is <a href="embed-{d["audience"]}.html">here</a>.</p>')
    if d['status'] == 'STANDS':
        out += '<h2>Block</h2>' + block_html(d)
    else:
        out += '<h2>Block</h2><p>No decision block: the source does not state alternatives to choose between. The open questions say why.</p>'
    if d['questions']:
        out += '<h2>Open questions</h2><div class=open><ul>' + ''.join(f'<li>{H.escape(q)}</li>' for q in d['questions']) + '</ul></div>'
    return out + '</main></html>'


def report_page(d):
    out = film._head('Evidence report', d['art']['title'],
                     f'<p class=src>Companion to the decision blocks (<a href="reader.html">reader</a>, <a href="operator.html">operator</a>). '
                     f'Source: {H.escape(d["source"])}. The two audiences share every line below; only the framing words differ.</p>'
                     '<h2>Gate</h2>' + ''.join(atoms._RENDERERS['toulmin_argument'](g) for g in d['gates']))
    if d['cases']:
        rows = [[c['label'], {'do': 'instruction', 'why': 'explanation'}[r], s] for c in d['cases'] for r, s in c['lines']]
        out += ('<h2>Lines, as the source states them</h2>' + atoms._RENDERERS['table'](dict(type='table', headers=['Case', 'Shown as', 'Source sentence'],
                rows=rows, col_widths=['26%', '18%', '56%'])))
    if d['paired'] or d['misses']:
        rows = [[d['cases'][k]['label'], o, 'paired: the answer contains every word of the condition'] for k, o in d['paired'].items()]
        rows += [[lab, best or '—', 'not paired: missing ' + ', '.join(miss)] for lab, best, miss in d['misses']]
        out += ('<h2>Listed answers</h2>' + atoms._RENDERERS['table'](dict(type='table', headers=['Case', 'Answer in the source', 'Result'],
                rows=rows, col_widths=['28%', '40%', '32%'])))
    return out + '</main></html>'
