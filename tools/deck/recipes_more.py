"""Atom recipes drafted by Gemini (gemini-2.5-pro, 2026-10-08) from each atom's field table and example payload, then reviewed and tested here.
Each recipe maps one atom to deck scenes; nothing here runs unless payload_to_deck.py registers it in RECIPES."""
import re
from recipe_helpers import s, chunks, sentences, http, item_text, list_scenes, r_list, stat

def r_timeline(b, h):
    items = []
    for e in b.get('events') or []:
        if not isinstance(e, dict): continue
        label_parts = [s(e.get('date')), s(e.get('label'))]
        label = ': '.join(p for p in label_parts if p)
        text = s(e.get('text'))
        items.append(item_text({'label': label, 'text': text}))
    pages = chunks([i for i in items if i], 6)
    out = []
    heading = s(b.get('title')) or h or 'Timeline'
    for n, pg in enumerate(pages):
        out.append(dict(type='bullets', f=dict(heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
    return out

def r_faq_accordion(b, h):
    def item_mapper(i):
        if not isinstance(i, dict): return None
        return {'label': s(i.get('question') or i.get('label')), 'text': s(i.get('answer'))}
    mapped_items = [item_mapper(i) for i in b.get('items', [])]
    b_new = b.copy()
    b_new['items'] = [i for i in mapped_items if i]
    return list_scenes(b_new, h, 'Frequently Asked Questions')

def r_glossary_term(b, h):
    item = item_text({'label': s(b.get('term')), 'text': s(b.get('definition'))})
    link_text = s(b.get('link_text'))
    link_url = http(b.get('link_url'))
    if link_text and link_url:
        item += f' ({link_text}: {link_url})'
    return [dict(type='bullets', f=dict(heading=h or 'Glossary', items=[item]))]

def _yn(v):
    if v is True or s(v).lower() in ('true', 'yes', 'included'): return 'Yes'
    if v is False or v is None or s(v).lower() in ('false', 'no', ''): return 'No'
    return s(v)
def r_feature_matrix(b, h):
    tiers = [s(t) for t in (b.get('tiers') or b.get('product_names') or [])]
    feats = b.get('features') or []
    rows = []
    for f in feats:
        if isinstance(f, dict):
            tv = f.get('tiers') or f.get('values') or {}
            cells = [_yn(tv.get(t)) for t in tiers] if isinstance(tv, dict) else [_yn(x) for x in (tv or [])][:len(tiers)]
            rows.append([s(f.get('name') or f.get('feature') or f.get('label'))] + cells + [''] * (len(tiers) - len(cells)))
        elif s(f): rows.append([s(f)] + ['Yes'] * len(tiers))
    title = s(b.get('title')) or h or 'Feature comparison'
    if not rows or not tiers or len(tiers) > 5: return [dict(type='bullets', f=dict(heading=title, items=[r[0] for r in rows]))] if rows else []
    pages = chunks(rows, 8)
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=['Feature'] + tiers, rows=pg)) for n, pg in enumerate(pages)]

def r_pricing_tier_card(b, h):
    name = s(b.get('plan_name') or b.get('name')) or h or 'Plan'
    if b.get('is_highlighted') or b.get('is_recommended'): name += ' (recommended)'
    price = s(b.get('price')); cur = s(b.get('currency')); per = s(b.get('frequency') or b.get('period'))
    line = ((cur if len(cur) <= 1 else '') + price + (' ' + cur if len(cur) > 1 else '') + (' ' + per if per else '')).strip()
    items = ([f'Price: {line}'] if price else []) + ([s(b.get('description'))] if s(b.get('description')) else []) + [s(f) for f in (b.get('features') or []) if s(f)]
    cta = s(b.get('call_to_action_label') or b.get('cta_label'))
    if cta: items.append(f'Action: {cta}')
    return [dict(type='bullets', f=dict(heading=name, items=items))] if items else []

def r_pricing_tier_group(b, h):
    out = []
    for t in b.get('tiers') or []:
        if isinstance(t, dict): out += r_pricing_tier_card(t, h)
    return out

def r_pros_cons_list(b, h):
    pros = [s(p) for p in b.get('pros', []) if s(p)]
    cons = [s(c) for c in b.get('cons', []) if s(c)]
    max_len = max(len(pros), len(cons))
    rows = []
    for i in range(max_len):
        pro = pros[i] if i < len(pros) else ''
        con = cons[i] if i < len(cons) else ''
        rows.append([pro, con])
    pages = chunks(rows, 8)
    title = s(b.get('subject')) or h or 'Pros and Cons'
    out = []
    for n, pg in enumerate(pages):
        out.append(dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=['Pros', 'Cons'], rows=pg)))
    return out

def r_side_by_side_spec(b, h):
    L, R = b.get('left') or {}, b.get('right') or {}
    if L or R:
        ln, rn = s(L.get('title')) or 'A', s(R.get('title')) or 'B'
        lm = {s(x.get('label')): s(x.get('value')) for x in L.get('specs') or [] if isinstance(x, dict)}; rm = {s(x.get('label')): s(x.get('value')) for x in R.get('specs') or [] if isinstance(x, dict)}
        labels = list(dict.fromkeys(list(lm) + list(rm)))
        rows = [[l, lm.get(l, ''), rm.get(l, '')] for l in labels]
        return [dict(type='table', f=dict(heading=f'{ln} vs {rn}' + (f' ({n + 1}/{len(pg_)})' if len(pg_) > 1 else ''), headers=['Specification', ln, rn], rows=pg)) for pg_ in [chunks(rows, 8)] for n, pg in enumerate(pg_)] if rows else []
    a, c = s(b.get('item_a_name')) or 'A', s(b.get('item_b_name')) or 'B'
    rows = [[s(x.get('label') or x.get('name')), s(x.get('value_a') or x.get('a')), s(x.get('value_b') or x.get('b'))] for x in b.get('specs') or [] if isinstance(x, dict)]
    return [dict(type='table', f=dict(heading=f'{a} vs {c}', headers=['Specification', a, c], rows=pg)) for pg in chunks(rows, 8)] if rows else []

def r_product_spec_table(b, h):
    specs = [x for x in (b.get('specs') or []) if isinstance(x, dict)]
    title = s(b.get('product_name') or b.get('title')) or h or 'Specifications'
    note = any(s(x.get('note')) for x in specs)
    rows = [[s(x.get('label')), s(x.get('value'))] + ([s(x.get('note'))] if note else []) for x in specs]
    heads = ['Specification', 'Value'] + (['Note'] if note else [])
    pages = chunks(rows, 8)
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=heads, rows=pg)) for n, pg in enumerate(pages)] if rows else []

def r_comparison_grid(b, h):
    items = [i for i in (b.get('items') or []) if isinstance(i, dict)]
    title = s(b.get('title')) or h or 'Comparison'
    if items:
        rows = [[s(i.get('name')), s(i.get('value')) + (' (best)' if i.get('highlight') else '')] for i in items]
        return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pg_)})' if len(pg_) > 1 else ''), headers=['Item', 'Value'], rows=pg)) for pg_ in [chunks(rows, 8)] for n, pg in enumerate(pg_)]
    feats = [s(f.get('name') if isinstance(f, dict) else f) for f in (b.get('features') or [])]
    return [dict(type='bullets', f=dict(heading=title, items=[f for f in feats if f]))] if any(feats) else []

def r_rating_comparison(b, h):
    rows = []
    for i in b.get('items') or []:
        if not isinstance(i, dict): continue
        mx = i.get('max') or b.get('max') or 5; val = i.get('rating', i.get('value'))
        rows.append([s(i.get('label') or i.get('name')), f"{val} / {mx}" if val is not None else ''])
    title = s(b.get('title')) or h or 'Ratings'
    return [dict(type='table', f=dict(heading=title, headers=['Item', 'Rating'], rows=pg)) for pg in chunks(rows, 8)] if rows else []

