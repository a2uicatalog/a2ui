"""latency_ledger: where one interaction's milliseconds went, drawn from spans and a per-owner budget. Reads a contract v2 DOCUMENT as it is (document=... or its fields at top level: spans, budget, interaction, delivery, audience, total_ms, payload, model, notes) as well as the older flat params.
Input: spans ([{owner, phase, ms, stage_id (or stage), kind, source, cached, category, subject, sensitive}]; owner is server, network, client or model), budget ({total, server, network, client, model} in ms; a missing or unusable value gets the profile default: total 100 (a frame 16.7),
caps 20 / 30 / 50 (a frame 4 / 4 / 8.7); the model has NO default cap: it is shown, not counted), title. Tolerant reader like the rest of the pack: spans that cannot be used (bad owner, phase that does not belong to its owner, ms not a number or below 0, neither a stage name nor a phase) are dropped and counted in a note,
ms is clamped at 60000, at most 60 spans are drawn, a bad delivery / kind / update / payload / budget / total_ms / model usage is left out with a note. A span with no stage name is labelled by its phase. A sensitive span, and every span of a public document, is labelled by its phase only (never stage text) and its ms is rounded to whole ms.
The headline total is total_ms when the document gives it (the owners' excess over it is shown as overlap); the total is judged against the profile total whichever owners were measured, owner caps judge the measured owners only, an owner with no cap (the model) is shown and not counted.
Round 2: a v2 DOCUMENT (document= or an interaction object) is read strictly like the JS core (phase-less span dropped, unknown kind / table+measured estimated, invalid stage_id labelled by phase, every event counted in result['dropped']); a legacy spans= call stays tolerant. A frame is judged on its total only (no owner caps). Any sensitive value but false/absent is sensitive; a public document shows no notes and no model id. No tokens/s when output_includes_thinking is true.
Returns BOTH views, {'owners': Result, 'categories': Result, '_default': 'owners'}: the owners view draws each owner's spend against its OWN cap (an overrun is a red segment past the cap and is said in words; the model is ONE bar of its input / think / output segments on its own scale, with token counts and tokens per second when known) and lists the stages; the categories view carves the
client's render time by Basic Catalog component category. Colour is never the only signal: every bar carries its numbers and an OVER label."""
import math, re
from .common import *
from .waterfall import safe_text
# Constants below are this pack's OWN copy of latency-panel/ledger-contract.json v2 (the pack stays self-contained for export; tests/test_latency.py compares them with the contract when it is present).
OWNERS = ('server', 'network', 'client', 'model'); DEFAULT_CAPS = {'server': 20.0, 'network': 30.0, 'client': 50.0}   # model has NO default cap: shown, not judged
PROFILE_TOTAL, FRAME_TOTAL, FRAME_CAPS = 100.0, 16.7, {'server': None, 'network': None, 'client': None}   # a frame is judged on its TOTAL only: owner caps are null (not judged individually, their time still counts)
CATEGORIES = ('text', 'action', 'media', 'layout', 'input', 'other'); MAX_SPANS, MAX_MS, BUDGET_MAX, MAX_BYTES = 60, 60000.0, 60000.0, 1000000000
PHASES = {'intake': ('server',), 'route': ('server',), 'build': ('server',), 'wrap': ('server',), 'transmit': ('network',), 'parse': ('client',), 'process': ('client',), 'render': ('client',), 'layout': ('client',), 'paint': ('client',), 'decide': ('server', 'client'), 'generate': ('model',), 'other': ('server', 'client', 'model'), 'input': ('model',), 'think': ('model',), 'output': ('model',)}
SOURCES = ('agent', 'page', 'harness', 'table'); DELIVERIES = ('a2ui', 'express', 'express-macro', 'html'); KINDS = ('first', 'update', 'action', 'frame'); UPDATES = ('data_patch', 'in_place_dom', 'refetch', 'none'); SUBJECT_KINDS = ('atom', 'macro', 'component'); AUDIENCES = ('internal', 'public')
SUBJECT_NAME = re.compile(r'^[a-z0-9][a-z0-9_]{0,63}\Z'); STAGE_MAX = 40; STAGE_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 _+().,/-]{0,39}\Z'); UNCOUNTED_WHEN_UNCAPPED = ('model',); KINDS_SPAN = ('measured', 'estimated'); PUBLIC_ROUNDING_MS = 1; MAX_NOTES, NOTE_MAX = 5, 120
MODEL_PHASE_ORDER = ('input', 'think', 'output'); MAX_TOKENS = 10000000; MODEL_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/-]{0,63}\Z'); TOKEN_KEYS = ('input_tokens', 'output_tokens', 'thinking_tokens', 'cached_input_tokens')
OWNER_FILL = {'server': '#4b4acf', 'network': '#007a82', 'client': '#b45f06', 'model': '#8a2b6f'}; OVER = '#cc3f56'; TRACK = '#e3e5ee'
KIND_WORDS = {'first': 'first render', 'update': 'update', 'action': 'action', 'frame': 'one frame'}; UPD_WORDS = {'data_patch': 'data patch', 'in_place_dom': 'in-place DOM patch', 'refetch': 'refetch', 'none': None}
def _whole(ms): return float(math.floor(ms / PUBLIC_ROUNDING_MS + 0.5) * PUBLIC_ROUNDING_MS)
def _hu(x, nd=0): return math.floor(x * 10 ** nd + 0.5) / 10 ** nd                                   # half-up (the contract's rounding rule); Python's round() and format() are half-even
def _f(x, nd=0): return f'{_hu(x, nd):,.{nd}f}'
class NoUsableSpan(ValueError):
    """Raised when no span can be used; carries the reader's `dropped` count (everything readable was counted before refusing) so a cross-reader test can compare it; a refusal has judged = total = 0."""
    def __init__(self, msg, dropped=0): super().__init__(msg); self.dropped = dropped; self.judged = 0.0; self.total = 0.0
