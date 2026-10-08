"""Small helpers shared by the atom recipes (payload_to_deck.py and recipes_more.py)."""
import re

def _num(v): return str(int(v)) if isinstance(v, float) and v.is_integer() and abs(v) < 1e15 else v          # 100.0 reads as 100 (JSON has one number type)
def s(v): v = _num(v); return re.sub(r'\s+', ' ', ', '.join(s(x) for x in v) if isinstance(v, (list, tuple)) else str(v if v is not None else '')).strip()     # a list reads as comma-separated text, not a Python repr
def chunks(xs, n): return [xs[i:i + n] for i in range(0, len(xs), n)] or [[]]
def sentences(t): return [x.strip() for x in re.split(r'(?<=[.!?])\s+', s(t)) if x.strip()]
def http(u): return s(u) if re.match(r'^https?://\S+$', s(u)) else ''

def item_text(it):
    if isinstance(it, str): return s(it)
    lab, txt = s(it.get('label') or it.get('title') or ''), s(it.get('text') or it.get('description') or it.get('action') or '')
    extra = ', '.join(s(it[k]) for k in ('owner', 'due') if it.get(k))
    return ' - '.join(x for x in (lab and f'{lab}:' if lab and txt else lab, txt) if x).replace(': -', ':') + (f' ({extra})' if extra else '')


def list_scenes(b, heading, label):
    items = [item_text(i) for i in (b.get('items') or b.get('steps') or [])]
    pages = chunks([i for i in items if i], 6); out = []
    for n, pg in enumerate(pages):
        h = s(b.get('title')) or heading or label
        out.append(dict(type='bullets', f=dict(heading=h + (f' ({n + 1}/{len(pages)})' if len(pages) > 1 else ''), items=pg)))
    return out
def r_list(label): return lambda b, h: list_scenes(b, h, label)
def stat(v, label): return (s(v), s(label))