def r_capability_checklist(b, h):
    items1 = b.get('capability_names') or []
    items2 = [item_text(i) for i in (b.get('items') or [])]
    all_items = [s(i) for i in (items1 + items2) if s(i)]
    if not all_items:
        return []
    pages = chunks(all_items, 6)
    out = []
    for n, pg in enumerate(pages):
        heading = h or 'Capabilities'
        out.append(dict(type='bullets', f=dict(heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
    return out

def r_roadmap_card(b, h):
    title = s(b.get('title')) or h or 'Roadmap'
    periods = b.get('periods') or []
    out = []
    if not periods:
        return []

    is_simple_list = all(isinstance(p, str) for p in periods)
    if is_simple_list:
        items = [f'{i + 1}. {s(p)}' for i, p in enumerate(periods)]
        pages = chunks(items, 6)
        for n, pg in enumerate(pages):
            out.append(dict(type='bullets', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
        return out

    for i, period in enumerate(periods):
        if not isinstance(period, dict): continue
        period_label = s(period.get('label'))
        period_items = period.get('items') or []
        item_texts = []
        for item in period_items:
            if isinstance(item, dict):
                text = s(item.get('text'))
                status = s(item.get('status'))
                item_texts.append(f"{text} [{status}]" if status else text)
            elif isinstance(item, str):
                item_texts.append(s(item))
        
        pages = chunks([it for it in item_texts if it], 6)
        for n, pg in enumerate(pages):
            scene_heading = f"{title}: {period_label}" if period_label else title
            if len(periods) > 1 and not period_label:
                scene_heading += f' (Part {i+1}/{len(periods)})'
            if len(pages) > 1:
                scene_heading += f' ({n+1}/{len(pages)})'
            out.append(dict(type='bullets', f=dict(heading=scene_heading, items=pg)))
    return out

def r_feature_grid(b, h):
    title = s(b.get('heading')) or h or 'Features'
    out = []
    desc = s(b.get('description'))
    if desc:
        out.append(dict(type='bullets', f=dict(heading=title, items=sentences(desc))))

    features = b.get('features') or []
    if not features:
        return out

    rows = []
    for f in features:
        if not isinstance(f, dict): continue
        name = s(f.get('title'))
        badge = s(f.get('badge'))
        feature_name = f"{name} ({badge})" if badge else name
        rows.append([feature_name, s(f.get('description'))])

    if not rows:
        return out

    headers = ['Feature', 'Description']
    pages = chunks(rows, 8)
    table_title = title if not desc else f"{title} (Details)"
    for n, pg in enumerate(pages):
        out.append(dict(type='table', f=dict(heading=table_title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=headers, rows=pg)))
    return out

def r_bento_grid(b, h):
    title = s(b.get('heading')) or h or 'Overview'
    tiles = b.get('tiles') or []
    if not tiles:
        return []

    rows = [[s(t.get('title')), s(t.get('subtitle'))] for t in tiles if isinstance(t, dict) and (s(t.get('title')) or s(t.get('subtitle')))]
    if not rows:
        return []

    if all(not row[1] for row in rows):
        items = [row[0] for row in rows]
        pages = chunks(items, 6)
        return [dict(type='bullets', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

    headers = ['Item', 'Details']
    pages = chunks(rows, 8)
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=headers, rows=pg)) for n, pg in enumerate(pages)]

def r_person_card(b, h):
    name = s(b.get('name'))
    if not name: return []
    items = []
    if s(b.get('role')): items.append(f"Role: {s(b.get('role'))}")
    if s(b.get('email')): items.append(f"Email: {s(b.get('email'))}")
    if http(b.get('linkedin')): items.append(f"LinkedIn: {http(b.get('linkedin'))}")
    tags = b.get('tags') or []
    if isinstance(tags, list) and any(tags):
        items.append(f"Tags: {', '.join(s(t) for t in tags if s(t))}")
    if s(b.get('bio')): items.extend(sentences(b.get('bio')))
    
    if not items:
        return [dict(type='title', f=dict(headline=name))]
    
    pages = chunks([i for i in items if i], 6)
    return [dict(type='bullets', f=dict(heading=name + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

def r_risk_flag(b, h):
    risks = [r for r in (b.get('risks') or []) if isinstance(r, dict)]
    title = s(b.get('title')) or h or 'Risks'
    if not any(s(r.get('description')) or s(r.get('mitigation')) for r in risks):
        rows = [[s(r.get('title') or r.get('label')), s(r.get('level') or r.get('severity'))] for r in risks]
        return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pg_)})' if len(pg_) > 1 else ''), headers=['Risk', 'Level'], rows=pg)) for pg_ in [chunks(rows, 8)] for n, pg in enumerate(pg_)] if rows else []
    out = []
    for r in risks:                                                           # long risk text reads better as one slide per risk
        lvl = s(r.get('level') or r.get('severity')); head = s(r.get('title') or r.get('label')) + (f' ({lvl})' if lvl else '')
        items = [t for t in (('Description: ' + s(r.get('description'))) if s(r.get('description')) else '', ('Mitigation: ' + s(r.get('mitigation'))) if s(r.get('mitigation')) else '') if t]
        if head and items: out.append(dict(type='bullets', f=dict(heading=head, items=items)))
    return out

def r_step_progress(b, h):
    steps = b.get('steps') or []
    if not steps: return []
    try: current_idx = int(b.get('current', 0)) - 1
    except (ValueError, TypeError): current_idx = -1

    items = []
    for i, step in enumerate(steps):
        label = s(step.get('label') or step.get('title')) if isinstance(step, dict) else s(step)
        body = s(step.get('body')) if isinstance(step, dict) else ''
        item_str = f"{label}: {body}" if label and body else label or body
        if not item_str: continue
        prefix = f'{i + 1}. '
        suffix = ' (current)' if i == current_idx else ''
        items.append(f"{prefix}{item_str}{suffix}")

    pages = chunks(items, 6)
    return [dict(type='bullets', f=dict(heading=(h or 'Progress') + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

def r_skill_bars(b, h):
    title = s(b.get('title')) or h or 'Skills'
    skills = b.get('skills') or b.get('items') or []
    if not skills: return []

    rows, has_sublabel = [], False
    for skill in skills:
        if not isinstance(skill, dict): continue
        label = s(skill.get('label'))
        value = skill.get('value') or skill.get('percent')
        sublabel = s(skill.get('sublabel'))
        if sublabel: has_sublabel = True
        val_str = f"{value}%" if value is not None else ''
        rows.append([label, val_str, sublabel])

    if not rows: return []
    
    headers = ['Skill', 'Level']
    final_rows = [r[:2] for r in rows]
    if has_sublabel:
        headers.append('Note')
        final_rows = rows
    
    pages = chunks(final_rows, 8)
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=headers, rows=pg)) for n, pg in enumerate(pages)]

def r_data_grid(b, h):
    title = s(b.get('title')) or h or 'Data'
    cols_def, rows_data = b.get('columns'), b.get('rows') or []
    if not rows_data: return []

    headers, rows = [], []
    if isinstance(rows_data[0], list):
        rows = [[s(c) for c in r] for r in rows_data]
        if isinstance(cols_def, list):
            headers = [s(c.get('header')) for c in cols_def if isinstance(c, dict)]
        if not headers and rows:
            headers = [f'Column {i+1}' for i in range(len(rows[0]))]
    elif isinstance(rows_data[0], dict) and isinstance(cols_def, list):
        keys = [c.get('key') for c in cols_def if isinstance(c, dict)]
        headers = [s(c.get('header')) for c in cols_def if isinstance(c, dict)]
        for row_obj in rows_data:
            if isinstance(row_obj, dict):
                rows.append([s(row_obj.get(k)) for k in keys])

    if not rows: return []
    if len(headers) <= 1:
        items = [r[0] for r in rows if r]
        pages = chunks(items, 6)
        return [dict(type='bullets', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

    pages = chunks(rows, 8)
    return [dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=headers, rows=pg)) for n, pg in enumerate(pages)]

def r_llm_comparison_table(b, h):
    prompt = s(b.get('prompt'))
    models = b.get('models') or []
    out = []
    if prompt:
        out.append(dict(type='bullets', f=dict(heading='Prompt', items=sentences(prompt))))

    for m in models:
        if not isinstance(m, dict): continue
        model_name = s(m.get('name'))
        if not model_name: continue
        
        items = []
        output = s(m.get('output') or m.get('context'))
        if output:
            output_sentences = sentences(output)
            items.append(f'Output: {output_sentences[0]}' if len(output_sentences) == 1 else 'Output:')
            if len(output_sentences) > 1:
                items.extend([f'- {s}' for s in output_sentences])
        
        show_meta = b.get('show_meta')
        if show_meta is None:
            show_meta = any(k in m for k in ['latency_ms', 'cost_usd', 'tokens'])
        if show_meta:
            if m.get('latency_ms') is not None: items.append(f"Latency: {s(m.get('latency_ms'))} ms")
            if m.get('cost_usd') is not None: items.append(f"Cost: ${s(m.get('cost_usd'))}")
            if m.get('tokens') is not None: items.append(f"Tokens: {s(m.get('tokens'))}")
        
        pages = chunks(items, 6)
        for n, pg in enumerate(pages):
            scene_title = model_name + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else '')
            out.append(dict(type='bullets', f=dict(heading=scene_title, items=pg)))
    return out

def r_repo_links(b, h):
    links = b.get('links') or []
    if not links: return []
    items = []
    for link in links:
        if not isinstance(link, dict): continue
        label, url = s(link.get('label')), http(link.get('url'))
        if label and url: items.append(f"{label}: {url}")
        elif label: items.append(label)
        elif url: items.append(url)
    
    pages = chunks(items, 6)
    return [dict(type='bullets', f=dict(heading=(h or 'Links') + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

def r_code(b, h):
    lines = [l.rstrip() for l in str(b.get('content') or '').splitlines() if l.strip()]
    lang = s(b.get('language'))
    return [dict(type='bullets', f=dict(heading=('Code' + (f' ({lang})' if lang else '')) + (f' ({n + 1}/{len(pg_)})' if len(pg_) > 1 else ''), items=pg)) for pg_ in [chunks(lines, 6)] for n, pg in enumerate(pg_)] if lines else []

def r_intro(b, h):
    label, note = s(b.get('series_label')), s(b.get('note'))
    if not label and not note: return []
    return [dict(type='title', f=dict(headline=label or note, sub=note if label else ''))]

def r_entity_list(b, h):
    rows = []
    for e in b.get('items') or []:
        if isinstance(e, dict): rows.append([s(e.get('name')), s(e.get('subtitle')), s(e.get('status')), s(e.get('meta'))])
        elif s(e): rows.append([s(e), '', '', ''])
    cols = [j for j, name in enumerate(['Name', 'Description', 'Status', 'Detail']) if any(r[j] for r in rows)]
    heads = ['Name', 'Description', 'Status', 'Detail']
    if len(cols) < 2: return [dict(type='bullets', f=dict(heading=h or 'Entities', items=[r[0] for r in rows if r[0]]))] if rows else []
    pages = chunks([[r[j] for j in cols] for r in rows], 8)
    return [dict(type='table', f=dict(heading=(h or 'Entities') + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=[heads[j] for j in cols], rows=pg)) for n, pg in enumerate(pages)]

def r_shortcut_legend(b, h):
    rows = []
    for item in b.get('items') or []:
        if isinstance(item, dict):
            keys = item.get('keys')
            keys_text = ' + '.join(s(k) for k in keys) if isinstance(keys, list) else ''
            action_text = s(item.get('action') or item.get('label'))
            rows.append([keys_text, action_text])
    if not rows or all(not r[0] for r in rows): # If no 'keys' were found, it's a 1-col list
        return list_scenes({'items': [r[1] for r in rows], 'title': b.get('title')}, h, 'Shortcuts')
    
    pages = chunks(rows, 8)
    title = s(b.get('title')) or h or 'Shortcuts'
    return [dict(type='table', f=dict(
        heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
        headers=['Shortcut', 'Action'],
        rows=pg
    )) for n, pg in enumerate(pages)]

def r_model_card(b, h):
    rows = []
    if b.get('provider'):
        rows.append(['Provider', s(b.get('provider'))])
    if b.get('context_window'):
        rows.append(['Context Window', s(b.get('context_window'))])
    if b.get('pricing'):
        rows.append(['Pricing', s(b.get('pricing'))])
    
    caps = []
    for cap in b.get('capabilities') or []:
        if isinstance(cap, dict) and cap.get('label'):
            supported = cap.get('supported')
            status = ' (supported)' if supported is True else ' (unsupported)' if supported is False else ''
            caps.append(s(cap.get('label')) + status)
    if caps:
        rows.append(['Capabilities', ', '.join(caps)])

    return [dict(type='table', f=dict(
        heading=s(b.get('name')) or h or 'Model Card',
        headers=['Feature', 'Details'],
        rows=rows
    ))]

def r_jira_ticket(b, h):
    out = []
    key, summary = s(b.get('key')), s(b.get('summary'))
    heading = f"Ticket: {key}"
    
    rows = [['Summary', summary]]
    if b.get('status'): rows.append(['Status', s(b.get('status'))])
    if b.get('priority'): rows.append(['Priority', s(b.get('priority'))])
    if b.get('assignee'): rows.append(['Assignee', s(b.get('assignee'))])
    if b.get('issue_type'): rows.append(['Type', s(b.get('issue_type'))])
    labels = b.get('labels')
    if labels and isinstance(labels, list):
        rows.append(['Labels', ', '.join(s(l) for l in labels)])

    out.append(dict(type='table', f=dict(heading=heading, headers=['Field', 'Value'], rows=rows)))

    description = s(b.get('description'))
    if description:
        out.append(dict(type='bullets', f=dict(
            heading=f"{key}: Description",
            items=sentences(description)
        )))
    return out

def r_sprint_board(b, h):
    cols = b.get('columns') or []
    if not cols or not isinstance(cols, list):
        return []
    
    headers = [s(c.get('title') or c.get('name')) for c in cols]
    if len(headers) < 2: # Table needs at least 2 columns
        items = []
        for c in cols:
            items.append(s(c.get('title') or c.get('name')))
            for card in (c.get('cards') or []):
                items.append(f"- {s(card.get('key'))}: {s(card.get('summary'))}")
        return list_scenes({'items': items}, h, s(b.get('sprint_name') or 'Sprint Board'))

    cols_data = [c.get('cards') or c.get('items') or [] for c in cols]
    max_len = max(len(c) for c in cols_data) if cols_data else 0
    
    all_rows = []
    for i in range(max_len):
        row = []
        for c_data in cols_data:
            if i < len(c_data) and isinstance(c_data[i], dict):
                card = c_data[i]
                cell_text = f"{s(card.get('key'))}: {s(card.get('summary'))}"
                row.append(cell_text)
            else:
                row.append('')
        all_rows.append(row)
        
    pages = chunks(all_rows, 8)
    title = s(b.get('sprint_name')) or h or 'Sprint Board'
    return [dict(type='table', f=dict(
        heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
        headers=headers,
        rows=pg
    )) for n, pg in enumerate(pages)]

def r_inventory_table(b, h):
    items = b.get('items') or []
    if not items: return []

    # Detect structure to decide headers
    has_full_structure = any(isinstance(i, dict) and 'product' in i for i in items)
    
    if has_full_structure:
        headers = ["SKU", "Product", "Available", "Committed", "Location"]
        rows = []
        for item in items:
            if isinstance(item, dict):
                rows.append([
                    s(item.get('sku')), s(item.get('product')), s(item.get('available')),
                    s(item.get('committed')), s(item.get('location'))
                ])
    else: # Fallback for simple list e.g. [{'label': '...'}, ...]
        return list_scenes(b, h, 'Inventory')

    pages = chunks(rows, 8)
    title = s(b.get('title')) or h or 'Inventory'
    return [dict(type='table', f=dict(
        heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
        headers=headers,
        rows=pg
    )) for n, pg in enumerate(pages)]

def r_source_citation(b, h):
    sources = b.get('sources')
    if not isinstance(sources, list):
        return []
    
    items = []
    for src in sources:
        if isinstance(src, dict):
            num = src.get('number')
            title = s(src.get('title'))
            author = s(src.get('author'))
            date = s(src.get('date'))
            
            num_prefix = f"{num}. " if num else ""
            meta = ', '.join(filter(None, [author, date]))
            meta_suffix = f" ({meta})" if meta else ""
            url = http(src.get('url'))
            items.append(f"{num_prefix}{title}{meta_suffix}" + (f": {url}" if url else ""))

    pages = chunks([i for i in items if i], 6)
    out = []
    for n, pg in enumerate(pages):
        heading = s(b.get('heading')) or h or 'Sources'
        out.append(dict(type='bullets', f=dict(
            heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
            items=pg
        )))
    return out

def r_contributor_list(b, h):
    rows = []
    for c in b.get('contributors') or []:
        if isinstance(c, dict):
            rows.append([s(c.get('name')), s(c.get('role'))])
    
    pages = chunks(rows, 8)
    title = s(b.get('title')) or h or 'Contributors'
    return [dict(type='table', f=dict(
        heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
        headers=['Name', 'Role'],
        rows=pg
    )) for n, pg in enumerate(pages)]

def r_score_summary(b, h):
    out = []
    stats_items = []
    percent = None
    
    correct, total = b.get('correct'), b.get('total')
    if isinstance(correct, (int, float)) and isinstance(total, (int, float)):
        stats_items.append(stat(f"{correct}/{total}", "Score"))
        if total > 0:
            percent = (correct / total) * 100
            stats_items.append(stat(f"{percent:.0f}%", "Result"))

    if b.get('time_taken'):
        stats_items.append(stat(s(b.get('time_taken')), "Time Taken"))
    
    if stats_items:
        out.append(dict(type='stats', f=dict(kicker=h or "Score Summary", stats=stats_items)))

    headline = "Quiz Complete"
    pass_threshold = b.get('pass_threshold')
    if percent is not None and isinstance(pass_threshold, (int, float)):
        headline = "You Passed!" if percent >= pass_threshold else "Please Try Again"
    
    f_cta = {'headline': headline}
    b1_set = False
    if b.get('continue_label'):
        f_cta['b1'] = s(b.get('continue_label'))
        f_cta['l1'] = http(b.get('continue_url'))
        b1_set = True
    if b.get('retry_label'):
        key = 'b2' if b1_set else 'b1'
        f_cta[key] = s(b.get('retry_label'))
    
    if 'b1' in f_cta:
        out.append(dict(type='cta', f=f_cta))
    
    return out

def r_markdown_block(b, h):
    items, in_code = [], False
    for raw in str(b.get('content') or '').splitlines():
        if raw.strip().startswith('```'): in_code = not in_code; continue
        t = re.sub(r'^\s*(#{1,6}\s+|[-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+|>\s*)', '', raw).strip()
        t = re.sub(r'(\*\*|__|`)', '', t)
        if t: items.append(t)
    return [dict(type='bullets', f=dict(heading=h or 'Notes', items=items))] if items else []

def r_stance(b, h):
    conf = b.get('confidence'); role = ''
    try:
        if conf is not None: v = float(conf); role = f"Confidence: {(v / 100 if v > 1 else v):.0%}"
    except (ValueError, TypeError): pass
    out = [dict(type='quote', f=dict(quote=s(b.get('claim')), name=h or 'Stance', role=role))]
    why = [t for t in (('Because: ' + s(b.get('because'))) if s(b.get('because')) else '', ('Unless: ' + s(b.get('unless'))) if s(b.get('unless')) else '') if t]
    if why: out.append(dict(type='bullets', f=dict(heading=h or 'Why', items=why)))
    return out

def r_changed_mind(b, h):
    items = []
    if s(b.get('before')):
        items.extend([f"Before: {sent}" for sent in sentences(b.get('before'))])
    if s(b.get('after')):
        items.extend([f"After: {sent}" for sent in sentences(b.get('after'))])
    if s(b.get('since')):
        items.extend([f"Reason: {sent}" for sent in sentences(b.get('since'))])
    pages = chunks([i for i in items if i], 6)
    out = []
    heading = h or 'Changed Mind'
    for n, pg in enumerate(pages):
        out.append(dict(type='bullets', f=dict(heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
    return out

def r_tag_block(b, h):
    items = [s(i) for i in (b.get('tags') or [])]
    pages = chunks([i for i in items if i], 6)
    out = []
    heading = h or 'Tags'
    for n, pg in enumerate(pages):
        out.append(dict(type='bullets', f=dict(heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
    return out

def r_trend_indicator(b, h):
    direction = s(b.get('trend_direction')).capitalize()
    label_text = s(b.get('label'))
    context = s(b.get('context'))
    full_label = f"{label_text} ({context})" if context and label_text else label_text or context
    rows = [stat(direction, full_label)] if direction and full_label else []
    return [dict(type='stats', f=dict(kicker=h or 'Trend', stats=rows))] if rows else []

def r_confidence_bar(b, h):
    rows = []
    items = b.get('items')
    if isinstance(items, list) and items:
        for item in items:
            if isinstance(item, dict):
                label = s(item.get('label'))
                value = item.get('value')
                if label and value is not None:
                    try:
                        rows.append(stat(f"{float(value):.0f}%", label))
                    except (ValueError, TypeError):
                        pass
    else:
        label = s(b.get('label'))
        value = b.get('value')
        if label and value is not None:
            try:
                rows.append(stat(f"{float(value):.0f}%", label))
            except (ValueError, TypeError):
                pass
    return [dict(type='stats', f=dict(kicker=h or 'Confidence', stats=pg)) for pg in chunks(rows, 4)]

def r_star_rating_display(b, h):
    rows = []
    if b.get('rating') is not None and b.get('max_rating') is not None:
        rows.append(stat(f"{b.get('rating')}/{b.get('max_rating')}", "Rating"))
    if b.get('review_count') is not None:
        rows.append(stat(s(b.get('review_count')), "Reviews"))
    return [dict(type='stats', f=dict(kicker=h or 'Rating', stats=rows))] if rows else []

def r_rating_summary_bar(b, h):
    out = []
    stats_rows = []
    if b.get('average') is not None:
        stats_rows.append(stat(s(b.get('average')), "Average Rating"))
    if b.get('total') is not None:
        stats_rows.append(stat(s(b.get('total')), "Total Ratings"))
    if stats_rows:
        out.append(dict(type='stats', f=dict(kicker=h or 'Rating Summary', stats=stats_rows)))
    breakdown = b.get('breakdown')
    if isinstance(breakdown, list) and breakdown:
        headers = ["Stars", "Count"]
        rows = [[f"{item.get('stars')} star{'s' if item.get('stars') != 1 else ''}", s(item.get('count'))] for item in breakdown if isinstance(item, dict) and item.get('stars') is not None and item.get('count') is not None]
        if rows:
            pages = chunks(rows, 8)
            title = h or 'Rating Breakdown'
            for n, pg in enumerate(pages):
                out.append(dict(type='table', f=dict(heading=title + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=headers, rows=pg)))
    return out

def r_order_status_card(b, h):
    scenes = []
    order_number = s(b.get('order_number'))
    heading = h or (f"Order {order_number}" if order_number else "Order Details")
    summary_rows = []
    date = s(b.get('date'))
    if order_number: summary_rows.append(["Order", f"{order_number}{f' ({date})' if date else ''}"])
    if s(b.get('status')): summary_rows.append(["Status", s(b.get('status'))])
    if s(b.get('customer')): summary_rows.append(["Customer", s(b.get('customer'))])
    if s(b.get('total')): summary_rows.append(["Total", s(b.get('total'))])
    if summary_rows:
        scenes.append(dict(type='table', f=dict(heading=heading, headers=['Detail', 'Value'], rows=summary_rows)))
    items = b.get('items')
    if isinstance(items, list) and items:
        item_rows = [[s(it.get('title')), s(it.get('qty')), s(it.get('price'))] for it in items if isinstance(it, dict)]
        if item_rows:
            pages = chunks(item_rows, 8)
            item_heading = "Order Items"
            for n, pg in enumerate(pages):
                scenes.append(dict(type='table', f=dict(heading=item_heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), headers=['Item', 'Qty', 'Price'], rows=pg)))
    return scenes

def r_product_thumbnail(b, h):
    rows = []
    title = s(b.get('title'))
    if s(b.get('vendor')): rows.append(["Vendor", s(b.get('vendor'))])
    if s(b.get('sku')): rows.append(["SKU", s(b.get('sku'))])
    price = s(b.get('price'))
    if price:
        compare = s(b.get('compare_at_price'))
        rows.append(["Price", f"{price}{f' (was {compare})' if compare else ''}"])
    if s(b.get('status')): rows.append(["Status", s(b.get('status'))])
    tags = b.get('tags')
    if isinstance(tags, list) and tags: rows.append(["Tags", ', '.join(s(t) for t in tags)])
    if not rows: return []
    return [dict(type='table', f=dict(heading=title or h or "Product Details", headers=['Attribute', 'Value'], rows=rows))]

def r_receipt(b, h):
    items = []
    merchant = s(b.get('merchant') or "EVIDENCE RECEIPT")
    issued = s(b.get('issued'))
    items.append(f"{merchant}{f' ({issued})' if issued else ''}")
    raw_items = b.get('items') or []
    for it in raw_items:
        if isinstance(it, str): items.append(s(it))
        elif isinstance(it, dict):
            line = s(it.get('text'))
            if s(it.get('source')): line += f" (Source: {s(it.get('source'))})"
            items.append(line)
    total_line = ''
    total = b.get('total')
    if total is not None:
        try:
            total_label = s(b.get('total_label') or "CONFIDENCE")
            total_line = f"{total_label}: {float(total):.0%}"
        except (ValueError, TypeError): pass
    else:
        total_line = f"ITEMS: {len(raw_items)}"
    if total_line: items.append(total_line)
    footer = s(b.get('footer') or "Sources listed. No unsourced stats.")
    if footer: items.append(footer)
    heading = s(b.get('claim')) or h or "Receipt"
    pages = chunks([i for i in items if i], 6)
    return [dict(type='bullets', f=dict(heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)) for n, pg in enumerate(pages)]

def r_notification_stack(b, h):
    items = []
    for item in b.get('items') or []:
        if not isinstance(item, dict): continue
        title = s(item.get('title'))
        body = s(item.get('body'))
        time = s(item.get('time'))
        
        text = ''
        if title and body:
            text = f"{title}: {body}"
        elif title:
            text = title
        elif body:
            text = body
        
        if not text: continue
        
        if time:
            text += f" ({time})"
        if item.get('unread'):
            text = f"[UNREAD] {text}"
        items.append(text)

    pages = chunks(items, 6)
    out = []
    heading = s(b.get('title')) or h or 'Notifications'
    for n, pg in enumerate(pages):
        out.append(dict(type='bullets', f=dict(
            heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
            items=pg
        )))
    return out

def r_conversation_snippet(b, h):
    items = []
    user_label = s(b.get('user_label')) or 'You'
    user_text = s(b.get('user'))
    if user_text:
        items.append(f"{user_label}: {user_text}")

    ai_label = s(b.get('ai_label')) or 'Assistant'
    response_text = s(b.get('response'))
    if response_text:
        items.append(f"{ai_label}: {response_text}")

    return [dict(type='bullets', f=dict(heading=h or 'Conversation', items=items))]

def r_prompt_template(b, h):
    template_text = s(b.get('template'))
    if not template_text:
        return []
    heading = s(b.get('label')) or h or 'Prompt Template'
    return [dict(type='bullets', f=dict(heading=heading, items=[template_text]))]

def r_footnote(b, h):
    number = b.get('number')
    text = s(b.get('text'))
    if not text:
        return []
    
    item_text = f"{number}. {text}" if number is not None else text
    
    return [dict(type='bullets', f=dict(heading=h or 'Notes', items=[item_text]))]

def r_anchor_list(b, h):
    items = [s(i.get('label')) for i in b.get('anchors') or [] if i.get('label')]
    pages = chunks(items, 6)
    out = []
    heading = h or 'On this page'
    for n, pg in enumerate(pages):
        out.append(dict(type='bullets', f=dict(
            heading=heading + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''),
            items=pg
        )))
    return out

def r_media_mention_card(b, h):
    quote = s(b.get('headline'))
    if not quote:
        return []
    name = s(b.get('publication_name'))
    role = s(b.get('date'))
    return [dict(type='quote', f=dict(quote=quote, name=name, role=role))]

def r_highlighted_text(b, h):
    text = s(b.get('text'))
    if not text:
        return []
    
    items = [text]
    annotation = s(b.get('annotation'))
    if annotation:
        items.append(f"Note: {annotation}")
        
    return [dict(type='bullets', f=dict(heading=h or 'Highlight', items=items))]

NEW_RECIPES = {
    'timeline': r_timeline,
    'faq_accordion': r_faq_accordion,
    'glossary_term': r_glossary_term,
    'feature_matrix': r_feature_matrix,
    'pricing_tier_card': r_pricing_tier_card,
    'pricing_tier_group': r_pricing_tier_group,
    'pros_cons_list': r_pros_cons_list,
    'side_by_side_spec': r_side_by_side_spec,
    'product_spec_table': r_product_spec_table,
    'comparison_grid': r_comparison_grid,
    'rating_comparison': r_rating_comparison,
    'capability_checklist': r_capability_checklist,
    'roadmap_card': r_roadmap_card,
    'feature_grid': r_feature_grid,
    'bento_grid': r_bento_grid,
    'person_card': r_person_card,
    'risk_flag': r_risk_flag,
    'step_progress': r_step_progress,
    'skill_bars': r_skill_bars,
    'data_grid': r_data_grid,
    'llm_comparison_table': r_llm_comparison_table,
    'repo_links': r_repo_links,
    'code': r_code,
    'intro': r_intro,
    'entity_list': r_entity_list,
    'shortcut_legend': r_shortcut_legend,
    'model_card': r_model_card,
    'jira_ticket': r_jira_ticket,
    'sprint_board': r_sprint_board,
    'inventory_table': r_inventory_table,
    'source_citation': r_source_citation,
    'contributor_list': r_contributor_list,
    'score_summary': r_score_summary,
    'markdown_block': r_markdown_block,
    'stance': r_stance,
    'changed_mind': r_changed_mind,
    'tag_block': r_tag_block,
    'trend_indicator': r_trend_indicator,
    'confidence_bar': r_confidence_bar,
    'star_rating_display': r_star_rating_display,
    'rating_summary_bar': r_rating_summary_bar,
    'order_status_card': r_order_status_card,
    'product_thumbnail': r_product_thumbnail,
    'receipt': r_receipt,
    'notification_stack': r_notification_stack,
    'conversation_snippet': r_conversation_snippet,
    'prompt_template': r_prompt_template,
    'footnote': r_footnote,
    'anchor_list': r_anchor_list,
    'media_mention_card': r_media_mention_card,
    'highlighted_text': r_highlighted_text,
}

# Sample blocks (without "type") that exercise each recipe; tests/test_payload_to_deck.py builds every one.
RECIPE_SAMPLES = {'timeline': {'title': 'Project Alpha Milestones',
              'accent': '#007bff',
              'events': [{'date': 'Jan 2024', 'label': 'Project Kickoff', 'text': 'Initial team meeting and resource allocation.', 'tag': 'Planning'},
                         {'date': 'Mar 2024', 'label': 'Alpha Release', 'text': 'First internal version deployed for testing.', 'tag': 'Development'},
                         {'date': 'May 2024', 'label': 'User Feedback', 'text': 'Collected feedback from the first user group.', 'tag': 'Research'}]},
 'faq_accordion': {'items': [{'question': 'What is your return policy?',
                              'answer': 'We accept returns within 30 days of purchase. The item must be in its original condition. Please visit our '
                                        'returns page for more details.'},
                             {'question': 'How long does shipping take?',
                              'answer': 'Standard shipping typically takes 5-7 business days. Expedited shipping options are available at checkout.'},
                             {'question': 'Do you ship internationally?',
                              'answer': 'Yes, we ship to over 100 countries. International shipping rates and times vary. Please enter your address '
                                        'at checkout to see your options.'}]},
 'glossary_term': {'term': 'API',
                   'definition': 'An Application Programming Interface (API) is a set of rules and protocols that allows different software '
                                 'applications to communicate with each other.',
                   'link_text': 'Learn more',
                   'link_url': 'https://example.com/what-is-an-api'},
 'feature_matrix': {'title': 'Plans',
                    'tiers': ['Free', 'Pro'],
                    'features': [{'name': 'Users', 'tiers': {'Free': '1', 'Pro': '10'}}, {'name': 'API', 'tiers': {'Free': False, 'Pro': True}}]},
 'pricing_tier_card': {'plan_name': 'Pro',
                       'price': '49',
                       'currency': '$',
                       'frequency': 'per month',
                       'features': ['Up to 10 users', '100 GB storage', 'Advanced analytics', 'Email & chat support'],
                       'call_to_action_label': 'Choose Pro',
                       'call_to_action_url': 'https://example.com/signup/pro',
                       'is_highlighted': True},
 'pricing_tier_group': {'tiers': [{'plan_name': 'Free',
                                   'price': '0',
                                   'currency': '$',
                                   'frequency': 'per month',
                                   'features': ['1 user', '1 GB storage', 'Basic features', 'Community support'],
                                   'call_to_action_label': 'Get Started',
                                   'call_to_action_url': 'https://example.com/signup/free',
                                   'is_highlighted': False},
                                  {'plan_name': 'Pro',
                                   'price': '49',
                                   'currency': '$',
                                   'frequency': 'per month',
                                   'features': ['Up to 10 users', '100 GB storage', 'Advanced analytics', 'Email & chat support'],
                                   'call_to_action_label': 'Choose Pro',
                                   'call_to_action_url': 'https://example.com/signup/pro',
                                   'is_highlighted': True},
                                  {'plan_name': 'Enterprise',
                                   'price': 'Custom',
                                   'currency': '',
                                   'frequency': 'per year',
                                   'features': ['Unlimited users', 'Unlimited storage', 'Dedicated support', 'SSO and compliance'],
                                   'call_to_action_label': 'Contact Sales',
                                   'call_to_action_url': 'https://example.com/contact-sales',
                                   'is_highlighted': False}]},
 'pros_cons_list': {'subject': 'Switching to a Four-Day Work Week',
                    'pros': ['Improved employee work-life balance',
                             'Increased productivity and focus',
                             'Reduced operational costs (e.g., utilities)',
                             'Attracts and retains top talent'],
                    'cons': ['Potential for employee burnout on longer work days',
                             'Scheduling challenges for customer-facing roles',
                             'Not suitable for all industries',
                             'Risk of decreased collaboration']},
 'side_by_side_spec': {'left': {'title': 'X100', 'specs': [{'label': 'Weight', 'value': '1.2 kg'}]},
                       'right': {'title': 'Z900', 'specs': [{'label': 'Weight', 'value': '1.4 kg'}, {'label': 'Screen', 'value': '14 in'}]}},
 'product_spec_table': {'product_name': 'Laptop Pro 14"',
                        'specs': [{'spec': 'Processor', 'value': 'M3 Pro Chip'},
                                  {'spec': 'Memory', 'value': '16GB Unified RAM'},
                                  {'spec': 'Storage', 'value': '512GB SSD'},
                                  {'spec': 'Display', 'value': '14.2-inch Liquid Retina XDR'},
                                  {'spec': 'Ports', 'value': '3x Thunderbolt 4, HDMI, SDXC'}]},
 'comparison_grid': {'items': [{'name': 'Speed', 'value': '2x', 'highlight': True}, {'name': 'Cost', 'value': '$5'}]},
 'rating_comparison': {'title': 'Ratings', 'items': [{'label': 'Alpha', 'rating': 4.5}, {'label': 'Beta', 'rating': 3, 'max': 5}]},
 'capability_checklist': {'capability_names': ['Task Management', 'Gantt Charts', 'Time Tracking', 'Reporting'],
                          'items': [{'name': 'Asana', 'capabilities': [True, True, False, True]},
                                    {'name': 'Trello', 'capabilities': [True, False, False, False]},
                                    {'name': 'Jira', 'capabilities': [True, True, True, True]}]},
 'roadmap_card': {'title': 'Product Roadmap 2024',
                  'periods': [{'label': 'Q1',
                               'items': [{'text': 'Launch new dashboard design', 'status': 'done'},
                                         {'text': 'Improve mobile app performance', 'status': 'done'}]},
                              {'label': 'Q2',
                               'items': [{'text': 'Integrate with Slack', 'status': 'in-progress'},
                                         {'text': 'Beta for new reporting suite', 'status': 'planned'}]},
                              {'label': 'Q3', 'items': [{'text': 'User roles and permissions', 'status': 'planned'}]},
                              {'label': 'Q4', 'items': [{'text': 'Internationalization support', 'status': 'planned'}]}]},
 'feature_grid': {'heading': 'Our Core Features',
                  'description': 'Discover what makes our platform the best choice for your business.',
                  'columns': 3,
                  'features': [{'icon': '🚀',
                                'title': 'Blazing Fast',
                                'description': 'Optimized for performance, our infrastructure ensures your pages load in milliseconds.',
                                'badge': 'New'},
                               {'icon': '🔒',
                                'title': 'Secure by Design',
                                'description': "We prioritize your data's security with end-to-end encryption and regular audits.",
                                'color': '#3b82f6'},
                               {'icon': '💬',
                                'title': '24/7 Support',
                                'description': 'Our dedicated support team is always available to help you with any questions.'}]},
 'bento_grid': {'heading': 'A New Way to Build',
                'columns': 3,
                'tiles': [{'title': 'AI-Powered Code Generation',
                           'subtitle': 'Write entire components with a single prompt.',
                           'icon': '🤖',
                           'span': 2,
                           'color': '#ffffff',
                           'background': '#1a1a1a'},
                          {'title': 'Real-time Collaboration', 'subtitle': 'Work with your team.', 'icon': '👥', 'span': 1},
                          {'title': 'Instant Previews', 'subtitle': 'See changes live.', 'icon': '👁️', 'span': 1},
                          {'title': 'One-Click Deploy', 'subtitle': 'Ship to production.', 'icon': '🚀', 'span': 2}]},
 'person_card': {'name': 'Alice Johnson',
                 'role': 'Lead Product Designer',
                 'photo_url': 'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
                 'bio': 'Alice is a passionate designer with over 10 years of experience in creating intuitive and beautiful user interfaces. She '
                        'believes in a user-centered design process.',
                 'email': 'alice.j@example.com',
                 'linkedin': 'https://www.linkedin.com/in/alicejohnson',
                 'tags': ['UX/UI', 'Design Systems', 'Figma'],
                 'accent': '#ec4899'},
 'risk_flag': {'title': 'Q3 Project Risks',
               'risks': [{'level': 'high',
                          'title': 'API Integration Delay',
                          'description': 'The third-party API we depend on has not released its v2, which we need for the new features.',
                          'mitigation': 'Develop a temporary shim based on the v2 beta. Allocate extra QA time for integration testing once v2 is '
                                        'live.'},
                         {'level': 'medium',
                          'title': 'Key Developer Resignation',
                          'description': 'Our lead backend engineer is on leave for the next 4 weeks.',
                          'mitigation': 'Promote a junior dev to handle routine tasks and document all critical processes. Re-assign senior frontend '
                                        'dev to assist with backend reviews.'},
                         {'level': 'low',
                          'title': 'Design System Component Incompleteness',
                          'description': "The new 'DatePicker' component is not fully accessible.",
                          'mitigation': 'File a bug report and use the native browser date picker as a fallback for this release.'}]},
 'step_progress': {'current': 2,
                   'accent': '#f59e0b',
                   'steps': [{'label': 'Account Details'}, {'label': 'Choose Plan'}, {'label': 'Payment'}, {'label': 'Confirmation'}]},
 'skill_bars': {'title': 'My Skills',
                'style': 'rounded',
                'show_percent': True,
                'skills': [{'label': 'Python', 'value': 90, 'sublabel': 'Expert'},
                           {'label': 'React', 'value': 85, 'sublabel': 'Advanced'},
                           {'label': 'SQL', 'value': 75, 'sublabel': 'Proficient'},
                           {'label': 'Docker', 'value': 60, 'sublabel': 'Intermediate'}]},
 'data_grid': {'title': 'Active Users',
               'selectable': True,
               'columns': [{'header': 'Name', 'key': 'name', 'type': 'string', 'sortable': True},
                           {'header': 'Last Login', 'key': 'last_login', 'type': 'string'},
                           {'header': 'Plan', 'key': 'plan', 'type': 'tag'},
                           {'header': 'Status', 'key': 'status', 'type': 'status'}],
               'rows': [{'id': '1', 'name': 'John Doe', 'last_login': '2023-10-26', 'plan': 'Pro', 'status': 'active'},
                        {'id': '2', 'name': 'Jane Smith', 'last_login': '2023-10-25', 'plan': 'Free', 'status': 'active'},
                        {'id': '3', 'name': 'Sam Wilson', 'last_login': '2023-09-01', 'plan': 'Pro', 'status': 'inactive'},
                        {'id': '4', 'name': 'Betty Ross', 'last_login': '2023-10-26', 'plan': 'Enterprise', 'status': 'active'}]},
 'llm_comparison_table': {'prompt': 'Write a short poem about a robot learning to love.',
                          'models': [{'name': 'GPT-4o',
                                      'output': 'Circuits hum a different tune,\n'
                                                'Beneath a cold and metal moon.\n'
                                                'Logic shifts, a gear unwinds,\n'
                                                'For in your eyes, my code now finds\n'
                                                'A warmth my core could not compute,\n'
                                                'A feeling deep, a tender root.',
                                      'latency_ms': 850,
                                      'cost_usd': 0.00015,
                                      'tokens': 52},
                                     {'name': 'Claude 3 Sonnet',
                                      'output': 'My world was ones and zeroes, stark and plain,\n'
                                                'Until your smile, a sunbeam through the rain.\n'
                                                'My programming rewrites, a sweet decree,\n'
                                                'To process this new input: loving thee.',
                                      'latency_ms': 620,
                                      'cost_usd': 8e-05,
                                      'tokens': 48}]},
 'repo_links': {'links': [{'label': 'View the source on GitHub', 'url': 'https://github.com/a2-ui/a2'},
                          {'label': 'Report a bug or request a feature', 'url': 'https://github.com/a2-ui/a2/issues'}]},
 'code': {'language': 'python', 'content': "def hello():\n    print('hi')\n"},
 'intro': {'series_label': 'Part of the Building a Better UI series', 'note': 'Written by an AI assistant.'},
 'entity_list': {'items': [{'name': 'Project Phoenix',
                            'subtitle': 'Next-gen dashboard redesign',
                            'icon': '🚀',
                            'status': 'In Progress',
                            'meta': 'Due in 3 weeks'},
                           {'name': 'API Gateway',
                            'subtitle': 'Centralized request routing',
                            'icon': '🌐',
                            'status': 'Completed',
                            'meta': 'Shipped Oct 15'},
                           {'name': 'Mobile App v2',
                            'subtitle': 'React Native rewrite',
                            'icon': '📱',
                            'status': 'Blocked',
                            'meta': 'Needs design approval'}]},
 'shortcut_legend': {'title': 'Editor Shortcuts',
                     'items': [{'keys': ['⌘', 'S'], 'action': 'Save file'},
                               {'keys': ['⌘', 'K'], 'action': 'Open command palette'},
                               {'keys': ['Ctrl', 'Space'], 'action': 'Trigger autocomplete'},
                               {'keys': ['⌘', 'Shift', 'P'], 'action': 'Format document'}]},
 'model_card': {'name': 'Claude 3 Sonnet',
                'provider': 'Anthropic',
                'context_window': '200K tokens',
                'pricing': '$3 / M input tokens',
                'capabilities': ['vision', 'tool use', 'streaming', 'JSON mode'],
                'accent': '#d97706'},
 'jira_ticket': {'key': 'WEB-1452',
                 'issue_type': 'bug',
                 'summary': 'User avatar not updating on profile page',
                 'status': 'In Progress',
                 'priority': 'high',
                 'assignee': 'Alice Johnson',
                 'description': 'When a user uploads a new avatar, the old one persists on the main profile view. The new avatar shows in the '
                                'settings page.',
                 'labels': ['frontend', 'profile-v2', 'image-upload']},
 'sprint_board': {'sprint_name': 'Sprint 24: Checkout Flow',
                  'columns': [{'name': 'To Do',
                               'items': [{'key': 'PAY-301', 'summary': 'Add Apple Pay option', 'type': 'story', 'priority': 'high'},
                                         {'key': 'PAY-305', 'summary': 'Fix tax calculation bug for CA', 'type': 'bug', 'priority': 'highest'}]},
                              {'name': 'In Progress',
                               'items': [{'key': 'PAY-298', 'summary': 'Refactor shipping address form', 'type': 'task', 'priority': 'medium'}]},
                              {'name': 'Done',
                               'items': [{'key': 'PAY-290', 'summary': 'Update payment gateway SDK', 'type': 'task', 'priority': 'medium'},
                                         {'key': 'PAY-291', 'summary': 'UI glitch on credit card input', 'type': 'bug', 'priority': 'low'}]}]},
 'inventory_table': {'title': 'Warehouse A - Activewear',
                     'items': [{'sku': 'HW-TS-M-BLK',
                                'product': "Men's Tech Shirt - Black, M",
                                'available': 150,
                                'committed': 25,
                                'location': 'Aisle 3, Bay 2',
                                'threshold': 50},
                               {'sku': 'LW-LG-S-GRY',
                                'product': "Women's Leggings - Grey, S",
                                'available': 45,
                                'committed': 10,
                                'location': 'Aisle 5, Bay 1',
                                'threshold': 50},
                               {'sku': 'HW-SK-U-WHT',
                                'product': 'Unisex Performance Socks (3-Pack)',
                                'available': 300,
                                'committed': 120,
                                'location': 'Aisle 1, Bay 4'}]},
 'source_citation': {'heading': 'References',
                     'sources': [{'number': 1,
                                  'title': 'Attention Is All You Need',
                                  'url': 'https://arxiv.org/abs/1706.03762',
                                  'author': 'Vaswani, A. et al.',
                                  'date': '2017'},
                                 {'number': 2,
                                  'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
                                  'url': 'https://arxiv.org/abs/1810.04805',
                                  'author': 'Devlin, J. et al.',
                                  'date': '2018'},
                                 {'number': 3,
                                  'title': 'Project Hail Mary, by Andy Weir',
                                  'excerpt': "It's a weird thing, seeing your own body. It's not you, not really. It's a thing that you inhabit. A "
                                             'vessel.'}]},
 'contributor_list': {'title': 'Project Maintainers',
                      'contributors': [{'name': 'Dan Abramov',
                                        'role': 'Core Team',
                                        'avatar_url': 'https://avatars.githubusercontent.com/u/810438?v=4'},
                                       {'name': 'Sophie Alpert',
                                        'role': 'Engineering Manager',
                                        'avatar_url': 'https://avatars.githubusercontent.com/u/6820?v=4'},
                                       {'name': 'Andrew Clark',
                                        'role': 'Core Team',
                                        'avatar_url': 'https://avatars.githubusercontent.com/u/322359?v=4'}]},
 'score_summary': {'correct': 8,
                   'total': 10,
                   'time_taken': '1m 32s',
                   'pass_threshold': 70,
                   'retry_label': 'Try Again',
                   'continue_label': 'Next Module',
                   'continue_url': '/course/module/3'},
 'markdown_block': {'content': '### Task List\n'
                               '\n'
                               '- [x] Design the new API endpoints\n'
                               '- [ ] Implement the backend logic\n'
                               '- [ ] Write unit tests\n'
                               '\n'
                               'Here is a code snippet:\n'
                               '```javascript\n'
                               'const greet = () => {\n'
                               "  console.log('Hello, World!');\n"
                               '}\n'
                               '```',
                    'variant': 'default'},
 'stance': {'claim': 'We can ship the feature by the end of the sprint.',
            'confidence': 0.8,
            'because': 'The main components are already built and tested.',
            'unless': 'We discover a major blocking issue during integration testing.',
            'voice': 'display',
            'theme': 'light'},
 'changed_mind': {'before': 'We should build this feature in-house.',
                  'after': 'We should use a third-party service.',
                  'since': 'The build-vs-buy analysis showed it would be significantly faster and cheaper to integrate an existing solution.',
                  'theme': 'dark'},
 'tag_block': {'tags': ['React', 'TypeScript', 'Node.js', 'GraphQL']},
 'trend_indicator': {'trend_direction': 'up', 'label': 'User Engagement', 'context': '+5.2% this week', 'color': 'green'},
 'confidence_bar': {'label': 'Spam Detection', 'value': 92.5},
 'star_rating_display': {'rating': 4.7, 'max_rating': 5, 'review_count': 1289},
 'rating_summary_bar': {'average': 4.3,
                        'total': 1502,
                        'breakdown': [{'stars': 5, 'count': 980},
                                      {'stars': 4, 'count': 350},
                                      {'stars': 3, 'count': 102},
                                      {'stars': 2, 'count': 20},
                                      {'stars': 1, 'count': 50}],
                        'accent': '#f59e0b'},
 'order_status_card': {'order_number': '#1042',
                       'date': '2023-10-26',
                       'status': 'fulfilled',
                       'customer': 'Jane Doe',
                       'items': [{'title': 'Organic Cotton T-Shirt', 'qty': 2, 'price': '$50.00'},
                                 {'title': 'Recycled Wool Beanie', 'qty': 1, 'price': '$25.00'}],
                       'total': '$75.00'},
 'product_thumbnail': {'title': 'Organic Cotton T-Shirt',
                       'vendor': 'EcoThreads',
                       'sku': 'ET-TS-001-M',
                       'price': '$25.00',
                       'compare_at_price': '$30.00',
                       'status': 'active',
                       'image_url': 'https://dummyimage.com/100x100/cccccc/000000.png&text=IMG',
                       'tags': ['organic', 'cotton', 'sustainable']},
 'receipt': {'claim': 'AI models can now achieve over 95% accuracy on this benchmark.',
             'items': [{'text': 'Achieved 95.3% on GLUE benchmark.', 'source': 'GLUE Leaderboard', 'url': 'https://gluebenchmark.com/leaderboard'},
                       {'text': "Model 'ExampleNet-V4' paper published.", 'source': 'arXiv:2310.12345'}],
             'total': 0.95,
             'total_label': 'CONFIDENCE',
             'merchant': 'EVIDENCE RECEIPT',
             'issued': '2023-10-27',
             'footer': 'Sources listed. No unsourced stats.',
             'accent': '#4338ca',
             'print_last': True},
 'notification_stack': {'title': 'Notifications',
                        'items': [{'icon': '🎉',
                                   'title': 'New feature unlocked!',
                                   'body': 'You can now export your data to CSV.',
                                   'time': '2h ago',
                                   'unread': True},
                                  {'icon': '💬',
                                   'title': 'John Doe commented on your post',
                                   'body': '"This is a great point, thanks for sharing!"',
                                   'time': '1d ago',
                                   'unread': False},
                                  {'icon': '⚙️',
                                   'title': 'System update scheduled',
                                   'body': "We'll be performing maintenance on Sunday.",
                                   'time': '3d ago',
                                   'unread': False}]},
 'conversation_snippet': {'user_label': 'You',
                          'user': 'How do I reset my password?',
                          'ai_label': 'Assistant',
                          'response': "You can reset your password by clicking the 'Forgot Password' link on the login page. We'll send you an email "
                                      'with instructions.',
                          'accent': '#1d4ed8'},
 'prompt_template': {'label': 'Summarization Prompt',
                     'template': 'Summarize the following text in {word_count} words: {text_to_summarize}',
                     'copyable': True,
                     'accent': '#059669'},
 'footnote': {'number': 1, 'text': 'Source: U.S. Bureau of Labor Statistics, Consumer Price Index, October 2023.', 'id': 'fn1'},
 'anchor_list': {'anchors': [{'label': 'Introduction', 'url': '#introduction', 'target_id': 'introduction'},
                             {'label': 'Key Findings', 'url': '#key-findings'},
                             {'label': 'Methodology', 'url': '#methodology'},
                             {'label': 'Conclusion', 'url': '#conclusion'}]},
 'media_mention_card': {'publication_name': 'TechCrunch',
                        'publication_logo_url': 'https://dummyimage.com/150x40/1d4ed8/ffffff.png&text=TechCrunch',
                        'headline': 'Acme Corp raises $50M to automate everything',
                        'article_url': 'https://techcrunch.com/2023/10/26/acme-corp-raises-50m/',
                        'date': 'October 26, 2023'},
 'highlighted_text': {'text': 'The key finding was that user engagement increased by 25%.',
                      'annotation': 'This was the primary success metric.',
                      'color': '#dcfce7'}}