def _spans(raw, notes, public=False, strict=False, cnt=None):
    """The usable spans. `strict` (a v2 DOCUMENT) matches the JS core: a span with no phase is dropped, an unknown kind or table+measured is counted and shown as estimated, an invalid stage_id is counted and the phase labels the span, a negative ms is clamped to 0 and counted. `cnt[0]` is the reader's dropped/neutralised count (one per event, like the JS core's dropped_count). A legacy call (strict False) stays tolerant."""
    cnt = cnt if cnt is not None else [0]
    out, bad, clamped, subj_bad, hidden, neg, sens_odd, kind_bad, tbl_bad, cat_bad, src_bad, st_bad, cache_bad, shown_bad = (0,) * 14
    lst = raw if isinstance(raw, list) else []
    if strict and not isinstance(raw, list): cnt[0] += 1
    if strict and len(lst) > MAX_SPANS: cnt[0] += len(lst) - MAX_SPANS; notes.append(f'{len(lst) - MAX_SPANS} spans beyond the {MAX_SPANS}th were not read.'); lst = lst[:MAX_SPANS]
    out = []
    for s in lst:
        if not isinstance(s, dict): bad += 1; cnt[0] += 1; continue
        ms, own = s.get('ms'), s.get('owner'); sv = s.get('sensitive'); sens = not (sv is None or sv is False); ph = s.get('phase'); hide = sens or public        # ANY sensitive value other than exactly false/absent is sensitive (fail closed)
        if own not in OWNERS: bad += 1; cnt[0] += 1; continue
        if strict:
            if not isinstance(ph, str) or ph not in PHASES or own not in PHASES[ph]: bad += 1; cnt[0] += 1; continue
        elif ph is not None and (not isinstance(ph, str) or ph not in PHASES or own not in PHASES[ph]): bad += 1; cnt[0] += 1; continue
        if not _fin(ms) or (ms < 0 and not strict): bad += 1; cnt[0] += 1; continue
        if ms < 0: neg += 1; cnt[0] += 1; ms = 0
        if sens and sv is not True: sens_odd += 1; cnt[0] += 1
        sid = s.get('stage_id'); stage_ok = None
        if strict and sid is not None and not hide: 
            if isinstance(sid, str) and STAGE_PATTERN.match(sid): stage_ok = sid; name = safe_text(sid, STAGE_MAX, '') or ''
            else: st_bad += 1; cnt[0] += 1; name = ''                                                     # an invalid stage_id: the phase labels the span
        else: name = safe_text(sid if sid not in (None, '') else s.get('stage'), STAGE_MAX, '') or ''        # what a public document or a sensitive span hides is hidden SILENTLY: not validated, not counted (public_hides_are_silent)
        subj = s.get('subject'); sj = None; sj_ok = False
        if subj is not None and not (strict and sens):
            if isinstance(subj, dict) and subj.get('kind') in SUBJECT_KINDS and isinstance(subj.get('name'), str) and SUBJECT_NAME.match(subj['name']): sj_ok = True; sj = f"{subj['kind']}:{subj['name']}"
            elif strict or not sens: subj_bad += 1; cnt[0] += strict
        if sens: sj = None
        if hide: hidden += bool(name); label = ph or 'other'                               # stage text of a sensitive span or of a public document is never shown
        elif name or ph: label = name or ph                                                  # no stage name: the phase labels the span
        else: bad += 1; cnt[0] += 1; continue
        if ms > MAX_MS: clamped += 1; cnt[0] += 1
        v = min(float(ms), MAX_MS); v = _whole(v) if hide else v
        cat = s.get('category') if s.get('category') in CATEGORIES else None; src = s.get('source') if s.get('source') in SOURCES else None
        k = s.get('kind'); est = k == 'estimated' or src == 'table'
        if strict:
            if s.get('category') is not None and cat is None: cat_bad += 1; cnt[0] += 1
            if s.get('source') is not None and src is None: src_bad += 1; cnt[0] += 1
            if k is not None and k not in KINDS_SPAN: kind_bad += 1; cnt[0] += 1; est = True       # an unknown kind is never shown as measured
            elif src == 'table' and k != 'estimated': tbl_bad += 1; cnt[0] += 1; est = True          # table + measured: counted, shown as estimated
            if s.get('cached') is not None and not isinstance(s.get('cached'), bool): cache_bad += 1; cnt[0] += 1
        out.append(dict(stage=label, label=label, mkey=ph or label if own == 'model' else label, owner=own, ms=v, cached=s.get('cached') is True, category=cat, est=est, whole=hide, phase=ph, source=src, subject=sj, sensitive=sens))
    if bad: notes.append(f'{bad} spans were left out (owner must be server, network, client or model; a phase must belong to its owner; ms a finite number of at least 0; a stage name or a phase).')
    if neg: notes.append(f'{neg} negative ms values were drawn as 0 ms.')
    if sens_odd: notes.append(f'{sens_odd} spans had a sensitive flag that was not true or false, so they are read as sensitive.')
    if kind_bad: notes.append(f'{kind_bad} spans had an unknown kind, so they are shown as estimated.')
    if tbl_bad: notes.append(f'{tbl_bad} table spans were marked measured, so they are shown as estimated.')
    if cat_bad: notes.append(f'{cat_bad} span categories were not known, so they are ignored.')
    if src_bad: notes.append(f'{src_bad} span sources were not known, so they are ignored.')
    if st_bad: notes.append(f'{st_bad} stage ids were not valid, so the phase is shown instead.')
    if cache_bad: notes.append(f'{cache_bad} cached flags were not true or false, so they are ignored.')
    if shown_bad: notes.append(f'{shown_bad} spans carried a stage id or subject that is never shown (public document or sensitive span).')
    if subj_bad: notes.append(f'{subj_bad} span subjects were ignored (a subject is {{kind: atom, macro or component; name: lower-case letters, digits and _}}).')
    if clamped: notes.append(f'{clamped} spans longer than {MAX_MS:.0f} ms are drawn as {MAX_MS:.0f} ms.')
    if hidden: notes.append(f'{hidden} stage names were not shown (never shown for a sensitive span or in a public document; the phase is shown instead).')
    if len(out) > MAX_SPANS: notes.append(f'{len(out) - MAX_SPANS} spans beyond the {MAX_SPANS}th were not drawn.'); cnt[0] += len(out) - MAX_SPANS; out = out[:MAX_SPANS]
    return out
