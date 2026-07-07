#!/usr/bin/env python3
"""lift.py — deterministic HTML→YAML lift for KB articles (no LLM).

Parses messy knowledge-article HTML into the KCS-shaped structure YAML that
render_kb.py / compose.py consume (contract in README.md). Parser-first
architecture: emits YAML + review_flags. A flag-free result was fully
mechanical; flagged articles (ambiguous decision logic, multi-issue
catalogues, headless structure) should be reviewed by a human — or an LLM —
at the YAML checkpoint before rendering. It never fabricates: unclear
content is flagged, not invented.

Usage: python3 lift.py article.html > article.yaml
"""
import sys, re, html as H, yaml

# Windows-safe I/O: force UTF-8 regardless of console codepage (cp1252 crashes on emoji)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ── Phase 0: normalize to a marked line stream ────────────────────────────────
EXTRAS = []   # structured blocks captured before flattening: ('table'|'code', payload)

def _strip(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = H.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()

def tokenize(raw):
    global EXTRAS
    EXTRAS = []
    h = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', '', raw)

    # capture TABLES as structure before flattening
    def cap_table(m):
        rows = []
        for rm in re.finditer(r'(?s)<tr[^>]*>(.*?)</tr>', m.group(0)):
            cells = [_strip(c) for c in re.findall(r'(?s)<t[hd][^>]*>(.*?)</t[hd]>', rm.group(1))]
            if any(cells): rows.append(cells)
        if not rows: return '\n'
        headers, body = (rows[0], rows[1:]) if len(rows) > 1 else ([], rows)
        EXTRAS.append(('table', {'headers': headers, 'rows': body}))
        return f'\n@@X{len(EXTRAS)-1}@@\n'
    h = re.sub(r'(?s)<table[^>]*>.*?</table>', cap_table, h)

    # capture CODE blocks
    def cap_pre(m):
        EXTRAS.append(('code', H.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()))
        return f'\n@@X{len(EXTRAS)-1}@@\n'
    h = re.sub(r'(?s)<pre[^>]*>(.*?)</pre>', cap_pre, h)

    # keep LINK targets: <a href="url">text</a> → "text [url]" (http only, no self-links)
    def cap_a(m):
        url, text = m.group(1), _strip(m.group(2))
        if url.startswith('http') and text and text != url and len(url) < 200:
            return f'{text} [{url}]'
        return text or url
    h = re.sub(r'(?s)<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', cap_a, h)

    # images → visible placeholder (never dropped silently)
    h = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', r'\n@@IMG@@ \1\n', h)
    h = re.sub(r'<img[^>]*>', r'\n@@IMG@@ (no alt)\n', h)

    # bold-only paragraphs act as headings in messy articles
    h = re.sub(r'<(p|div)[^>]*>\s*<(?:b|strong)[^>]*>([^<]{3,80})</(?:b|strong)>\s*</\1>',
               r'\n@@H4@@ \2\n', h)

    h = re.sub(r'<h([1-6])[^>]*>', r'\n@@H\1@@ ', h)
    h = re.sub(r'</h[1-6]>', '\n', h)
    h = re.sub(r'<li[^>]*>', '\n@@LI@@ ', h)
    h = re.sub(r'<(p|div|tr|br|ul|ol)[^>]*>', '\n', h)
    t = re.sub(r'<[^>]+>', '', h)
    t = H.unescape(t).replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    lines = []
    for ln in t.split('\n'):
        ln = re.sub(r'\s+', ' ', ln).strip()
        if ln: lines.append(ln)
    return lines

# ── Phase 1: KCS section segmentation (heading synonym table) ────────────────
SECTION_MAP = {   # synonyms from KCS + FAQ/Known-Error/How-To template families
    'issue':       ['summary', 'issue', 'problem', 'symptoms', 'description', 'question',
                    'error', 'overview', 'about'],
    'environment': ['environment', 'applies to', 'scope', 'prerequisites', 'prereqs',
                    'requirements', 'before you begin', 'affected versions', 'affected systems'],
    'cause':       ['cause', 'root cause', 'why this happens', 'background'],
    'cause_test':  ['confirm', 'verify this is your issue', 'cause test'],
    'resolution':  ['resolution', 'fix', 'workaround', 'possible solutions', 'procedure',
                    'steps', 'answer', 'solution', 'how to', 'remediation',
                    'troubleshooting steps', 'instructions'],
}
STOP_HEADINGS = ['further reading', 'need additional help', 'details', 'related articles', 'feedback']
NAV_NOISE = {'print', 'print:', 'back to list', 'body', 'summary body'}
PLATFORMS = {'windows', 'macos', 'mac os', 'os x', 'ios', 'android', 'linux', 'chromeos'}

def classify_heading(text):
    t = text.lower().strip().rstrip(':')
    for sec, syns in SECTION_MAP.items():
        if any(t == s or t.startswith(s) for s in syns): return sec
    if any(t.startswith(s) for s in STOP_HEADINGS): return 'STOP'
    return None

STEP_RE = re.compile(r'^(?:\(optional\)\s*)?step\s+\d+\s*[-–—:.]\s*', re.I)
NOTE_RE = re.compile(r'^(note|warning|important|caution|tip)\s*[:\-]\s*', re.I)
QUESTION_RE = re.compile(r'^(is|are|does|do|can|what|which|check)\b.{4,}\?\s*$', re.I)
METHOD_RE = re.compile(r'^(method|option|solution|alternative|approach)\s*\d*\b', re.I)
ERRHEAD_RE = re.compile(r'\berror\b|\b0x[0-9a-f]{4,}\b|"[^"]{4,}"', re.I)
KV_RE = re.compile(r'^([A-Z][\w /&()-]{1,28}):\s+(\S.*)$')
ESCAL_RE = re.compile(r'contact (?:the )?(?:[\w\s&]*?)(service desk|help ?desk|support)|submit a (ticket|request|support request)', re.I)
XREF_RE = re.compile(r'\b(K[BA]\s?\d{3,})\b', re.I)
URL_IN = re.compile(r'\[(https?://[^\]\s]+)\]')

# ── Phase 2/3: blocks within a section ────────────────────────────────────────
def flush_blocks(buf, flags):
    """Turn a run of (kind, text) items into atom blocks."""
    blocks, steps, items = [], [], []
    def close():
        nonlocal steps, items
        if steps: blocks.append({'steps': steps}); steps = []
        if items:
            # a bullet run that is all step-prefixed is a procedure
            if all(STEP_RE.match(i) for i in items):
                blocks.append({'steps': [STEP_RE.sub('', i) for i in items]})
            else:
                blocks.append({'list': items})
            items = []
    for kind, text in buf:
        if kind == 'extra':                        # pre-captured table / code block
            close()
            xkind, payload = EXTRAS[text]
            blocks.append({'table': payload} if xkind == 'table' else {'code_block': payload})
            continue
        m = NOTE_RE.match(text)
        if m:
            close()
            k = m.group(1).lower(); k = {'important': 'caution'}.get(k, k)
            k = k if k in ('info','tip','warning','caution') else 'info'
            blocks.append({'callout': {'kind': k, 'text': NOTE_RE.sub('', text)}})
            continue
        if QUESTION_RE.match(text):
            flags.add('BRANCH_CANDIDATE')          # detected, not auto-committed
        if kind == 'li':
            items.append(text); continue
        # paragraph
        close()
        if STEP_RE.match(text): steps.append(STEP_RE.sub('', text))
        else:
            if steps: blocks.append({'steps': steps}); steps = []
            blocks.append({'body': text})
    close()
    # post-pass: runs of ≥2 consecutive "Label: value" bodies → key_value
    out, kvrun = [], []
    def close_kv():
        nonlocal kvrun
        if len(kvrun) >= 2: out.append({'key_value': [{'key': k, 'value': v} for k, v in kvrun]})
        else: out.extend({'body': f'{k}: {v}'} for k, v in kvrun)
        kvrun = []
    for b in blocks:
        m = KV_RE.match(b['body']) if 'body' in b else None
        if m: kvrun.append((m.group(1), m.group(2)))
        else: close_kv(); out.append(b)
    close_kv()
    return out

def lift(raw):
    lines = tokenize(raw)
    flags = set()
    title = next((l[6:].strip() for l in lines if l.startswith('@@H1@@')), None) or \
            next((l for l in lines if not l.startswith('@@') and l.lower() not in NAV_NOISE), 'Untitled')

    # walk: current KCS section + sub-structure (platform H3/H4 under resolution)
    sections = {}          # sec -> list of (context, buf) chunks
    cur_sec, cur_sub = None, None       # cur_sub = platform name or None
    chunks = []            # (sec, sub, subkind, buf)
    buf, sub_kind = [], None

    def push():
        nonlocal buf
        if cur_sec and buf: chunks.append((cur_sec, cur_sub, sub_kind, buf))
        buf = []

    meta, pending_meta = {}, None
    issue_catalog = 0
    for ln in lines:
        hm = re.match(r'@@H(\d)@@\s*(.*)', ln)
        if hm:
            lvl, text = int(hm.group(1)), hm.group(2).strip()
            if not text or text.lower() in NAV_NOISE: continue
            sec = classify_heading(text)
            if sec == 'STOP':
                push(); cur_sec = None; continue
            if sec and lvl <= 2:
                if sec == 'issue' and re.match(r'^(issue|problem|question)\b\s*[-–:]', text, re.I):
                    issue_catalog += 1
                    if issue_catalog >= 2: flags.add('MULTI_ISSUE')
                push(); cur_sec, cur_sub, sub_kind = sec, None, None; continue
            if cur_sec == 'resolution':
                tl = text.lower().rstrip(':')
                if tl in PLATFORMS:
                    push(); cur_sub, sub_kind = text, 'platform'; continue
                if tl in ('instructions',): continue                 # structural noise
                if tl in ('outcome', 'result'):
                    push(); sub_kind = 'outcome'; continue
                if 'related errors' in tl or 'symptoms' == tl or 'applies when' in tl:
                    push(); sub_kind = 'related_errors'; flags.add('BRANCH_CANDIDATE'); continue
                if METHOD_RE.match(tl):                              # Method 1 / Option A / Alternative
                    push(); buf.append(('p', f'**{text}**')); sub_kind = None; continue
                if ERRHEAD_RE.search(text):                          # error-named heading → implicit-What signal
                    flags.add('BRANCH_CANDIDATE')
                    push(); buf.append(('p', f'**{text}**')); sub_kind = None; continue
                # generic sub-heading inside resolution → keep as a body lead-in
                push(); buf.append(('p', f'**{text}**')); sub_kind = None; continue
            if cur_sec:                                              # sub-heading in other sections
                continue
            continue
        if ln.lower() in NAV_NOISE: continue
        # provenance capture (TDClient/SNOW chrome — outside content sections)
        if cur_sec is None:
            lo = ln.lower()
            if lo.startswith('article id'): pending_meta = 'article_id'; continue
            if lo == 'modified': pending_meta = 'modified'; continue
            if pending_meta:
                meta[pending_meta] = ln; pending_meta = None; continue
            continue
        xm = re.match(r'@@X(\d+)@@', ln)
        if xm:
            buf.append(('extra', int(xm.group(1)))); continue
        im = re.match(r'@@IMG@@\s*(.*)', ln)
        if im:
            buf.append(('p', f'[image: {im.group(1).strip() or "no alt"}]'))
            flags.add('CONTENT_DROPPED'); continue
        m = re.match(r'@@LI@@\s*(.*)', ln)
        if m:
            if m.group(1).strip(): buf.append(('li', m.group(1).strip()))
        else:
            buf.append(('p', ln))
    push()

    # FALLBACK: no KCS heading ever matched → headless article. Re-walk with
    # everything under `resolution`, unclassified headings as bold lead-ins.
    if not chunks:
        flags.add('SECTIONS_INFERRED')
        cur_sec, cur_sub, sub_kind, buf = 'resolution', None, None, []
        for ln in lines:
            hm = re.match(r'@@H(\d)@@\s*(.*)', ln)
            if hm:
                text = hm.group(2).strip()
                if not text or text.lower() in NAV_NOISE: continue
                if classify_heading(text) == 'STOP':
                    push(); cur_sec = None; continue
                if cur_sec: push(); buf.append(('p', f'**{text}**'))
                continue
            if cur_sec is None or ln.lower() in NAV_NOISE: continue
            xm = re.match(r'@@X(\d+)@@', ln)
            if xm: buf.append(('extra', int(xm.group(1)))); continue
            im = re.match(r'@@IMG@@\s*(.*)', ln)
            if im:
                buf.append(('p', f'[image: {im.group(1).strip() or "no alt"}]'))
                flags.add('CONTENT_DROPPED'); continue
            m = re.match(r'@@LI@@\s*(.*)', ln)
            if m:
                if m.group(1).strip(): buf.append(('li', m.group(1).strip()))
            else:
                buf.append(('p', ln))
        push()

    # assemble
    art = {'title': title}
    secs = {}
    tabs = []               # platform tabs under resolution
    res_pre = []            # resolution blocks before platform tabs
    outcome_of = {}         # platform -> outcome text
    for sec, sub, kind, b in chunks:
        if sec == 'resolution' and sub:
            blocks = flush_blocks(b, flags)
            if kind == 'outcome':
                text = " ".join(x.get('body','') for x in blocks if 'body' in x).strip()
                if text: outcome_of[sub] = text
            else:
                existing = next((t for t in tabs if t['label'] == sub), None)
                if existing: existing['content'] += blocks
                else: tabs.append({'label': sub, 'content': blocks})
        elif sec == 'resolution':
            blocks = flush_blocks(b, flags)
            if kind == 'outcome':
                if blocks: res_pre.append({'callout': {'kind':'tip','title':'Outcome','text': " ".join(x.get('body','') for x in blocks if 'body' in x)}})
            else:
                res_pre += blocks
        else:
            secs.setdefault(sec, [])
            secs[sec] += flush_blocks(b, flags)
    for t in tabs:
        if t['label'] in outcome_of:
            t['content'].append({'callout': {'kind':'tip','title':'Outcome','text': outcome_of[t['label']]}})
    # drop a platform-TOC list that just names the tabs
    labels = {t['label'].lower() for t in tabs}
    if labels:
        res_pre = [b for b in res_pre if not ('list' in b and {i.lower().rstrip(':') for i in b['list']} <= labels)]
    resolution = res_pre + ([{'tabs': tabs}] if tabs else [])
    if resolution: secs['resolution'] = resolution

    # merge adjacent steps blocks (each "Step N" paragraph parses alone)
    def merge_steps(blocks):
        out=[]
        for b in blocks:
            if 'steps' in b and out and 'steps' in out[-1]: out[-1]['steps'] += b['steps']
            else:
                if 'tabs' in b:
                    for tb in b['tabs']: tb['content']=merge_steps(tb['content'])
                out.append(b)
        return out
    for k in list(secs): secs[k]=merge_steps(secs[k])

    # dedup consecutive identical bodies (print views often duplicate Summary)
    for k, blocks in secs.items():
        seen, out = set(), []
        for b in blocks:
            key = str(b)[:160]
            if 'body' in b and key in seen: continue
            seen.add(key); out.append(b)
        secs[k] = out

    # ── Phase 4: features + layout (deterministic) ────────────────────────────
    def count(blocks, key):
        n = 0
        for b in blocks:
            if key in b: n += len(b[key]) if isinstance(b[key], list) else 1
            for sub in (b.get('tabs') or []):
                n += count(sub.get('content', []), key)
        return n
    steps_n  = sum(count(v, 'steps') for v in secs.values())
    tables_n = sum(count(v, 'table') for v in secs.values())
    platforms = len(tabs)
    questions = 0                       # mechanical pass commits no branches
    features = {'questions': questions, 'tables': tables_n, 'platforms': platforms, 'steps': steps_n}
    layout = 'diagnostic' if (questions or secs.get('cause_test')) else \
             ('reference-dense' if (tables_n >= 2 or platforms > 1) else 'linear')

    if not secs.get('resolution'): flags.add('NO_RESOLUTION')

    # actions: ONLY from what the source states (escalation sentences, KB cross-refs, urls)
    actions, seen = [], set()
    def texts(blocks):
        for b in blocks:
            if 'body' in b: yield b['body']
            if 'steps' in b: yield from b['steps']
            if 'callout' in b: yield b['callout'].get('text','')
            for t in (b.get('tabs') or []): yield from texts(t.get('content',[]))
    for txt in [t for v in secs.values() for t in texts(v)]:
        em = ESCAL_RE.search(txt)
        if em and 'escalate' not in seen:
            um = URL_IN.search(txt)
            actions.append({'label': em.group(0).strip().capitalize(),
                            **({'url': um.group(1)} if um else {})})
            seen.add('escalate')
        for xr in XREF_RE.findall(txt):
            key = xr.upper().replace(' ', '')
            if key not in seen:
                actions.append({'label': f'See {xr.upper()}', 'ref': key}); seen.add(key)

    art.update({'layout': layout, 'features': features})
    if meta: art['meta'] = meta                       # provenance: source article id / modified
    for k in ('issue','environment','cause','cause_test','resolution'):
        if secs.get(k): art[k] = {'source': 'heading (mechanical)', 'blocks': secs[k]}
    if actions: art['actions'] = actions
    art['review_flags'] = sorted(flags)
    return {'article': art}

if __name__ == '__main__':
    raw = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
    print(yaml.dump(lift(raw), sort_keys=False, allow_unicode=True, width=100))