def _caps(raw, notes, frame=False, cnt=None):
    """{owner: cap or None}; a frame has no owner caps (judged on its total only); the model has a cap only if the budget gives one."""
    cnt = cnt if cnt is not None else [0]
    caps, bad = {**(FRAME_CAPS if frame else DEFAULT_CAPS), 'model': None}, []
    for o in OWNERS:
        v = raw.get(o) if isinstance(raw, dict) else None
        if v is None: continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (v == v) or v <= 0 or v > BUDGET_MAX: bad.append(o); cnt[0] += 1
        else: caps[o] = float(v)
    if bad: notes.append(f"The budget for {', '.join(bad)} was not a number above 0, so the default is used" + (' (no cap for the model).' if 'model' in bad else '.'))
    return caps
def _ms(v): return _f(v, 0) if v >= 10 else _f(v, 1)
def _cap(v): return _f(v, 0) if abs(v - math.floor(v + 0.5)) < 1e-9 else _f(v, 1)          # a cap or budget is shown with one decimal when it is not a whole number (16.7)
def _kb(b): return f'{b} B' if b < 1024 else _f(b / 1024, 0 if b >= 10240 else 1) + ' KB'
def _isint(v):
    """A whole number as the JS core reads it: an int, or a float with no fraction (JSON 1.0 and -0.0 are whole numbers; -0 is 0)."""
    return (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, float) and math.isfinite(v) and v == math.floor(v))
def _fin(v):
    """True when v is a finite real number (not a bool); a Python int too big for a float (JSON 1e400 parses to Infinity in JS) is NOT finite, never an OverflowError."""
    if isinstance(v, bool) or not isinstance(v, (int, float)): return False
    try: return math.isfinite(float(v))
    except OverflowError: return False
def _tag(delivery, kind, update, payload, notes, cnt=None):
    """The tag line (delivery, kind, update mechanism, payload) from VALIDATED values; a value outside its list is dropped with a note."""
    given = {'delivery': (delivery, DELIVERIES), 'kind': (kind, KINDS), 'update': (update, UPDATES)}; ok = {}
    for k, (v, allowed) in given.items():
        if v is None: continue
        if isinstance(v, str) and v in allowed: ok[k] = v
        else: notes.append(f'The {k} was not one of {", ".join(allowed)}, so it is left out.')
    pl = None; cnt = cnt if cnt is not None else [0]
    if isinstance(payload, dict): cnt[0] += sum(1 for k in ('bytes', 'gzip_bytes') if payload.get(k) is not None and not (_isint(payload[k]) and 0 <= payload[k] <= MAX_BYTES))       # one count per unusable size, like the JS core
    if payload is not None:
        if isinstance(payload, dict) and _isint(payload.get('bytes')) and 0 <= payload['bytes'] <= MAX_BYTES:
            g = payload.get('gzip_bytes'); pl = {'bytes': int(payload['bytes']), 'gzip_bytes': int(g) if _isint(g) and 0 <= g <= MAX_BYTES else None}
            if g is not None and pl['gzip_bytes'] is None: notes.append('The payload gzip size was not an integer of at least 0, so it is left out.')
        else: notes.append('The payload was not {bytes, gzip_bytes} with whole numbers of at least 0, so it is left out.')
    parts = []
    if 'delivery' in ok: parts.append(ok['delivery'])
    upd = UPD_WORDS.get(ok.get('update')); kw = KIND_WORDS.get(ok.get('kind'))
    if kw or upd: parts.append((kw or 'update') + (f' via {upd}' if upd else ''))
    if pl: parts.append('payload ' + _kb(pl['bytes']) + (f" ({_kb(pl['gzip_bytes'])} gzip)" if pl['gzip_bytes'] is not None else ''))
    return ' · '.join(parts), ok
def from_document(doc):
    """Pack-local adapter: the macro's parameters from a contract v2 document (interaction.kind / interaction.update, delivery, audience, total_ms, payload, budget, model, spans, version, notes). Values are returned RAW: the macro validates and counts them."""
    d = doc if isinstance(doc, dict) else {}; ix = d.get('interaction') if isinstance(d.get('interaction'), dict) else {}
    return dict(spans=d.get('spans'), budget=d.get('budget'), version=d.get('version'), delivery=d.get('delivery'), kind=ix.get('kind'), update=ix.get('update'), payload=d.get('payload'), audience=d.get('audience'), total_ms=d.get('total_ms'), model=d.get('model'), clock=d.get('clock'), notes=d.get('notes'))
def _total_ms(v, notes, strict=False, cnt=None):
    cnt = cnt if cnt is not None else [0]
    if v is None: return None
    if not _fin(v) or (v < 0 and not strict): cnt[0] += 1; notes.append('The total_ms was not a number of at least 0, so the total is the sum of the spans.'); return None
    if v < 0: cnt[0] += 1; notes.append('The total_ms was negative, so it is read as 0.'); return 0.0
    if v > MAX_MS: cnt[0] += 1; notes.append(f'The total_ms is longer than {MAX_MS:.0f} ms, so it is drawn as {MAX_MS:.0f} ms.')
    return min(float(v), MAX_MS)
def _usage(raw, notes, cnt=None, public=False):
    """Model usage {id?, input_tokens, output_tokens, thinking_tokens, cached_input_tokens, output_includes_thinking} (flat, or the agent's event form with a `usage` object); bad values are dropped with a note, nothing is guessed."""
    cnt = cnt if cnt is not None else [0]
    if raw is None: return {}
    if not isinstance(raw, dict): cnt[0] += 1; notes.append('The model usage was not an object, so it is left out.'); return {}
    src = {**(raw['usage'] if isinstance(raw.get('usage'), dict) else {}), **raw}; out, bad = {}, 0
    for k in TOKEN_KEYS:
        v = src.get(k)
        if v is None: continue
        if _isint(v) and 0 <= v <= MAX_TOKENS: out[k] = int(v)
        else: bad += 1
    mid = src.get('id')
    if mid is not None and not public:                                                                  # a public document hides the id silently (an invalid one too: not counted)
        if isinstance(mid, str) and MODEL_ID.match(mid): out['id'] = mid
        else: bad += 1
    oi = src.get('output_includes_thinking')
    if oi is not None:
        if isinstance(oi, bool): out['output_includes_thinking'] = oi
        else: bad += 1
    cnt[0] += bad
    if bad: notes.append(f'{bad} model usage values were left out (token counts are whole numbers from 0 to {MAX_TOKENS:,}; the model id is letters, digits and . _ : / -; output_includes_thinking is true or false).')
    return out
def _usage_line(u, rate, nobreak=False):
    """'output 340 tokens · 38 tok/s' style text from the usage that is known; '' when none is. When the output count includes thinking it says so and carries no rate; when the provider gave no breakdown it says that."""
    t = lambda n: f'{n:,}'; p = []
    if 'input_tokens' in u: p.append(f"input {t(u['input_tokens'])} tokens")
    if 'thinking_tokens' in u: p.append(f"thinking {t(u['thinking_tokens'])} tokens")
    if 'output_tokens' in u: p.append(f"output {t(u['output_tokens'])} tokens" + (' (incl. thinking)' if u.get('output_includes_thinking') is True else ''))
    if rate is not None: p.append(f'{_f(rate, 0 if rate >= 10 else 1)} tok/s')
    if 'cached_input_tokens' in u: p.append(f"cached {t(u['cached_input_tokens'])} tokens")
    if nobreak: p.append('provider gave no breakdown')
    return ' · '.join(p)
def latency_ledger(spans=None, budget=None, title='', version=None, delivery=None, kind=None, update=None, payload=None, interaction=None, audience=None, total_ms=None, model=None, document=None, clock=None, notes=None):
    notes_out = []; cnt = [0]; ttl = safe_text(title, 80, '') or ''; nts = notes_out
    d = from_document(document) if isinstance(document, dict) else {}
    if document is not None and not isinstance(document, dict): nts.append('The document was not an object, so it is ignored.')
    ix = interaction if isinstance(interaction, dict) else {}
    if interaction is not None and not isinstance(interaction, dict): nts.append('The interaction was not an object, so it is ignored.')
    pick = lambda a, b: a if a is not None else b
    spans, budget, version, delivery = pick(spans, d.get('spans')), pick(budget, d.get('budget')), pick(version, d.get('version')), pick(delivery, d.get('delivery'))
    kind, update = pick(kind, pick(ix.get('kind'), d.get('kind'))), pick(update, pick(ix.get('update'), d.get('update')))
    payload, audience, total_ms, model, clock, doc_notes = pick(payload, d.get('payload')), pick(audience, d.get('audience')), pick(total_ms, d.get('total_ms')), pick(model, d.get('model')), pick(clock, d.get('clock')), pick(notes, d.get('notes'))
    if isinstance(version, (int, float)) and not isinstance(version, bool) and _fin(version) and version > 2: nts.append(f'Contract version {min(version, 10**9):g} is newer than this reader knows (2); what it understands is drawn.')
    if isinstance(document, dict) and not (_fin(version) and version == 2): cnt[0] += 1; (nts.append('The version was not 2, so it is read as version 2.') if not (_fin(version) and version > 2) else None)      # document_detection: a document is read whatever its version; a version other than 2 is counted once
    if clock is not None and clock != 'duration': nts.append('The clock was not "duration"; the spans are read as durations.')
    strict = isinstance(document, dict) or isinstance(interaction, dict)      # a v2 DOCUMENT (document=, or its top-level fields with an interaction object) is read strictly (parity with the JS core); a legacy spans= call stays tolerant
    public = audience == 'public'
    if audience is not None and audience not in AUDIENCES: public = True; cnt[0] += 1; nts.append('The audience was not internal or public, so it is drawn as public (no stage names, whole milliseconds).')
    tag, okv = _tag(delivery, kind, update, payload, nts, cnt)
    sp = _spans(spans, nts, public, strict, cnt)
    frame = okv.get('kind') == 'frame'; caps = _caps(budget, nts, frame, cnt); ptotal = FRAME_TOTAL if frame else PROFILE_TOTAL
    bt = budget.get('total') if isinstance(budget, dict) else None
    if bt is not None:
        if isinstance(bt, bool) or not isinstance(bt, (int, float)) or not (bt == bt) or bt <= 0 or bt > BUDGET_MAX: nts.append('The budget total was not a number above 0, so the default is used.')
        else: ptotal = float(bt)
        if isinstance(bt, bool) or not isinstance(bt, (int, float)) or not (bt == bt) or bt <= 0 or bt > BUDGET_MAX: cnt[0] += 1
    tm = _total_ms(total_ms, nts, strict, cnt); tm = _whole(tm) if tm is not None and public else tm; usage = _usage(model, nts, cnt, public)
    if public: usage.pop('id', None)                                                                    # a public document carries no model id (a fine-tune name can leak): never shown or hashed
    if doc_notes is not None and not public:                                                            # the document's own notes (plain text); a public document's notes are never read, shown or hashed
        if not isinstance(doc_notes, list): cnt[0] += 1; nts.append('The notes were not a list, so they are left out.')
        else:
            got = []
            for x in doc_notes:
                if not isinstance(x, str): cnt[0] += 1; continue
                t = safe_text(x, NOTE_MAX, '')
                if t: got.append(t)
            if len(got) > MAX_NOTES: cnt[0] += len(got) - MAX_NOTES
            nts.extend(got[:MAX_NOTES])
    if not sp: raise NoUsableSpan('there must be at least one usable span', cnt[0])                       # refused: judged and total are 0, and everything readable above was counted first
    has = {o: any(x['owner'] == o for x in sp) for o in OWNERS}; shown = [o for o in OWNERS if o != 'model' or has['model']]; used = {o: sum(s['ms'] for s in sp if s['owner'] == o) for o in OWNERS}; S = sum(used.values())
    if not has['model']: used = {o: v for o, v in used.items() if o != 'model'}                      # 'used' gains model only when present
    if usage and not has['model']: nts.append('Model usage was given but no span belongs to the model, so it is not drawn.')
    mod = used.get('model', 0.0); free = sum(used.get(o, 0.0) for o in UNCOUNTED_WHEN_UNCAPPED if has[o] and caps[o] is None)
    total = tm if tm is not None else S; overlap = max(0.0, S - tm) if tm is not None else 0.0; unacc = max(0.0, tm - S) if tm is not None else 0.0; judged = max(0.0, total - free)   # an uncapped model is shown, never judged
    mcap = caps['model'] if has['model'] else None
    btotal = ptotal + (mcap or 0.0)                                                                  # the total is judged against the profile total whichever owners were measured; a model that took part AND has a cap counts in the judged total and the budget is profile total + model cap (total_budget_rule)
    capped = [o for o in shown if has[o] and caps[o] is not None]
    over = sorted(((o, used[o] - caps[o], max((s for s in sp if s['owner'] == o), key=lambda s: s['ms'])['label']) for o in capped if used[o] > caps[o]), key=lambda x: -x[1])
    tover = judged > btotal; inside = not over and not tover
    out_ms = sum(s['ms'] for s in sp if s['owner'] == 'model' and s['phase'] == 'output'); out_est = any(s['est'] for s in sp if s['owner'] == 'model' and s['phase'] == 'output'); think_ran = any(s['owner'] == 'model' and s['phase'] == 'think' for s in sp)
    rate = usage['output_tokens'] / (out_ms / 1000) if has['model'] and 'output_tokens' in usage and out_ms > 0 and not out_est and usage.get('output_includes_thinking') is not True else None   # tokens per second only from a measured output time and a known token count, and NEVER when output_includes_thinking is true (even with no think phase measured: thinking ran, the rate would be overstated)
    mseg = [(k, v) for k, v, _ in _segments(sp)['model']] if has['model'] else []
    nobreak = has['model'] and bool(mseg) and all(k in ('generate', 'other') for k, _ in mseg) and any(k == 'generate' for k, _ in mseg)       # only the coarse span: the provider gave no breakdown
    uline = _usage_line(usage, rate, nobreak) if has['model'] else ''; mid = usage.get('id') if has['model'] else None
    mdesc = (f'Model time {_ms(mod)} ms' + (': ' + ', '.join(f'{k} {_ms(v)} ms' for k, v in mseg) if mseg else '') + (f' ({uline})' if uline else '') + '.') if has['model'] else ''
    head = ttl or 'Latency ledger'
    def part(o):
        if not has[o]: return f'{o} not measured'
        return f'{o} {_ms(used[o])} of {_cap(caps[o])}' if caps[o] is not None else f'{o} {_ms(used[o])} ({"not judged on its own" if frame and o != "model" else "no cap set"})'
    summary = (f'{tag}. ' if tag else '') + (f'Total {_ms(total)} ms (model {_ms(mod)} · rest {_ms(max(0.0, total - mod))}). ' if has['model'] else '') + f'{_ms(judged)} ms of a {_cap(btotal)} ms budget' + (f' (profile {_cap(ptotal)} ms + model cap {_cap(mcap)} ms)' if mcap is not None else '') + (f' (the model time, {_ms(free)} ms, is shown but not counted)' if free else '') + ': ' + ', '.join(part(o) for o in shown) + '. ' + ('Over budget: ' + ', '.join(f'{o} by {_ms(x)} ms (largest span: {st})' for o, x, st in over) + '.' if over else ('A frame is judged on its total only; its owners have no cap of their own.' if frame and not capped else 'Every owner is inside its own cap.' if all(has[o] for o in shown) else 'Every measured owner is inside its own cap.'))
    if tover: summary += f' The total is over the {_cap(btotal)} ms budget by {_ms(judged - btotal)} ms' + (' (no owner is over its own cap).' if not over else '.')
    if overlap > 1e-9: summary += f' The owners add up to {_ms(S)} ms, {_ms(overlap)} ms more than the measured total of {_ms(tm)} ms: that is overlap (work that ran at the same time).'
    if unacc > 1e-9: summary += f' {_ms(unacc)} ms of the measured total is in no span.'
    if mdesc: summary += ' ' + mdesc
    def row(s): return f"{s['owner']} {s['label']} {(_f(s['ms']) if s['whole'] else _ms(s['ms']))} ms" + (' (cached)' if s['cached'] else '') + (f" [{s['category']}]" if s['category'] else '') + (f" (phase {s['phase']})" if s['phase'] and s['phase'] != s['label'] else '') + (f" (source {s['source']})" if s['source'] else '') + (f" (subject {s['subject']})" if s['subject'] else '') + (' (sensitive)' if s['sensitive'] else '') + (' (estimated)' if s['est'] else '')
    table = (tag + '; ' if tag else '') + '; '.join(row(s) for s in sp) + (f'; total {_ms(total)} ms' if tm is not None else '') + (f'; overlap {_ms(overlap)} ms' if overlap > 1e-9 else '') + (f'; model usage: {(mid + ": ") if mid else ""}{uline}' if uline or mid else '')
    ctx = dict(frame=frame, nobreak=nobreak, total=total, judged=judged, free=free, mod=mod, overlap=overlap, uline=uline, mid=mid, inside=inside, tover=tover, S=S, mdesc=mdesc)
    r1 = finish('latency_ledger', head, _owners(sp, caps, used, over, head, btotal, has, shown, tag, ctx), summary, table, nts)
    cats = {c: sum(s['ms'] for s in sp if s['owner'] == 'client' and s['category'] == c) for c in CATEGORIES}; cats = {c: v for c, v in cats.items() if v > 0}
    csum = ('Client render time by component category: ' + ', '.join(f'{c} {_ms(v)} ms' for c, v in sorted(cats.items(), key=lambda x: -x[1])) + f' (of {_ms(used["client"])} ms client time).') if cats else 'No client span carries a component category, so there is no category breakdown.'
    r2 = finish('latency_ledger', f'{head}: client render by category', _categories(cats, used['client'], caps['client'], head), csum, table, nts)
    r1['dropped'] = r2['dropped'] = cnt[0]; r1['used'] = used; r2['used'] = used; r1['caps'] = {o: c for o, c in caps.items() if c is not None}; r2['caps'] = r1['caps']; r1['over'] = [o for o, _, _ in over]; r2['over'] = r1['over']
    for r in (r1, r2): r['total'] = total; r['judged'] = judged; r['overlap'] = overlap; r['budget_total'] = btotal
    return {'owners': r1, 'categories': r2, '_default': 'owners'}
def _segments(sp):
    """{owner: [(label, ms, estimated)]} in first-seen order: spans of one owner are merged when they have the same key (a categorised client span merges by its CATEGORY, any other by its STAGE: a stage called 'text' is never merged into the text category; if two keys would show the same label the stage one is shown as 'text (stage)').
    The model's spans merge by PHASE (input, think, output, generate) and come in that order. A segment is estimated if any span in it is."""
    out = {o: {} for o in OWNERS}
    for x in sp:
        key = ('s', x['mkey']) if x['owner'] == 'model' else ('c', x['category']) if x['category'] else ('s', x['label']); d = out[x['owner']]; ms, est = d.get(key, (0.0, False)); d[key] = (ms + x['ms'], est or x['est'])
    res = {}
    for o, d in out.items():
        labels = [k[1] for k in d]; res[o] = [(k[1] if labels.count(k[1]) == 1 or k[0] == 'c' else f'{k[1]} (stage)', v[0], v[1]) for k, v in d.items()]
    order = MODEL_PHASE_ORDER + ('generate', 'other'); res['model'].sort(key=lambda t: order.index(t[0]) if t[0] in order else len(order))
    return res
def _num(cx, cy, n, fill): return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="{fill}"/>' + label(cx, cy + 4.5, str(n), 12, 'middle', text_on(fill), 700)
def _owners(sp, caps, used, over, head, btotal, has, shown, tag, ctx):
    """ONE stacked bar chart: a row per owner, its bar cut into that owner's segments (the client's by component category), the cap drawn as a line, the part past the cap marked in red AND in words, a legend with every segment's ms.
    The model row is one bar of its phase segments on its OWN scale (labelled 'bar not to scale' when it is not to the scale of the rest), with its token counts and tokens per second under the legend when known."""
    total, tj, free, mod, overlap, uline, mid = ctx['total'], ctx['judged'], ctx['free'], ctx['mod'], ctx['overlap'], ctx['uline'], ctx['mid']
    seg = _segments(sp); keys = []; val = {(o, k): (v, est) for o in shown for k, v, est in seg[o]}
    for o in shown:
        for k, _, _ in seg[o]:
            if (o, k) not in keys: keys.append((o, k))
    colour = {}
    for o in shown:                                                                                   # one hue per owner (the same as everywhere), a lighter tint for each further segment, so a colour says WHO and the label says WHAT
        ks = [k for ow, k in keys if ow == o]
        for j, k in enumerate(ks):
            c = blend(OWNER_FILL[o], 0.55 * j / max(1, len(ks) - 1) if len(ks) > 1 else 0.0); colour[(o, k)] = blend(c, 0.5) if val[(o, k)][1] else c       # an estimated segment is the same hue, lighter, and outlined
    nr = len(shown); rows = (len(keys) + 1) // 2; mline = bool(uline or mid or ctx['nobreak']); L, T, BW = 110, 74 + (18 if tag else 0), 360; w, h = 760, T + 46 + 38 * (nr + 1) + 48 + 24 * rows + 24 + (24 if mline else 0)
    sj = ctx['S'] - free; base = max(tj, sj, *[used[o] for o in shown if caps[o] is not None or o != 'model'], 1e-9); scale = BW / max(base, min(btotal, max(100.0, 4 * base))); mscale = min(scale, 300 / max(mod, 1e-9))
    headline = f'Total {_ms(total)} ms (model {_ms(mod)} · rest {_ms(max(0.0, total - mod))})' if has['model'] else f'Total {_ms(total)} ms of {_cap(btotal)} ms budget'
    b = label(w / 2, 32, head, 22, 'middle', INK, 700) + label(w / 2, 54, headline, 14, 'middle', MUTED) + (label(w / 2, 72, tag, 13, 'middle', MUTED) if tag else '')
    for i, o in enumerate(shown):
        y = T + 38 * i; cap = caps[o]; capw = min((cap or 0.0) * scale, float(BW)); offs = cap is not None and cap * scale > BW; own = mscale if o == 'model' and cap is None else scale
        b += _num(24, y + 11, i + 1, OWNER_FILL[o]) + label(L - 10, y + 17, o.capitalize(), 14, 'end', INK, 700) + (f'<rect x="{L}" y="{y}" width="{capw:.2f}" height="22" rx="4" fill="{TRACK}"/>' if cap is not None else '')
        x = float(L)
        for k, v, est in seg[o]:
            sw = v * own; b += f'<rect x="{x:.2f}" y="{y}" width="{max(sw, 0.5):.2f}" height="22" fill="{colour[(o, k)]}" ' + (f'stroke="{INK}" stroke-width="1"/>' if est else 'stroke="#ffffff" stroke-width="1"/>')
            if sw >= 58: b += label(x + sw / 2, y + 16, k if len(k) * 7 < sw else k[:max(1, int(sw / 7) - 1)] + '.', 12, 'middle', text_on(colour[(o, k)]), 700)
            x += sw
        if cap is not None: b += f'<line x1="{L + capw:.2f}" y1="{y - 3}" x2="{L + capw:.2f}" y2="{y + 25}" stroke="{INK}" stroke-width="2"/>'
        if cap is not None and used[o] > cap: b += f'<rect x="{L + capw:.2f}" y="{y + 24}" width="{min((used[o] - caps[o]) * scale, BW):.2f}" height="4" fill="{OVER}"/>'
        ov = cap is not None and used[o] > cap
        b += label(L + capw + 10, y + 17, (f'not measured (cap {_cap(cap)} ms)' if cap is not None else 'not measured'), 13, 'start', MUTED) if not has[o] else label(L + max(capw, used[o] * own) + 10, y + 17, (f'{_ms(used[o])} of {_cap(cap)} ms' + (f' · cap {_f(cap)} ms (off scale)' if offs else '') if cap is not None else f'{_ms(used[o])} ms · ' + ('not judged on its own' if ctx['frame'] and o != 'model' else 'no cap set') + (' · bar not to scale' if mscale < scale else '')) + (f' · OVER by {_ms(used[o] - cap)} ms' if ov else ''), 13, 'start', OVER if ov else MUTED, 700 if ov else 400)
    y = T + 38 * nr + 6; ow = min(btotal * scale, float(BW))                                                           # the total: every owner's segments end to end against the profile total, on the same scale as the rows above (an uncapped model is left out)
    b += f'<line x1="{L - 100}" y1="{y - 9}" x2="{w - 20}" y2="{y - 9}" stroke="{TRACK}" stroke-width="1"/>' + _num(24, y + 11, nr + 1, INK) + label(L - 10, y + 17, 'Total', 14, 'end', INK, 700) + f'<rect x="{L}" y="{y}" width="{ow:.2f}" height="22" rx="4" fill="{TRACK}"/>'
    x = float(L)
    for o, k in (kk for kk in keys if not (kk[0] == 'model' and caps['model'] is None)):
        sw = val[(o, k)][0] * scale; b += f'<rect x="{x:.2f}" y="{y}" width="{max(sw, 0.5):.2f}" height="22" fill="{colour[(o, k)]}" ' + (f'stroke="{INK}" stroke-width="1"/>' if val[(o, k)][1] else 'stroke="#ffffff" stroke-width="1"/>'); x += sw
    b += f'<line x1="{L + ow:.2f}" y1="{y - 3}" x2="{L + ow:.2f}" y2="{y + 25}" stroke="{INK}" stroke-width="2"/>'
    if tj > btotal: b += f'<rect x="{L + ow:.2f}" y="{y + 24}" width="{min((tj - btotal) * scale, BW):.2f}" height="4" fill="{OVER}"/>'
    b += label(L + max(ow, tj * scale, sj * scale) + 10, y + 17, f'{_ms(tj)} of {_cap(btotal)} ms' + (f' · budget {_f(btotal)} ms (off scale)' if btotal * scale > BW else '') + (f' · OVER by {_ms(tj - btotal)} ms' if tj > btotal else ''), 13, 'start', OVER if tj > btotal else INK, 700)
    tx = L + tj * scale; b += f'<line x1="{tx:.2f}" y1="{y - 3}" x2="{tx:.2f}" y2="{y + 30}" stroke="{INK}" stroke-width="2"/><polygon points="{tx - 6:.2f},{y + 36} {tx + 6:.2f},{y + 36} {tx:.2f},{y + 28}" fill="{INK}"/>' + label(min(max(tx, L + 70), w - 110), y + 52, f'Total taken: {_ms(tj)} ms' + (' (without the model)' if free else '') + (f' · overlap {_ms(overlap)} ms' if overlap > 1e-9 else ''), 15, 'middle', INK, 700)       # the marker at the END of the filled part: how long it actually took, apart from the cap line
    y0 = T + 38 * (nr + 1) + 52; b += label(L - 10, y0, 'Made up of', 14, 'end', INK, 700)
    for n, (o, k) in enumerate(keys):
        cx = L + (n % 2) * 300; y = y0 + 24 * (n // 2); v, est = val[(o, k)]; b += _num(cx + 9, y - 4, shown.index(o) + 1, colour[(o, k)]) + label(cx + 24, y, k, 13, 'start', INK, 700) + (label(cx + 28 + 7 * len(k), y, 'est.', 12, 'start', MUTED) if est else '') + label(cx + 280, y, f'{_ms(v)} ms', 13, 'end', MUTED)
    if mline: b += label(L, y0 + 24 * rows, 'Model' + (f' {mid}' if mid else '') + (': ' + uline if uline else ''), 13, 'start', INK, 700)
    state = 'over budget: ' + ', '.join(o for o, _, _ in over) if over else ('total over the budget' if ctx['tover'] else 'inside the frame budget' if ctx['frame'] and not any(caps[o] is not None for o in shown) else 'inside every cap')
    return svg(b, f'Latency ledger: {_ms(total)} ms' + (f' (model {_ms(mod)} · rest {_ms(max(0.0, total - mod))})' if has['model'] else '') + f', {_ms(tj)} ms of {_cap(btotal)} counted; {state}' + (f'. {ctx["mdesc"]}' if has['model'] else ''), w, h)
def _categories(cats, client_ms, client_cap, head):
    rows = sorted(cats.items(), key=lambda x: -x[1]); w, h = 720, 120 + 36 * max(1, len(rows)); L, T, BW = 110, 74, 330; b = label(w / 2, 32, head + ': client render', 20, 'middle', INK, 700)
    b += label(w / 2, 54, (f'{_ms(client_ms)} ms of the {_cap(client_cap)} ms client cap' if client_cap is not None else f'{_ms(client_ms)} ms of client time (no client cap: judged on the total)'), 14, 'middle', MUTED)
    if not rows: return svg(b + label(w / 2, 150, 'No client span has a component category.', 15, 'middle', MUTED), 'No category breakdown', w, 200)
    scale = BW / max(v for _, v in rows)
    for i, (c, v) in enumerate(rows):
        y = T + 36 * i; b += label(L - 10, y + 17, c.capitalize(), 14, 'end', INK, 700) + f'<rect x="{L}" y="{y}" width="{max(2.0, v * scale):.2f}" height="22" rx="4" fill="{PAL[i % len(PAL)]}"/>' + label(L + max(2.0, v * scale) + 10, y + 17, f'{_ms(v)} ms · {_f(100 * v / client_ms)}% of client', 13, 'start', MUTED)
    return svg(b, f'Client render time by category: ' + ', '.join(f'{c} {_ms(v)} ms' for c, v in rows), w, h)
